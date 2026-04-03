import tkinter as tk
import customtkinter as ctk  # type: ignore
import os
from PIL import Image  # type: ignore

from utils.logger import Logger  # type: ignore
from utils.path_utils import get_asset_path  # type: ignore
from ui.components.factory import get_color, get_font, get_radius, TOKENS, make_button  # type: ignore
from ui.ui_shared import CTkTooltip  # type: ignore
from ui.components.priority_grid import PriorityIconGrid  # type: ignore
from ui.components.settings_modal import SettingsModal  # type: ignore
from ui.components.lol_toggle import LolToggle  # type: ignore
from ui.components.friend_list import FriendPriorityList  # type: ignore
from core.constants import SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL  # type: ignore

class SidebarWidget(ctk.CTkFrame):
    def __init__(self, master, toggle_callback, config, lcu=None, assets=None, scraper=None):
        super().__init__(  # type: ignore
            master, 
            corner_radius=0,  # type: ignore
            fg_color=get_color("colors.background.app"),  # type: ignore
            border_width=1,  # type: ignore
            border_color=get_color("colors.border.subtle")  # type: ignore
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
        self._queue_timer_job = None

        self._setup_ui()
        self.after(100, self._load_icons_async)

    def _setup_ui(self):
        # ── Header / Drag Area ──
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.header.pack(fill="x", pady=(SPACING_MD, SPACING_SM), padx=SPACING_MD)
        
        self.lbl_title = ctk.CTkLabel(
            self.header, text="League Loop", 
            font=get_font("title", "bold"), 
            text_color=get_color("colors.text.primary")
        )
        self.lbl_title.pack(side="left", fill="x", expand=True, padx=SPACING_XS)

        # ✕ Close
        self.btn_close = ctk.CTkButton(
            self.header, text="✕", width=20, height=20,
            corner_radius=10, font=("Arial", 11),
            fg_color="transparent", hover_color="#e81123",
            command=self.master._on_close, cursor="hand2",
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
            command=self._open_settings, cursor="hand2",
            )
        self.btn_settings.pack(side="right", padx=(4, 1))
        CTkTooltip(self.btn_settings, "Open Settings")

        # ▼ Minimize
        self.btn_minimize = ctk.CTkButton(
            self.header, text="—", width=20, height=20,
            corner_radius=10, font=("Arial", 10, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._minimize_window, cursor="hand2",
            )
        self.btn_minimize.pack(side="right", padx=(4, 1))
        hk_compact = self.config.get("hotkey_compact_mode", "ctrl+shift+m").upper()
        self.tooltip_minimize = CTkTooltip(self.btn_minimize, f"Minimize Sidebar ({hk_compact})")

        self.drag_widgets = [self, self.header, self.lbl_title]

        # ── Collapsible Body ──
        self.main_body = ctk.CTkFrame(self, fg_color="transparent")
        self.main_body.pack(fill="both", expand=True, padx=SPACING_MD, pady=SPACING_MD)

        self.power_state = True
        self.var_power = ctk.BooleanVar(value=True)

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
        hk_auto = self.config.get("hotkey_toggle_automation", "ctrl+shift+a").upper()
        CTkTooltip(self.btn_power_status, f"Toggle Automation ({hk_auto})")

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
            command=self._on_mode_change,
            cursor="hand2",
        )
        self.opt_game_mode.pack(side="left", fill="x", expand=True)
        CTkTooltip(self.opt_game_mode, "Select Game Mode")

        # ── Session Info Block (always visible) ──
        self.session_frame = ctk.CTkFrame(
            self.main_body,
            height=64,
            fg_color="#0F1A24",
            corner_radius=get_radius("md")
        )
        self.session_frame.pack(fill="x", pady=(0, SPACING_MD))
        self.session_frame.pack_propagate(False)
        self.session_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.queue_label = ctk.CTkLabel(
            self.session_frame,
            text=self.var_game_mode.get(),
            font=("Segoe UI", 12, "bold"),
            text_color="#C8AA6E"
        )
        self.queue_label.grid(row=0, column=0, padx=8, pady=(10, 2), sticky="w", columnspan=2)

        self.time_label = ctk.CTkLabel(
            self.session_frame,
            text="Queue: Idle",
            font=("Segoe UI", 11),
            text_color=get_color("colors.text.primary")
        )
        self.time_label.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="w")

        self.estimate_label = ctk.CTkLabel(
            self.session_frame,
            text="● Connected",
            font=("Segoe UI", 11),
            text_color="#00C853"
        )
        self.estimate_label.grid(row=1, column=1, padx=8, pady=(0, 10), sticky="e")

        self.session_separator = ctk.CTkFrame(
            self.session_frame,
            height=1,
            fg_color="#1F2A36"
        )
        self.session_separator.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw")

        self.progress_bar = ctk.CTkProgressBar(
            self.session_frame,
            height=3,
            corner_radius=0,
            progress_color=get_color("colors.accent.gold", "#C8AA6E")
        )
        self.progress_bar.set(0)
        self.progress_bar.place(relx=0, rely=0.98, relwidth=1.0, anchor="sw")

        # ── Action Buttons ──
        self.action_container = ctk.CTkFrame(self.main_body, fg_color="#0F1A24", corner_radius=get_radius("md"))
        self.action_container.pack(fill="x", pady=(0, SPACING_LG))

        self.btn_frame = ctk.CTkFrame(self.action_container, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=12, pady=12)

        # Session Block relocated above self.action_container

        # ── Find Match (primary action) ──
        self.btn_find_match = make_button(
            self.btn_frame, 
            text="▶  Find Match",
            style="primary",
            font=("Arial", 13, "bold"), 
            height=32,
            border_width=1,
            border_color="#F0E6D2",
            command=self._find_match
        )
        self.btn_find_match.pack(fill="x", pady=0)
        hk_find = self.config.get("hotkey_find_match", "ctrl+shift+f").upper()
        CTkTooltip(self.btn_find_match, f"Start or Cancel Matchmaking ({hk_find})")

        # ── STEP 2: Divider above Quick Actions ──
        self.actions_divider = ctk.CTkFrame(
            self.btn_frame,
            height=1,
            fg_color="#1F2A36"
        )
        # Starts hidden — shown alongside quick action buttons

        # ── STEP 2: Quick Actions Row (2-column grid, fixed height) ──
        self.quick_actions_frame = ctk.CTkFrame(
            self.btn_frame,
            height=44,
            fg_color="transparent"
        )
        # Starts hidden — revealed dynamically during Matchmaking/ChampSelect
        self.quick_actions_frame.pack_propagate(False)
        self.quick_actions_frame.grid_columnconfigure((0, 1), weight=1)

        self.requeue_button = make_button(
            self.quick_actions_frame,
            text="Requeue",
            style="primary",
            font=("Arial", 12, "bold"),
            height=32,
            border_width=1,
            border_color="#F0E6D2",
            command=self._force_requeue,
        )
        # NOT gridded here — dynamically revealed in _show_quick_actions()
        CTkTooltip(self.requeue_button, "Cancel and re-enter matchmaking queue")

        self.dodge_button = make_button(
            self.quick_actions_frame,
            text="Dodge",
            style="secondary",
            font=("Arial", 12, "bold"),
            height=32,
            border_width=1,
            border_color="#F0E6D2",
            command=self._force_dodge,
        )
        # NOT gridded here — dynamically revealed in _show_quick_actions()
        CTkTooltip(self.dodge_button, "Force quit the client to dodge the lobby")

        # ── Launch Client ──
        self.btn_launch_client = make_button(
            self.btn_frame,
            text="🚀 Launch Client",
            style="secondary",
            font=get_font("body", "bold"),
            height=32,
            command=lambda: self.master._hotkey_launch_client() if hasattr(self.master, "_hotkey_launch_client") else None
        )
        self.btn_launch_client.pack(fill="x", pady=(SPACING_SM, 0))
        hk_launch = self.config.get("hotkey_launch_client", "ctrl+shift+l").upper()
        CTkTooltip(self.btn_launch_client, f"Open the Riot Client and start League ({hk_launch})")

        # Divider after button
        self.divider_btn = ctk.CTkFrame(self.main_body, height=1, fg_color="#1E2328")
        self.divider_btn.pack(fill="x", pady=SPACING_MD)

        # ── Toggles Section ──
        self.auto_container = ctk.CTkFrame(self.main_body, fg_color="#0F1A24", corner_radius=get_radius("md"))
        self.auto_container.pack(fill="x", pady=(0, SPACING_LG))

        self.auto_expanded = False
        self.lbl_auto_section = ctk.CTkLabel(
            self.auto_container, text="▶  AUTOMATION",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
            cursor="hand2"
        )
        self.lbl_auto_section.pack(fill="x", padx=SPACING_MD, pady=(SPACING_SM, SPACING_SM))
        CTkTooltip(self.lbl_auto_section, "Toggle Automation")
        self.lbl_auto_section.bind("<Button-1>", self._toggle_auto_collapse)
        self.lbl_auto_section.bind("<Enter>", lambda e: self.lbl_auto_section.configure(text_color=get_color("colors.text.primary")))
        self.lbl_auto_section.bind("<Leave>", lambda e: self.lbl_auto_section.configure(text_color=get_color("colors.text.muted")))
        
        TOGGLE_ROW_HEIGHT = 28
        self.automation_frame = ctk.CTkFrame(self.auto_container, height=155, fg_color="transparent")
        self.automation_frame.pack_propagate(False)

        # Auto Accept
        self.var_accept = ctk.BooleanVar(value=self.config.get("auto_accept", True))
        row1 = ctk.CTkFrame(self.automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row1.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row1.pack_propagate(False)
        lbl_accept = ctk.CTkLabel(row1, text="✅ Auto Accept", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2")
        lbl_accept.pack(side="left")
        CTkTooltip(lbl_accept, "Automatically accepts match queue pops")
        self.sw_accept = LolToggle(row1, variable=self.var_accept, command=self._on_toggle_accept)
        self.sw_accept.pack(side="right")
        CTkTooltip(self.sw_accept, "Automatically accepts match queue pops")

        # ARAM Picker
        self.var_priority = ctk.BooleanVar(value=self.config.get("priority_picker", {}).get("enabled", False))
        row3 = ctk.CTkFrame(self.automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row3.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row3.pack_propagate(False)
        lbl_priority = ctk.CTkLabel(row3, text="🎯 ARAM Picker", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2")
        lbl_priority.pack(side="left")
        CTkTooltip(lbl_priority, "Attempts to pick highest available champion from ARAM List")
        self.sw_priority = LolToggle(row3, variable=self.var_priority, command=self._on_toggle_priority)
        self.sw_priority.pack(side="right")
        CTkTooltip(self.sw_priority, "Attempts to pick highest available champion from ARAM List")
        
        # Friend Auto-Join
        self.var_auto_join = ctk.BooleanVar(value=self.config.get("auto_join_enabled", True))
        row4 = ctk.CTkFrame(self.automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row4.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row4.pack_propagate(False)
        lbl_auto_join = ctk.CTkLabel(row4, text="🤝 Friend Auto-Join", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2")
        lbl_auto_join.pack(side="left")
        CTkTooltip(lbl_auto_join, "Automatically joins available friend lobbies")
        self.sw_auto_join = LolToggle(row4, variable=self.var_auto_join, command=self._on_toggle_auto_join)
        self.sw_auto_join.pack(side="right")
        CTkTooltip(self.sw_auto_join, "Automatically joins available friend lobbies")

        # Auto Honor
        self.var_auto_honor = ctk.BooleanVar(value=self.config.get("auto_honor_enabled", False))
        row5 = ctk.CTkFrame(self.automation_frame, fg_color="transparent", height=TOGGLE_ROW_HEIGHT)
        row5.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        row5.pack_propagate(False)
        lbl_honor = ctk.CTkLabel(row5, text="🏅 Auto Honor", font=get_font("body"), width=120, anchor="w", text_color="#F0E6D2")
        lbl_honor.pack(side="left")
        CTkTooltip(lbl_honor, "Automatically honors a teammate after each game")
        self.sw_auto_honor = LolToggle(row5, variable=self.var_auto_honor, command=self._on_toggle_auto_honor)
        self.sw_auto_honor.pack(side="right")
        CTkTooltip(self.sw_auto_honor, "Automatically honors a teammate after each game")
        self._update_auto_header()
        
        # Divider after automation
        divider_auto = ctk.CTkFrame(self.main_body, height=1, fg_color="#1E2328")
        divider_auto.pack(fill="x", pady=SPACING_MD)

        # ── Priority Icon Grid ──
        # Let grid module handle spacing internally for right-pad and bottom pad
        self.priority_grid = PriorityIconGrid(self.main_body, self.config, self.assets)
        self.priority_grid.pack(fill="x", pady=(0, SPACING_MD), padx=0)
        
        # ── Friend Auto-Join List ──
        self.friend_list = FriendPriorityList(self.main_body, config=self.config, lcu=self.lcu)
        self.friend_list.pack(fill="x", pady=(0, SPACING_MD), padx=0)

        # UI status and dummy stats stripped for cleaner layout

        # ── Profile Section ──
        self.profile_container = ctk.CTkFrame(self.main_body, fg_color="#0F1A24", corner_radius=get_radius("md"))
        self.profile_container.pack(fill="x", pady=(0, SPACING_MD))

        self.profile_expanded = False
        self.lbl_profile_section = ctk.CTkLabel(
            self.profile_container, text="▶  PROFILE",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
            cursor="hand2"
        )
        self.lbl_profile_section.pack(fill="x", padx=SPACING_MD, pady=(SPACING_SM, SPACING_SM))
        self.tooltip_profile = CTkTooltip(self.lbl_profile_section, "Toggle Profile")
        self.lbl_profile_section.bind("<Button-1>", self._toggle_profile_collapse)
        self.lbl_profile_section.bind("<Enter>", lambda e: self.lbl_profile_section.configure(text_color=get_color("colors.text.primary")))
        self.lbl_profile_section.bind("<Leave>", lambda e: self.lbl_profile_section.configure(text_color=get_color("colors.text.muted")))

        self.profile_frame = ctk.CTkFrame(self.profile_container, fg_color="transparent")
        # starts collapsed

        lbl_status = ctk.CTkLabel(self.profile_frame, text="Custom Status", font=get_font("caption"), text_color=get_color("colors.text.muted"), anchor="w")
        lbl_status.pack(fill="x", padx=SPACING_MD, pady=(0, 2))

        self.entry_status = ctk.CTkEntry(
            self.profile_frame,
            placeholder_text="Set your status...",
            font=get_font("body"),
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_color=get_color("colors.border.subtle"),
            height=30,
        )
        self.entry_status.pack(fill="x", padx=SPACING_MD, pady=(0, SPACING_SM))
        self.entry_status.bind("<Return>", self._on_status_submit)
        CTkTooltip(self.entry_status, "Press Enter to update your League Client status")

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

        action_row = ctk.CTkFrame(self.main_body, fg_color="transparent")
        action_row.pack(fill="x", padx=14, pady=8)

        self.lbl_action = ctk.CTkLabel(
            action_row, text="Waiting for client...",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
            wraplength=170, anchor="w"
        )
        self.lbl_action.pack(side="left", fill="x", expand=True)

        self.btn_clear_log = ctk.CTkButton(
            action_row, text="✕", width=18, height=18,
            corner_radius=9, font=("Arial", 10),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover", "#e81123"),
            command=self._clear_action_log, cursor="hand2",
            )
        self.btn_clear_log.pack(side="right", padx=(4, 0))
        CTkTooltip(self.btn_clear_log, "Clear Log")

    # ── Callbacks ──
    def _load_icons_async(self):
        if not self.winfo_exists(): return  # type: ignore
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
        h = self.master.winfo_height()
        if self._body_expanded:
            self.header.pack_configure(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)
            self.lbl_title.pack(side="left")
            self.btn_close.pack(side="right", padx=(4, 2))
            self.btn_settings.pack(side="right", padx=(4, 1))
            self.btn_minimize.pack(side="right", padx=(4, 1))
            self.btn_collapse.pack(side="right", padx=(4, 1))
            self.main_body.pack(fill="both", expand=True)
            self.btn_collapse.configure(text="◀")
            self.master.geometry(f"200x{h}")
            if hasattr(self, 'tooltip_collapse'):
                self.tooltip_collapse.configure(text="Collapse Sidebar")
        else:
            self.main_body.pack_forget()
            self.btn_close.pack_forget()
            self.btn_settings.pack_forget()
            self.btn_minimize.pack_forget()
            self.lbl_title.pack_forget()
            
            self.header.pack_configure(fill="both", expand=True, padx=0, pady=0)
            self.btn_collapse.pack_configure(side="top", pady=10, padx=0)
            
            self.btn_collapse.configure(text="▶")
            self.master.geometry("44x44")
            if hasattr(self, 'tooltip_collapse'):
                self.tooltip_collapse.configure(text="Expand Sidebar")
            
    def _minimize_window(self):
        """Minimize via Win32 API — tkinter's iconify() is blocked by overrideredirect(True)."""
        import ctypes
        SW_MINIMIZE = 6
        hwnd = ctypes.windll.user32.GetParent(self.master.winfo_id())
        if hwnd == 0:
            hwnd = self.master.winfo_id()
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)



    def _toggle_auto_collapse(self, event=None):
        self.auto_expanded = not getattr(self, "auto_expanded", True)
        if self.auto_expanded:
            self.automation_frame.pack(fill="x")
        else:
            self.automation_frame.pack_forget()
        self._update_auto_header()

    def _on_mode_change(self, new_mode):
        self.config.set("aram_mode", new_mode)
        if self.scraper:
            self.scraper.set_mode(new_mode)
        if hasattr(self, "queue_label"):
            self.queue_label.configure(text=new_mode)

    # ── Handlers ──
    def on_lcu_connection_changed(self, connected: bool):
        if not self.winfo_exists(): return
        if connected:
            if hasattr(self, "btn_launch_client") and bool(self.btn_launch_client.winfo_manager()):
                self.btn_launch_client.pack_forget()
                if hasattr(self, "divider_btn"):
                    self.divider_btn.pack_forget()
        else:
            self._hide_quick_actions()
            self._stop_local_queue_timer()
            
            if hasattr(self, "btn_launch_client") and not bool(self.btn_launch_client.winfo_manager()):
                self.btn_launch_client.pack(fill="x", pady=(SPACING_SM, 0))
                if hasattr(self, "divider_btn") and hasattr(self, "auto_container"):
                    self.divider_btn.pack(fill="x", pady=SPACING_MD, before=self.auto_container)
            self.time_label.configure(text="Disconnected", text_color="#ff4444")
            self.estimate_label.configure(text="● Offline", text_color="#ff4444")

    def set_power_state(self, state: bool):
        """Pure visual/logical toggle without user-cancel side effects."""
        if getattr(self, "power_state", None) == state: return
        self.power_state = state
        try:
            self.var_power.set(state)
        except Exception as e:
            from utils.logger import Logger  # type: ignore
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

    def _get_queue_id_for_mode(self, mode: str):
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

                # ⚡ Bolt: Hoist the target string's normalization outside the loop
                # to prevent redundant string allocations on every iteration.
                if isinstance(mode, str):
                    mode_lower = mode.lower()
                    for q in queues:
                        if q.get("isCustom"): continue
                        q_name = q.get("name")
                        if isinstance(q_name, str):
                            if mode_lower in q_name.lower():
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
        self._update_auto_header()

    def _on_toggle_priority(self):
        cfg = self.config.get("priority_picker", {})
        cfg["enabled"] = self.var_priority.get()
        self.config.set("priority_picker", cfg)
        self._update_auto_header()

    def _on_toggle_auto_join(self):
        self.config.set("auto_join_enabled", self.var_auto_join.get())
        self._update_auto_header()

    def _on_toggle_auto_honor(self):
        self.config.set("auto_honor_enabled", self.var_auto_honor.get())
        self._update_auto_header()

    def _on_mass_invite(self):
        engine = getattr(self.master, "automation", None)
        if engine:
            import threading
            def _invite():
                engine.mass_invite_friends()
            threading.Thread(target=_invite, daemon=True).start()
        else:
            self.update_action_log("Automation engine not available.")

    def _toggle_profile_collapse(self, event=None):
        self.profile_expanded = not getattr(self, "profile_expanded", False)
        if self.profile_expanded:
            self.lbl_profile_section.configure(text="▼  PROFILE")
            self.profile_frame.pack(fill="x")
        else:
            self.lbl_profile_section.configure(text="▶  PROFILE")
            self.profile_frame.pack_forget()

    def _on_status_submit(self, event=None):
        text = self.entry_status.get().strip()
        engine = getattr(self.master, "automation", None)
        if engine and text:
            import threading
            threading.Thread(target=lambda: engine.set_custom_status(text), daemon=True).start()

    def _update_auto_header(self):
        emojis = []
        if getattr(self, "var_accept", None) and self.var_accept.get(): emojis.append("✅")
        if getattr(self, "var_priority", None) and self.var_priority.get(): emojis.append("🎯")
        if getattr(self, "var_auto_join", None) and self.var_auto_join.get(): emojis.append("🤝")
        if getattr(self, "var_auto_honor", None) and self.var_auto_honor.get(): emojis.append("🏅")
        
        arrow = "▼" if getattr(self, "auto_expanded", True) else "▶"
        base_text = f"{arrow}  AUTOMATION"
        
        if emojis:
            self.lbl_auto_section.configure(text=f"{base_text}    {' '.join(emojis)}")
        else:
            self.lbl_auto_section.configure(text=base_text)

    def update_action_log(self, text):
        if self.winfo_exists():
            self.lbl_action.configure(text=text)

    def _clear_action_log(self):
        if self.winfo_exists():
            self.lbl_action.configure(text="Idle.")

    def _force_requeue(self):
        if hasattr(self, "master") and hasattr(self.master, "lcu"):
            try:
                # Cancel current queue if active, then restart it
                self.master.lcu.request("DELETE", "/lol-lobby/v2/lobby/matchmaking/search")
                import time
                time.sleep(0.5)
                self.master.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
                self.update_action_log("Re-queued Matchmaking.")
            except Exception as e:
                self.update_action_log(f"Requeue error: {e}")

    def _force_dodge(self):
        if hasattr(self, "master") and hasattr(self.master, "lcu"):
            try:
                # Most reliable way to dodge is terminating the client UX
                self.master.lcu.request("POST", "/process-control/v1/process/quit")
                self.update_action_log("Client exiting (Dodging)...")
            except Exception as e:
                self.update_action_log(f"Dodge error: {e}")


    def _show_quick_actions(self):
        """Reveal the Requeue & Dodge buttons during active matchmaking phases."""
        if hasattr(self, "quick_actions_frame") and not self.quick_actions_frame.winfo_viewable():
            self.requeue_button.grid(row=0, column=0, padx=(0, 6), pady=6, sticky="ew")
            self.dodge_button.grid(row=0, column=1, padx=(6, 0), pady=6, sticky="ew")
            self.actions_divider.pack(fill="x", pady=(6, 4))
            self.quick_actions_frame.pack(fill="x", pady=(4, 8))

    def _hide_quick_actions(self):
        """Hide the Requeue & Dodge buttons when idle or in-game."""
        if hasattr(self, "quick_actions_frame") and self.quick_actions_frame.winfo_viewable():
            self.requeue_button.grid_remove()
            self.dodge_button.grid_remove()
            self.quick_actions_frame.pack_forget()
            self.actions_divider.pack_forget()

    def _start_local_queue_timer(self, time_in_queue, estimated_time):
        """Start or re-sync the local queue timer. Idempotent — won't restart if already running."""
        self._estimated_queue_time = estimated_time if estimated_time > 0 else 120

        # If the timer is already ticking, only re-sync if drift is extreme (>5s)
        if hasattr(self, "_queue_timer_job") and self._queue_timer_job is not None:
            drift = abs(getattr(self, "_current_queue_time", 0) - time_in_queue)
            if drift <= 5:
                return  # Timer is running fine, don't touch it
        
        self._stop_local_queue_timer()
        self._current_queue_time = time_in_queue
        self._tick_local_timer()

    def _tick_local_timer(self):
        if not self.winfo_exists():
            return

        mins = int(self._current_queue_time // 60)
        secs = int(self._current_queue_time % 60)
        time_str = f"Queue: {mins}:{secs:02d}"

        self.time_label.configure(text=time_str)

        est = getattr(self, "_estimated_queue_time", 120)
        if est > 0:
            est_mins = int(est // 60)
            est_secs = int(est % 60)
            self.estimate_label.configure(text=f"Est: {est_mins}:{est_secs:02d}", text_color=get_color("colors.text.muted"))

            progress = min(1.0, self._current_queue_time / est)
            self.progress_bar.set(progress)

            if self._current_queue_time > est:
                # Overtime: solid warning color, no pulsing
                self.progress_bar.configure(progress_color="#ff4444")
                self.time_label.configure(text_color="#ff4444")
                self.estimate_label.configure(text="Overtime!", text_color="#ff4444")
            else:
                self.progress_bar.configure(progress_color=get_color("colors.accent.gold", "#C8AA6E"))
                self.time_label.configure(text_color=get_color("colors.text.primary"))
        else:
            self.progress_bar.set(0)

        self._current_queue_time += 1
        self._queue_timer_job = self.after(1000, self._tick_local_timer)

    def _stop_local_queue_timer(self):
        if hasattr(self, "_queue_timer_job") and self._queue_timer_job is not None:
            self.after_cancel(self._queue_timer_job)
            self._queue_timer_job = None
        if hasattr(self, "progress_bar"):
            self.progress_bar.set(0)
            self.progress_bar.configure(progress_color=get_color("colors.accent.gold", "#C8AA6E"))
        if hasattr(self, "time_label"):
            self.time_label.configure(text_color=get_color("colors.text.primary"))


    def update_queue_state(self, phase, search_state):
        if not self.winfo_exists():
            return

        # Track the last phase we processed to avoid redundant resets
        prev_ui_phase = getattr(self, "_last_ui_phase", None)

        if phase == "Matchmaking" and search_state and search_state.get("searchState") == "Searching":
            time_in_queue = search_state.get("timeInQueue", 0)
            estimated_time = search_state.get("estimatedQueueTime", 0)
            self._start_local_queue_timer(time_in_queue, estimated_time)
            self._show_quick_actions()
            self._last_ui_phase = "Matchmaking"

        elif phase == "ReadyCheck":
            if prev_ui_phase != "ReadyCheck":
                self._stop_local_queue_timer()
                self.time_label.configure(text="Match Found!", text_color=get_color("colors.state.success", "#00C853"))
                self.estimate_label.configure(text="● Ready", text_color="#00C853")
                self.progress_bar.set(1.0)
                self.progress_bar.configure(progress_color="#00C853")
                self._show_quick_actions()

                try:
                    from ui.components.toast import ToastManager
                    ToastManager.get_instance().show("Match Found!", icon="⚔️", duration=4000, theme="success", confetti=True)
                except Exception as e:
                    Logger.error("UI", f"Failed to show match found toast: {e}")
            self._last_ui_phase = "ReadyCheck"

        elif phase == "ChampSelect":
            if prev_ui_phase != "ChampSelect":
                self._stop_local_queue_timer()
                self.time_label.configure(text="Champ Select", text_color=get_color("colors.accent.purple", "#A855F7"))
                self.estimate_label.configure(text="● Drafting", text_color="#A855F7")
                self.progress_bar.set(1.0)
                self.progress_bar.configure(progress_color="#A855F7")
                self._show_quick_actions()
            self._last_ui_phase = "ChampSelect"

        elif phase in ["InProgress", "EndOfGame"]:
            if prev_ui_phase not in ["InProgress", "EndOfGame"]:
                self._stop_local_queue_timer()
                self.time_label.configure(text="In Game", text_color=get_color("colors.text.primary"))
                self.estimate_label.configure(text="● Playing", text_color="#3B82F6")
                self.progress_bar.set(0)
                self._hide_quick_actions()
            self._last_ui_phase = phase

        else:
            # Lobby / None — only update if we actually changed phases
            if prev_ui_phase not in ["Lobby", "None", None] or prev_ui_phase is None:
                self._stop_local_queue_timer()
                if getattr(self.master, "lcu", None) and self.master.lcu.is_connected:
                    self.time_label.configure(text="Queue: Idle", text_color=get_color("colors.text.primary"))
                    self.estimate_label.configure(text="● Connected", text_color="#00C853")
                else:
                    self.time_label.configure(text="Disconnected", text_color="#ff4444")
                    self.estimate_label.configure(text="● Offline", text_color="#ff4444")
                self.progress_bar.set(0)
                self._hide_quick_actions()
            self._last_ui_phase = phase

    def update_lobby_stats(self, team, bench, me=None):
        """Called from AutomationEngine during ChampSelect to show winrate stats."""
        if not self.winfo_exists(): return
        
        # Pass hovered champion to priority grid
        champ_id = me.get("championId", 0) if me else 0
        if hasattr(self, "priority_grid") and hasattr(self.priority_grid, "set_hovered_champion"):
            self.priority_grid.set_hovered_champion(champ_id)

        if not team and not bench:
            self.stats_frame.pack_forget()
            self._last_stats_hash = None
            return

        mode = self.config.get("aram_mode", "ARAM")

        # Resolve active queue_id from LCU lobby for precise win rate dataset
        queue_id = None
        if self.lcu:
            try:
                lobby_req = self.lcu.request("GET", "/lol-lobby/v2/lobby")
                if lobby_req and lobby_req.status_code == 200:
                    queue_id = lobby_req.json().get("gameConfig", {}).get("queueId")
            except Exception:
                pass

        # Sync scraper dataset — prefer queue_id for precision, fall back to mode string
        if self.scraper:
            if queue_id and hasattr(self.scraper, "set_mode_by_queue_id"):
                self.scraper.set_mode_by_queue_id(queue_id)
            else:
                self.scraper.set_mode(mode)

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

        # ⚡ Bolt: Apply LICM for faster lobby stats rendering
        font_body = get_font("body")
        font_body_bold = get_font("body", "bold")
        color_text_primary = get_color("colors.text.primary")
        color_text_muted = get_color("colors.text.muted")

        # Render Top 5
        for i, (cname, wr) in enumerate(champ_stats[:5]):  # type: ignore
            row = ctk.CTkFrame(self.stats_content, fg_color="transparent")
            row.pack(fill="x", pady=1)

            lbl_name = ctk.CTkLabel(row, text=cname, font=font_body, text_color=color_text_primary)
            lbl_name.pack(side="left")

            color = "#00cc66" if wr >= 52.0 else "#ff4444" if wr < 48.0 else color_text_muted

            lbl_wr = ctk.CTkLabel(row, text=f"{wr:.1f}%", font=font_body_bold, text_color=color)
            lbl_wr.pack(side="right")



    def _open_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():  # type: ignore
            self.settings_window = SettingsModal(self.master, self.config, on_save_callback=self.master.on_settings_saved)
        else:
            self.settings_window.focus_force()  # type: ignore
            self.settings_window.lift()  # type: ignore
