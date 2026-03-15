import ctypes
import os
import sys
import threading
import time
import tkinter
import traceback
import queue

import customtkinter as ctk
from PIL import Image

from services.api_handler import LCUClient
from services.asset_manager import AssetManager, ConfigManager
from services.automation import AutomationEngine
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
        
        self.automation = None
        self.running = True
        self._stop_event = threading.Event()
        self._drag_data = {"x": 0, "y": 0}

        self.setup_ui()
        self._setup_window_dragging()

        self.automation = AutomationEngine(
            self.lcu,
            self.assets,
            self.config,
            log_func=self.sidebar.update_action_log,
            stop_func=lambda: self.after(0, lambda: self.sidebar._on_power_click())
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
        self.sidebar = SidebarWidget(self, self.toggle_power, self.config, lcu=self.lcu, assets=self.assets)
        self.sidebar.pack(fill="both", expand=True)

    def _setup_window_dragging(self):
        for widget in self.sidebar.drag_widgets:
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            
        # Add exit button manually somewhere or hotkey. We'll add a small 'X' top right
        self.btn_close = ctk.CTkButton(
            self.sidebar.header, 
            text="✕", 
            width=24, 
            height=24,
            corner_radius=12,
            fg_color="transparent", 
            hover_color="#e81123", # Windows close red
            command=self._on_close
        )
        self.btn_close.pack(side="right", padx=5)

    def on_drag_start(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def on_drag_motion(self, event):
        x = self.winfo_x() - self._drag_data["x"] + event.x
        y = self.winfo_y() - self._drag_data["y"] + event.y
        self.geometry(f"+{x}+{y}")

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
        while self.running and not self._stop_event.is_set():
            try:
                # We can check for standard Riot Client or League Client
                hwnd = ctypes.windll.user32.FindWindowW(None, "League of Legends")
                if hwnd == 0:
                     hwnd = ctypes.windll.user32.FindWindowW(None, "Riot Client")
                     
                if hwnd != 0:
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
            except Exception as e:
                pass
            time.sleep(0.5)

    def _on_close(self):
        self.running = False
        self._stop_event.set()
        self.destroy()

if __name__ == "__main__":
    app = LeagueLoopApp()
    app.mainloop()
