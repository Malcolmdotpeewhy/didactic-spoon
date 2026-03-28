import tkinter as tk
import customtkinter as ctk  # type: ignore
import keyboard  # type: ignore

from ui.ui_shared import CTkTooltip  # type: ignore
from ui.components.factory import get_color, get_font, get_radius, make_button  # type: ignore
from ui.components.lol_toggle import LolToggle  # type: ignore
from utils.logger import Logger  # type: ignore


class HotkeyRecorder(ctk.CTkButton):
    """A button that records keyboard shortcuts when clicked.

    Click to start recording → press your key combo → it captures and displays it.
    """

    def __init__(self, master, initial_value="", **kwargs):
        self._hotkey_value = initial_value
        self._recording = False
        self._pressed_keys = set()
        self._hook = None

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
            # type: ignore
            **kwargs,
        )

    def _toggle_recording(self):
        if self._recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._recording = True
        self._pressed_keys = set()
        self.configure(
            text="⏺ Press keys...",
            fg_color=get_color("colors.accent.primary"),
            text_color="#ffffff",
            border_color=get_color("colors.accent.primary"),
        )
        self._hook = keyboard.on_press(self._on_key_press)

    def _on_key_press(self, event):
        """Capture key presses and build the hotkey combo string."""
        ev_name = getattr(event, "name", None)
        name = ev_name.lower() if isinstance(ev_name, str) else ""

        modifiers_map = {
            "left ctrl": "ctrl", "right ctrl": "ctrl",
            "left shift": "shift", "right shift": "shift",
            "left alt": "alt", "right alt": "alt",
            "left windows": "win", "right windows": "win",
            "control_l": "ctrl", "control_r": "ctrl",
            "shift_l": "shift", "shift_r": "shift",
            "alt_l": "alt", "alt_r": "alt",
        }
        name = modifiers_map.get(name, name)
        self._pressed_keys.add(name)

        modifier_names = {"ctrl", "shift", "alt", "win"}
        non_modifiers = self._pressed_keys - modifier_names
        if non_modifiers:
            parts = []
            for mod in ["ctrl", "shift", "alt", "win"]:
                if mod in self._pressed_keys:
                    parts.append(mod)
            parts.extend(sorted(non_modifiers))
            combo = "+".join(parts)
            self._hotkey_value = combo
            self.after(50, lambda: self._stop_recording())

    def _stop_recording(self):
        self._recording = False
        if self._hook is not None:
            keyboard.unhook(self._hook)
            self._hook = None
        self.configure(
            text=self._hotkey_value or "Click to set",
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_color=get_color("colors.border.subtle"),
        )

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
        self.geometry("380x560")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=get_color("colors.background.app"))

        # Center relative to master
        self.update_idletasks()
        x = master.winfo_rootx() - self.winfo_width() - 20
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        if x < 10:
            x = 10
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
            header, text="v1.0",
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
        self.slider_delay.bind("<Enter>", lambda e: self.slider_delay.configure())
        self.slider_delay.bind("<Leave>", lambda e: self.slider_delay.configure(cursor=""))
        self.slider_delay.pack(side="right", padx=(8, 4))
        CTkTooltip(self.slider_delay, "Delay before auto-accepting a match (0 = instant)")

        _divider(body)

        # ━━━━━━━━ BEHAVIOR ━━━━━━━━
        _section_header(body, "BEHAVIOR")

        row_stealth = ctk.CTkFrame(body, fg_color="transparent")
        row_stealth.pack(fill="x", pady=4)
        ctk.CTkLabel(
            row_stealth, text="Stealth Mode",
            font=get_font("body"),
            text_color=get_color("colors.text.primary"),
        ).pack(side="left")

        self.stealth_var = ctk.BooleanVar(value=bool(self.config.get("stealth_mode", False)))
        self.stealth_switch = LolToggle(
            row_stealth,
            variable=self.stealth_var,
        )
        self.stealth_switch.pack(side="right")
        CTkTooltip(
            self.stealth_switch,
            "Keep LeagueLoop in the background during automations.\n"
            "It will only pop up when a game starts or ends."
        )

        _divider(body)

        # ━━━━━━━━ HOTKEYS ━━━━━━━━
        _section_header(body, "HOTKEYS")

        hotkeys = [
            ("Client Launch", "hotkey_launch_client", "ctrl+shift+l"),
            ("Toggle Automation", "hotkey_toggle_automation", "ctrl+shift+a"),
            ("Find Match", "hotkey_find_match", "ctrl+shift+f"),
            ("Compact Mode", "hotkey_compact_mode", "ctrl+shift+m"),
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

        # Update LolToggle state safely
        self.stealth_var.set(False)
        self.stealth_switch._state = False
        self.stealth_switch._animate()

        # Default hotkeys
        default_hotkeys = {
            "hotkey_launch_client": "ctrl+shift+l",
            "hotkey_toggle_automation": "ctrl+shift+a",
            "hotkey_find_match": "ctrl+shift+f",
            "hotkey_compact_mode": "ctrl+shift+m",
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

        # Save stealth mode
        self.config.set("stealth_mode", bool(self.stealth_var.get()))

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
