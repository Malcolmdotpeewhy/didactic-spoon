import ctypes
import os
import sys
import threading
import time
import tkinter
import traceback
import queue
import subprocess

import customtkinter as ctk
import keyboard
from PIL import Image

from services.api_handler import LCUClient
from services.asset_manager import AssetManager, ConfigManager
from services.automation import AutomationEngine
from services.stats_scraper import StatsScraper
from utils.logger import Logger
from utils.path_utils import resource_path
from core.version import __version__

from ui.app_sidebar import SidebarWidget
from ui.components.factory import get_color, get_font, TOKENS
from ui.ui_shared import show_toast
from ui.components.toast import ToastManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class LeagueLoopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self._ui_queue = queue.Queue()
        self._process_ui_queue()
        
        self.title("League Loop")
        self.geometry("200x400") # Small footprint sidebar
        self.overrideredirect(True) # Borderless for docking
        self.attributes("-topmost", True)
        
        self.configure(fg_color=get_color("colors.background.app"))

        try:
            ToastManager(self)
        except Exception as e:
            Logger.error("SYS", f"ToastManager initialization error: {e}")
            
        self.config = ConfigManager()
        self.assets = AssetManager()
        self.lcu = LCUClient()
        self.scraper = StatsScraper(mode=self.config.get("aram_mode", "ARAM"))
        
        self.automation = None
        self.running = True
        self._stop_event = threading.Event()
        self._drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self._setup_window_dragging()

        # Keyboard shortcuts
        self._compact_mode = False
        self._full_geometry = None
        self._compact_hotkey = None
        self._launch_hotkey = None
        self._automation_hotkey = None
        self._queue_hotkey = None
        self._bind_hotkeys()

        # Automation Engine
        self.automation = AutomationEngine(
            self.lcu,
            self.assets,
            self.config,
            log_func=self.sidebar.update_action_log,
            stop_func=lambda: self.after(0, lambda: self.sidebar._on_power_click()),
            stats_func=lambda team, bench: self.after(0, lambda: self.sidebar.update_lobby_stats(team, bench)),
            window_func=lambda state: self.after(0, lambda: self._handle_window_state(state))
        )
        self.automation.start(start_paused=True)

        self.assets.start_loading()
        threading.Thread(target=self.connection_loop, daemon=True).start()
        threading.Thread(target=self.docking_loop, daemon=True).start()
        
    def _process_ui_queue(self):
        try:
            for _ in range(100):
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
                def _delayed():
                    time.sleep(ms / 1000.0)
                    self._ui_queue.put((func, args, {}))
                threading.Thread(target=_delayed, daemon=True).start()
            return "queued"

    def setup_ui(self):
        self.sidebar = SidebarWidget(self, self.toggle_power, self.config, lcu=self.lcu, assets=self.assets, scraper=self.scraper)
        self.sidebar.pack(fill="both", expand=True)

    def _setup_window_dragging(self):
        for widget in self.sidebar.drag_widgets:
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

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
            self.state("iconic")
            Logger.info("SYS", "Game started. Minimizing window.")
        elif state == "restore":
            self.state("normal")
            self.attributes("-topmost", True)
            self.lift()
            Logger.info("SYS", "Game ended. Restoring window.")

    def _hotkey_launch_client(self):
        def _launch():
            path_override = self.config.get("league_path_override", "")
            if path_override and os.path.exists(path_override):
                candidates = [path_override]
            else:
                candidates = [
                    r"C:\Riot Games\Riot Client\RiotClientServices.exe",
                    r"D:\Riot Games\Riot Client\RiotClientServices.exe",
                    r"E:\Riot Games\Riot Client\RiotClientServices.exe"
                ]
            for c in candidates:
                if os.path.exists(c):
                    if self.sidebar:
                        self.sidebar.update_action_log("Launching Riot Client...")
                    subprocess.Popen([c, "--launch-product=league_of_legends", "--launch-patchline=live"])
                    return
            if self.sidebar:
                self.sidebar.update_action_log("Error: Could not find Riot Client.")
        self.after(0, _launch)

    def _hotkey_toggle_automation(self):
        self.after(0, self.sidebar._on_power_click)

    def _bind_hotkeys(self):
        try:
            keyboard.unhook_all()
        except:
            pass
            
        self._compact_hotkey = self.config.get("hotkey_compact_mode", "ctrl+shift+m")
        self._launch_hotkey = self.config.get("hotkey_launch_client", "ctrl+shift+l")
        self._automation_hotkey = self.config.get("hotkey_toggle_automation", "ctrl+shift+a")
        self._queue_hotkey = self.config.get("hotkey_find_match", "ctrl+shift+f")

        try:
            keyboard.add_hotkey(self._compact_hotkey, lambda: self.after(0, self.toggle_compact_mode), suppress=False)
            keyboard.add_hotkey(self._launch_hotkey, self._hotkey_launch_client, suppress=False)
            keyboard.add_hotkey(self._automation_hotkey, self._hotkey_toggle_automation, suppress=False)
            keyboard.add_hotkey(self._queue_hotkey, self._hotkey_find_match, suppress=False)
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
            except Exception:
                pass

            self.sidebar.grid()
            if hasattr(self, "_compact_frame"):
                self._compact_frame.destroy()

            if self._full_geometry:
                self.geometry(self._full_geometry)
            else:
                self.geometry("200x400")

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

            self.geometry("90x90")
            self.attributes("-topmost", True)
            self.overrideredirect(True)
            try:
                self.attributes("-transparentcolor", trans_color)
            except Exception:
                pass

            self._compact_frame.bind("<ButtonPress-1>", self.on_drag_start)
            btn_compact.bind("<ButtonPress-1>", self.on_drag_start)
            self._compact_frame.bind("<B1-Motion>", self.on_drag_motion)
            btn_compact.bind("<B1-Motion>", self.on_drag_motion)

    def toggle_power(self, power_state):
        Logger.info("SYS", f"Power Toggled: {power_state}")
        if power_state:
            self.automation.resume()
        else:
            self.automation.pause()

    def connection_loop(self):
        while self.running and not self._stop_event.is_set():
            try:
                if not self.lcu.is_connected:
                    connected = self.lcu.connect()
                    if connected:
                        Logger.info("LCU", "Connected to League Client")
                        self.after(0, lambda: self.sidebar.lbl_action.configure(text="Connected!"))
                    else:
                        self.after(0, lambda: self.sidebar.lbl_action.configure(text="Waiting for Client..."))
                time.sleep(2)
            except Exception as e:
                Logger.error("SYS", f"Connection loop error: {e}")
                time.sleep(5)

    def docking_loop(self):
        """Finds League of Legends client and clips to the right side of it."""
        last_hwnd = 0
        while self.running and not self._stop_event.is_set():
            try:
                hwnd = 0
                if last_hwnd != 0 and ctypes.windll.user32.IsWindow(last_hwnd):
                    hwnd = last_hwnd
                else:
                    # We can check for standard Riot Client or League Client
                    hwnd = ctypes.windll.user32.FindWindowW(None, "League of Legends")
                    if hwnd == 0:
                        hwnd = ctypes.windll.user32.FindWindowW(None, "Riot Client")

                if hwnd != 0:
                    last_hwnd = hwnd
                    rect = ctypes.wintypes.RECT()
                    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    
                    # Window placement: attach to the right side of the client
                    client_x = rect.left
                    client_y = rect.top
                    client_w = rect.right - rect.left
                    client_h = rect.bottom - rect.top
                    
                    # Ignore minimized windows or invalid states
                    if client_w > 100:
                        my_w = 200 # Sidebar width
                        my_h = min(client_h, 800) # Max height
                        # Snap to the right
                        self.after(0, lambda x=client_x + client_w, y=client_y, h=my_h: self.geometry(f"{my_w}x{h}+{x}+{y}"))
                    time.sleep(0.5)
                else:
                    last_hwnd = 0
                    time.sleep(2.0)
            except Exception as e:
                time.sleep(2.0)

    def _on_close(self):
        self.running = False
        try:
            keyboard.unhook_all()
        except:
            pass
        self._stop_event.set()
        self.destroy()

if __name__ == "__main__":
    app = LeagueLoopApp()
    app.mainloop()
