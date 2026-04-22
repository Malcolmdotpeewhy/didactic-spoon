"""
Arena Synergy Picker V4
─────────────────────────────────────
Two-step guided pair creation:
  Step 1 → Pick the teammate champion (IF they lock X)
  Step 2 → Build a fallback priority array of YOUR champions (THEN I lock Y₁, Y₂, …)

V4 Improvements:
  • Move up/down for pair priority ordering (first match wins)
  • Inline edit — re-enter step 2 to modify fallbacks without deleting
  • Rich empty state with explanation of how synergy works
  • Per-pair enable/disable toggle
  • Clone (duplicate) pair button
  • Pair count badge in header
  • Master toggle + Auto-lock toggle
  • Live status indicator during champ select (active pair glows)
  • Undo history

Champion lookup uses the same pill-style autocomplete as PriorityIconGrid.
Pairs render with champion icons and removable tags.
Backend already supports ban evasion via automation.py's _perform_arena_synergy.
"""
import os
import customtkinter as ctk

from ui.components.factory import get_color, get_font, get_radius
from ui.components.champion_input import ChampionInput
from ui.components.toast import ToastManager  # Item #112: Hoist from inline imports
from ui.ui_shared import CTkTooltip
from utils.path_utils import get_asset_path  # Item #102: Hoist from _scan_known_champions
from core.constants import SPACING_SM, SPACING_MD

ICON_SIZE = 28
_CLEAN_TRANS = str.maketrans("", "", " '.")


class ArenaTool(ctk.CTkFrame):
    """Arena Synergy Picker V4: IF Teammate locks X → I lock Y (fallback priority)."""

    def __init__(self, master, config, assets, **kw):
        super().__init__(master, fg_color=get_color("colors.background.panel", "#0F1A24"), corner_radius=8, **kw)
        self.config = config
        self.assets = assets

        self._expanded = False
        self._known_champions = self._scan_known_champions()

        # Add-flow state
        self._add_step = 0          # 0=idle, 1=picking teammate, 2=picking my champs
        self._pending_teammate = ""
        self._pending_me_list = []
        self._debounce_timer = None

        # Live status — index of the pair currently being acted on by the engine
        self._active_pair_idx = -1

        # Edit mode — index of pair being edited, -1 = new pair
        self._editing_pair_idx = -1

        # Undo
        self._undo_stack = []

        self._build_header()
        self._build_body()
        self._render_pairs()

    # ───────────── data helpers ─────────────
    def _get_pairs(self):
        return self.config.get("arena_pairs", [])

    def _save_pairs(self, pairs, record_history=True):
        if record_history:
            current = self._get_pairs()
            if current != pairs:
                self._undo_stack.append([dict(p) for p in current])
                if len(self._undo_stack) > 10:
                    self._undo_stack.pop(0)
        self.config.set("arena_pairs", pairs)
        self._render_pairs()
        self._sync_undo_btn()

    def _sync_undo_btn(self):
        if not hasattr(self, "btn_undo"):
            return
        if self._undo_stack:
            self.btn_undo.configure(state="normal", text_color=get_color("colors.text.primary"))
        else:
            self.btn_undo.configure(state="disabled", text_color=get_color("colors.text.disabled"))

    # ───────────── champion resolution ─────────────
    def _scan_known_champions(self):
        known = {}
        cache_dir = get_asset_path("assets")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    real = f[len("champion_"):-len(".png")]
                    known[real.lower()] = real

        self._search_cache = sorted(
            [(v.lower(), v) for v in known.values()], key=lambda x: x[1]
        )
        return known

    def _resolve_champion_name(self, raw):
        res = self._known_champions.get(raw)
        if res:
            return res
        normalized = raw.translate(_CLEAN_TRANS).lower()
        return self._known_champions.get(normalized)

    # ───────────── header ─────────────
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
        self.lbl_section.bind("<Enter>", lambda e: self.lbl_section.configure(
            text_color=get_color("colors.text.primary")))
        self.lbl_section.bind("<Leave>", lambda e: self.lbl_section.configure(
            text_color=get_color("colors.text.muted")))

        # Pair count badge
        self.lbl_count = ctk.CTkLabel(
            self.header, text="",
            font=("Inter", 9, "bold"),
            text_color="#A855F7", anchor="w",
            width=20
        )
        self.lbl_count.pack(side="left", padx=(2, 0))

        # + Add button
        self.btn_add_pair = ctk.CTkButton(
            self.header, text="+", width=20, height=20,
            corner_radius=10, font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._show_add_input, cursor="hand2",
        )
        self.btn_add_pair.pack(side="right")
        CTkTooltip(self.btn_add_pair, "Add Synergy Pair")

        # Undo button
        self.btn_undo = ctk.CTkButton(
            self.header, text="↶", width=20, height=20,
            corner_radius=10, font=("Segoe UI", 14),
            fg_color="transparent",
            text_color=get_color("colors.text.disabled"),
            hover_color=get_color("colors.state.hover"),
            command=self._undo_action,
            state="disabled", cursor="hand2",
        )
        self.btn_undo.pack(side="right", padx=2)
        CTkTooltip(self.btn_undo, "Undo Last Action")

    def _update_header_count(self):
        """Update pair count badge in header."""
        pairs = self._get_pairs()
        count = len(pairs)
        enabled_count = sum(1 for p in pairs if p.get("enabled", True))
        if count > 0:
            self.lbl_count.configure(text=f"({enabled_count}/{count})")
        else:
            self.lbl_count.configure(text="")

    # ───────────── body ─────────────
    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")

        # ── Master toggle ──
        self.master_row = ctk.CTkFrame(self.body, fg_color="transparent", height=26)
        self.master_row.pack(fill="x", padx=4, pady=(4, 0))
        self.master_row.pack_propagate(False)

        ctk.CTkLabel(
            self.master_row, text="⚡ Arena Synergy",
            font=get_font("caption", "bold"), text_color=get_color("colors.text.primary"),
            anchor="w"
        ).pack(side="left", padx=(2, 0))

        self.var_synergy_enabled = ctk.BooleanVar(value=self.config.get("arena_synergy_enabled", True))
        self.sw_synergy = ctk.CTkSwitch(
            self.master_row,
            variable=self.var_synergy_enabled,
            width=36, height=18,
            switch_width=32, switch_height=16,
            fg_color=get_color("colors.border.subtle", "#1E2328"),
            progress_color=get_color("colors.accent.purple", "#A855F7"),
            button_color=get_color("colors.accent.gold", "#C8AA6E"),
            button_hover_color="#D9C382",
            text="", command=self._on_toggle_synergy_enabled
        )
        self.sw_synergy.pack(side="right")
        CTkTooltip(self.sw_synergy, "Master switch — enables/disables all arena synergy automation")

        # ── Auto-lock toggle ──
        self.lock_row = ctk.CTkFrame(self.body, fg_color="transparent", height=26)
        self.lock_row.pack(fill="x", padx=4, pady=(2, 0))
        self.lock_row.pack_propagate(False)

        ctk.CTkLabel(
            self.lock_row, text="🔒 Auto-Lock Pick",
            font=get_font("caption"), text_color=get_color("colors.text.muted"),
            anchor="w"
        ).pack(side="left", padx=(2, 0))

        self.var_auto_lock = ctk.BooleanVar(value=self.config.get("arena_auto_lock", False))
        self.sw_auto_lock = ctk.CTkSwitch(
            self.lock_row,
            variable=self.var_auto_lock,
            width=36, height=18,
            switch_width=32, switch_height=16,
            fg_color=get_color("colors.border.subtle", "#1E2328"),
            progress_color=get_color("colors.accent.primary"),
            button_color=get_color("colors.accent.gold", "#C8AA6E"),
            button_hover_color="#D9C382",
            text="", command=self._on_toggle_auto_lock
        )
        self.sw_auto_lock.pack(side="right")
        CTkTooltip(self.sw_auto_lock, "When ON, auto-locks your pick when teammate locks theirs")

        # ── Add-champion input (hidden initially) ──
        self.add_container = ctk.CTkFrame(self.body, fg_color="transparent")

        # Step indicator label
        self.step_label = ctk.CTkLabel(
            self.add_container, text="",
            font=get_font("caption", "bold"),
            text_color="#A855F7", anchor="w"
        )
        self.step_label.pack(fill="x", pady=(0, 4), padx=2)

        # Input row (entry + button)
        self.add_row = ctk.CTkFrame(self.add_container, fg_color="transparent", height=28)
        self.add_row.pack(fill="x")

        self.add_entry = ChampionInput(
            self.add_row,
            placeholder="Champion name...",
            width=130,
            height=24,
            on_commit=lambda c: self._commit_add_step(c)
        )
        self.add_entry.pack(side="left", padx=(0, 4))
        self.add_entry.bind("<Escape>", lambda e: self._cancel_add(), add="+")

        self.btn_commit = ctk.CTkButton(
            self.add_row, text="Add", width=44, height=24,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            text_color="#ffffff",
            command=self._commit_add_step, cursor="hand2",
        )
        self.btn_commit.pack(side="left")

        # Cancel button
        ctk.CTkButton(
            self.add_row, text="✕", width=24, height=24,
            corner_radius=get_radius("sm"), font=("Segoe UI", 11, "bold"),
            fg_color="transparent", hover_color=get_color("colors.state.danger.muted", "#4d1111"),
            text_color=get_color("colors.state.danger", "#ff4444"),
            command=self._cancel_add, cursor="hand2"
        ).pack(side="right", padx=(4, 0))

        # Tags row for step 2 fallback picks (hidden initially)
        self.tags_frame = ctk.CTkFrame(self.add_container, fg_color="transparent")

        # ── Pair list ──
        self.list_frame = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=180,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
            scrollbar_fg_color="transparent",
        )
        try:
            self.list_frame._scrollbar.configure(width=6)
        except Exception:
            pass
        self.list_frame.pack(fill="x")

    def _on_toggle_synergy_enabled(self):
        self.config.set("arena_synergy_enabled", self.var_synergy_enabled.get())

    def _on_toggle_auto_lock(self):
        self.config.set("arena_auto_lock", self.var_auto_lock.get())

    # ───────────── collapse ─────────────
    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)
            self.lbl_section.configure(text="▼  ARENA SYNERGY")
        else:
            self.body.pack_forget()
            self._cancel_add()
            self.lbl_section.configure(text="▶  ARENA SYNERGY")
        self._update_header_count()

    # ───────────── two-step add flow ─────────────
    def _show_add_input(self):
        if self.add_container.winfo_manager():
            self._cancel_add()
            return

        self._add_step = 1
        self._pending_teammate = ""
        self._pending_me_list = []
        self.step_label.configure(text="STEP 1 ─ IF teammate picks:", text_color=get_color("colors.accent.purple", "#A855F7"))
        self.add_entry.delete(0, "end")
        self.add_entry.configure(placeholder_text="Teammate champion...")
        self.btn_commit.configure(text="Next →",
                                  fg_color=get_color("colors.accent.primary"))
        self.tags_frame.pack_forget()

        self.list_frame.pack_forget()
        self.add_container.pack(fill="x", padx=4, pady=(4, 0))
        self.list_frame.pack(fill="x")
        self.add_entry.focus_set()

    def _advance_to_step2(self):
        self._add_step = 2
        self.step_label.configure(
            text=f"STEP 2 ─ IF {self._pending_teammate} → THEN I pick:",
            text_color=get_color("colors.state.success", "#00C853")
        )
        self.add_entry.delete(0, "end")
        self.add_entry.configure(placeholder_text="My champion...")
        self.btn_commit.configure(text="Add",
                                  fg_color=get_color("colors.accent.primary"))
        self._pending_me_list = []
        self.tags_frame.pack(fill="x", pady=(4, 0))
        self._render_tags()
        self.add_entry.focus_set()

    def _cancel_add(self):
        self._add_step = 0
        self._pending_teammate = ""
        self._pending_me_list = []
        self._editing_pair_idx = -1
        self.add_container.pack_forget()
        self.tags_frame.pack_forget()
        self.add_entry.delete(0, "end")

    def _commit_add_step(self, resolved=None):
        if not resolved:
            raw = self.add_entry.get().strip()
            if not raw:
                return
            resolved = self._resolve_champion_name(raw)

        if not resolved:
            self._flash_entry()
            return

        if self._add_step == 1:
            self._pending_teammate = resolved
            self._advance_to_step2()

        elif self._add_step == 2:
            # Prevent duplicates in pending list
            if resolved not in self._pending_me_list:
                self._pending_me_list.append(resolved)
                self._render_tags()

            self.add_entry.delete(0, "end")
            self.add_entry.focus_set()

    def _save_completed_pair(self):
        """Save the finished synergy pair to config."""
        if not self._pending_teammate or not self._pending_me_list:
            return

        pairs = self._get_pairs()

        # Edit mode: update the specific pair we're editing
        if self._editing_pair_idx >= 0 and self._editing_pair_idx < len(pairs):
            pairs[self._editing_pair_idx]["me"] = list(self._pending_me_list)
            action_word = "Updated"
        else:
            # New pair: check if teammate already has a pair, update it
            updated = False
            for pair in pairs:
                if pair.get("teammate", "").lower() == self._pending_teammate.lower():
                    pair["me"] = list(self._pending_me_list)
                    updated = True
                    break

            if not updated:
                pairs.append({
                    "teammate": self._pending_teammate,
                    "me": list(self._pending_me_list),
                    "enabled": True
                })
            action_word = "Saved"

        saved_teammate = self._pending_teammate
        saved_count = len(self._pending_me_list)
        self._save_pairs(pairs)
        self._editing_pair_idx = -1
        self._cancel_add()

        try:
            from ui.components.toast import ToastManager
            ToastManager.get_instance().show(
                f"Synergy {action_word.lower()}: {saved_teammate} → {saved_count} fallback(s)",
                icon="🎯" if action_word == "Saved" else "✎", theme="success"
            )
        except Exception:
            pass

    # ───────────── tags (step 2 fallback picks) ─────────────
    def _render_tags(self):
        for w in self.tags_frame.winfo_children():
            w.destroy()

        if not self._pending_me_list:
            ctk.CTkLabel(
                self.tags_frame,
                text="Type champion names and click Add. Save when done.",
                font=get_font("caption"),
                text_color=get_color("colors.text.disabled"),
                anchor="w"
            ).pack(side="left", padx=4, fill="x")
            return

        # Champion tags with priority numbers
        tag_row = ctk.CTkFrame(self.tags_frame, fg_color="transparent")
        tag_row.pack(fill="x")

        for i, champ in enumerate(self._pending_me_list):
            tag = ctk.CTkFrame(
                tag_row,
                fg_color=get_color("colors.background.card"),
                corner_radius=10,
                border_width=1,
                border_color=get_color("colors.state.success", "#00C853") if i == 0 else get_color("colors.state.success.muted", "#2E7D32")
            )
            tag.pack(side="left", padx=2, pady=2)

            ctk.CTkLabel(
                tag, text=f"#{i + 1}",
                font=("Inter", 9, "bold"),
                text_color=get_color("colors.text.disabled"),
                width=16
            ).pack(side="left", padx=(6, 0))

            ctk.CTkLabel(
                tag, text=champ,
                font=get_font("caption"),
                text_color=get_color("colors.text.primary")
            ).pack(side="left", padx=(2, 2))

            ctk.CTkButton(
                tag, text="×", width=14, height=14,
                corner_radius=7, font=("Arial", 10),
                fg_color="transparent", hover_color=get_color("colors.state.danger.muted", "#4d1111"),
                text_color=get_color("colors.state.danger", "#ff4444"),
                command=lambda idx=i: self._remove_pending_tag(idx),
                cursor="hand2"
            ).pack(side="left", padx=(0, 4))

        # Save button at the end
        ctk.CTkButton(
            tag_row, text="💾 Save", width=56, height=22,
            corner_radius=10, font=get_font("caption", "bold"),
            fg_color=get_color("colors.state.success"),
            hover_color="#00b359", text_color="#ffffff",
            command=self._save_completed_pair, cursor="hand2"
        ).pack(side="right", padx=(4, 0))

    def _remove_pending_tag(self, idx):
        if 0 <= idx < len(self._pending_me_list):
            self._pending_me_list.pop(idx)
            self._render_tags()

    def _flash_entry(self):
        """Red flash on invalid input."""
        self.add_entry.configure(border_color="#e81123")
        self.after(800, lambda: self.add_entry.winfo_exists() and self.add_entry.configure(
            border_color=get_color("colors.border.subtle")))

    # ───────────── live status ─────────────
    def set_active_pair(self, idx):
        """Called externally to indicate which pair the engine is acting on."""
        if idx != self._active_pair_idx:
            self._active_pair_idx = idx
            self._render_pairs()

    # ───────────── render saved pairs ─────────────
    def _render_pairs(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        pairs = self._get_pairs()
        self._update_header_count()

        if not pairs:
            # Rich empty state explaining how Arena Synergy works
            empty_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            empty_frame.pack(fill="x", pady=8, padx=6)

            ctk.CTkLabel(
                empty_frame,
                text="How Arena Synergy Works",
                font=get_font("caption", "bold"),
                text_color=get_color("colors.text.primary"),
                anchor="w"
            ).pack(fill="x", pady=(0, 4))

            for line in [
                "① Your teammate hovers or locks a champion",
                "② LeagueLoop detects a matching synergy rule",
                "③ Your champion is auto-hovered (or locked)",
                "④ If banned, the next fallback is used",
            ]:
                ctk.CTkLabel(
                    empty_frame, text=line,
                    font=("Inter", 10), text_color=get_color("colors.text.muted"),
                    anchor="w"
                ).pack(fill="x", padx=(8, 0))

            empty_btn = ctk.CTkButton(
                empty_frame,
                text="+ Create First Synergy Rule",
                font=get_font("body", "bold"),
                fg_color="transparent",
                border_width=1,
                border_color=get_color("colors.accent.purple", "#A855F7"),
                text_color=get_color("colors.accent.purple", "#A855F7"),
                hover_color=get_color("colors.background.card"),
                height=36,
                corner_radius=8,
                command=self._show_add_input,
                cursor="hand2"
            )
            empty_btn.pack(fill="x", pady=(8, 0))
            return

        _card_bg = get_color("colors.background.card")
        _radius = get_radius("sm")
        _muted = get_color("colors.text.muted")
        _disabled_bg = get_color("colors.background.disabled", "#0A0E14")

        for i, pair in enumerate(pairs):
            is_enabled = pair.get("enabled", True)
            is_active = (i == self._active_pair_idx)

            card_bg = _card_bg if is_enabled else _disabled_bg
            # Active pair gets a subtle glow border
            border_color = get_color("colors.accent.purple", "#A855F7") if is_active else card_bg

            row = ctk.CTkFrame(
                self.list_frame, fg_color=card_bg,
                corner_radius=_radius,
                border_width=1 if is_active else 0,
                border_color=border_color
            )
            row.pack(fill="x", pady=2, padx=2)

            # ── Top: Teammate row ──
            top = ctk.CTkFrame(row, fg_color="transparent")
            top.pack(fill="x", padx=6, pady=(6, 0))

            teammate_name = pair.get("teammate", "?")

            # ── Action buttons FIRST (right side) so they're never pushed off ──
            btn_frame = ctk.CTkFrame(top, fg_color="transparent")
            btn_frame.pack(side="right")

            # Live status dot
            if is_active:
                ctk.CTkLabel(
                    top, text="●", font=("Arial", 8),
                    text_color="#00C853", width=10
                ).pack(side="left", padx=(0, 2))

            # Teammate icon
            t_icon_lbl = ctk.CTkLabel(top, text="", width=ICON_SIZE, height=ICON_SIZE, fg_color="transparent")
            t_icon_lbl.pack(side="left", padx=(0, 4))

            def _load_t_icon(img, label=t_icon_lbl):
                try:
                    if label.winfo_exists():
                        label.configure(image=img, text="")
                except Exception:
                    pass

            self.assets.get_icon_async(
                "champion", teammate_name, _load_t_icon,
                size=(ICON_SIZE, ICON_SIZE), widget=t_icon_lbl
            )

            # IF label (dimmed when disabled, truncated to prevent overflow)
            text_alpha = "#A855F7" if is_enabled else "#4A2D6B"
            ctk.CTkLabel(
                top, text=f"IF  {teammate_name}",
                font=get_font("caption", "bold"),
                text_color=text_alpha, anchor="w"
            ).pack(side="left", padx=(0, 4), fill="x", expand=True)

            ctk.CTkLabel(
                top, text="→", font=get_font("body", "bold"),
                text_color=_muted if is_enabled else "#333"
            ).pack(side="left")

            # Enable/Disable toggle
            var_enabled = ctk.BooleanVar(value=is_enabled)
            sw = ctk.CTkSwitch(
                btn_frame,
                variable=var_enabled,
                width=32, height=16,
                switch_width=28, switch_height=14,
                fg_color=get_color("colors.border.subtle", "#1E2328"),
                progress_color=get_color("colors.accent.purple", "#A855F7"),
                button_color=get_color("colors.accent.gold", "#C8AA6E"),
                button_hover_color="#D9C382",
                text="",
                command=lambda idx=i, v=var_enabled: self._toggle_pair_enabled(idx, v.get())
            )
            sw.pack(side="left", padx=(0, 2))
            CTkTooltip(sw, "Enable/Disable")

            # Move up
            if i > 0:
                ctk.CTkButton(
                    btn_frame, text="▲", width=18, height=18,
                    corner_radius=get_radius("sm"),
                    font=("Arial", 9),
                    fg_color="transparent", hover_color=get_color("colors.state.hover"),
                    text_color=get_color("colors.text.muted"),
                    command=lambda idx=i: self._move_pair(idx, -1),
                    cursor="hand2"
                ).pack(side="left", padx=0)

            # Move down
            if i < len(pairs) - 1:
                ctk.CTkButton(
                    btn_frame, text="▼", width=18, height=18,
                    corner_radius=get_radius("sm"),
                    font=("Arial", 9),
                    fg_color="transparent", hover_color=get_color("colors.state.hover"),
                    text_color=get_color("colors.text.muted"),
                    command=lambda idx=i: self._move_pair(idx, 1),
                    cursor="hand2"
                ).pack(side="left", padx=0)

            # Edit button
            ctk.CTkButton(
                btn_frame, text="✎", width=20, height=20,
                corner_radius=get_radius("sm"),
                font=("Segoe UI", 11),
                fg_color="transparent", hover_color=get_color("colors.state.hover"),
                text_color="#A855F7",
                command=lambda idx=i: self._edit_pair(idx),
                cursor="hand2"
            ).pack(side="left", padx=(0, 2))
            CTkTooltip(btn_frame.winfo_children()[-1], "Edit Fallbacks")

            # Clone button
            ctk.CTkButton(
                btn_frame, text="⧉", width=20, height=20,
                corner_radius=get_radius("sm"),
                font=("Segoe UI", 11),
                fg_color="transparent", hover_color=get_color("colors.state.hover"),
                text_color=get_color("colors.text.muted"),
                command=lambda idx=i: self._clone_pair(idx),
                cursor="hand2"
            ).pack(side="left", padx=(0, 2))
            CTkTooltip(btn_frame.winfo_children()[-1], "Duplicate")

            # Delete button
            ctk.CTkButton(
                btn_frame, text="✕", width=20, height=20,
                corner_radius=get_radius("sm"),
                font=("Segoe UI", 11, "bold"),
                fg_color="transparent", hover_color=get_color("colors.state.danger.muted", "#4d1111"),
                text_color=get_color("colors.state.danger", "#ff4444"),
                command=lambda idx=i: self._remove_pair(idx),
                cursor="hand2"
            ).pack(side="left")

            # ── Bottom: My champions as icon tags ──
            bottom = ctk.CTkFrame(row, fg_color="transparent")
            bottom.pack(fill="x", padx=6, pady=(2, 6))

            me_val = pair.get("me", [])
            me_list = me_val if isinstance(me_val, list) else [me_val]

            for j, me_champ in enumerate(me_list):
                color_str = "#00C853" if j == 0 else "#4CAF50"
                if not is_enabled:
                    color_str = "#2A3A2A" if j == 0 else "#1E2E1E"

                tag = ctk.CTkFrame(
                    bottom, fg_color=get_color("colors.background.app", "#0A1428"),
                    corner_radius=10,
                    border_width=1,
                    border_color=color_str
                )
                tag.pack(side="left", padx=(0, 4), pady=1)

                # Mini icon
                m_icon_lbl = ctk.CTkLabel(
                    tag, text="", width=18, height=18,
                    fg_color="transparent"
                )
                m_icon_lbl.pack(side="left", padx=(4, 0), pady=2)

                def _load_m_icon(img, label=m_icon_lbl):
                    try:
                        if label.winfo_exists():
                            label.configure(image=img, text="")
                    except Exception:
                        pass

                self.assets.get_icon_async(
                    "champion", me_champ, _load_m_icon,
                    size=(18, 18), widget=m_icon_lbl
                )

                # Priority number + name
                ctk.CTkLabel(
                    tag,
                    text=f"#{j + 1} {me_champ}",
                    font=("Inter", 10),
                    text_color=color_str
                ).pack(side="left", padx=(2, 6), pady=2)

    # ───────────── pair actions ─────────────
    def _toggle_pair_enabled(self, idx, enabled):
        pairs = self._get_pairs()
        if 0 <= idx < len(pairs):
            pairs[idx]["enabled"] = enabled
            self._save_pairs(pairs)

    def _move_pair(self, idx, direction):
        """Move a pair up (-1) or down (+1) in the list."""
        pairs = self._get_pairs()
        new_idx = idx + direction
        if 0 <= new_idx < len(pairs):
            pairs[idx], pairs[new_idx] = pairs[new_idx], pairs[idx]
            self._save_pairs(pairs)
            try:
                from ui.components.toast import ToastManager
                name = pairs[new_idx].get('teammate', 'Pair')
                ToastManager.get_instance().show(
                    f"Moved {name} {'up' if direction < 0 else 'down'}",
                    icon="↕", theme="success"
                )
            except Exception:
                pass

    def _edit_pair(self, idx):
        """Open step 2 pre-populated with the pair's existing fallbacks for editing."""
        pairs = self._get_pairs()
        if not (0 <= idx < len(pairs)):
            return

        pair = pairs[idx]
        self._editing_pair_idx = idx
        self._pending_teammate = pair.get("teammate", "")
        me_val = pair.get("me", [])
        self._pending_me_list = list(me_val) if isinstance(me_val, list) else [me_val]
        self._add_step = 2

        self.step_label.configure(
            text=f"EDITING ─ {self._pending_teammate} → fallbacks:",
            text_color="#FFA726"
        )
        self.add_entry.delete(0, "end")
        self.add_entry.configure(placeholder_text="Add champion...")
        self.btn_commit.configure(text="Add",
                                  fg_color=get_color("colors.accent.primary"))

        self.tags_frame.pack(fill="x", pady=(4, 0))
        self._render_tags()

        self.list_frame.pack_forget()
        self.add_container.pack(fill="x", padx=4, pady=(4, 0))
        self.list_frame.pack(fill="x")
        self.add_entry.focus_set()

    def _clone_pair(self, idx):
        pairs = self._get_pairs()
        if 0 <= idx < len(pairs):
            original = pairs[idx]
            clone = {
                "teammate": original.get("teammate", ""),
                "me": list(original.get("me", [])),
                "enabled": True
            }
            # Insert clone right after the original
            pairs.insert(idx + 1, clone)
            self._save_pairs(pairs)
            try:
                ToastManager.get_instance().show(
                    f"Cloned: {clone['teammate']}",
                    icon="⧉", theme="success"
                )
            except Exception:
                pass

    def _remove_pair(self, idx):
        pairs = self._get_pairs()
        if 0 <= idx < len(pairs):
            removed = pairs[idx].get("teammate", "pair")
            pairs.pop(idx)
            self._save_pairs(pairs)
            try:
                ToastManager.get_instance().show(
                    f"Removed {removed}",
                    icon="🗑️", theme="error"
                )
            except Exception:
                pass

    # ───────────── undo ─────────────
    def _undo_action(self):
        if not self._undo_stack:
            return
        previous = self._undo_stack.pop()
        self._save_pairs(previous, record_history=False)
        self._sync_undo_btn()

        pulse_color = get_color("colors.accent.primary", "#C8AA6E")
        orig_color = self.btn_undo.cget("text_color")
        self.btn_undo.configure(text_color=pulse_color)
        self.after(200, lambda: self.btn_undo.winfo_exists() and self.btn_undo.configure(
            text_color=orig_color
        ))

        try:
            ToastManager.get_instance().show("Undid last action", icon="↶", theme="success")
        except Exception:
            pass
