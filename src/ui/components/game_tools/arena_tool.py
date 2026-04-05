import os
import tkinter as tk
import customtkinter as ctk

from ui.components.factory import get_color, get_font, get_radius, make_input
from ui.ui_shared import CTkTooltip
from core.constants import SPACING_SM, SPACING_MD

class ArenaTool(ctk.CTkFrame):
    """Arena Synergy Picker: If Teammate locks X -> I lock Y."""

    def __init__(self, master, config, assets, **kw):
        super().__init__(master, fg_color="#0F1A24", corner_radius=8, **kw)
        self.config = config
        self.assets = assets

        self._expanded = False
        
        self._known_champions = self._scan_known_champions()
        self._active_entry = None  # Tracks which entry is triggering autocomplete
        
        self._build_header()
        self._build_body()
        self._render_pairs()

    def _get_pairs(self):
        return self.config.get("arena_pairs", [])

    def _save_pairs(self, pairs):
        self.config.set("arena_pairs", pairs)
        self._render_pairs()

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=24)
        self.header.pack(fill="x", padx=SPACING_MD, pady=(SPACING_MD, 0))

        self.lbl_section = ctk.CTkLabel(
            self.header, text="▶  ARENA SYNERGY",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
            cursor="hand2"
        )
        self.lbl_section.pack(side="left", padx=2)
        CTkTooltip(self.lbl_section, "Toggle Arena Synergy Settings")
        self.lbl_section.bind("<Button-1>", lambda e: self._toggle_collapse())
        self.lbl_section.bind("<Enter>", lambda e: self.lbl_section.configure(text_color=get_color("colors.text.primary")))
        self.lbl_section.bind("<Leave>", lambda e: self.lbl_section.configure(text_color=get_color("colors.text.muted")))

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        
        self.add_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        self.add_frame.pack(fill="x", pady=(0, SPACING_MD))

        # IF
        ctk.CTkLabel(self.add_frame, text="IF", font=get_font("caption", "bold"), text_color="#A855F7").pack(side="left", padx=(0, 4))
        self.entry_teammate = make_input(self.add_frame, placeholder="Teammate picks...", width=100, height=24, font=get_font("caption"))
        self.entry_teammate.pack(side="left")
        self.entry_teammate.bind("<KeyRelease>", lambda e: self._on_add_typing(e, self.entry_teammate))

        # THEN
        ctk.CTkLabel(self.add_frame, text="THEN", font=get_font("caption", "bold"), text_color="#00C853").pack(side="left", padx=(8, 4))
        self.entry_me = make_input(self.add_frame, placeholder="I pick...", width=100, height=24, font=get_font("caption"))
        self.entry_me.pack(side="left")
        self.entry_me.bind("<KeyRelease>", lambda e: self._on_add_typing(e, self.entry_me))

        self.btn_add = ctk.CTkButton(
            self.add_frame, text="Save Pair", width=60, height=24,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.state.success"), text_color="#ffffff",
            hover_color="#00b359",
            command=self._add_pair
        )
        self.btn_add.pack(side="right", padx=(4, 0))

        # Suggestions frame
        self.suggestions_frame = ctk.CTkFrame(self.body, fg_color="transparent")
        
        self.list_frame = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=150,
            scrollbar_button_color=get_color("colors.text.disabled")
        )
        self.list_frame.pack(fill="x")

    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)
            self.lbl_section.configure(text="▼  ARENA SYNERGY")
        else:
            self.body.pack_forget()
            self.lbl_section.configure(text="▶  ARENA SYNERGY")

    def _add_pair(self):
        t_champ = self.entry_teammate.get().strip().title()
        m_champ_raw = self.entry_me.get().strip()
        
        if not t_champ or not m_champ_raw:
            return
            
        m_list = [c.strip().title() for c in m_champ_raw.split(',') if c.strip()]
        if not m_list:
            return
            
        pairs = self._get_pairs()
        pairs.append({"teammate": t_champ, "me": m_list})
        self._save_pairs(pairs)
        
        self.entry_teammate.delete(0, 'end')
        self.entry_me.delete(0, 'end')

    def _remove_pair(self, idx):
        pairs = self._get_pairs()
        if 0 <= idx < len(pairs):
            pairs.pop(idx)
            self._save_pairs(pairs)

    def _render_pairs(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        pairs = self._get_pairs()
        
        if not pairs:
            ctk.CTkLabel(self.list_frame, text="No synergy pairs defined.", font=get_font("caption"), text_color=get_color("colors.text.muted")).pack(pady=20)
            return
            
        for i, pair in enumerate(pairs):
            row = ctk.CTkFrame(self.list_frame, fg_color=get_color("colors.background.card"), corner_radius=get_radius("sm"), height=36)
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)
            
            ctk.CTkLabel(row, text=f"{pair['teammate']}", font=get_font("body", "bold"), text_color="#A855F7").pack(side="left", padx=10)
            ctk.CTkLabel(row, text="->", font=get_font("caption"), text_color=get_color("colors.text.muted")).pack(side="left")
            
            me_val = pair['me']
            me_str = ", ".join(me_val) if isinstance(me_val, list) else str(me_val)
            
            ctk.CTkLabel(row, text=me_str, font=get_font("body", "bold"), text_color="#00C853").pack(side="left", padx=10)
            
            ctk.CTkButton(
                row, text="✕", width=24, height=24,
                corner_radius=get_radius("sm"), font=("Segoe UI", 12, "bold"),
                fg_color="transparent", hover_color="#4d1111", text_color="#ff4444",
                command=lambda idx=i: self._remove_pair(idx)
            ).pack(side="right", padx=6)

    # ───────────── autocomplete logic ─────────────
    def _scan_known_champions(self):
        from utils.path_utils import get_asset_path
        known = {}
        cache_dir = get_asset_path("assets")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    real = f[len("champion_"):-len(".png")]
                    known[real.lower()] = real

        self._search_cache = sorted([(v.lower(), v) for v in known.values()], key=lambda x: x[1])
        return known

    def _on_add_typing(self, event, entry_widget):
        if event.keysym in ("Return", "Escape", "Up", "Down", "Left", "Right", "Tab"):
            return

        self._active_entry = entry_widget

        if hasattr(self, "_debounce_timer") and self._debounce_timer is not None:
            self.after_cancel(self._debounce_timer)

        self._debounce_timer = self.after(150, self._perform_add_search)

    def _perform_add_search(self):
        if not self._active_entry:
            return

        full_text = self._active_entry.get()
        parts = full_text.split(',')
        query = parts[-1].strip().lower()

        # Clear existing suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        if not query:
            self.suggestions_frame.pack_forget()
            return

        # Find matches
        matches = []
        for champ_lower, champ in self._search_cache:
            if champ_lower.startswith(query):
                matches.append(champ)
            elif query in champ_lower:
                matches.append(champ)

        unique_matches = list(dict.fromkeys(matches))

        if not unique_matches:
            self.suggestions_frame.pack_forget()
            return

        # Display top 4 matches
        self.suggestions_frame.pack(fill="x", pady=(4, 0), before=self.list_frame)

        for i, champ in enumerate(unique_matches[:4]):
            display_name = champ

            pill = ctk.CTkButton(
                self.suggestions_frame, text=display_name, width=0, height=20,
                corner_radius=10, font=get_font("caption"),
                fg_color=get_color("colors.background.card"),
                border_width=1, border_color=get_color("colors.accent.gold", "#C8AA6E"),
                hover_color=get_color("colors.state.hover"),
                text_color=get_color("colors.text.primary"),
                command=lambda c=display_name: self._select_suggestion(c), cursor="hand2",
            )
            pill.pack(side="left", padx=(0, 4))

    def _select_suggestion(self, display_name):
        if self._active_entry:
            full_text = self._active_entry.get()
            parts = full_text.split(',')
            parts[-1] = " " + display_name if len(parts) > 1 else display_name
            
            new_text = ",".join(parts).strip()
            
            self._active_entry.delete(0, "end")
            self._active_entry.insert(0, new_text)
            self._active_entry.configure(border_color=get_color("colors.accent.primary"))

            def reset_border(entry=self._active_entry):
                if entry.winfo_exists():
                    entry.configure(border_color=get_color("colors.border.subtle"))

            self.after(200, reset_border)

        self.suggestions_frame.pack_forget()
