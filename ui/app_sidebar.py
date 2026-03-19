import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image

from utils.logger import Logger
from utils.path_utils import get_asset_path
from ui.components.factory import get_color, get_font, get_radius, TOKENS, make_button
from ui.ui_shared import CTkTooltip
from ui.components.priority_grid import PriorityIconGrid
from ui.components.settings_modal import SettingsModal
from ui.components.lol_toggle import LolToggle
from core.constants import SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL

class SidebarWidget(ctk.CTkFrame):
    def __init__(self, master, toggle_callback, config, lcu=None, assets=None, scraper=None):
        super().__init__(
            master, 
            corner_radius=0,
            fg_color=get_color("colors.background.app"),
            border_width=1,
            border_color=get_color("colors.border.subtle")
        )
        self.toggle_callback = toggle_callback
        self.config = config
        self.lcu = lcu
        self.assets = assets
        self.scraper = scraper
        self.power_state = False
        self.settings_window = None
        self.img_on = None
        self.img_off = None

        self._setup_ui()
        self.after(100, self._load_icons_async)

    def _setup_ui(self):
        # ── Header / Drag Area ──
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.header.pack(fill="x", pady=(SPACING_MD, SPACING_SM), padx=SPACING_MD)
        
        self.lbl_title = ctk.CTkLabel(
            self.header, text="League Loop", 
            font=get_font("body", "bold"),
            text_color=get_color("colors.text.primary"),
            anchor="w"
        )
        self.lbl_title.pack(side="left", fill="x", expand=True, padx=SPACING_XS)

        # ✕ Close
        self.btn_close = ctk.CTkButton(
            self.header, text="✕", width=20, height=20,
            corner_radius=10, font=("Arial", 11),
            fg_color="transparent", hover_color="#e81123",
            command=self.master._on_close,
            cursor="hand2"
        )
        self.btn_close.pack(side="right", padx=(4, 2))
        CTkTooltip(self.btn_close, "Close Application")

        # ⚙ Settings
        self.btn_settings = ctk.CTkButton(
            self.header, text="⚙", width=20, height=20,
            corner_radius=10, font=("Arial", 13),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._open_settings,
            cursor="hand2"
        )
        self.btn_settings.pack(side="right", padx=(4, 1))
        CTkTooltip(self.btn_settings, "Open Settings")

        # ▼ Collapse
        self._body_expanded = True
        self.btn_collapse = ctk.CTkButton(
            self.header, text="▼", width=20, height=20,
            corner_radius=10, font=("Arial", 10, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_body_collapse,
            cursor="hand2"
        )
        self.btn_collapse.pack(side="right", padx=(4, 1))
        self.tooltip_collapse = CTkTooltip(self.btn_collapse, "Collapse Sidebar")

        self.drag_widgets = [self, self.header, self.lbl_title]

        # ── Collapsible Body ──
        self.main_body = ctk.CTkFrame(self, fg_color="transparent")
        self.main_body.pack(fill="both", expand=True, padx=SPACING_MD, pady=SPACING_MD)

        # ── Status & Mode Selection ──
        status_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        status_frame.pack(fill="x", pady=(0, SPACING_MD))

        self.btn_power_status = make_button(
            status_frame, 
            text="▶ Active" if getattr(self, "power_state", False) else "⏸ Paused", 
            style="ghost",
            font=get_font("body", "bold"),
            text_color=get_color("colors.accent.primary") if getattr(self, "power_state", False) else get_color("colors.text.muted"),
            width=80,
            height=28,
            command=self._on_power_click
        )
        self.btn_power_status.pack(side="left", padx=(0, 4))
        CTkTooltip(self.btn_power_status, "Toggle Automation")

        self.var_game_mode = ctk.StringVar(value=self.config.get("aram_mode", "ARAM"))
        self.opt_game_mode = ctk.CTkOptionMenu(
            status_frame,
            variable=self.var_game_mode,
            values=[
                "Quickplay",
                "Draft Pick",
                "Ranked Solo/Duo",
                "Ranked Flex",
                "ARAM",
                "ARAM Mayhem",
                "Arena",
                "URF",
                "ARURF",
                "Nexus Blitz",
                "One For All",
                "Ultimate Spellbook",
                "TFT Normal",
                "TFT Ranked"
            ],
            font=get_font("caption"),
            fg_color=get_color("colors.background.card"),
            button_color=get_color("colors.background.card"),
            button_hover_color=get_color("colors.state.hover"),
            dropdown_fg_color=get_color("colors.background.app"),
            dropdown_hover_color=get_color("colors.state.hover"),
            dropdown_font=get_font("caption"),
            width=110,
            height=28,
            command=self._on_mode_change
        )
        self.opt_game_mode.pack(side="left", fill="x", expand=True)

        # Divider NOT here according to rules, instead replace with just action buttons
        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=0, pady=(0, SPACING_LG))

        self.btn_find_match = make_button(
            btn_frame, 
            text="▶  Find Match",
            style="primary",
            font=("Arial", 13, "bold"), 
            height=32,
            border_width=1,
            border_color="#F0E6D2",
            command=self._find_match
        )
        self.btn_find_match.pack(fill="x", pady=0)
        
        # Divider after button
        divider_btn = ctk.CTkFrame(self.main_body, height=1, fg_color="#1E2328")
        divider_btn.pack(fill="x", pady=SPACING_MD)

        # ── Toggles Section ──
        toggles_label = ctk.CTkLabel(
            self.main_body, text="AUTOMATION", font=("Arial", 11, "bold"),
            text_color=get_color("colors.accent.gold", "#C8AA6E"), anchor="w"
        )
        toggles_label.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        
        TOGGLE_ROW_HEIGHT = 28
        automation_frame = ctk.CTkFrame(self.main_body, height=110, fg_color="transparent")
        automation_frame.pack(fill="x", pady=(0, SPACING_LG))
        automation_frame.pack_propagate(False)

        # Auto Accept
        self.var_accept = ctk.BooleanVar(value=self.config.get("auto_accept", True))
        row1 = ctk.CTkFrame(automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row1.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row1.pack_propagate(False)
        ctk.CTkLabel(row1, text="Auto Accept", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2").pack(side="left")
        self.sw_accept = LolToggle(row1, variable=self.var_accept, command=self._on_toggle_accept)
        self.sw_accept.pack(side="right")

        # Auto Re-Queue
        self.var_requeue = ctk.BooleanVar(value=self.config.get("auto_requeue", False))
        row2 = ctk.CTkFrame(automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row2.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row2.pack_propagate(False)
        ctk.CTkLabel(row2, text="Auto Re-Queue", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2").pack(side="left")
        self.sw_requeue = LolToggle(row2, variable=self.var_requeue, command=self._on_toggle_requeue)
        self.sw_requeue.pack(side="right")

        # Priority Picker
        self.var_priority = ctk.BooleanVar(value=self.config.get("priority_picker", {}).get("enabled", False))
        row3 = ctk.CTkFrame(automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row3.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row3.pack_propagate(False)
        ctk.CTkLabel(row3, text="Priority Sniper", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2").pack(side="left")
        self.sw_priority = LolToggle(row3, variable=self.var_priority, command=self._on_toggle_priority)
        self.sw_priority.pack(side="right")
        
        # Divider after automation
        divider_auto = ctk.CTkFrame(self.main_body, height=1, fg_color="#1E2328")
        divider_auto.pack(fill="x", pady=SPACING_MD)

        # ── Priority Icon Grid ──
        # Let grid module handle spacing internally for right-pad and bottom pad
        self.priority_grid = PriorityIconGrid(self.main_body, self.config, self.assets)
        self.priority_grid.pack(fill="x", pady=(0, SPACING_MD), padx=(0, SPACING_SM)) # padx for scrollbar prevention

        # Divider before status
        divider_status = ctk.CTkFrame(self.main_body, height=1, fg_color="#1E2328")
        divider_status.pack(fill="x", pady=SPACING_MD)

        # ── Status Readout (Bottom Area) ──
        status_info_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        status_info_frame.pack(fill="x", padx=SPACING_MD, pady=(SPACING_LG, SPACING_MD))
        
        self.lbl_match_status = ctk.CTkLabel(status_info_frame, text="Status: Connected", font=("Arial", 10), text_color="#6C757D", anchor="w")
        self.lbl_match_status.pack(fill="x", pady=(0, SPACING_XS))
        
        self.lbl_queue_timer = ctk.CTkLabel(status_info_frame, text="Queue: Idle", font=("Arial", 10), text_color="#6C757D", anchor="w")
        self.lbl_queue_timer.pack(fill="x", pady=(0, SPACING_XS))

        # ── Action Log (Bottom) ──
        self.spacer = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.spacer.pack(fill="both", expand=True)

        # ── Lobby Stats (Hidden initially, packed before spacer when shown) ──
        self.stats_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        
        self.lbl_stats_title = ctk.CTkLabel(
            self.stats_frame, text="LOBBY STATS", font=("Arial", 11, "bold"),
            text_color=get_color("colors.accent.gold", "#C8AA6E"), anchor="w"
        )
        self.lbl_stats_title.pack(fill="x", padx=14, pady=(8, 2))
        
        ctk.CTkFrame(self.stats_frame, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=14, pady=(0, 8))
        
        self.stats_content = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="x", padx=14)
        # stats_frame is NOT packed yet — it appears only during ChampSelect

        ctk.CTkFrame(self.main_body, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=14)
        self.lbl_action = ctk.CTkLabel(
            self.main_body, text="Waiting for client...",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
            wraplength=200, anchor="w"
        )
        self.lbl_action.pack(fill="x", padx=14, pady=8)

    # ── Callbacks ──
    def _load_icons_async(self):
        if not self.winfo_exists(): return
        try:
            idle_path = get_asset_path("assets/icon_idle.png")
            active_path = get_asset_path("assets/icon_active.png")
            if os.path.exists(idle_path):
                self.img_off = ctk.CTkImage(Image.open(idle_path), size=(56, 56))
            if os.path.exists(active_path):
                self.img_on = ctk.CTkImage(Image.open(active_path), size=(56, 56))
        except Exception as e:
            print(f"Icon load error: {e}")

    def _toggle_body_collapse(self):
        self._body_expanded = not self._body_expanded
        if self._body_expanded:
            self.main_body.pack(fill="both", expand=True)
            self.btn_collapse.configure(text="▼")
            self.master.geometry("200x400")
            if hasattr(self, 'tooltip_collapse'):
                self.tooltip_collapse.text = "Collapse Sidebar"
        else:
            self.main_body.pack_forget()
            self.btn_collapse.configure(text="▶")
            self.master.geometry("200x44")
            if hasattr(self, 'tooltip_collapse'):
                self.tooltip_collapse.text = "Expand Sidebar"
    def _on_mode_change(self, new_mode):
        self.config.set("aram_mode", new_mode)
        if self.scraper:
            self.scraper.set_mode(new_mode)

    # ── Handlers ──
    def set_power_state(self, state: bool):
        """Pure visual/logical toggle without user-cancel side effects."""
        if getattr(self, "power_state", None) == state: return
        self.power_state = state
        try:
            self.var_power.set(state)
        except Exception as e:
            from utils.logger import Logger
            Logger.debug("UI", f"State sync error: {e}")

        if hasattr(self, "btn_power_status") and self.btn_power_status.winfo_exists():
            if state:
                self.btn_power_status.configure(text="▶ Active", text_color=get_color("colors.accent.primary"))
            else:
                self.btn_power_status.configure(text="⏸ Paused", text_color=get_color("colors.text.muted"))

        if self.toggle_callback:
            self.toggle_callback(self.power_state)

    def _on_power_click(self):
        """User clicks power button (may cancel search if active)."""
        if hasattr(self, "var_power"):
            new_state = self.var_power.get()
        else:
            new_state = not getattr(self, "power_state", False)
            
        self.set_power_state(new_state)

        if self.toggle_callback:
            state_req = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
            state_data = state_req.json() if state_req and state_req.status_code == 200 else {}
            
            if state_data.get("searchState") == "Searching":
                # Cancel search if already searching
                self.lcu.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
                self.update_action_log("Matchmaking Cancelled.")
                if getattr(self, "power_state", False):
                    self.set_power_state(False)
                return

    def _get_queue_id_for_mode(self, mode):
        """Dynamically resolve the queue ID from the client."""
        mode_map = {
            "Quickplay": 490,
            "Draft Pick": 400,
            "Ranked Solo/Duo": 420,
            "Ranked Flex": 440,
            "ARAM": 450,
            "ARAM Mayhem": 2400,
            "Arena": 1700,
            "URF": 900,
            "ARURF": 1010,
            "Nexus Blitz": 1300,
            "One For All": 1020,
            "Ultimate Spellbook": 1400,
            "TFT Normal": 1090,
            "TFT Ranked": 1100,
        }
        if mode in mode_map:
            return mode_map[mode]

        try:
            queues_req = self.lcu.request("GET", "/lol-game-queues/v1/queues")
            if queues_req and queues_req.status_code == 200:
                queues = queues_req.json()
                
                if mode == "ARAM Mayhem":
                    for q in queues:
                        if q.get("isCustom"): continue
                        name = q.get("name", "").lower()
                        desc = q.get("description", "").lower()
                        if "mayhem" in name or "mayhem" in desc:
                            return int(q.get("id"))

                for q in queues:
                    if q.get("isCustom"): continue
                    if mode.lower() in q.get("name", "").lower():
                        return int(q.get("id"))
        except Exception:
            pass
        return 450 # Default to ARAM

    def _find_match(self):
        """Aggressive matchmaking: Stay in the lobby tab, just change the queue."""
        if not self.lcu: return

        # 1. Check if already searching
        state_req = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
        state_data = state_req.json() if state_req and state_req.status_code == 200 else {}
        
        if state_data.get("searchState") == "Searching":
            self.lcu.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
            self.update_action_log("Matchmaking Cancelled.")
            if getattr(self, "power_state", False):
                self._on_power_click()
            return

        # 2. Resolve Queue ID
        mode = self.config.get("aram_mode", "ARAM")
        target_q_id = self._get_queue_id_for_mode(mode)
        self.update_action_log(f"Initiating {mode}...")

        def _execute_sync():
            import time
            # 1. Check current state
            lobby_req = self.lcu.request("GET", "/lol-lobby/v2/lobby")
            in_lobby = lobby_req and lobby_req.status_code == 200

            should_create = True

            if in_lobby:
                try:
                    data = lobby_req.json()
                    current_q = data.get("gameConfig", {}).get("queueId")

                    # If we are in the correct lobby already
                    if current_q == target_q_id:
                        should_create = False
                    else:
                        # Wrong lobby - Quit it
                        self.lcu.request(
                            "DELETE", "/lol-lobby/v2/lobby/matchmaking/search"
                        )  # Stop search if active
                        time.sleep(0.5)
                        self.lcu.request("DELETE", "/lol-lobby/v2/lobby")
                        time.sleep(0.5)
                except Exception:
                    # Failsafe if json serialization fails
                    should_create = True

            if should_create:
                self.lcu.request(
                    "POST", "/lol-lobby/v2/lobby", {"queueId": target_q_id}
                )
                time.sleep(1)

            # 2. Start Search
            res = self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
            
            def _update_ui():
                if res and res.status_code in [200, 204]:
                    self.update_action_log(f"Searching ({mode})...")
                    self.set_power_state(True)
                else:
                    self.update_action_log("Matchmaking failed — check client.")

            self.after(0, _update_ui)

        import threading
        threading.Thread(target=_execute_sync, daemon=True).start()

    def _on_toggle_accept(self):
        self.config.set("auto_accept", self.var_accept.get())

    def _on_toggle_requeue(self):
        self.config.set("auto_requeue", self.var_requeue.get())

    def _on_toggle_priority(self):
        cfg = self.config.get("priority_picker", {})
        cfg["enabled"] = self.var_priority.get()
        self.config.set("priority_picker", cfg)

    def update_action_log(self, text):
        if self.winfo_exists():
            self.lbl_action.configure(text=text)

    def update_lobby_stats(self, team, bench):
        """Called from AutomationEngine during ChampSelect to show winrate stats."""
        if not self.winfo_exists(): return
        if not team and not bench:
            self.stats_frame.pack_forget()
            self._last_stats_hash = None
            return

        mode = self.config.get("aram_mode", "ARAM")

        # Collect available champion IDs
        available = []
        for p in team:
            cid = p.get("championId")
            if cid:
                available.append(cid)
        for p in bench:
            cid = p.get("championId")
            if cid:
                available.append(cid)

        # Memoize rendering: only update if mode or champ pool changes
        current_hash = (mode, tuple(sorted(available)))
        if getattr(self, "_last_stats_hash", None) == current_hash:
            return
        self._last_stats_hash = current_hash

        self.stats_frame.pack(fill="x", padx=12, pady=6, before=self.spacer)

        # Clear existing rows
        for child in self.stats_content.winfo_children():
            child.destroy()

        if not self.scraper:
            return

        title_text = f"{mode} Win Rates"
        title_color = get_color("colors.accent.gold", "#C8AA6E")
        if getattr(self.scraper, "is_offline", False):
            title_text += " (Offline Mode)"
            title_color = get_color("colors.text.muted", "#6C757D")
            
        self.lbl_stats_title.configure(text=title_text, text_color=title_color)

        # Resolve names and winrates
        champ_stats = []
        for cid in set(available):
            cname = self.assets.get_champ_name(cid) if self.assets else None
            if cname:
                wr = self.scraper.get_winrate(cname)
                champ_stats.append((cname, wr))

        # Sort descending by win rate
        champ_stats.sort(key=lambda x: x[1], reverse=True)

        # Render Top 5
        for i, (cname, wr) in enumerate(champ_stats[:5]):
            row = ctk.CTkFrame(self.stats_content, fg_color="transparent")
            row.pack(fill="x", pady=1)

            lbl_name = ctk.CTkLabel(row, text=cname, font=get_font("body"), text_color=get_color("colors.text.primary"))
            lbl_name.pack(side="left")

            color = "#00cc66" if wr >= 52.0 else "#ff4444" if wr < 48.0 else get_color("colors.text.muted")

            lbl_wr = ctk.CTkLabel(row, text=f"{wr:.1f}%", font=get_font("body", "bold"), text_color=color)
            lbl_wr.pack(side="right")

    def _open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsModal(self.master, self.config, on_save_callback=self.master.on_settings_saved)
        else:
            self.settings_window.focus_force()
            self.settings_window.lift()
