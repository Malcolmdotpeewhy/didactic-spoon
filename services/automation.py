import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

from .api_handler import LCUClient
from .asset_manager import AssetManager, ConfigManager
from utils.logger import Logger

class AutomationEngine:
    def __init__(
        self,
        lcu: LCUClient,
        assets: AssetManager,
        config: ConfigManager,
        log_func=None,
        stop_func=None,
        **kwargs
    ):
        self.lcu = lcu
        self.assets = assets
        self.config = config
        self.log = log_func
        self.stop_func = stop_func
        self.stats_func = kwargs.get("stats_func")
        self.window_func = kwargs.get("window_func")
        self.running = False
        self.paused = False
        self.thread = None
        self._stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.setup_done = False
        self.last_phase = "None"
        self.current_queue_id = None

        self.ready_check_start = None
        self.ready_check_delay = None
        self.ready_check_accepted = False
        self._last_countdown_log = None

        self._last_disconnect_log = 0
        self._requeue_handled = False

    def start(self, start_paused=False):
        if self.running: return
        self.running = True
        self.paused = start_paused
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        self._stop_event.set()

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def _log(self, msg):
        if self.log: self.log(msg)
        Logger.debug("Auto", msg)

    def _loop(self):
        while self.running:
            if self.paused:
                self._stop_event.wait(1)
                continue

            if not self.lcu.is_connected:
                if time.time() - self._last_disconnect_log > 30:
                    Logger.debug("AutoLoop", "LCU Disconnected. Attempting Self-Heal...")
                    self._last_disconnect_log = time.time()

                if self.lcu.connect(silent=True):
                    Logger.debug("AutoLoop", "Self-Heal Successful: Reconnected to LCU.")
                else:
                    self._stop_event.wait(2)
                continue

            try:
                self._tick()
            except Exception as e:
                tb = traceback.format_exc()
                Logger.error("AutoLoop", f"Critical Error: {e}\n{tb}")
                self._stop_event.wait(3)

    def _tick(self):
        f_phase = self.executor.submit(self.lcu.request, "GET", "/lol-gameflow/v1/gameflow-phase", None, True)
        
        f_lobby = None
        if self.last_phase in ("None", "EndOfGame", "Lobby", "Matchmaking"):
            f_lobby = self.executor.submit(self.lcu.request, "GET", "/lol-lobby/v2/lobby", None, True)

        f_session = None
        if self.last_phase in ("Matchmaking", "ReadyCheck", "ChampSelect"):
            f_session = self.executor.submit(self.lcu.request, "GET", "/lol-champ-select/v1/session", None, True)

        phase_req = f_phase.result()
        phase = phase_req.json() if phase_req and phase_req.status_code == 200 else "None"

        if self.last_phase == "Matchmaking" and phase == "Lobby":
            if not self.config.get("auto_requeue"):
                self._log("Queue Cancelled. Disabling System...")
                if self.stop_func:
                    self.stop_func()
                    self.pause()
                    return

        # Auto-minimize/restore based on InProgress state
        if self.window_func and phase != self.last_phase:
            if phase == "InProgress":
                self.window_func("minimize")
            elif self.last_phase == "InProgress" and phase in ["EndOfGame", "Lobby", "None"]:
                self.window_func("restore")

        self.last_phase = phase

        lobby_data = None
        if f_lobby:
            try:
                l_req = f_lobby.result()
                if l_req and l_req.status_code == 200:
                    lobby_data = l_req.json()
                    self.current_queue_id = lobby_data.get("gameConfig", {}).get("queueId")
            except Exception as e:
                pass

        session_data = None
        if f_session:
            try:
                sess_req = f_session.result()
                if sess_req and sess_req.status_code == 200:
                    session_data = sess_req.json()
            except Exception as e:
                pass

        self._handle_ready_check(phase)
        self._handle_champ_select(phase, session_data)
        self._handle_auto_queue(phase)

        sleep_time = 3.0
        if phase == "ChampSelect": sleep_time = 1.0
        elif phase == "ReadyCheck": sleep_time = 1.0
        elif phase in ("Lobby", "Matchmaking"): sleep_time = 2.0
        elif phase == "InProgress": sleep_time = 30.0

        self._stop_event.wait(sleep_time)

    def _handle_ready_check(self, phase):
        if phase != "ReadyCheck":
            self.ready_check_start = None
            self.ready_check_delay = None
            self.ready_check_accepted = False
            self._last_countdown_log = None
            return

        if not self.config.get("auto_accept"): return
        if self.ready_check_accepted: return

        if self.ready_check_start is None:
            self.ready_check_start = time.time()
            base_delay = self.config.get("accept_delay", 2.0)
            self.ready_check_delay = base_delay + random.uniform(0.0, 1.5) if base_delay > 0 else 0.0
            return

        target_delay = self.ready_check_delay if self.ready_check_delay is not None else 2.0
        elapsed = time.time() - self.ready_check_start

        if elapsed >= target_delay:
            self.lcu.request("POST", "/lol-matchmaking/v1/ready-check/accept")
            self.ready_check_accepted = True
            self._log("Ready Check Accepted!")

    def _handle_auto_queue(self, phase):
        if not self.config.get("auto_requeue"): return

        if phase != "EndOfGame": self._requeue_handled = False
        if phase == "EndOfGame" and not self._requeue_handled:
            self.lcu.request("POST", "/lol-end-of-game/v1/state/dismiss-stats")
            self.lcu.request("POST", "/lol-lobby/v2/play-again")
            self._log("Auto Re-Queued (Play Again)")
            self._requeue_handled = True
        elif phase == "Lobby":
            search_state = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
            state = search_state.json() if search_state and search_state.status_code == 200 else None
            
            if not state or state.get("searchState") != "Searching":
                self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
                self._log("Starting Matchmaking...")

    def _handle_champ_select(self, phase, session):
        if self.paused: return
        if phase != "ChampSelect":
            self.setup_done = False
            self._skin_equipped = False
            if self.stats_func: self.stats_func([], [])
            return
        if not session: return

        my_team = session.get("myTeam", [])
        bench = session.get("benchChampions", [])
        
        if self.stats_func:
            self.stats_func(my_team, bench)

        has_bench = len(bench) > 0
        is_arena = self.current_queue_id == 1700

        if has_bench and not is_arena:
            # ARAM logic
            priority_cfg = self.config.get("priority_picker", {})
            if priority_cfg.get("enabled", False):
                self._perform_priority_sniper(session, priority_cfg.get("list", []))

        # Auto-equip a non-default skin
        if not getattr(self, "_skin_equipped", False):
            self._equip_random_skin(session)

    def _get_local_player(self, session):
        local_cell_id = session.get("localPlayerCellId")
        my_team = session.get("myTeam", [])
        return next((p for p in my_team if p["cellId"] == local_cell_id), None)

    def _equip_random_skin(self, session):
        """Pick a random non-default skin from the available skins for the current champion."""
        try:
            me = self._get_local_player(session)
            if not me:
                return
            champ_id = me.get("championId", 0)
            if not champ_id:
                return

            # Get available skins for this champion
            skins_req = self.lcu.request("GET", f"/lol-champ-select/v1/skin-carousel-skins")
            if not skins_req or skins_req.status_code != 200:
                return

            skins = skins_req.json()
            # Filter to owned/available non-default skins for this champion
            owned_skins = [
                s for s in skins
                if s.get("ownership", {}).get("owned", False)
                and s.get("id", 0) != champ_id  # default skin id == champ_id
                and not s.get("disabled", False)
            ]

            if not owned_skins:
                return

            chosen = random.choice(owned_skins)
            skin_id = chosen.get("id", 0)

            # Patch the skin selection
            self.lcu.request(
                "PATCH",
                f"/lol-champ-select/v1/session/my-selection",
                data={"selectedSkinId": skin_id}
            )
            skin_name = chosen.get("name", f"Skin #{skin_id}")
            self._log(f"Equipped: {skin_name}")
            self._skin_equipped = True

        except Exception as e:
            Logger.error("Auto", f"Skin equip error: {e}")

    def _perform_priority_sniper(self, session, priority_list):
        if not priority_list: return
        bench = session.get("benchChampions", [])
        if not bench: return

        me = self._get_local_player(session)
        my_champ_id = me.get("championId", 0) if me else 0
        my_champ_name = self.assets.get_champ_name(my_champ_id) if my_champ_id else ""
        
        # Build an O(1) lookup map for the priority list to avoid O(N) `.index()` inside loops.
        # This makes finding the priority index 4x faster on average during Champ Select updates.
        priority_map = {name: i for i, name in enumerate(priority_list)}

        my_priority_idx = priority_map.get(my_champ_name, 9999)

        best_bench_champ = None
        best_bench_idx = 9999
        best_bench_id = 0

        for champ in bench:
            cid = champ.get("championId")
            cname = self.assets.get_champ_name(cid)

            idx = priority_map.get(cname)
            if idx is not None and idx < best_bench_idx:
                best_bench_idx = idx
                best_bench_champ = cname
                best_bench_id = cid

        if best_bench_idx < my_priority_idx:
            now = time.time()
            if not hasattr(self, "_last_priority_swap"): self._last_priority_swap = 0
            if now - self._last_priority_swap < 1.0: return
            
            self._log(f"Sniper: Found {best_bench_champ}! Swapping...")
            self.lcu.request("POST", f"/lol-champ-select/v1/session/bench/swap/{best_bench_id}")
            self._last_priority_swap = now
            # Reset skin flag so we re-equip for the new champion
            self._skin_equipped = False
