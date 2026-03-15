import tkinter as tk
import customtkinter as ctk
import os
from PIL import Image

from utils.path_utils import resource_path
from ui.components.factory import get_color, get_font, get_radius, TOKENS, make_button
from ui.ui_shared import CTkTooltip
from ui.components.priority_grid import PriorityIconGrid

class SidebarWidget(ctk.CTkFrame):
    def __init__(self, master, toggle_callback, config, lcu=None, assets=None):
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
        self.power_state = False

        self._setup_ui()

    def _setup_ui(self):
        # ── Header / Drag Area ──
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.header.pack(fill="x", pady=(8, 0), padx=8)
        
        self.lbl_title = ctk.CTkLabel(
            self.header, text="League Loop", 
            font=get_font("title", "bold"),
            text_color=get_color("colors.text.primary")
        )
        self.lbl_title.pack(side="left", padx=6)

        # Collapse toggle for the whole sidebar body
        self._body_expanded = True
        self.btn_collapse = ctk.CTkButton(
            self.header, text="▼", width=24, height=24,
            corner_radius=12, font=("Arial", 12, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_body_collapse,
        )
        self.btn_collapse.pack(side="right", padx=(0, 2))

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
        spacer = ctk.CTkFrame(self.main_body, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

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
            self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
            self.update_action_log("Starting Matchmaking...")
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
