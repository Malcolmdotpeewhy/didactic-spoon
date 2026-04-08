import ctypes
import os
import random
import sys
import threading
import time
import traceback
import queue
import subprocess
from tkinter import TclError

import customtkinter as ctk  # type: ignore
import keyboard  # type: ignore
from PIL import Image  # type: ignore

from typing import Optional, TYPE_CHECKING

from services.api_handler import LCUClient  # type: ignore
from services.asset_manager import AssetManager, ConfigManager  # type: ignore
from services.automation import AutomationEngine  # type: ignore
from services.stats_scraper import StatsScraper  # type: ignore
from utils.logger import Logger  # type: ignore
from utils.path_utils import get_asset_path  # type: ignore
from core.version import __version__  # type: ignore
from core.constants import (  # type: ignore
    SIDEBAR_WIDTH, SIDEBAR_HEIGHT, COMPACT_SIZE, COMPACT_BUTTON_SIZE,
    COMPACT_GLOW_SIZE, DOCKING_POLL_INTERVAL, DOCKING_IDLE_INTERVAL,
    CONNECTION_POLL_INTERVAL, CONNECTION_ERROR_INTERVAL,
    GEOMETRY_THRESHOLD,
)

from ui.app_sidebar import SidebarWidget  # type: ignore
from ui.components.factory import get_color, get_font, TOKENS  # type: ignore
from ui.components.toast import ToastManager  # type: ignore
from ui.ui_shared import CTkTooltip  # type: ignore
from ui.components.omnibar import Omnibar  # type: ignore
from tkinterdnd2 import TkinterDnD  # type: ignore

if TYPE_CHECKING:
    import ctypes.wintypes

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    err_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    Logger.error("SYS", f"Uncaught exception:\n{err_str}")

sys.excepthook = global_exception_handler

class LeagueLoopApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.report_callback_exception = self._on_tk_error
        
        self._ui_queue = queue.Queue()
        self._process_ui_queue()


        try:
            myappid = "league.loop.app.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
            
        self.title("League Loop")
        try:
            icon_path = get_asset_path("assets/app.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                backup = get_asset_path("assets/icon.png")
                self.iconphoto(False, tk.PhotoImage(file=backup))
        except Exception as e:
            Logger.warning("SYS", f"Could not set window icon: {e}")
        self.geometry(f"{SIDEBAR_WIDTH}x{SIDEBAR_HEIGHT}+100+100") # Spawn visibly on screen
        self.minsize(260, 520)
        self.overrideredirect(True) # Borderless for docking
        self.attributes("-topmost", True) # Keep visible until docked
        self.attributes("-topmost", True)
        
        self.configure(fg_color=get_color("colors.background.app"))

        try:
            ToastManager.get_instance(self)
        except Exception as e:
            Logger.error("SYS", f"ToastManager initialization error: {e}")
            
        self.config = ConfigManager()
        self.assets = AssetManager()
        self.lcu = LCUClient()
        self.scraper = StatsScraper(mode=self.config.get("aram_mode", "ARAM"))
        
        self.running = True
        self._stop_event = threading.Event()
        self._drag_data = {"x": 0, "y": 0}
        self.omnibar = None

        # Initialize automation before UI to avoid NoneType in callbacks
        self.automation: Optional[AutomationEngine] = AutomationEngine(
            self.lcu,
            self.assets,
            self.config,
            log_func=None, # Will be set after sidebar is created
            stop_func=lambda: self.after(0, lambda: self.sidebar._on_power_click()) if hasattr(self, "sidebar") else None,
            stats_func=lambda team, bench, me=None: self.after(0, lambda: self.sidebar.update_lobby_stats(team, bench, me)) if hasattr(self, "sidebar") else None,
            window_func=lambda state: self.after(0, lambda: self._handle_window_state(state)),
            queue_func=lambda phase, state: self.after(0, lambda: self.sidebar.update_queue_state(phase, state)) if hasattr(self, "sidebar") else None
        )

        self.setup_ui()
        
        # Link automation to sidebar log
        auto = self.automation
        if auto is not None and hasattr(self, "sidebar"):
            auto.log = self.sidebar.update_action_log

        self._setup_window_dragging()

        # Keyboard shortcuts
        self._compact_mode = False
        self._full_geometry = None
        self._compact_hotkey = None
        self._launch_hotkey = None
        self._automation_hotkey = None
        self._queue_hotkey = None
        self._bind_hotkeys()

        if self.automation is not None:
            self.automation.start(start_paused=False)  # type: ignore

        self.assets.start_loading()
        threading.Thread(target=self.connection_loop, daemon=True).start()
        threading.Thread(target=self.docking_loop, daemon=True).start()
        
    def _on_tk_error(self, exc, val, tb):
        err_str = "".join(traceback.format_exception(exc, val, tb))
        Logger.error("UI", f"Tkinter Error:\n{err_str}")

    def _process_ui_queue(self):
        # Bolt optimization: checking .empty() is faster than catching queue.Empty
        # in a 16ms polling loop where the queue is usually empty.
        for _ in range(100):
            if self._ui_queue.empty():
                break
            try:
                task, args, kwargs = self._ui_queue.get_nowait()
                if task:
                    task(*args, **kwargs)
            except queue.Empty:
                pass
        super().after(16, self._process_ui_queue)

    def after(self, ms, func=None, *args):
        if threading.current_thread() is threading.main_thread():
            return super().after(ms, func, *args)
        else:
            if ms == 0:
                self._ui_queue.put((func, args, {}))
            else:
                self._ui_queue.put((super().after, (ms, func) + args, {}))
            return "queued"

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.sidebar = SidebarWidget(self, self.toggle_power, self.config, lcu=self.lcu, assets=self.assets, scraper=self.scraper)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.omnibar = Omnibar(self, self._provide_commands)

    def _setup_window_dragging(self):
        for widget in self.sidebar.drag_widgets:
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        if getattr(self, "compact_mode", False) and hasattr(self, "_compact_frame"):
            try:
                self._compact_frame.configure(border_color=get_color("colors.accent.primary", "#0ac8b9"))
            except Exception:
                pass

    def on_drag_stop(self, event):
        if getattr(self, "compact_mode", False) and hasattr(self, "_compact_frame"):
            try:
                self._compact_frame.configure(border_color=get_color("colors.accent.gold", "#C8AA6E"))
            except Exception:
                pass

    def on_drag_motion(self, event):
        x = self.winfo_x() - self._drag_data["x"] + event.x
        y = self.winfo_y() - self._drag_data["y"] + event.y
        self.geometry(f"+{x}+{y}")

    def _hotkey_find_match(self):
        self.state("normal")
        self.attributes("-topmost", True)
        self.after(0, self.sidebar._find_match)

    def _handle_window_state(self, state):
        if state == "minimize":
            self.attributes("-topmost", False)
            try:
                import ctypes
                SW_MINIMIZE = 6
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if hwnd == 0: hwnd = self.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
            except Exception:
                self.withdraw()
            Logger.info("SYS", "Game started. Minimizing window.")
        elif state == "restore":
            try:
                import ctypes
                SW_RESTORE = 9
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if hwnd == 0: hwnd = self.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            except Exception:
                pass
            self.deiconify()
            # Do not set topmost=True here anymore, OS handles Z-order
            self.lift()
            Logger.info("SYS", "Game ended. Restoring window.")
        elif state == "restore_quiet":
            try:
                import ctypes
                SW_RESTORE = 9
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                if hwnd == 0: hwnd = self.winfo_id()
                ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            except Exception:
                pass
            self.deiconify()
            Logger.info("SYS", "Game ended. Window restored (stealth).")

    def _attach_to_hwnd(self, parent_hwnd):
        """OS-level bond to League Client. Syncs minimize/restore and Z-order natively."""
        try:
            import ctypes
            GWLP_HWNDPARENT = -8
            my_hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            if my_hwnd == 0:
                my_hwnd = self.winfo_id()
                
            # For 64-bit windows, SetWindowLongPtr is required.
            if hasattr(ctypes.windll.user32, "SetWindowLongPtrW"):
                ctypes.windll.user32.SetWindowLongPtrW(my_hwnd, GWLP_HWNDPARENT, parent_hwnd)
            else:
                ctypes.windll.user32.SetWindowLongW(my_hwnd, GWLP_HWNDPARENT, parent_hwnd)
                
            # We are now an owned window. We stay precisely above the League Client,
            # but NEVER above other apps like web browsers unless League itself is focused.
            self.attributes("-topmost", False)
        except Exception as e:
            pass

    def _hotkey_launch_client(self):
        def _launch():
            path_override = self.config.get("league_path_override", "")
            if path_override and os.path.exists(path_override):
                candidates = [path_override]
            else:
                candidates = [
                    r"C:\Riot Games\Riot Client\RiotClientServices.exe",
                    r"D:\Riot Games\Riot Client\RiotClientServices.exe",
                    r"E:\Riot Games\Riot Client\RiotClientServices.exe",
                    r"C:\Program Files (x86)\Riot Games\Riot Client\RiotClientServices.exe",
                    os.path.join(os.environ.get("USERPROFILE", ""), r"Riot Games\Riot Client\RiotClientServices.exe")
                ]
                
                # Proactive Registry Lookup
                try:
                    import winreg
                    for hkey in [getattr(winreg, "HKEY_CURRENT_USER", 0), getattr(winreg, "HKEY_LOCAL_MACHINE", 0)]:
                        try:
                            key = getattr(winreg, "OpenKey")(hkey, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game league_of_legends.live")
                            val, _ = getattr(winreg, "QueryValueEx")(key, "UninstallString")
                            # Typically "C:\Riot Games\Riot Client\RiotClientServices.exe" --uninstall-product=...
                            if val and "RiotClientServices.exe" in val:
                                path = val.split('"')[1] if '"' in val else val.split(' ')[0]
                                if os.path.exists(path): candidates.insert(0, path)
                        except Exception as e:
                            from utils.logger import Logger  # type: ignore
                            Logger.debug("SYS", f"Registry iteration failed: {e}")
                except Exception as e:
                    from utils.logger import Logger  # type: ignore
                    Logger.debug("SYS", f"Registry module failed: {e}")

            for c in candidates:
                if os.path.exists(c):
                    if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
                        self.sidebar.update_action_log("Launching Riot Client...")
                    subprocess.Popen([c, "--launch-product=league_of_legends", "--launch-patchline=live"])
                    return
            if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
                self.sidebar.update_action_log("Error: Could not find Riot Client.")
        self.after(0, _launch)

    def _hotkey_toggle_automation(self):
        self.after(0, self.sidebar._on_power_click)

    def _provide_commands(self):
        base_cmds = [
            {
                "title": "Launch League of Legends",
                "subtitle": "Opens the Riot Client and boots League",
                "icon": "🚀",
                "action": self._hotkey_launch_client
            },
            {
                "title": "Restart League UX",
                "subtitle": "Restarts LeagueClientUx without closing the game",
                "icon": "🔄",
                "action": self._restart_ux
            },
            {
                "title": "Clear UI Cache",
                "subtitle": "Deletes downloaded champion images",
                "icon": "🗑️",
                "action": self.assets.clear_cache
            },
            {
                "title": "Toggle Compact Mode",
                "subtitle": "Shrinks LeagueLoop to a glowing orb",
                "icon": "🗖",
                "action": lambda: self.after(0, self.toggle_compact_mode)
            },
            {
                "title": "Quit LeagueLoop",
                "subtitle": "Closes the application completely",
                "icon": "❌",
                "action": self._on_close
            },
            {
                "title": "Queue Roulette",
                "subtitle": "Feeling lucky? Randomly pick a mode and queue up!",
                "icon": "🎲",
                "action": self._queue_roulette
            }
        ]

        # Inject dynamic queue modes
        modes = [
            "Quickplay", "Draft Pick", "Ranked Solo/Duo", "Ranked Flex",
            "ARAM", "ARAM Mayhem", "Arena", "URF", "ARURF", "Nexus Blitz",
            "One For All", "Ultimate Spellbook", "TFT Normal", "TFT Ranked"
        ]

        for mode in modes:
            # We capture the mode name via a default argument in the lambda
            # so the loop closure binds correctly
            base_cmds.append({
                "title": f"Queue: {mode}",
                "subtitle": f"Switch mode and start searching for {mode}",
                "icon": "🎮",
                "action": lambda m=mode: self._quick_queue(m)
            })

        return base_cmds

    def _quick_queue(self, mode_name):
        if not hasattr(self, "sidebar") or not self.sidebar.winfo_exists():
            return

        self.sidebar.var_game_mode.set(mode_name)
        self.sidebar._on_mode_change(mode_name)
        self.after(50, self.sidebar._find_match)

        try:
            ToastManager.get_instance().show(
                f"Queued up for {mode_name}!",
                icon="🎮",
                duration=3000,
                theme="success"
            )
        except Exception as e:
            Logger.error("SYS", f"Toast error: {e}")

    def _queue_roulette(self):
        if not hasattr(self, "sidebar") or not self.sidebar.winfo_exists():
            return

        modes = [
            "Quickplay", "Draft Pick", "Ranked Solo/Duo", "Ranked Flex",
            "ARAM", "Arena", "TFT Normal"
        ]

        # 1. Cancel existing search
        if getattr(self.sidebar, "power_state", False):
            self.sidebar._on_power_click()

        # 2. Spin animation parameters
        spins = random.randint(15, 25)
        delay = 50

        def do_spin(count):
            if count > 0:
                current_mode = random.choice(modes)
                self.sidebar.var_game_mode.set(current_mode)

                # Slow down towards the end
                next_delay = delay + int((spins - count) * 4)
                self.after(next_delay, lambda: do_spin(count - 1))
            else:
                # Landed!
                winner = self.sidebar.var_game_mode.get()
                self.sidebar._on_mode_change(winner)

                try:
                    ToastManager.get_instance().show(
                        f"Roulette landed on {winner}!",
                        icon="🎰",
                        duration=4000,
                        theme="success",
                        confetti=True
                    )
                except Exception as e:
                    Logger.error("SYS", f"Toast error: {e}")

                # Queue it up
                self.after(500, self.sidebar._find_match)

        # Start spin
        do_spin(spins)

    def _restart_ux(self):
        if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            self.sidebar.update_action_log("Restarting League UX...")
        
        def _execute():
            success = False
            if self.lcu and self.lcu.is_connected:
                res = self.lcu.request("POST", "/riotclient/kill-and-restart-ux")
                if res and res.status_code in [200, 204]:
                    success = True
            
            if not success:
                import subprocess
                subprocess.run(["taskkill", "/IM", "LeagueClientUx.exe", "/F"], capture_output=True)
                
            self.after(0, lambda: self.sidebar.update_action_log("UX Restart Triggered."))
                
        threading.Thread(target=_execute, daemon=True).start()

    def _bind_hotkeys(self):
        try:
            keyboard.unhook_all()
        except Exception as e:
            Logger.debug("SYS", f"Failed to unhook hotkeys: {e}")
            
        self._compact_hotkey = self.config.get("hotkey_compact_mode", "ctrl+shift+m")
        self._launch_hotkey = self.config.get("hotkey_launch_client", "ctrl+shift+l")
        self._automation_hotkey = self.config.get("hotkey_toggle_automation", "ctrl+shift+a")
        self._queue_hotkey = self.config.get("hotkey_find_match", "ctrl+shift+f")
        self._omnibar_hotkey = self.config.get("hotkey_omnibar", "ctrl+k")

        try:
            keyboard.add_hotkey(self._compact_hotkey, lambda: self.after(0, self.toggle_compact_mode), suppress=False)
            keyboard.add_hotkey(self._launch_hotkey, self._hotkey_launch_client, suppress=False)
            keyboard.add_hotkey(self._automation_hotkey, self._hotkey_toggle_automation, suppress=False)
            keyboard.add_hotkey(self._queue_hotkey, self._hotkey_find_match, suppress=False)
            keyboard.add_hotkey(self._omnibar_hotkey, lambda: self.after(0, self.omnibar.show) if self.omnibar is not None else None, suppress=False)  # type: ignore
        except Exception as e:
            Logger.error("SYS", f"Failed to register hotkeys: {e}")

    def on_settings_saved(self):
        self._bind_hotkeys()
        self.scraper.set_mode(self.config.get("aram_mode", "ARAM"))

    def toggle_compact_mode(self):
        if self._compact_mode:
            self._compact_mode = False
            self.attributes("-topmost", True)
            self.overrideredirect(True)
            try:
                self.attributes("-transparentcolor", "")
            except TclError:
                pass

            self.sidebar.grid()
            if hasattr(self, "_compact_frame"):
                self._compact_frame.destroy()

            if self._full_geometry:
                self.geometry(self._full_geometry)
            else:
                self.geometry(f"{SIDEBAR_WIDTH}x{SIDEBAR_HEIGHT}")

            if self.sidebar:
                self.sidebar.update_action_log("Restored Full Mode")
        else:
            self._compact_mode = True
            self._full_geometry = self.geometry()
            self.sidebar.grid_remove()

            trans_color = "black"
            self._compact_frame = ctk.CTkFrame(self, fg_color=trans_color, corner_radius=0)
            self._compact_frame.grid(row=0, column=0, sticky="nsew")

            compact_icon = self.sidebar.img_on if self.sidebar.power_state else self.sidebar.img_off
            compact_text = "" if compact_icon else "⏻"
            
            ring_color = get_color("colors.accent.primary") if self.sidebar.power_state else get_color("colors.text.muted")
            
            glow_frame = ctk.CTkFrame(
                self._compact_frame, fg_color=trans_color, bg_color=trans_color,
                corner_radius=40, border_width=3, border_color=ring_color,
                width=80, height=80
            )
            glow_frame.place(relx=0.5, rely=0.5, anchor="center")
            glow_frame.pack_propagate(False)

            btn_compact = ctk.CTkButton(
                glow_frame, text=compact_text, image=compact_icon,
                font=("Arial", 20, "bold"), width=72, height=72, corner_radius=36,
                fg_color=trans_color, hover_color=get_color("colors.state.hover"),
                command=self.toggle_compact_mode,
            )
            btn_compact.place(relx=0.5, rely=0.5, anchor="center")
            CTkTooltip(btn_compact, "Return to Full Mode")

            self.geometry(f"{COMPACT_SIZE}x{COMPACT_SIZE}")
            self.attributes("-topmost", True)
            self.overrideredirect(True)
            try:
                self.attributes("-transparentcolor", trans_color)
            except TclError:
                pass

            self._compact_frame.bind("<ButtonPress-1>", self.on_drag_start)
            btn_compact.bind("<ButtonPress-1>", self.on_drag_start)
            self._compact_frame.bind("<B1-Motion>", self.on_drag_motion)
            btn_compact.bind("<B1-Motion>", self.on_drag_motion)
            self._compact_frame.bind("<ButtonRelease-1>", self.on_drag_stop)
            btn_compact.bind("<ButtonRelease-1>", self.on_drag_stop)

    def toggle_power(self, power_state):
        Logger.info("SYS", f"Power Toggled: {power_state}")
        if self.automation is not None:
            if power_state:
                self.automation.resume()  # type: ignore
            else:
                self.automation.pause()  # type: ignore

    def connection_loop(self):
        last_state = None
        while self.running and not self._stop_event.is_set():
            try:
                current_state = self.lcu.is_connected
                if current_state != last_state:
                    last_state = current_state
                    if hasattr(self, "sidebar") and hasattr(self.sidebar, "on_lcu_connection_changed"):
                        self.after(0, lambda s=current_state: getattr(self, "sidebar").on_lcu_connection_changed(s))

                if not current_state:
                    connected = self.lcu.connect()
                    if connected:
                        Logger.info("LCU", "Connected to League Client")
                        self.after(0, lambda: self.sidebar.lbl_action.configure(text="Connected!"))
                    else:
                        self.after(0, lambda: self.sidebar.lbl_action.configure(text="Waiting for Client..."))
                time.sleep(CONNECTION_POLL_INTERVAL)
            except Exception as e:
                Logger.error("SYS", f"Connection loop error: {e}")
                time.sleep(CONNECTION_ERROR_INTERVAL)

    def docking_loop(self):
        """Finds League of Legends client and clips to the right side of it."""
        last_hwnd = 0
        last_geom = (0, 0, 0, 0) # x, y, w, h
        
        while self.running and not self._stop_event.is_set():  # type: ignore
            try:
                hwnd = 0
                windll = getattr(ctypes, "windll", None)
                user32 = getattr(windll, "user32", None) if windll else None
                
                if not user32:
                    time.sleep(2.0)
                    continue

                if last_hwnd != 0 and user32.IsWindow(last_hwnd):
                    hwnd = last_hwnd
                else:
                    hwnd = user32.FindWindowW(None, "League of Legends")
                    if hwnd == 0:
                        hwnd = user32.FindWindowW(None, "Riot Client")

                if hwnd != 0:
                    if hwnd != last_hwnd:
                        last_hwnd = hwnd
                        # Bond cleanly to the newly detected HWND
                        self.after(0, lambda h=hwnd: self._attach_to_hwnd(h))

                    rect = ctypes.wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    client_x = rect.left
                    client_y = rect.top
                    client_w = rect.right - rect.left
                    client_h = rect.bottom - rect.top
                    
                    if client_w > 100:
                        is_expanded = getattr(self, "sidebar", None) is None or getattr(self.sidebar, "_body_expanded", True)
                        my_w = 200 if is_expanded else 44
                        my_h = client_h if is_expanded else 44
                        target_x = client_x + client_w
                        target_y = client_y
                        
                        curr_geom = (target_x, target_y, my_w, my_h)
                        if any(abs(curr_geom[i] - last_geom[i]) > GEOMETRY_THRESHOLD for i in range(4)):  # type: ignore
                            self.after(0, lambda x=target_x, y=target_y, h=my_h: self.geometry(f"{my_w}x{h}+{x}+{y}"))
                            last_geom = curr_geom
                        
                    time.sleep(DOCKING_POLL_INTERVAL)
                else:
                    last_hwnd = 0
                    last_geom = (0, 0, 0, 0)
                    time.sleep(DOCKING_IDLE_INTERVAL)
            except Exception as e:
                Logger.debug("SYS", f"Docking loop error: {e}")
            time.sleep(DOCKING_POLL_INTERVAL)

    def _on_close(self):
        """Robust shutdown: stop all subsystems, then force-exit."""
        Logger.info("SYS", "Exit requested — shutting down...")
        self.running = False
        self._stop_event.set()

        # 1. Stop the automation engine
        try:
            if hasattr(self, 'engine') and self.engine:
                self.engine.stop()
        except Exception as e:
            Logger.debug("SYS", f"Engine stop error: {e}")

        # 2. Unhook keyboard hotkeys
        try:
            keyboard.unhook_all()
        except Exception as e:
            Logger.debug("SYS", f"Unhook error: {e}")

        # 3. Destroy the Tk window
        try:
            self.destroy()
        except Exception as e:
            Logger.debug("SYS", f"Destroy error: {e}")

        # 4. Force-exit to kill any lingering daemon threads
        Logger.info("SYS", "Shutdown complete.")
        os._exit(0)

def _kill_other_instances():
    """Terminate any other running instances of LeagueLoop."""
    import psutil  # type: ignore
    my_pid = os.getpid()
    # Also protect the parent (e.g. the shell that launched us)
    try:
        my_parent_pid = psutil.Process(my_pid).ppid()
    except Exception:
        my_parent_pid = -1
    
    safe_pids = {my_pid, my_parent_pid}
    killed = 0
    
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.pid in safe_pids:
                continue
            pname = (proc.info.get("name") or "").lower()
            if "python" not in pname:
                continue
            # Only read cmdline for python processes (expensive call)
            try:
                cmdline = proc.cmdline()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                continue
            cmdline_str = " ".join(cmdline).lower()
            if "core.main" in cmdline_str or "core\\main" in cmdline_str:
                Logger.info("SYS", f"Killing stale instance PID {proc.pid}")
                proc.kill()
                killed += 1  # type: ignore
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if killed:
        Logger.info("SYS", f"Terminated {killed} stale instance(s).")
        time.sleep(0.3)

if __name__ == "__main__":
    _kill_other_instances()
    app = LeagueLoopApp()
    app.mainloop()
