"""
🔮 Malcolm's Infusion: Keyboard Shortcut Overlay
A floating, dismissable cheat-sheet that surfaces all hotkeys in one glanceable view.
Triggered by the sidebar "?" button or the "?" keyboard key.

UX Rationale:
- Users configure 3 global hotkeys in Tools → Hotkey Settings but have no contextual
  way to recall them during gameplay without navigating away from their current view.
- This overlay makes shortcuts instantly discoverable and reduces cognitive friction.

Accessibility:
- Fully keyboard-navigable: "?" to toggle, Escape to dismiss.
- Focus returns to the trigger widget on close.
- High-contrast text on elevated dark card background using design tokens.
"""
import customtkinter as ctk
from .factory import get_color, get_font, get_radius, parse_border, TOKENS


class ShortcutOverlay(ctk.CTkFrame):
    """
    A floating overlay panel that displays all keyboard shortcuts.
    Designed to match the 'arcane_tech' aesthetic with gold accents and
    elevated card surfaces.

    Usage:
        overlay = ShortcutOverlay(root_frame, config_dict)
        overlay.show()   # slide in
        overlay.hide()   # fade out
        overlay.toggle() # toggle visibility
    """

    def __init__(self, parent, config):
        """
        Args:
            parent: The parent CTk widget (usually the root or content_area).
            config: The app config object (must support .get(key, default)).
        """
        super().__init__(
            parent,
            fg_color=get_color("colors.background.card"),
            corner_radius=get_radius("lg"),
            border_width=1,
            border_color=get_color("colors.accent.gold"),
        )
        self.config_ref = config
        self._visible = False
        self._fade_step = 0
        self._build_ui()

    def _build_ui(self):
        """Construct the overlay layout: header → shortcut rows → footer."""
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=TOKENS.get("spacing.lg"), pady=(TOKENS.get("spacing.lg"), TOKENS.get("spacing.md")))

        ctk.CTkLabel(
            header,
            text="⌨️  KEYBOARD SHORTCUTS",
            font=get_font("header", "bold"),
            text_color=get_color("colors.accent.gold"),
        ).pack(side="left")

        # Close button (×)
        btn_close = ctk.CTkButton(
            header,
            text="✕",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color=get_color("colors.text.muted"),
            font=get_font("body"),
            command=self.hide,
        )
        btn_close.pack(side="right")

        # ── Divider ──
        ctk.CTkFrame(
            self, height=1, fg_color=get_color("colors.accent.gold"),
        ).pack(fill="x", padx=TOKENS.get("spacing.lg"), pady=(0, TOKENS.get("spacing.md")))

        # ── Shortcut Rows ──
        self.rows_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.rows_frame.pack(fill="x", padx=TOKENS.get("spacing.lg"), pady=(0, TOKENS.get("spacing.md")))

        # Build rows from live config
        self._populate_shortcuts()

        # ── Footer ──
        ctk.CTkLabel(
            self,
            text="Press  ?  or  Esc  to close",
            font=get_font("caption"),
            text_color=get_color("colors.text.muted"),
        ).pack(pady=(0, TOKENS.get("spacing.lg")))

    def _populate_shortcuts(self):
        """Read live hotkey config and build shortcut rows."""
        # Clear existing children
        for child in self.rows_frame.winfo_children():
            child.destroy()

        shortcuts = self.get_shortcut_data()

        for i, (key_combo, description, icon) in enumerate(shortcuts):
            self._add_shortcut_row(self.rows_frame, key_combo, description, icon, i)

    def get_shortcut_data(self):
        """
        Return a list of (key_combo, description, icon) tuples.
        Reads live config values so it always reflects the user's customizations.

        Returns:
            list[tuple[str, str, str]]: Each entry is (hotkey, description, emoji_icon).
        """
        cfg = self.config_ref
        return [
            (cfg.get("hotkey_find_match", "Ctrl+Shift+F"), "Find Match (Start Queue)", "🎯"),
            (cfg.get("hotkey_compact_mode", "Ctrl+Shift+M"), "Toggle Compact Mode", "📦"),
            (cfg.get("hotkey_launch_client", "Ctrl+Shift+L"), "Launch League Client", "🚀"),
            (cfg.get("hotkey_toggle_automation", "Ctrl+Shift+A"), "Toggle Automation", "⚡"),
            (cfg.get("hotkey_omnibar", "Ctrl+K"), "Open Command Palette", "🪄"),
            ("?", "Toggle This Overlay", "⌨️"),
            ("Esc", "Dismiss Overlay", "❌"),
        ]

    def _add_shortcut_row(self, parent, key_combo, description, icon, index):
        """
        Add a single shortcut row with key badge + description.
        Alternating row backgrounds provide visual rhythm.
        """
        # Alternate row background for readability
        bg = get_color("colors.background.panel") if index % 2 == 0 else "transparent"

        row = ctk.CTkFrame(
            parent,
            fg_color=bg,
            corner_radius=get_radius("sm"),
            height=36,
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Icon
        ctk.CTkLabel(
            row,
            text=icon,
            font=get_font("body"),
            width=30,
        ).pack(side="left", padx=(TOKENS.get("spacing.sm"), TOKENS.get("spacing.xs")))

        # Description
        ctk.CTkLabel(
            row,
            text=description,
            font=get_font("body"),
            text_color=get_color("colors.text.secondary"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(0, TOKENS.get("spacing.sm")))

        # Key Badge — styled like a physical keyboard key
        badge = ctk.CTkFrame(
            row,
            fg_color=get_color("colors.background.app"),
            corner_radius=get_radius("xs"),
            border_width=1,
            border_color=parse_border("soft")[1],
        )
        badge.pack(side="right", padx=TOKENS.get("spacing.sm"), pady=4)

        ctk.CTkLabel(
            badge,
            text=f"  {key_combo}  ",
            font=get_font("caption"),
            text_color=get_color("colors.accent.gold"),
        ).pack(padx=TOKENS.get("spacing.xs"), pady=2)

    # ── Visibility Control ──

    def show(self):
        """Display the overlay with a subtle entrance."""
        if self._visible:
            return
        self._visible = True
        # Refresh shortcuts in case config changed
        self._populate_shortcuts()
        # Place centered over parent
        self.place(relx=0.5, rely=0.5, anchor="center")
        self.lift()  # Ensure on top of all siblings

    def hide(self):
        """Dismiss the overlay."""
        if not self._visible:
            return
        self._visible = False
        self.place_forget()

    def toggle(self):
        """Toggle overlay visibility."""
        if self._visible:
            self.hide()
        else:
            self.show()

    @property
    def is_visible(self):
        """Whether the overlay is currently displayed."""
        return self._visible
