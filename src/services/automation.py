import random
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Callable, List

from .api_handler import LCUClient  # type: ignore
from .asset_manager import AssetManager, ConfigManager  # type: ignore
from utils.logger import Logger  # type: ignore
from core.constants import (  # type: ignore
    QUEUE_ARENA, TICK_SLEEP_DEFAULT, TICK_SLEEP_CHAMPSELECT,
    TICK_SLEEP_READYCHECK, TICK_SLEEP_LOBBY, TICK_SLEEP_INGAME,
    PRIORITY_SWAP_COOLDOWN,
)

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
        self.log: Optional[Callable] = log_func
        self.stop_func: Optional[Callable] = stop_func
        self.stats_func: Optional[Callable] = kwargs.get("stats_func")
        self.window_func: Optional[Callable] = kwargs.get("window_func")
        self.toast_func: Optional[Callable] = kwargs.get("toast_func")
        self.queue_func: Optional[Callable] = kwargs.get("queue_func")
        self.running: bool = False
        self.paused: bool = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._last_error_times: dict = {}
        self.setup_done: bool = False
        self.last_phase: str = "None"
        self.current_queue_id: Optional[int] = None

        self.ready_check_start: Optional[float] = None
        self.ready_check_delay: Optional[float] = None
        self.ready_check_accepted: bool = False
        self._last_countdown_log: Optional[float] = None

        self._last_disconnect_log: float = 0.0
        self._requeue_handled: bool = False
        self._skin_equipped: bool = False
        self._last_priority_swap: float = 0.0
        self._last_search_state_time: float = 0.0
        self._honor_handled: bool = False
        self._cached_search_state: Optional[dict] = None

    def start(self, start_paused: bool = False) -> None:
        if self.running: return
        self.running = True
        self.paused = start_paused
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()  # type: ignore

    def stop(self) -> None:
        self.running = False
        self._stop_event.set()

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def _log(self, msg: str) -> None:
        log_hook = self.log
        if log_hook is not None:
            log_hook(msg)
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
                # Flood-suppress: only log identical errors once per 30s
                err_key = str(e)
                now = time.time()
                last_time = self._last_error_times.get(err_key, 0)
                if now - last_time > 30:
                    tb = traceback.format_exc()
                    Logger.error("AutoLoop", f"Critical Error: {e}\n{tb}")
                    self._last_error_times[err_key] = now
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

        search_state = None
        if phase == "Matchmaking":
            search_req = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
            if search_req and search_req.status_code == 200:
                search_state = search_req.json()

        qf = getattr(self, "queue_func", None)
        if qf is not None:
            qf(phase, search_state)

        # Auto-minimize/restore based on InProgress state
        wf = self.window_func
        if wf is not None and phase != self.last_phase:
            if phase == "InProgress":
                wf("minimize")
            elif self.last_phase == "InProgress" and phase in ["EndOfGame", "Lobby", "None"]:
                if self.config.get("stealth_mode"):
                    wf("restore_quiet")
                else:
                    wf("restore")

        self.last_phase = phase

        lobby_data = None
        if f_lobby:
            try:
                l_req = f_lobby.result()
                if l_req and l_req.status_code == 200:
                    lobby_data = l_req.json()
                    self.current_queue_id = lobby_data.get("gameConfig", {}).get("queueId")
            except Exception as e:
                Logger.debug("AutoLoop", f"Lobby data fetch error: {e}")

        session_data = None
        if f_session:
            try:
                sess_req = f_session.result()
                if sess_req and sess_req.status_code == 200:
                    session_data = sess_req.json()
            except Exception as e:
                Logger.debug("AutoLoop", f"Session data fetch error: {e}")

        self._handle_ready_check(phase)
        self._handle_champ_select(phase, session_data)
        self._handle_dodge_requeue(phase)
        self._handle_auto_honor(phase)
        self._check_friend_lobby(phase)

        sleep_time = TICK_SLEEP_DEFAULT
        if phase == "ChampSelect": sleep_time = TICK_SLEEP_CHAMPSELECT
        elif phase == "ReadyCheck": sleep_time = TICK_SLEEP_READYCHECK
        elif phase in ["Lobby", "Matchmaking"]: sleep_time = TICK_SLEEP_LOBBY
        elif phase == "InProgress": sleep_time = TICK_SLEEP_INGAME

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
        
        if self.ready_check_start is None:
            return
            
        elapsed = time.time() - self.ready_check_start  # type: ignore

        if elapsed >= target_delay:  # type: ignore
            self.lcu.request("POST", "/lol-matchmaking/v1/ready-check/accept")
            self.ready_check_accepted = True
            self._log("Ready Check Accepted!")

    def _handle_dodge_requeue(self, phase):
        # Auto requeue is stripped out, but we still ensure we re-enter matchmaking
        # if another player dodges and drops us back to the Lobby phase unexpectedly.
        if phase == "Lobby" and self.last_phase in ("ChampSelect", "ReadyCheck"):
            now = time.time()
            if hasattr(self, "_cached_search_state") and hasattr(self, "_last_search_state_time") and (now - self._last_search_state_time < 3.0):
                state = self._cached_search_state
            else:
                search_state = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
                state = search_state.json() if search_state and search_state.status_code == 200 else None
                self._cached_search_state = state
                self._last_search_state_time = now
            
            if not state or state.get("searchState") != "Searching":
                self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
                self._log("Dodge detected. Restarting Matchmaking...")
                self._last_search_state_time = 0

    def _handle_champ_select(self, phase, session):
        if self.paused: return
        if phase != "ChampSelect":
            self.setup_done = False
            self._skin_equipped = False
            sf = self.stats_func
            if sf is not None:
                sf([], [])
            return
        if not session: return

        my_team = session.get("myTeam", [])
        bench = session.get("benchChampions", [])
        
        sf2 = self.stats_func
        if sf2 is not None:
            local_cell_id = session.get("localPlayerCellId")
            me = next((p for p in my_team if p.get("cellId") == local_cell_id), None)
            sf2(my_team, bench, me)

        has_bench = len(bench) > 0
        is_arena = self.current_queue_id == QUEUE_ARENA

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
                and not s.get("isBase", False)
                and s.get("id", 0) != (champ_id * 1000)
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
        
        # ⚡ Bolt: Fast-path priority sniper early-return optimization.
        # Instead of traversing the entire bench and evaluating every champion against a priority map,
        # we index the bench for O(1) lookups, then walk down the sorted priority list.
        # The first priority champion found on the bench is mathematically guaranteed to be the best,
        # allowing an instant early-return break without further iteration.
        bench_map = {}
        for champ in bench:
            cid = champ.get("championId")
            cname = self.assets.get_champ_name(cid)
            if cname:
                bench_map[cname] = cid

        my_priority_idx = 9999
        try:
            my_priority_idx = priority_list.index(my_champ_name)
        except ValueError:
            pass

        best_bench_champ = None
        best_bench_id = 0
        best_bench_idx = 9999

        for i, target_name in enumerate(priority_list):
            if i >= my_priority_idx:
                # We've reached or passed our current champion's priority.
                # Any further matches would be downgrades.
                break

            if target_name in bench_map:
                # Guaranteed best pick due to priority list ordering
                best_bench_champ = target_name
                best_bench_id = bench_map[target_name]
                best_bench_idx = i
                break

        if best_bench_id != 0:
            now = time.time()
            if not hasattr(self, "_last_priority_swap"): self._last_priority_swap = 0
            if now - self._last_priority_swap < PRIORITY_SWAP_COOLDOWN: return
            
            self._log(f"Sniper: Found {best_bench_champ}! Swapping...")
            self.lcu.request("POST", f"/lol-champ-select/v1/session/bench/swap/{best_bench_id}")
            self._last_priority_swap = now
            # Reset skin flag so we re-equip for the new champion
            self._skin_equipped = False

    def _check_friend_lobby(self, phase):
        # We only try to join when not in game/champ select/readycheck
        if phase in ("InProgress", "ChampSelect", "ReadyCheck"):
            return

        if not self.config.get("auto_join_enabled", True):
            return

        friend_list = self.config.get("auto_join_list", [])
        active_friends = [f for f in friend_list if f.get("enabled") and f.get("name", "").strip()]
        if not active_friends:
            return

        now = time.time()
        # Rate limit checks to every ~5 seconds to avoid spamming the friends endpoint
        if not hasattr(self, "_last_friend_check"): self._last_friend_check = 0.0
        if now - self._last_friend_check < 5.0:
            return
        self._last_friend_check = now

        res = self.lcu.request("GET", "/lol-chat/v1/friends")
        if not res or res.status_code != 200:
            return
        friends = res.json()

        # ⚡ Bolt: Fast-path priority sniper early-return optimization.
        # Instead of an O(N*M) nested loop evaluating every friend against the priority list,
        # we index the active online friends into an O(1) dictionary mapping their lowercased names.
        friend_map = {}
        for f in friends:
            game_name = f.get("gameName", "")
            game_tag = f.get("gameTag", "")
            combo_name = f"{game_name}#{game_tag}" if game_tag else game_name
            
            friend_map[game_name.lower()] = f
            if combo_name:
                friend_map[combo_name.lower()] = f

        for target_dict in active_friends:
            target_friend = target_dict.get("name", "").strip().lower()
            
            f = friend_map.get(target_friend)
            if not f:
                continue

            game_name = f.get("gameName", "")
            lol = f.get("lol", {})
            if lol.get("ptyType") == "open":
                pty_str = lol.get("pty", "")
                if pty_str:
                    import json
                    try:
                        pty_data = json.loads(pty_str)
                        party_id = pty_data.get("partyId")
                        if party_id:
                            # Check if we are already in this specific party
                            my_res = self.lcu.request("GET", "/lol-lobby/v2/lobby")
                            if my_res and my_res.status_code == 200:
                                my_lobby = my_res.json()
                                if my_lobby.get("partyId") == party_id:
                                    return  # Already in their party

                            # If we are currently searching for a match, cancel it first
                            if phase == "Matchmaking":
                                self.lcu.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
                                time.sleep(0.5)

                            # Join party
                            join_res = self.lcu.request("POST", f"/lol-lobby/v2/party/{party_id}/join")
                            if join_res and join_res.status_code in [200, 204]:
                                self._log(f"Auto-joined {game_name}'s Party!")
                                break # Joined a friend, stop iterating the priority list
                    except Exception as e:
                        Logger.debug("Auto", f"Failed parsing friend party: {e}")

    # ── Auto-Honor ──
    def _handle_auto_honor(self, phase):
        if phase != "EndOfGame":
            self._honor_handled = False
            return

        if not self.config.get("auto_honor_enabled", False):
            return
        if self._honor_handled:
            return

        try:
            eog = self.lcu.request("GET", "/lol-end-of-game/v1/eog-stats-block")
            if not eog or eog.status_code != 200:
                return
            
            self._honor_handled = True
            data = eog.json()
            game_id = data.get("gameId")
            my_puuid = None
            me_req = self.lcu.request("GET", "/lol-chat/v1/me")
            if me_req and me_req.status_code == 200:
                my_puuid = me_req.json().get("puuid")

            teams = data.get("teams", [])
            teammates = []
            for team in teams:
                for player in team.get("players", []):
                    puuid = player.get("puuid", "")
                    if puuid and puuid != my_puuid:
                        teammates.append(player)

            if not teammates:
                return

            strategy = self.config.get("honor_strategy", "random")
            if strategy == "best_kda":
                def kda(p):
                    k = p.get("stats", {}).get("CHAMPIONS_KILLED", 0)
                    a = p.get("stats", {}).get("ASSISTS", 0)
                    d = max(p.get("stats", {}).get("NUM_DEATHS", 1), 1)
                    return (k + a) / d
                target = max(teammates, key=kda)
            elif strategy == "mvp":
                def score(p):
                    s = p.get("stats", {})
                    return s.get("CHAMPIONS_KILLED", 0) + s.get("ASSISTS", 0)
                target = max(teammates, key=score)
            else:
                target = random.choice(teammates)

            summoner_id = target.get("summonerId", 0)
            honor_body = {
                "gameId": game_id,
                "honorCategory": "HEART",
                "summonerId": summoner_id,
            }
            res = self.lcu.request("POST", "/lol-honor-v2/v1/honor-player", honor_body)
            name = target.get("summonerName", "teammate")
            if res and res.status_code in [200, 204]:
                self._log(f"Honored {name} ({strategy})")
            else:
                Logger.debug("Auto", f"Honor request returned {res.status_code if res else 'None'}")
        except Exception as e:
            Logger.debug("Auto", f"Auto-honor error: {e}")

    # ── Mass Invite ──
    def mass_invite_friends(self):
        """Invite all online friends (or VIP list) to the current lobby."""
        try:
            vip_raw = self.config.get("vip_invite_list", "")
            vip_names = set()
            if vip_raw.strip():
                vip_names = {n.strip().lower() for n in vip_raw.split(",") if n.strip()}

            res = self.lcu.request("GET", "/lol-chat/v1/friends")
            if not res or res.status_code != 200:
                self._log("Failed to fetch friends.")
                return 0
            friends = res.json()

            invitations = []
            for f in friends:
                avail = f.get("availability", "offline")
                if avail == "offline":
                    continue
                game_name = f.get("gameName", "")
                summoner_id = f.get("summonerId", 0)
                if not summoner_id:
                    continue
                if vip_names and game_name.lower() not in vip_names:
                    continue
                invitations.append({
                    "toSummonerId": summoner_id,
                    "state": "Requested",
                })

            if not invitations:
                self._log("No online friends to invite.")
                return 0

            inv_res = self.lcu.request("POST", "/lol-lobby/v2/lobby/invitations", invitations)
            count = len(invitations)
            if inv_res and inv_res.status_code in [200, 204]:
                self._log(f"Invited {count} friend(s) to lobby!")
            else:
                self._log(f"Invite failed (status {inv_res.status_code if inv_res else 'N/A'})")
            return count
        except Exception as e:
            Logger.debug("Auto", f"Mass invite error: {e}")
            self._log("Mass invite failed.")
            return 0

    # ── Custom Status ──
    def set_custom_status(self, status_text: str):
        """Push a custom status message to the League Client."""
        try:
            body = {"statusMessage": status_text}
            res = self.lcu.request("PUT", "/lol-chat/v1/me", body)
            if res and res.status_code in [200, 201]:
                self._log(f"Status → \"{status_text}\"")
            else:
                self._log("Status update failed.")
        except Exception as e:
            Logger.debug("Auto", f"Set status error: {e}")
