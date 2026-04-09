import os
import tkinter as tk
import customtkinter as ctk  # type: ignore
import keyboard  # type: ignore

from ui.ui_shared import CTkTooltip  # type: ignore
from ui.components.factory import get_color, get_font, make_button  # type: ignore
from ui.components.lol_toggle import LolToggle  # type: ignore
from ui.components.hover import apply_click_animation  # type: ignore
from utils.logger import Logger  # type: ignore
from utils.path_utils import get_asset_path  # type: ignore
from core.version import __version__  # type: ignore



class HotkeyRecorder(ctk.CTkButton):
    """A button that records keyboard shortcuts when clicked.

    Click to start recording → press your key combo → it captures and displays it.
    """
    _active_recorder = None

    _MODIFIERS_MAP = {
        "left ctrl": "ctrl", "right ctrl": "ctrl",
        "left shift": "shift", "right shift": "shift",
        "left alt": "alt", "right alt": "alt",
        "left windows": "win", "right windows": "win",
        "control_l": "ctrl", "control_r": "ctrl",
        "shift_l": "shift", "shift_r": "shift",
        "alt_l": "alt", "alt_r": "alt",
    }
    _MODIFIER_NAMES = {"ctrl", "shift", "alt", "win"}
    _MODIFIER_ORDER = ["ctrl", "shift", "alt", "win"]

    def __init__(self, master, initial_value="", **kwargs):
        self._hotkey_value = initial_value
        self._recording = False
        self._pressed_keys = set()
        self._hook = None
        self._pulse_job = None
        self._pulse_state = False

        super().__init__(
            master,  # type: ignore
            text=initial_value or "Click to set",  # type: ignore
            width=kwargs.pop("width", 140),  # type: ignore
            height=kwargs.pop("height", 28),  # type: ignore
            corner_radius=6,  # type: ignore
            font=get_font("body", "bold"),  # type: ignore
            fg_color=get_color("colors.background.card"),  # type: ignore
            text_color=get_color("colors.text.primary"),  # type: ignore
            border_width=1,  # type: ignore
            border_color=get_color("colors.border.subtle"),  # type: ignore
            hover_color=get_color("colors.state.hover"),  # type: ignore
            command=self._toggle_recording,  # type: ignore
            cursor="hand2",  # type: ignore
            # type: ignore
            **kwargs,
        )
        self._tooltip = CTkTooltip(self, "Click to record a new hotkey")

        # 🎨 Palette: Keyboard Accessibility Focus States
        self._focus_border = get_color("colors.accent.primary", "#0AC8B9")
        self._unfocus_border = get_color("colors.border.subtle")

        apply_click_animation(self, get_color("colors.background.card"), pulse_color=get_color("colors.accent.primary"))

        if hasattr(self, "_canvas"):
            self._canvas.configure(takefocus=1)
            self._canvas.bind("<FocusIn>", self._on_focus, add="+")
            self._canvas.bind("<FocusOut>", self._on_unfocus, add="+")
            self._canvas.bind("<KeyPress-space>", lambda e: self._toggle_recording(), add="+")
            self._canvas.bind("<KeyPress-Return>", lambda e: self._toggle_recording(), add="+")

    def _on_focus(self, event=None):
        if not self._recording:
            self.configure(border_color=self._focus_border, border_width=2)

    def _on_unfocus(self, event=None):
        if not self._recording:
            self.configure(border_color=self._unfocus_border, border_width=1)

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording(cancel=True)
        else:
            self._start_recording()

    def _start_recording(self):
        if HotkeyRecorder._active_recorder and HotkeyRecorder._active_recorder is not self:
            HotkeyRecorder._active_recorder._stop_recording()
        HotkeyRecorder._active_recorder = self

        self._recording = True
        self._pressed_keys = set()
        self.configure(
            text="⏺ Listening...",
            fg_color=get_color("colors.accent.primary"),
            text_color="#ffffff",
            border_color=get_color("colors.accent.primary"),
        )
        if hasattr(self, "_tooltip"):
            self._tooltip.configure(text="Press your desired key combination")
        self._hook = keyboard.on_press(self._on_key_press)
        self._animate_pulse()

    def _animate_pulse(self):
        """Malcolm's Infusion: Pulse animation while recording to indicate active listening."""
        if not self._recording or not self.winfo_exists():
            return

        self._pulse_state = not self._pulse_state
        if self._pulse_state:
            # Dimmed state
            self.configure(fg_color="#A88A4E", border_color="#A88A4E")
        else:
            # Bright state
            self.configure(fg_color=get_color("colors.accent.primary"), border_color=get_color("colors.accent.primary"))

        self._pulse_job = self.after(600, self._animate_pulse)

    def _on_key_press(self, event):
        """Capture key presses and build the hotkey combo string."""
        ev_name = getattr(event, "name", None)
        name = ev_name.lower() if isinstance(ev_name, str) else ""

        # ⚡ Bolt: Use pre-allocated static maps to avoid dictionary allocation overhead on every keystroke
        name = self._MODIFIERS_MAP.get(name, name)
        self._pressed_keys.add(name)

        non_modifiers = self._pressed_keys - self._MODIFIER_NAMES
        if non_modifiers:
            parts = []
            for mod in self._MODIFIER_ORDER:
                if mod in self._pressed_keys:
                    parts.append(mod)
            parts.extend(sorted(non_modifiers))
            combo = "+".join(parts)
            self._hotkey_value = combo
            self.after(50, lambda: self._stop_recording(success=True))

    def _stop_recording(self, success=False, cancel=False):
        if HotkeyRecorder._active_recorder is self:
            HotkeyRecorder._active_recorder = None


        self._recording = False
        if self._hook is not None:
            keyboard.unhook(self._hook)
            self._hook = None
        if self._pulse_job is not None:
            self.after_cancel(self._pulse_job)
            self._pulse_job = None

        if cancel:
            # Check if they only pressed modifiers
            non_modifiers = self._pressed_keys - self._MODIFIER_NAMES
            if self._pressed_keys and not non_modifiers:
                # Invalid hotkey (only modifiers)
                self.configure(
                    text="! Needs a key",
                    fg_color=get_color("colors.state.warning", "#E67E22"),
                    text_color="#ffffff",
                    border_color=get_color("colors.state.warning", "#E67E22"),
                )
                if hasattr(self, "_tooltip"):
                    self._tooltip.configure(text="A non-modifier key is required")
                self.after(1200, self._revert_visuals)
                return
            else:
                self._revert_visuals()
                return

        if success:
            # Malcolm's Infusion: Satisfying success flash
            self.configure(
                text=f"✓ {self._hotkey_value}",
                fg_color=get_color("colors.state.success", "#27AE60"),
                text_color="#ffffff",
                border_color=get_color("colors.state.success", "#27AE60"),
            )
            self.after(800, self._revert_visuals)
        else:
            self._revert_visuals()

    def _revert_visuals(self):
        if not self.winfo_exists():
            return
        self.configure(
            text=self._hotkey_value or "Click to set",
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_color=get_color("colors.border.subtle"),
        )
        if hasattr(self, "_tooltip"):
            self._tooltip.configure(text="Click to record a new hotkey")

    def get(self):
        return self._hotkey_value

    def destroy(self):
        """Custom destroy with safety guards for CustomTkinter's '_font' bug."""
        if getattr(self, "_hook", None) is not None:
            try:
                keyboard.unhook(self._hook)
                self._hook = None
            except Exception:
                pass

        if not hasattr(self, "_font") or not self.winfo_exists():
            return

        try:
            super().destroy()
        except Exception:
            try:
                tk.Button.destroy(self)
            except Exception:
                pass


# ────────────────────────────────────────────────────────────
#  Section Builder — Creates a collapsible group with a header
# ────────────────────────────────────────────────────────────
def _section_header(parent, title):
    """Create a styled section header label."""
    hdr = ctk.CTkLabel(
        parent, text=title,
        font=get_font("caption", "bold"),
        text_color="#C8AA6E",
        anchor="w",
    )
    hdr.pack(fill="x", pady=(12, 4))
    return hdr


def _divider(parent):
    """Create a subtle horizontal rule."""
    ctk.CTkFrame(parent, height=1, fg_color=get_color("colors.border.subtle")).pack(
        fill="x", pady=8
    )


class SettingsModal(ctk.CTkToplevel):
    def __init__(self, master, config, on_save_callback=None):
        super().__init__(master)  # type: ignore

        self.config = config
        self.on_save_callback = on_save_callback
        self.recorders = {}

        self.title("League Loop — Settings")
        try:
            icon_path = get_asset_path("assets/app.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self.geometry("380x560")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=get_color("colors.background.app"))

        # Position relative to master, rigidly clamped to physical screen boundaries.
        # This prevents the settings modal from rendering off-screen no matter where
        # the main window has been dragged (edge, corner, partially off-screen).
        self.update_idletasks()
        win_w = self.winfo_width() or 380
        win_h = self.winfo_height() or 560
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Safe margins — never closer than this to any screen edge
        MARGIN = 10
        TASKBAR_RESERVE = 48  # reserve space for Windows taskbar

        # Get master's actual position (handles overrideredirect windows correctly)
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_w = master.winfo_width()
        master_h = master.winfo_height()

        # Strategy 1: Place to the LEFT of master
        x = master_x - win_w - 20
        y = master_y + (master_h // 2) - (win_h // 2)

        # If left placement goes off-screen, try RIGHT of master
        if x < MARGIN:
            x = master_x + master_w + 20

        # If right placement also goes off-screen, center on screen
        if x + win_w > screen_w - MARGIN:
            x = (screen_w - win_w) // 2

        # Rigid clamp: force X within viewable horizontal bounds
        x = max(MARGIN, min(x, screen_w - win_w - MARGIN))

        # Rigid clamp: force Y within viewable vertical bounds (accounting for taskbar)
        y = max(MARGIN, min(y, screen_h - win_h - TASKBAR_RESERVE))

        self.geometry(f"+{int(x)}+{int(y)}")

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.after(150, self._deferred_init)

    def _deferred_init(self):
        self._setup_ui()
        self.lift()
        self.focus_force()

    # ──────────────────────────────────────────────
    #  UI Layout
    # ──────────────────────────────────────────────
    def _setup_ui(self):
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="#0A1428", corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text="⚙  SETTINGS",
            font=("Beaufort for LOL", 16, "bold"),
            text_color="#C8AA6E",
        ).pack(side="left", padx=16, pady=12)

        ctk.CTkLabel(
            header, text=f"v{__version__}",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
        ).pack(side="right", padx=(8, 16), pady=12)

        btn_info = ctk.CTkButton(
            header, text="ⓘ Info", width=50, height=24,
            font=get_font("caption", "bold"), 
            fg_color="transparent",
            text_color=get_color("colors.text.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._open_info_page,
            cursor="hand2",
        )
        btn_info.pack(side="right", padx=(8, 0), pady=12)

        # ── Scrollable body ──
        body = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=get_color("colors.background.card"),
            scrollbar_button_hover_color=get_color("colors.state.hover"),
        )
        body.pack(fill="both", expand=True, padx=16, pady=(8, 0))

        self.recorders = {}

        # ━━━━━━━━ GENERAL ━━━━━━━━
        _section_header(body, "GENERAL")

        row_mode = ctk.CTkFrame(body, fg_color="transparent")
        row_mode.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_mode, text="Game Mode",
            font=get_font("body"),
            text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        self.mode_var = ctk.StringVar(value=self.config.get("aram_mode", "ARAM"))
        self.mode_select = ctk.CTkOptionMenu(
            row_mode,
            values=[
                "Quickplay", "Draft Pick", "Ranked Solo/Duo", "Ranked Flex",
                "ARAM", "ARAM Mayhem", "Arena", "URF", "ARURF",
                "Nexus Blitz", "One For All", "Ultimate Spellbook",
                "TFT Normal", "TFT Ranked",
            ],
            variable=self.mode_var,
            width=160,
            font=get_font("body", "bold"),
            fg_color=get_color("colors.background.card"),
            button_color="#1A2733",
            button_hover_color=get_color("colors.state.hover"),
            dropdown_fg_color=get_color("colors.background.app"),
            dropdown_hover_color=get_color("colors.state.hover"),
            dropdown_font=get_font("caption"),
            cursor="hand2",
        )
        self.mode_select.pack(side="right")
        CTkTooltip(self.mode_select, "Select the game mode for lobby creation")

        # Accept Delay
        row_delay = ctk.CTkFrame(body, fg_color="transparent")
        row_delay.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_delay, text="Accept Delay",
            font=get_font("body"),
            text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        delay_val = float(self.config.get("accept_delay", 2.0))
        self.delay_var = ctk.DoubleVar(value=delay_val)
        self.lbl_delay_val = ctk.CTkLabel(
            row_delay, text=f"{delay_val:.1f}s",
            font=get_font("body", "bold"),
            text_color="#C8AA6E",
            width=40,
        )
        self.lbl_delay_val.pack(side="right")

        self.slider_delay = ctk.CTkSlider(
            row_delay,
            from_=0, to=8,
            number_of_steps=16,
            variable=self.delay_var,
            width=100,
            fg_color=get_color("colors.background.card"),
            progress_color="#C8AA6E",
            button_color="#F0E6D2",
            button_hover_color="#FFFFFF",
            command=self._on_delay_slide,
        )
        self.slider_delay.bind("<Enter>", lambda e: self.slider_delay.configure(cursor="hand2"))
        self.slider_delay.bind("<Leave>", lambda e: self.slider_delay.configure(cursor=""))
        self.slider_delay.pack(side="right", padx=(8, 4))
        CTkTooltip(self.slider_delay, "Delay before auto-accepting a match (0 = instant)")

        _divider(body)

        # ━━━━━━━━ BEHAVIOR ━━━━━━━━
        _section_header(body, "BEHAVIOR")

        _divider(body)

        # ━━━━━━━━ AUTOMATION ━━━━━━━━
        _section_header(body, "AUTOMATION")

        # Auto Honor
        row_honor_toggle = ctk.CTkFrame(body, fg_color="transparent")
        row_honor_toggle.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_honor_toggle, text="Auto-Honor Teammate",
            font=get_font("body"), text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        self.honor_enabled_var = ctk.BooleanVar(value=bool(self.config.get("auto_honor_enabled", True)))
        self.honor_enabled_switch = LolToggle(row_honor_toggle, variable=self.honor_enabled_var)
        self.honor_enabled_switch.pack(side="right")
        CTkTooltip(self.honor_enabled_switch, "Automatically honor a teammate at end-of-game")

        # Honor Strategy
        row_honor = ctk.CTkFrame(body, fg_color="transparent")
        row_honor.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_honor, text="Honor Strategy",
            font=get_font("body"),
            text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        self.honor_var = ctk.StringVar(value=self.config.get("honor_strategy", "random"))
        self.honor_select = ctk.CTkOptionMenu(
            row_honor,
            values=["random", "best_kda", "mvp"],
            variable=self.honor_var,
            width=120,
            font=get_font("body", "bold"),
            fg_color=get_color("colors.background.card"),
            button_color="#1A2733",
            button_hover_color=get_color("colors.state.hover"),
            dropdown_fg_color=get_color("colors.background.app"),
            dropdown_hover_color=get_color("colors.state.hover"),
            dropdown_font=get_font("caption"),
            cursor="hand2",
        )
        self.honor_select.pack(side="right")
        CTkTooltip(self.honor_select, "Strategy used by Auto Honor\nrandom = random teammate\nbest_kda = highest KDA\nmvp = most kills+assists")

        _divider(body)

        # ━━━━━━━━ SOCIAL ━━━━━━━━
        _section_header(body, "SOCIAL")

        # Auto Join
        row_join_toggle = ctk.CTkFrame(body, fg_color="transparent")
        row_join_toggle.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_join_toggle, text="Auto-Join VIP Lobbies",
            font=get_font("body"), text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        self.join_enabled_var = ctk.BooleanVar(value=bool(self.config.get("auto_join_enabled", True)))
        self.join_enabled_switch = LolToggle(row_join_toggle, variable=self.join_enabled_var)
        self.join_enabled_switch.pack(side="right")
        CTkTooltip(self.join_enabled_switch, "Automatically accept lobby invites from VIP friends")

        # Custom Status
        ctk.CTkLabel(
            body, text="Custom Status Message",
            font=get_font("caption"), text_color=get_color("colors.text.muted"),
        ).pack(anchor="w", pady=(0, 2))

        self.status_var = ctk.StringVar(value=self.config.get("custom_status", ""))
        self.entry_status = ctk.CTkEntry(
            body, textvariable=self.status_var,
            placeholder_text="e.g. Powered by LeagueLoop",
            font=get_font("body"),
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_color=get_color("colors.border.subtle"),
            height=30,
        )
        self.entry_status.pack(fill="x", pady=(0, 10))
        CTkTooltip(self.entry_status, "Automatically sets your League status text.")
        
        # VIP Invite List
        ctk.CTkLabel(
            body, text="VIP Invite List (comma-separated)",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
        ).pack(anchor="w", pady=(0, 2))

        self.vip_var = ctk.StringVar(value=self.config.get("vip_invite_list", ""))
        self.entry_vip = ctk.CTkEntry(
            body,
            textvariable=self.vip_var,
            placeholder_text="Friend1, Friend2, ...",
            font=get_font("body"),
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_color=get_color("colors.border.subtle"),
            height=30,
        )
        self.entry_vip.pack(fill="x", pady=(0, 6))
        CTkTooltip(self.entry_vip, "Leave blank to invite ALL online friends")



        # ━━━━━━━━ HOTKEYS ━━━━━━━━
        _section_header(body, "HOTKEYS")

        hotkeys = [
            ("Client Launch", "hotkey_launch_client", "ctrl+shift+l"),
            ("Toggle Automation", "hotkey_toggle_automation", "ctrl+shift+a"),
            ("Find Match", "hotkey_find_match", "ctrl+shift+f"),
            ("Omnibar", "hotkey_omnibar", "ctrl+k"),
        ]

        for label_text, config_key, default_val in hotkeys:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=label_text,
                font=get_font("body"),
                text_color=get_color("colors.text.primary"),
            ).pack(side="left")

            current_val = self.config.get(config_key, default_val)
            recorder = HotkeyRecorder(row, initial_value=str(current_val), width=140)
            recorder.pack(side="right")
            self.recorders[config_key] = recorder

        _divider(body)

        # ━━━━━━━━ ABOUT ━━━━━━━━
        _section_header(body, "ABOUT")

        ctk.CTkLabel(
            body, text="League Loop",
            font=("Beaufort for LOL", 13, "bold"),
            text_color=get_color("colors.text.primary"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            body, text="Companion overlay for League of Legends",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            body,
            text="Built with CustomTkinter • LCU API • Python",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
        ).pack(anchor="w", pady=(0, 8))

        # ── Footer buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="#0A1428", corner_radius=0)
        btn_frame.pack(fill="x", side="bottom")

        # Malcolm's UI enhancement: Add a Reset button with inline confirmation
        self._reset_confirm_mode = False
        self._reset_timer = None

        inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)

        self.btn_reset = ctk.CTkButton(
            inner, text="Reset Defaults", width=100, height=32,
            font=get_font("body", "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._on_reset_clicked, cursor="hand2",
            )
        self.btn_reset.pack(side="left")
        self.tooltip_reset = CTkTooltip(self.btn_reset, "Restore all settings to default")

        btn_save = ctk.CTkButton(
            inner, text="Save", width=80, height=32,
            font=get_font("body", "bold"),
            fg_color="#C8AA6E",
            text_color="#0A1428",
            hover_color="#F0E6D2",
            command=self._save_settings, cursor="hand2",
            )
        btn_save.pack(side="right")
        CTkTooltip(btn_save, "Save changes and close")

        btn_cancel = ctk.CTkButton(
            inner, text="Cancel", width=80, height=32,
            font=get_font("body", "bold"),
            fg_color="transparent",
            border_width=1,
            border_color=get_color("colors.border.subtle"),
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=lambda: self.after(50, self._close), cursor="hand2",
            )
        btn_cancel.pack(side="right", padx=(0, 8))
        CTkTooltip(btn_cancel, "Discard changes and close")

    # ──────────────────────────────────────────────
    #  Callbacks
    # ──────────────────────────────────────────────
    def _on_reset_clicked(self):
        """Malcolm's Infusion: Inline confirmation without popup fatigue."""
        if not self._reset_confirm_mode:
            # Enter confirm mode
            self._reset_confirm_mode = True
            self.btn_reset.configure(
                text="Confirm Reset?",
                text_color="#ffffff",
                fg_color=get_color("colors.state.danger")
            )
            self._reset_timer = self.after(3000, self._cancel_reset)
        else:
            # Execute reset
            if self._reset_timer:
                self.after_cancel(self._reset_timer)
            self._execute_reset()

    def _cancel_reset(self):
        """Revert the reset button to normal state if not clicked."""
        if not self.winfo_exists(): return
        self._reset_confirm_mode = False
        self.btn_reset.configure(
            text="Reset Defaults",
            text_color=get_color("colors.text.muted"),
            fg_color="transparent"
        )

    def _execute_reset(self):
        """Restores UI to default state and triggers a delightful confetti toast."""
        self._cancel_reset()

        # Reset variables
        self.mode_var.set("ARAM")
        self.delay_var.set(2.0)
        self.slider_delay.set(2.0)
        self._on_delay_slide(2.0)

        self.honor_enabled_var.set(True)
        self.honor_enabled_switch._state = True
        self.honor_enabled_switch._animate()
        
        self.join_enabled_var.set(True)
        self.join_enabled_switch._state = True
        self.join_enabled_switch._animate()
        
        self.honor_var.set("random")
        self.status_var.set("🎮 LeagueLoop ⚙️ https://github.com/Intrusive-Thots/LeagueLoop-Installer")
        self.vip_var.set("")

        # Default hotkeys
        default_hotkeys = {
            "hotkey_launch_client": "ctrl+shift+l",
            "hotkey_toggle_automation": "ctrl+shift+a",
            "hotkey_find_match": "ctrl+shift+f",
            "hotkey_omnibar": "ctrl+k",
        }
        for key, default_val in default_hotkeys.items():
            if key in self.recorders:
                recorder = self.recorders[key]
                recorder._hotkey_value = default_val
                recorder._stop_recording()

        # Try to show delightful confetti toast using ToastManager
        try:
            from ui.components.toast import ToastManager
            # master is app_sidebar, master.master is the main window
            main_window = self.master.master if hasattr(self.master, "master") else self.master
            ToastManager.get_instance(main_window).show(
                "Settings restored to defaults!",
                icon="♻️",
                theme="success",
                confetti=True
            )
        except Exception as e:
            Logger.error("settings_modal.py", f"Failed to show toast: {e}")

    def _on_delay_slide(self, value):
        self.lbl_delay_val.configure(text=f"{value:.1f}s")

    def _save_settings(self):
        # Save hotkeys
        for config_key, recorder in self.recorders.items():
            val = recorder.get().strip().lower()
            if val:
                self.config.set(config_key, val)

        # Save game mode
        self.config.set("aram_mode", self.mode_var.get())

        # Save accept delay
        self.config.set("accept_delay", round(self.delay_var.get(), 1))

        # Save honor strategy
        self.config.set("auto_honor_enabled", bool(self.honor_enabled_var.get()))
        self.config.set("honor_strategy", self.honor_var.get())

        # Save social
        self.config.set("auto_join_enabled", bool(self.join_enabled_var.get()))
        self.config.set("custom_status", self.status_var.get().strip())
        self.config.set("vip_invite_list", self.vip_var.get().strip())

        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception as e:
                Logger.error("SYS", f"Settings callback failed: {e}")

        self.after(50, self._close)

    def _open_info_page(self):
        try:
            from ui.components.about_page import AboutPage
            AboutPage(self.master)
            self.after(50, self._close)
        except Exception as e:
            Logger.error("SYS", f"Failed to open About Page: {e}")

    def _close(self):
        """Properly clean up recorders and destroy the window."""
        try:
            if hasattr(self, "master") and self.master and self.master.winfo_exists():
                self.master.focus_set()
        except Exception:
            pass
        try:
            for recorder in getattr(self, "recorders", {}).values():
                try:
                    if hasattr(recorder, "_hook") and recorder._hook is not None:
                        keyboard.unhook(recorder._hook)
                        recorder._hook = None
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if hasattr(self.master, "settings_window"):
                self.master.settings_window = None
        except Exception:
            pass

        try:
            if self.winfo_exists():
                for child in self.winfo_children():
                    try:
                        if child.winfo_exists():
                            child.destroy()
                    except Exception:
                        pass

                if self.winfo_exists():
                    super().destroy()
        except Exception:
            pass
