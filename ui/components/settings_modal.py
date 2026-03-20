import tkinter as tk
import customtkinter as ctk
import keyboard

from ui.ui_shared import CTkTooltip
from ui.components.factory import get_color, get_font, get_radius, make_button
from utils.logger import Logger


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
            master,
            text=initial_value or "Click to set",
            width=kwargs.pop("width", 140),
            height=kwargs.pop("height", 28),
            corner_radius=6,
            font=get_font("body", "bold"),
            fg_color=get_color("colors.background.card"),
            text_color=get_color("colors.text.primary"),
            border_width=1,
            border_color=get_color("colors.border.subtle"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_recording,
            cursor="hand2",
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
        # Hook into keyboard events
        self._hook = keyboard.on_press(self._on_key_press)

    def _on_key_press(self, event):
        """Capture key presses and build the hotkey combo string."""
        name = event.name.lower()

        # Normalize modifier names
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

        # If we have at least one non-modifier key, finalize
        modifier_names = {"ctrl", "shift", "alt", "win"}
        non_modifiers = self._pressed_keys - modifier_names
        if non_modifiers:
            # Build the combo string: modifiers first, then the key
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
        
        # If _font is already gone, or it's already being destroyed, don't re-enter
        if not hasattr(self, "_font") or not self.winfo_exists():
            return
            
        try:
            # Call the underlying tkinter destroy if super().destroy() fails
            super().destroy()
        except Exception:
            try:
                tk.Button.destroy(self)
            except Exception:
                pass


class SettingsModal(ctk.CTkToplevel):
    def __init__(self, master, config, on_save_callback=None):
        super().__init__(master)
        
        self.config = config
        self.on_save_callback = on_save_callback
        self.recorders = {}
        
        self.title("Global Settings")
        self.geometry("360x480")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.configure(fg_color=get_color("colors.background.app"))
        
        # Center relative to master, but shift to the left of the sidebar
        self.update_idletasks()
        # master is the sidebar (200px), we want to be to the left of it
        # master.winfo_rootx() is the left edge of the sidebar
        x = master.winfo_rootx() - self.winfo_width() - 20
        y = master.winfo_rooty() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        
        # Ensure we don't go off-screen to the left
        if x < 10: x = 10
        
        self.geometry(f"+{int(x)}+{int(y)}")
        
        self.protocol("WM_DELETE_WINDOW", self._close)
        
        # Delay UI setup — CTkToplevel has a rendering bug with overrideredirect parents
        self.after(150, self._deferred_init)

    def _deferred_init(self):
        self._setup_ui()
        self.lift()
        self.focus_force()

    def _setup_ui(self):
        # ── Title ──
        lbl_title = ctk.CTkLabel(
            self, text="⚙ Settings", 
            font=get_font("title", "bold"), 
            text_color=get_color("colors.text.primary")
        )
        lbl_title.pack(pady=(16, 4))

        lbl_subtitle = ctk.CTkLabel(
            self, text="Click a hotkey field then press your combo",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted")
        )
        lbl_subtitle.pack(pady=(0, 12))
        
        self.recorders = {}
        
        # Define hotkeys to expose
        hotkeys = [
            ("Client Launch", "hotkey_launch_client", "ctrl+shift+l"),
            ("Toggle Automation", "hotkey_toggle_automation", "ctrl+shift+a"),
            ("Find Match", "hotkey_find_match", "ctrl+shift+f"),
            ("Compact Mode", "hotkey_compact_mode", "ctrl+shift+m")
        ]
        
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=10)
        form_frame.columnconfigure(1, weight=1)
        
        # ── Mode Selection Toggle ──
        mode_lbl = ctk.CTkLabel(
            form_frame, text="Game Mode", 
            font=get_font("body"), 
            text_color=get_color("colors.text.muted")
        )
        mode_lbl.grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        
        self.mode_var = ctk.StringVar(value=self.config.get("aram_mode", "ARAM"))
        self.mode_select = ctk.CTkOptionMenu(
            form_frame, values=["ARAM", "ARAM Mayhem"],
            variable=self.mode_var, width=150,
            font=get_font("body", "bold"),
            fg_color=get_color("colors.background.card"),
            button_color=get_color("colors.accent.primary"),
            button_hover_color=get_color("colors.state.hover")
        )
        self.mode_select.grid(row=0, column=1, sticky="e", pady=8)
        CTkTooltip(self.mode_select, "Select the active ARAM mode (determines lobby creation payload)")

        # ── Divider ──
        ctk.CTkFrame(form_frame, height=1, fg_color=get_color("colors.border.subtle")).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=8
        )

        hotkey_header = ctk.CTkLabel(
            form_frame, text="HOTKEYS",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"),
        )
        hotkey_header.grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 2))
        
        # ── Hotkey Recorders ──
        for idx, (label_text, config_key, default_val) in enumerate(hotkeys):
            row_idx = idx + 3  # offset for mode + divider + header
            lbl = ctk.CTkLabel(
                form_frame, text=label_text, 
                font=get_font("body"), 
                text_color=get_color("colors.text.muted")
            )
            lbl.grid(row=row_idx, column=0, sticky="w", pady=6, padx=(0, 10))
            
            current_val = self.config.get(config_key, default_val)
            recorder = HotkeyRecorder(form_frame, initial_value=str(current_val), width=150)
            recorder.grid(row=row_idx, column=1, sticky="e", pady=6)
            
            self.recorders[config_key] = recorder
            
        # ── Buttons ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, side="bottom", pady=20)
        
        btn_cancel = make_button(
            parent=btn_frame, text="Cancel", command=self._close,
            variant="secondary", width=100
        )
        btn_cancel.pack(side="left")
        
        btn_save = make_button(
            parent=btn_frame, text="Save", command=self._save_settings,
            variant="primary", width=100
        )
        btn_save.pack(side="right")
        
    def _save_settings(self):
        # Save mode
        self.config.set("aram_mode", self.mode_var.get())
        
        # Save hotkeys from recorders
        for config_key, recorder in self.recorders.items():
            val = recorder.get().strip().lower()
            if val:
                self.config.set(config_key, val)
                
        if self.on_save_callback:
            try:
                self.on_save_callback()
            except Exception as e:
                Logger.error("SYS", f"Settings callback failed: {e}")
                
        self._close()

    def _close(self):
        """Properly clean up recorders and destroy the window with extreme prejudice."""
        try:
            # 1. Unhook recorders immediately
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
            # 2. Clear reference in parent
            if hasattr(self.master, "settings_window"):
                self.master.settings_window = None
        except Exception:
            pass
            
        try:
            # 3. Explicitly destroy children first with guards
            if self.winfo_exists():
                for child in self.winfo_children():
                    try:
                        if child.winfo_exists():
                            child.destroy()
                    except Exception:
                        pass

            # 4. Final destruction of the Toplevel
            if self.winfo_exists():
                super().destroy()
        except Exception as e:
            # Silent fail for destruction is safer in threaded UI environments
            pass
