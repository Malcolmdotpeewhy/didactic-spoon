from utils.logger import Logger
import customtkinter as ctk
from .factory import get_color, get_font, make_button

class SpellSelector(ctk.CTkFrame):
    """Full-page summoner spell browser with a scrollable grid."""

    def __init__(self, parent, asset_manager, on_select_callback, on_close_callback):
        super().__init__(parent, fg_color=get_color("colors.background.app"), corner_radius=0)
        self.asset_manager = asset_manager
        self.on_select = on_select_callback
        self.on_close = on_close_callback
        self.buttons = []
        self._image_refs = {}  # Strong refs to prevent CTkImage GC
        self._last_width = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── TOP CONTROL BAR ──
        self._bar = ctk.CTkFrame(
            self,
            fg_color=get_color("colors.background.panel"),
            corner_radius=0,
            height=56,
        )
        self._bar.grid(row=0, column=0, sticky="ew")
        self._bar.pack_propagate(False)

        lbl_title = ctk.CTkLabel(
            self._bar,
            text="Select Summoner Spell",
            font=get_font("title"),
            text_color=get_color("colors.text.primary")
        )
        lbl_title.pack(side="left", padx=16)

        btn_close = make_button(
            self._bar,
            text="✕",
            style="ghost",
            width=40,
            command=self.on_close
        )
        btn_close.pack(side="right", padx=16, pady=8)

        # ── SCROLLABLE LIST ──
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            bg_color="transparent"
        )
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=4, pady=(4, 0))

        # Re-calc layout on resize
        self.bind("<Configure>", self._on_resize)
        
        # Load spells
        self.after(50, self._load)

    def _on_resize(self, event):
        if abs(event.width - self._last_width) > 40:
            self._last_width = event.width
            if self.buttons:
                self.after(50, self._layout_grid)

    def _load(self):
        """Builds the list of spell buttons based on asset_manager data."""
        # Clean up old buttons
        for btn in self.buttons:
            btn.destroy()
        self.buttons.clear()

        # Spell Data maps Spell ID (int) -> Spell Name (e.g. "SummonerSmite")
        spells = list(self.asset_manager.spell_data.values()) if hasattr(self.asset_manager, "spell_data") else []
        spells.sort()

        target_size = 64

        for s_name in spells:
            if "Placeholder" in s_name or "SnowURF" in s_name or "Poro" in s_name or "Cherry" in s_name:
                continue

            btn = ctk.CTkButton(
                self.scroll,
                text=s_name.replace("Summoner", ""),
                image=None,
                compound="top",
                width=target_size,
                height=target_size,
                fg_color="transparent",
                hover_color=get_color("colors.accent.primary").replace(")", ", 0.3)").replace("rgb", "rgba"),
                corner_radius=8,
                text_color=get_color("colors.text.primary"),
                font=get_font("caption"),
                command=lambda n=s_name: self.on_select(n)
            )
            btn.spell_name = s_name
            self.buttons.append(btn)

            # Assign Icons Async
            def _set_icon(img, b=btn, n=s_name):
                try:
                    if b.winfo_exists():
                        if img:
                            self._image_refs[n] = img
                            b.configure(image=img)
                except Exception as e:
                    Logger.error("spell_selector.py", f"Handled exception: {e}")

            # Fast cache or threaded load
            self.asset_manager.get_icon_async("spell", s_name, _set_icon, size=(50, 50), widget=self)

        self._layout_grid()

    def _layout_grid(self):
        """Arranges buttons into a responsive grid."""
        if not self.buttons:
            return

        cols = max(3, self.scroll.winfo_width() // 85)
        row, col = 0, 0

        for btn in self.buttons:
            btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            col += 1
            if col >= cols:
                col = 0
                row += 1
