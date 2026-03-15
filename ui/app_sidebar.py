import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image

from utils.path_utils import resource_path
from ui.components.factory import get_color, get_font, get_radius, TOKENS, make_button
from ui.ui_shared import CTkTooltip
from ui.components.priority_grid import PriorityIconGrid
from ui.components.settings_modal import SettingsModal

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

        self._setup_ui()

    def _setup_ui(self):
        # ── Header / Drag Area ──
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.header.pack(fill="x", pady=(6, 0), padx=4)
        
        self.lbl_title = ctk.CTkLabel(
            self.header, text="League Loop", 
            font=get_font("body", "bold"),
            text_color=get_color("colors.text.primary")
        )
        self.lbl_title.pack(side="left", padx=4)

        # ✕ Close
        self.btn_close = ctk.CTkButton(
            self.header, text="✕", width=20, height=20,
            corner_radius=10, font=("Arial", 11),
            fg_color="transparent", hover_color="#e81123",
            command=self.master._on_close
        )
        self.btn_close.pack(side="right", padx=(0, 2))

        # ⚙ Settings
        self.btn_settings = ctk.CTkButton(
            self.header, text="⚙", width=20, height=20,
            corner_radius=10, font=("Arial", 13),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._open_settings
        )
        self.btn_settings.pack(side="right", padx=(0, 1))

        # ▼ Collapse
        self._body_expanded = True
        self.btn_collapse = ctk.CTkButton(
            self.header, text="▼", width=20, height=20,
            corner_radius=10, font=("Arial", 10, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_body_collapse,
        )
        self.btn_collapse.pack(side="right", padx=(0, 1))

        self.drag_widgets = [self, self.header, self.lbl_title]

        # ── Collapsible Body ──
        self.main_body = ctk.CTkFrame(self, fg_color="transparent")
        self.main_body.pack(fill="both", expand=True)

        # ── Power Button ──
        self.img_off = None
        self.img_on = None
        try:
            idle_path = resource_path("assets/icon_idle.png")
            active_path = resource_path("assets/icon_active.png")
            if os.path.exists(idle_path):
                self.img_off = ctk.CTkImage(Image.open(idle_path), size=(56, 56))
            if os.path.exists(active_path):
                self.img_on = ctk.CTkImage(Image.open(active_path), size=(56, 56))
        except Exception as e:
            print(f"Icon load error: {e}")

        init_img = self.img_off or None
        init_text = "⏻" if not init_img else ""

        self.btn_power = ctk.CTkButton(
            self.main_body, text=init_text, image=init_img,
            font=("Arial", 20, "bold"), width=64, height=64,
            corner_radius=32, border_width=2,
            border_color=get_color("colors.text.muted"),
            fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            command=self._on_power_click,
        )
        self.btn_power.pack(pady=(12, 4))
        CTkTooltip(self.btn_power, "Click to Activate Automation")
        
        # Status
        self.lbl_status = ctk.CTkLabel(
            self.main_body, text="⏸ Paused", font=get_font("caption"),
            text_color=get_color("colors.text.muted")
        )
        self.lbl_status.pack(pady=(0, 8))

        # ── Divider ──
        ctk.CTkFrame(self.main_body, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=12, pady=4)

        # ── Action Buttons ──
        btn_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=6)

        self.btn_find_match = ctk.CTkButton(
            btn_frame, text="▶  Find Match",
            font=get_font("body", "bold"), height=32,
            corner_radius=get_radius("sm"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._find_match
        )
        self.btn_find_match.pack(fill="x", pady=2)

        # ── Toggles Section ──
        ctk.CTkFrame(self.main_body, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=12, pady=6)

        toggles_label = ctk.CTkLabel(
            self.main_body, text="AUTOMATION", font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w"
        )
        toggles_label.pack(fill="x", padx=14, pady=(2, 4))

        # Auto Accept
        self.var_accept = ctk.BooleanVar(value=self.config.get("auto_accept", True))
        self.sw_accept = ctk.CTkSwitch(
            self.main_body, text="Auto Accept", font=get_font("body"),
            variable=self.var_accept, command=self._on_toggle_accept,
            fg_color=get_color("colors.text.disabled"),
            progress_color=get_color("colors.accent.primary"),
            button_color=get_color("colors.text.primary"),
        )
        self.sw_accept.pack(fill="x", padx=14, pady=2)

        # Auto Re-Queue
        self.var_requeue = ctk.BooleanVar(value=self.config.get("auto_requeue", False))
        self.sw_requeue = ctk.CTkSwitch(
            self.main_body, text="Auto Re-Queue", font=get_font("body"),
            variable=self.var_requeue, command=self._on_toggle_requeue,
            fg_color=get_color("colors.text.disabled"),
            progress_color=get_color("colors.accent.primary"),
            button_color=get_color("colors.text.primary"),
        )
        self.sw_requeue.pack(fill="x", padx=14, pady=2)

        # Priority Picker
        self.var_priority = ctk.BooleanVar(value=self.config.get("priority_picker", {}).get("enabled", False))
        self.sw_priority = ctk.CTkSwitch(
            self.main_body, text="Priority Sniper", font=get_font("body"),
            variable=self.var_priority, command=self._on_toggle_priority,
            fg_color=get_color("colors.text.disabled"),
            progress_color=get_color("colors.accent.primary"),
            button_color=get_color("colors.text.primary"),
        )
        self.sw_priority.pack(fill="x", padx=14, pady=2)

        # ── Priority Icon Grid ──
        ctk.CTkFrame(self.main_body, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=12, pady=6)

        self.priority_grid = PriorityIconGrid(self.main_body, self.config, self.assets)
        self.priority_grid.pack(fill="x", padx=10, pady=2)

        # ── Action Log (Bottom) ──
        self.spacer = ctk.CTkFrame(self.main_body, fg_color="transparent")
        self.spacer.pack(fill="both", expand=True)

        # ── Lobby Stats (Hidden initially, packed before spacer when shown) ──
        self.stats_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")
        
        self.lbl_stats_title = ctk.CTkLabel(
            self.stats_frame, text="Lobby Stats", font=get_font("caption", "bold"),
            text_color=get_color("colors.accent.primary"), anchor="w"
        )
        self.lbl_stats_title.pack(fill="x", pady=(0, 4))
        
        self.stats_content = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        self.stats_content.pack(fill="x")
        # stats_frame is NOT packed yet — it appears only during ChampSelect

        ctk.CTkFrame(self.main_body, height=1, fg_color=get_color("colors.border.subtle")).pack(fill="x", padx=12)
        self.lbl_action = ctk.CTkLabel(
            self.main_body, text="Waiting for client...",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
            wraplength=170, anchor="w"
        )
        self.lbl_action.pack(fill="x", padx=14, pady=8)

    # ── Callbacks ──
    def _toggle_body_collapse(self):
        self._body_expanded = not self._body_expanded
        if self._body_expanded:
            self.main_body.pack(fill="both", expand=True)
            self.btn_collapse.configure(text="▼")
            self.master.geometry("200x400")
        else:
            self.main_body.pack_forget()
            self.btn_collapse.configure(text="▶")
            self.master.geometry("200x44")

    def _on_power_click(self):
        self.power_state = not self.power_state
        self.toggle_callback(self.power_state)
        
        if self.power_state:
            self.btn_power.configure(
                image=self.img_on or None,
                border_color=get_color("colors.accent.primary")
            )
            self.lbl_status.configure(text="▶ Active", text_color=get_color("colors.accent.primary"))
        else:
            self.btn_power.configure(
                image=self.img_off or None,
                border_color=get_color("colors.text.muted")
            )
            self.lbl_status.configure(text="⏸ Paused", text_color=get_color("colors.text.muted"))

    def _find_match(self):
        if self.lcu:
            # 1. Check current state
            state_req = self.lcu.request("GET", "/lol-lobby/v2/lobby/matchmaking/search-state")
            state_data = state_req.json() if state_req and state_req.status_code == 200 else {}
            
            if state_data.get("searchState") == "Searching":
                # Cancel search if already searching
                self.lcu.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
                self.update_action_log("Matchmaking Cancelled.")
                if self.power_state:
                    self._on_power_click()
                return

            # 2. Determine Queue ID based on ARAM Mode
            mode = self.config.get("aram_mode", "ARAM")
            # ARAM is generally 450. ARAM Mayhem queue ID varies depending on event, usually 1110 or similar.
            # We'll default to 450 for ARAM and a placeholder or known RGM ID for mayhem for now.
            queue_id = 450 if mode == "ARAM" else 1110 
            
            # 3. Create Lobby if needed
            self.lcu.request("POST", "/lol-lobby/v2/lobby", data={"queueId": queue_id})
            
            # 4. Start Search
            self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
            self.update_action_log(f"Starting Matchmaking ({mode})...")
            
            # 5. Turn on auto if it isn't
            if not self.power_state:
                self._on_power_click()

    def _on_toggle_accept(self):
        self.config.set("auto_accept", self.var_accept.get())

    def _on_toggle_requeue(self):
        self.config.set("auto_requeue", self.var_requeue.get())

    def _on_toggle_priority(self):
        cfg = self.config.get("priority_picker", {})
        cfg["enabled"] = self.var_priority.get()
        self.config.set("priority_picker", cfg)

    def update_action_log(self, text):
        self.lbl_action.configure(text=text)

    def update_lobby_stats(self, team, bench):
        """Called from AutomationEngine during ChampSelect to show winrate stats."""
        if not team and not bench:
            self.stats_frame.pack_forget()
            return

        self.stats_frame.pack(fill="x", padx=12, pady=6, before=self.spacer)

        # Clear existing rows
        for child in self.stats_content.winfo_children():
            child.destroy()

        if not self.scraper:
            return

        mode = self.config.get("aram_mode", "ARAM")
        self.lbl_stats_title.configure(text=f"{mode} Win Rates")

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
        SettingsModal(self.master, self.config, on_save_callback=self.master.on_settings_saved)
