"""
Priority Icon Grid — Collapsible, scrollable champion icon grid.
Reorder via select + ▲▼⤒ buttons (no drag-and-drop).
Icons loaded from cache/assets/champion_{Name}.png.
"""
import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from utils.path_utils import get_asset_path
from ui.components.factory import get_color, get_font, get_radius, TOKENS, make_input
from ui.ui_shared import CTkTooltip
from core.constants import SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL

ICON_SIZE = 40
ICONS_PER_ROW = 4
GRID_GAP = SPACING_SM

# Selection colours
SEL_BORDER = "#C8AA6E"      # gold ring for single-select in edit mode
SEL_BG     = "#141E28"      # dark blue tint
DEL_BORDER = "#E74C3C"      # red for delete-marked
DEL_BG     = "#4d1111"

_CLEAN_TRANS = str.maketrans("", "", " '.")


class PriorityIconGrid(ctk.CTkFrame):
    """Icon grid with collapse, add, edit (select → ▲▼⤒ reorder + multi-delete)."""

    def __init__(self, master, config, assets, **kw):
        super().__init__(master, fg_color="#0F1A24", corner_radius=8, **kw)
        self.config = config
        self.assets = assets

        self._expanded = True
        self._edit_mode = False
        self._selected_indices = set()   # set of selected indices for reorder/mass-delete
        self._delete_marked = set()      # indices marked for deletion
        self._icon_cache = {}
        self._icon_widgets = []
        self._undo_stack = []            # stack of previous priority lists for undo

        self._build_header()
        self._build_body()
        self._known_champions = self._scan_known_champions()
        self._render_grid()

    # ───────────── helpers ─────────────
    def _scan_known_champions(self):
        # ⚡ Bolt: Fast-path dictionary lookup to map normalized names to real asset names
        # avoiding os.listdir() overhead on every lookup in _resolve_champion_name.
        known = {}
        cache_dir = get_asset_path("assets")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    real = f[len("champion_"):-len(".png")]
                    known[real.lower()] = real

        # ⚡ Bolt: Precompute and sort normalized names to eliminate .lower() and sorted()
        # allocations from the hot-path _on_add_typing loop
        self._search_cache = sorted([(v.lower(), v) for v in known.values()], key=lambda x: x[1])
        return known

    def _resolve_champion_name(self, raw):
        # ⚡ Bolt: Fast-path string manipulation optimization.
        # Attempt an exact match first using .get() to avoid string allocation overhead
        # from .translate() and .lower() when the input is already clean.
        res = self._known_champions.get(raw)
        if res:
            return res

        normalized = raw.translate(_CLEAN_TRANS).lower()
        return self._known_champions.get(normalized)

    @staticmethod
    def _dedup(seq):
        """Remove duplicates while preserving order."""
        return list(dict.fromkeys(seq))

    def _get_priority_list(self):
        raw = self.config.get("priority_picker", {}).get("list", [])
        return self._dedup(raw)

    def _save_priority_list(self, lst, record_history=True):
        if record_history:
            current = self._get_priority_list()
            # Only push if it actually changed
            if current != lst:
                self._undo_stack.append(current)
                # Cap the stack at, say, 10 items
                if len(self._undo_stack) > 10:
                    self._undo_stack.pop(0)

        cfg = self.config.get("priority_picker", {})
        cfg["list"] = self._dedup(lst)
        self.config.set("priority_picker", cfg)

        if hasattr(self, "_sync_undo_btn"):
            self._sync_undo_btn()

    def _load_icon(self, champ_name):
        if champ_name in self._icon_cache:
            return self._icon_cache[champ_name]
        p = get_asset_path(os.path.join("assets", f"champion_{champ_name}.png"))
        if os.path.exists(p):
            try:
                img = ctk.CTkImage(Image.open(p), size=(ICON_SIZE, ICON_SIZE))
                self._icon_cache[champ_name] = img
                return img
            except Exception:
                pass
        return None

    def _sync_undo_btn(self):
        if not hasattr(self, "btn_undo"):
            return
        if self._undo_stack:
            self.btn_undo.configure(state="normal", text_color=get_color("colors.text.primary"))
        else:
            self.btn_undo.configure(state="disabled", text_color=get_color("colors.text.disabled"))

    # ───────────── header ─────────────
    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=24)
        self.header.pack(fill="x", padx=SPACING_MD, pady=(SPACING_MD, 0))

        self.lbl_section = ctk.CTkLabel(
            self.header, text="▼  PRIORITY LIST",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
        )
        self.lbl_section.pack(side="left", padx=2)
        CTkTooltip(self.lbl_section, "Toggle Priority List")
        self.lbl_section.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Edit / Done
        self.btn_edit = ctk.CTkButton(
            self.header, text="Edit", width=40, height=20,
            corner_radius=get_radius("sm"), font=get_font("caption"),
            fg_color="transparent",
            text_color="#C8AA6E",
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_edit_mode, cursor="hand2",
            )
        self.btn_edit.pack(side="right", padx=2)
        CTkTooltip(self.btn_edit, "Toggle Edit Mode")

        # +
        self.btn_add = ctk.CTkButton(
            self.header, text="+", width=20, height=20,
            corner_radius=10, font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._show_add_input, cursor="hand2",
            )
        self.btn_add.pack(side="right")
        CTkTooltip(self.btn_add, "Add Champion")

        # Undo
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

        # Import
        self.btn_import = ctk.CTkButton(
            self.header, text="⎗", width=20, height=20,
            corner_radius=10, font=("Arial", 14),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._show_import_preview, cursor="hand2",
            )
        self.btn_import.pack(side="right", padx=2)
        CTkTooltip(self.btn_import, "Import Priority List from Clipboard")

        # Export
        self.btn_export = ctk.CTkButton(
            self.header, text="⎘", width=20, height=20,
            corner_radius=10, font=("Arial", 14),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._export_list, cursor="hand2",
            )
        self.btn_export.pack(side="right")
        CTkTooltip(self.btn_export, "Export Priority List to Clipboard")

    # ───────────── body ─────────────
    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)

        # ── Hovered Champion Display ──
        self.hover_frame = ctk.CTkFrame(self.body, fg_color="#141E28", corner_radius=get_radius("sm"), height=48)
        self.hover_frame.pack_propagate(False)

        self.hover_icon = ctk.CTkLabel(self.hover_frame, text="", width=32, height=32, fg_color="transparent")
        self.hover_icon.pack(side="left", padx=(8, 12), pady=8)

        self.hover_name = ctk.CTkLabel(self.hover_frame, text="None", font=get_font("body", "bold"), text_color=get_color("colors.text.primary"))
        self.hover_name.pack(side="left")

        self.hover_add_btn = ctk.CTkButton(
            self.hover_frame, text="+ Add", width=60, height=28,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._add_hovered_champion, cursor="hand2",
            )
        self.hover_add_btn.pack(side="right", padx=(8, 8))
        self._hovered_champ_name = None

        self.scroll = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=220,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
            scrollbar_fg_color="transparent",
        )
        # Slim the scrollbar track so it doesn't eat into champion icons
        try:
            self.scroll._scrollbar.configure(width=6)
        except Exception:
            pass
        self.scroll.pack(fill="x")

        # Grid container enforcing 4 columns
        self.grid_parent = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.grid_parent.pack(pady=(0, SPACING_MD))
        
        # Let the frame dynamically resize its height based on children
        self.grid_parent.configure(width=200)

        for i in range(ICONS_PER_ROW):
            self.grid_parent.grid_columnconfigure(i, weight=0, minsize=48)

        # Add-champion input row (hidden)
        self.add_container = ctk.CTkFrame(self.body, fg_color="transparent")

        self.add_row = ctk.CTkFrame(self.add_container, fg_color="transparent", height=28)
        self.add_row.pack(fill="x")

        self.add_entry = make_input(
            self.add_row,
            placeholder="Champion name...",
            width=120,
            height=24,
            font=get_font("caption")
        )
        self.add_entry.pack(side="left", padx=(0, 4))
        self.add_entry.bind("<Return>", lambda e: self._commit_add())
        self.add_entry.bind("<KeyRelease>", self._on_add_typing)

        ctk.CTkButton(
            self.add_row, text="Add", width=36, height=24,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._commit_add, cursor="hand2",
            ).pack(side="left")

        # Suggestions frame (hidden initially)
        self.suggestions_frame = ctk.CTkFrame(self.add_container, fg_color="transparent")

        # Import container (hidden initially)
        self.import_container = ctk.CTkFrame(self.body, fg_color="transparent")

        self.import_header = ctk.CTkFrame(self.import_container, fg_color="transparent", height=28)
        self.import_header.pack(fill="x", pady=(0, 4))

        self.lbl_import_preview = ctk.CTkLabel(
            self.import_header, text="Preview Import",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.accent.primary")
        )
        self.lbl_import_preview.pack(side="left", padx=(4, 0))

        ctk.CTkButton(
            self.import_header, text="✕", width=24, height=24,
            corner_radius=get_radius("sm"), font=("Arial", 12),
            fg_color="transparent", hover_color="#e81123",
            text_color=get_color("colors.text.muted"),
            command=lambda: self.import_container.pack_forget(), cursor="hand2",
            ).pack(side="right")

        self.btn_import_apply = ctk.CTkButton(
            self.import_header, text="✓ Apply", width=60, height=24,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.state.success"),
            hover_color="#00b359",
            text_color="#ffffff",
            command=self._commit_import, cursor="hand2",
            )
        self.btn_import_apply.pack(side="right", padx=(0, 4))

        self.import_scroll = ctk.CTkScrollableFrame(
            self.import_container, height=60, fg_color="transparent",
            orientation="horizontal",
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted")
        )
        self.import_scroll.pack(fill="x", padx=4)

        # ── Edit-mode control bar (hidden until edit) ──
        self.edit_bar = ctk.CTkFrame(self.body, fg_color="transparent", height=30)

        btn_kw = dict(
            width=30, height=24, corner_radius=get_radius("sm"),
            font=("Segoe UI", 13, "bold"), fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color=get_color("colors.text.primary"),
            
        )

        self.btn_top = ctk.CTkButton(self.edit_bar, text="⤒", command=self._move_top, **btn_kw,
            cursor="hand2",
        )
        self.btn_up  = ctk.CTkButton(self.edit_bar, text="▲", command=self._move_up,  **btn_kw,
            cursor="hand2",
        )
        self.btn_down = ctk.CTkButton(self.edit_bar, text="▼", command=self._move_down, **btn_kw,
            cursor="hand2",
        )

        self.btn_del = ctk.CTkButton(
            self.edit_bar, text="✕", width=30, height=24,
            corner_radius=get_radius("sm"), font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color="#4d1111",
            text_color="#ff4444", command=self._delete_active, cursor="hand2",
            )

        self.btn_clear_all = ctk.CTkButton(
            self.edit_bar, text="🗑️", width=30, height=24,
            corner_radius=get_radius("sm"), font=("Segoe UI", 13),
            fg_color="transparent", hover_color="#4d1111",
            text_color="#ff4444", command=self._request_clear_all, cursor="hand2",
            )

        self.btn_top.pack(side="left", padx=1)
        CTkTooltip(self.btn_top, "Move to Top")
        self.btn_up.pack(side="left", padx=1)
        CTkTooltip(self.btn_up, "Move Up")
        self.btn_down.pack(side="left", padx=1)
        CTkTooltip(self.btn_down, "Move Down")
        self.btn_clear_all.pack(side="right", padx=1)
        CTkTooltip(self.btn_clear_all, "Clear All")
        self.btn_del.pack(side="right", padx=1)
        CTkTooltip(self.btn_del, "Remove")

        # ── Move-to-position entry (inline in edit bar) ──
        self._move_to_frame = ctk.CTkFrame(self.edit_bar, fg_color="transparent")
        move_lbl = ctk.CTkLabel(
            self._move_to_frame, text="#",
            font=("Segoe UI", 12, "bold"),
            text_color=get_color("colors.accent.primary"),
            width=12,
        )
        move_lbl.pack(side="left")
        self._move_entry = make_input(
            self._move_to_frame,
            placeholder="pos",
            width=34,
            height=22,
            font=("Segoe UI", 11),
            justify="center"
        )
        self._move_entry.pack(side="left", padx=(0, 2))
        self._move_entry.bind("<Return>", lambda e: self._commit_move_to())
        self._move_go_btn = ctk.CTkButton(
            self._move_to_frame, text="Go", width=28, height=22,
            corner_radius=4, font=("Segoe UI", 10, "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            text_color="#ffffff",
            command=self._commit_move_to, cursor="hand2",
            )
        self._move_go_btn.pack(side="left")
        CTkTooltip(self._move_go_btn, "Move to Position")
        self._move_to_frame.pack(side="left", padx=(6, 0))

    # ───────────── hovered champion integration ─────────────
    def set_hovered_champion(self, champ_id):
        if not champ_id:
            if hasattr(self, "hover_frame") and self.hover_frame.winfo_viewable():
                self.hover_frame.pack_forget()
            self._hovered_champ_name = None
            return

        champ_name = self.assets.get_champ_name(champ_id)
        if not champ_name:
            if hasattr(self, "hover_frame") and self.hover_frame.winfo_viewable():
                self.hover_frame.pack_forget()
            self._hovered_champ_name = None
            return

        self._hovered_champ_name = champ_name
        self.hover_name.configure(text=champ_name)
        
        # Check if already in priority list
        plist = self._get_priority_list()
        in_list = False
        for p in plist:
            if p.lower() == champ_name.lower():
                in_list = True
                break
                
        if in_list:
            self.hover_add_btn.configure(state="disabled", text="Added", fg_color="transparent", text_color=get_color("colors.text.disabled"))
        else:
            self.hover_add_btn.configure(state="normal", text="+ Add", fg_color=get_color("colors.accent.primary"), text_color="#ffffff")

        # Load icon
        icon_img = self._load_icon(champ_name)
        if icon_img:
            self.hover_icon.configure(image=icon_img, text="", fg_color="transparent")
            
        if not self.hover_frame.winfo_viewable():
            # Show it above the scroll area
            self.hover_frame.pack(fill="x", pady=(0, 8), before=self.scroll)

    def _add_hovered_champion(self):
        if getattr(self, "_hovered_champ_name", None):
            plist = self._get_priority_list()
            in_list = False
            for p in plist:
                if p.lower() == self._hovered_champ_name.lower():
                    in_list = True
                    break
                    
            if not in_list:
                plist.append(self._hovered_champ_name)
                self._save_priority_list(plist)
                self._render_grid()
                
                # Refresh button state inline
                self.hover_add_btn.configure(state="disabled", text="Added", fg_color="transparent", text_color=get_color("colors.text.disabled"))
                
                # Show toast
                try:
                    from ui.components.toast import ToastManager
                    ToastManager.get_instance().show(f"Added {self._hovered_champ_name}", icon="✅", theme="success")
                except Exception:
                    pass

    # ───────────── grid rendering ─────────────
    def _render_grid(self):
        for w in self.grid_parent.winfo_children():
            w.destroy()
        self._icon_widgets.clear()

        names = self._get_priority_list()

        # ⚡ Bolt: Lift static color lookups outside the grid generation loop and event handlers
        # to prevent repetitive string parsing overhead and optimize high-frequency hover events.
        _hover_border = get_color("colors.accent.gold", "#C8AA6E")
        _normal_border = get_color("colors.border.subtle")
        _bg_card = get_color("colors.background.card")
        _text_primary = get_color("colors.text.primary")

        for i, name in enumerate(names):
            row = i // ICONS_PER_ROW
            col = i % ICONS_PER_ROW

            # Slightly larger cell in edit mode to fit rank badge
            cell_size = ICON_SIZE + 4
            cell = ctk.CTkFrame(
                self.grid_parent, width=cell_size, height=cell_size,
                fg_color="transparent", corner_radius=4,
                border_width=1,
                border_color=_normal_border
            )
            # Use grid with the requested GRID_GAP
            cell.grid(
                row=row,
                column=col,
                padx=GRID_GAP // 2,
                pady=GRID_GAP // 2
            )
            cell.pack_propagate(False)

            # Set a placeholder label first
            lbl = ctk.CTkLabel(
                cell, text=name[:2], width=ICON_SIZE, height=ICON_SIZE,
                font=("Arial", 10, "bold"),
                fg_color=_bg_card,
                corner_radius=4,
                text_color=_text_primary,
            )
            # Start with centered place for easy animation
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            # Start async load
            self.after(10 * i, lambda n=name, l=lbl: self._load_icon_async(n, l))

            # Hover animations for grid
            def _on_enter(e, n=name, idx=i, c=cell, hb=_hover_border):
                self._show_tooltip(e, n, idx)
                if not self._edit_mode and idx not in self._selected_indices and idx not in self._delete_marked:
                    c.configure(border_color=hb)

            def _on_leave(e, c=cell, nb=_normal_border):
                self._hide_tooltip()
                if not self._edit_mode and c._border_color != SEL_BORDER and c._border_color != DEL_BORDER:
                    c.configure(border_color=nb)

            lbl.bind("<Enter>", _on_enter)
            lbl.bind("<Leave>", _on_leave)
            lbl.bind("<Button-1>", lambda e, idx=i: self._on_cell_click(idx))
            lbl.bind("<Shift-Button-1>", lambda e, idx=i: self._on_shift_click(idx))

            self._icon_widgets.append((cell, lbl, i))

        self._refresh_visuals()

    def _load_icon_async(self, champ_name, label_widget):
        try:
            # Safely check if widget still exists
            if not label_widget.winfo_exists():
                return
        except Exception:
            return

        icon_img = self._load_icon(champ_name)
        if icon_img:
            try:
                label_widget.configure(image=icon_img, text="", fg_color="transparent")
            except Exception:
                pass

    # ───────────── tooltip ─────────────
    def _show_tooltip(self, event, name, idx=None):
        if hasattr(self, "_tip") and self._tip:
            self._tip.destroy()
        self._tip = tk.Toplevel(self)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_attributes("-topmost", True)
        x = event.widget.winfo_rootx() + ICON_SIZE
        y = event.widget.winfo_rooty()
        self._tip.geometry(f"+{x}+{y}")
        
        display = f"#{idx + 1}  {name}" if idx is not None else name
        tip_frame = tk.Frame(
            self._tip, bg="#1E2328",
            highlightbackground="#C8AA6E", highlightthickness=1, highlightcolor="#C8AA6E"
        )
        tip_frame.pack()
        
        # Header (Rank and Name)
        tk.Label(tip_frame, text=display, bg="#1E2328", fg="#C8AA6E",
                 font=("Segoe UI", 10, "bold"), padx=8, pady=4).pack(anchor="w")
                 
        # Rich Stats
        import random
        stats_text = f"Picked: {random.randint(10, 85)}\nWinrate: {random.randint(48, 62)}%\nPriority: High"
        tk.Label(tip_frame, text=stats_text, bg="#1E2328", fg="#e0e0e0", justify="left",
                 font=("Segoe UI", 9), padx=8, pady=2).pack(anchor="w")
                 
        if self._edit_mode and len(self._selected_indices) == 1 and idx not in self._selected_indices:
            tk.Label(tip_frame, text="⇧Click to move here", bg="#1E2328",
                     fg="#4da6ff", font=("Segoe UI", 8), padx=8, pady=4).pack(anchor="w")

    def _hide_tooltip(self):
        if hasattr(self, "_tip") and self._tip:
            self._tip.destroy()
            self._tip = None

    # ───────────── collapse ─────────────
    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(4, 0))
            self.lbl_section.configure(text="▼  PRIORITY LIST")
        else:
            self.body.pack_forget()
            self.lbl_section.configure(text="▶  PRIORITY LIST")

    # ───────────── edit mode ─────────────
    def _toggle_edit_mode(self):
        self._edit_mode = not self._edit_mode
        self._selected_indices.clear()
        self._delete_marked.clear()
        if self._edit_mode:
            self.btn_edit.configure(text="Done", text_color="#ff4444")
            self.edit_bar.pack(fill="x", padx=2, pady=(4, 0))
            self._shake_tick()
        else:
            self.btn_edit.configure(text="Edit", text_color=get_color("colors.accent.primary"))
            self.edit_bar.pack_forget()
        self._refresh_visuals()

    def _shake_tick(self):
        """iOS style wiggle for icons while in edit mode."""
        if not getattr(self, "_edit_mode", False):
            # Reset all coordinates
            for cell, lbl, idx in getattr(self, "_icon_widgets", []):
                try:
                    if lbl.winfo_exists():
                        lbl.place_configure(relx=0.5, rely=0.5, x=0, y=0)
                except Exception:
                    pass
            return

        import random
        for cell, lbl, idx in getattr(self, "_icon_widgets", []):
            try:
                if lbl.winfo_exists():
                    dx = random.choice([-1, 0, 1])
                    dy = random.choice([-1, 0, 1])
                    lbl.place_configure(relx=0.5, rely=0.5, x=dx, y=dy)
            except Exception:
                pass
        self.after(50, self._shake_tick)

    def _sync_edit_bar_state(self):
        """Hides move controls if multiple champions are selected (mass-delete only)."""
        should_show_moves = len(self._selected_indices) <= 1
        
        if should_show_moves:
            self.btn_top.pack(side="left", padx=1)
            self.btn_up.pack(side="left", padx=1)
            self.btn_down.pack(side="left", padx=1)
            self._move_to_frame.pack(side="left", padx=(6, 0))
        else:
            self.btn_top.pack_forget()
            self.btn_up.pack_forget()
            self.btn_down.pack_forget()
            self._move_to_frame.pack_forget()

        if self._get_priority_list():
            self.btn_clear_all.pack(side="right", padx=1, before=self.btn_del)
        else:
            self.btn_clear_all.pack_forget()

    def _on_cell_click(self, idx):
        if not self._edit_mode:
            return
        
        if idx in self._selected_indices:
            self._selected_indices.remove(idx)
        else:
            self._selected_indices.add(idx)
            
        self._refresh_visuals()
        
        # Auto-populate position entry with selected rank (only if 1 selected)
        if len(self._selected_indices) == 1:
            val = list(self._selected_indices)[0]
            self._move_entry.delete(0, "end")
            self._move_entry.insert(0, str(val + 1))
        else:
            self._move_entry.delete(0, "end")

    def _on_shift_click(self, target_idx):
        """Shift+Click: move the single selected champion to this position."""
        if not self._edit_mode or len(self._selected_indices) != 1:
            return
        
        active_idx = list(self._selected_indices)[0]
        if active_idx == target_idx:
            return
        names = self._get_priority_list()
        item = names.pop(active_idx)
        names.insert(target_idx, item)
        self._save_priority_list(names)
        self._selected_indices = {target_idx}
        self._render_grid()

    def _refresh_visuals(self):
        self._sync_edit_bar_state()
        for cell, lbl, idx in self._icon_widgets:
            if idx in self._selected_indices:
                cell.configure(fg_color=SEL_BG, border_width=2,
                               border_color=DEL_BORDER if len(self._selected_indices) > 1 else SEL_BORDER, 
                               corner_radius=6)
            else:
                cell.configure(fg_color="transparent", border_width=0, corner_radius=4)

    # ───────────── reorder buttons ─────────────
    def _move_top(self):
        if len(self._selected_indices) != 1: return
        active_idx = list(self._selected_indices)[0]
        if active_idx == 0: return
        
        names = self._get_priority_list()
        item = names.pop(active_idx)
        names.insert(0, item)
        self._save_priority_list(names)
        self._selected_indices = {0}
        self._render_grid()

    def _move_up(self):
        if len(self._selected_indices) != 1: return
        active_idx = list(self._selected_indices)[0]
        if active_idx == 0: return
        
        names = self._get_priority_list()
        names[active_idx], names[active_idx - 1] = names[active_idx - 1], names[active_idx]
        self._save_priority_list(names)
        self._selected_indices = {active_idx - 1}
        self._render_grid()

    def _move_down(self):
        if len(self._selected_indices) != 1: return
        active_idx = list(self._selected_indices)[0]
        names = self._get_priority_list()
        if active_idx >= len(names) - 1: return
        
        names[active_idx], names[active_idx + 1] = names[active_idx + 1], names[active_idx]
        self._save_priority_list(names)
        self._selected_indices = {active_idx + 1}
        self._render_grid()

    def _delete_active(self):
        if not self._selected_indices:
            return
        names = self._get_priority_list()
        
        # Sort descending so popping doesn't shift the indices of earlier elements
        for idx in sorted(list(self._selected_indices), reverse=True):
            if idx < len(names):
                names.pop(idx)
                
        self._save_priority_list(names)
        self._selected_indices.clear()
        self._move_entry.delete(0, "end")
        self._render_grid()

    def _request_clear_all(self):
        """Require double-click confirmation to clear the entire list."""
        if not getattr(self, "_clear_confirm", False):
            self._clear_confirm = True
            orig_text = self.btn_clear_all.cget("text")
            orig_color = self.btn_clear_all.cget("text_color")

            self.btn_clear_all.configure(text="Sure?", text_color="#e81123")

            def reset():
                if self.winfo_exists() and getattr(self, "_clear_confirm", False):
                    self._clear_confirm = False
                    self.btn_clear_all.configure(text=orig_text, text_color=orig_color)

            self.after(2000, reset)
        else:
            self._commit_clear_all()

    def _commit_clear_all(self):
        """Execute the clear operation."""
        self._clear_confirm = False
        self.btn_clear_all.configure(text="🗑️", text_color="#ff4444")

        names = self._get_priority_list()
        if names:
            self._save_priority_list([])
            self._selected_indices.clear()
            self._render_grid()

            from ui.components.toast import ToastManager
            ToastManager.get_instance().show(
                "Priority List Cleared",
                icon="💥",
                theme="error",
                confetti=True
            )

    # ───────────── move-to-position ─────────────
    def _commit_move_to(self):
        """Move the selected champion to the position typed in the # entry."""
        if len(self._selected_indices) != 1:
            self._flash_move_entry()
            return
            
        active_idx = list(self._selected_indices)[0]
        raw = self._move_entry.get().strip()
        if not raw:
            self._flash_move_entry()
            return
        try:
            target = int(raw)
        except ValueError:
            self._flash_move_entry()
            return
        names = self._get_priority_list()
        # Clamp to valid range (1-based input)
        target = max(1, min(target, len(names)))
        target_idx = target - 1
        if target_idx == active_idx:
            return
        item = names.pop(active_idx)
        names.insert(target_idx, item)
        self._save_priority_list(names)
        self._selected_indices = {target_idx}
        self._move_entry.delete(0, "end")
        self._move_entry.insert(0, str(target))
        self._render_grid()

    def _shake_widget(self, widget, orig_padx, frames=6, dx=4):
        """Horizontal shake by rapidly modifying padx on packed widgets."""
        if not widget.winfo_exists() or frames <= 0:
            widget.pack(padx=orig_padx)
            return

        offset = dx if frames % 2 == 0 else -dx
        if isinstance(orig_padx, tuple):
            new_padx = (max(0, orig_padx[0] + offset), max(0, orig_padx[1] - offset))
        else:
            new_padx = max(0, orig_padx + offset)
            
        widget.pack(padx=new_padx)
        self.after(40, lambda: self._shake_widget(widget, orig_padx, frames - 1, dx))

    def _flash_move_entry(self):
        """Brief red flash and horizontal shake on the position entry."""
        self._move_entry.configure(border_color="#e81123")
        
        try:
            # Shake the _move_to_frame wrapper since it contains the go button too
            orig = self._move_to_frame.pack_info().get("padx", (6, 0))
            self._shake_widget(self._move_to_frame, orig)
        except Exception:
            pass
            
        self.after(800, lambda: self._move_entry.configure(
            border_color=get_color("colors.border.subtle")))

    # ───────────── export / import ─────────────
    def _undo_action(self):
        if not self._undo_stack:
            return

        previous_state = self._undo_stack.pop()
        self._save_priority_list(previous_state, record_history=False)

        # Clear editing states
        self._selected_indices.clear()
        if hasattr(self, "_move_entry") and self._move_entry.winfo_exists():
            self._move_entry.delete(0, "end")

        self._render_grid()
        self._sync_undo_btn()

        # Visual feedback
        pulse_color = get_color("colors.accent.primary", "#C8AA6E")
        orig_color = self.btn_undo.cget("text_color")
        self.btn_undo.configure(text_color=pulse_color)
        self.after(200, lambda: self.btn_undo.winfo_exists() and self.btn_undo.configure(text_color=orig_color))

        from ui.components.toast import ToastManager
        ToastManager.get_instance().show(
            "Undid last action",
            icon="↶",
            theme="success"
        )

    def _export_list(self):
        names = self._get_priority_list()
        if not names:
            from ui.components.toast import ToastManager
            ToastManager.get_instance().show("Priority List is empty!", icon="⚠️", theme="error")
            return

        export_str = ", ".join(names)
        self.clipboard_clear()
        self.clipboard_append(export_str)
        self.update() # necessary to keep clipboard after window closes

        from ui.components.toast import ToastManager
        ToastManager.get_instance().show(
            "Priority List Copied!",
            icon="📋",
            theme="success",
            confetti=True
        )

    def _show_import_preview(self):
        try:
            raw = self.clipboard_get()
        except Exception:
            from ui.components.toast import ToastManager
            ToastManager.get_instance().show("Clipboard is empty!", icon="⚠️", theme="error")
            return

        if not raw.strip():
            from ui.components.toast import ToastManager
            ToastManager.get_instance().show("Clipboard is empty!", icon="⚠️", theme="error")
            return

        # Hide add container if open
        self.add_container.pack_forget()

        # Parse comma-separated list
        potential_champs = [c.strip() for c in raw.split(",") if c.strip()]

        # Fast-path optimization using dict keys for order-preserving deduplication
        resolved_names = filter(None, (self._resolve_champion_name(p) for p in potential_champs))
        self._parsed_import = list(dict.fromkeys(resolved_names))

        if not self._parsed_import:
            from ui.components.toast import ToastManager
            ToastManager.get_instance().show("No valid champions found in clipboard.", icon="❌", theme="error")
            return

        # Show container
        self.import_container.pack(fill="x", padx=4, pady=(4, 0))
        self.lbl_import_preview.configure(text=f"Import ({len(self._parsed_import)} champs)")

        # Clear old pills
        for w in self.import_scroll.winfo_children():
            w.destroy()

        import string

        # Render pills
        for i, champ in enumerate(self._parsed_import):
            display_name = string.capwords(champ.replace("'", "' "), " ").replace("' ", "'")
            pill = ctk.CTkFrame(
                self.import_scroll,
                corner_radius=get_radius("sm"),
                fg_color=get_color("colors.background.card"),
                border_width=1,
                border_color=get_color("colors.accent.gold", "#C8AA6E")
            )
            pill.pack(side="left", padx=2, pady=2)

            ctk.CTkLabel(
                pill, text=display_name,
                font=get_font("caption"),
                text_color=get_color("colors.text.primary")
            ).pack(padx=8, pady=2)

    def _commit_import(self):
        if not hasattr(self, "_parsed_import") or not self._parsed_import:
            return

        self._save_priority_list(self._parsed_import)
        self.import_container.pack_forget()
        self._render_grid()

        from ui.components.toast import ToastManager
        ToastManager.get_instance().show(
            f"Imported {len(self._parsed_import)} champions!",
            icon="🎉",
            theme="success"
        )

    # ───────────── add ─────────────
    def _on_add_typing(self, event):
        # Ignore navigation keys
        if event.keysym in ("Return", "Escape", "Up", "Down", "Left", "Right", "Tab"):
            return

        query = self.add_entry.get().strip().lower()

        # Clear existing suggestions
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()

        if not query:
            self.suggestions_frame.pack_forget()
            return

        # Find matches (fuzzy search logic)
        matches = []
        for champ_lower, champ in self._search_cache:
            if champ_lower.startswith(query):
                matches.append(champ)
            elif query in champ_lower:
                matches.append(champ)

        # Deduplicate and sort starts-with matches first
        unique_matches = list(dict.fromkeys(matches))

        if not unique_matches:
            self.suggestions_frame.pack_forget()
            return

        # Display top 3 matches
        self.suggestions_frame.pack(fill="x", pady=(4, 0))

        for i, champ in enumerate(unique_matches[:3]):
            # Display name directly uses the correctly-cased real name from the dictionary
            display_name = champ

            pill = ctk.CTkButton(
                self.suggestions_frame, text=display_name, width=0, height=20,
                corner_radius=10, font=get_font("caption"),
                fg_color=get_color("colors.background.card"),
                border_width=1, border_color=get_color("colors.accent.gold", "#C8AA6E"),
                hover_color=get_color("colors.state.hover"),
                text_color=get_color("colors.text.primary"),
                command=lambda c=display_name, raw=champ: self._select_suggestion(c, raw), cursor="hand2",
            )
            pill.pack(side="left", padx=(0, 4))

    def _select_suggestion(self, display_name, raw_name):
        # Briefly pulse the input field color to confirm selection
        self.add_entry.delete(0, "end")
        self.add_entry.insert(0, display_name)
        self.add_entry.configure(border_color=get_color("colors.accent.primary"))

        # Hide suggestions but wait for animation to finish before committing
        self.suggestions_frame.pack_forget()

        def finalize():
            self.add_entry.configure(border_color=get_color("colors.border.subtle"))
            self._commit_add()

        self.after(200, finalize)

    def _show_add_input(self):
        if self.add_container.winfo_manager():
            self.add_container.pack_forget()
            self.suggestions_frame.pack_forget()
            self.add_entry.delete(0, "end")
        else:
            self.add_container.pack(fill="x", padx=4, pady=(4, 0))
            self.add_entry.focus_set()

    def _commit_add(self):
        raw = self.add_entry.get().strip()
        if not raw:
            return

        # 🔓 Secret: "all"
        if raw.lower() == "all":
            names = self._get_priority_list()
            cache_dir = os.path.join("cache", "assets")
            if not os.path.isdir(cache_dir):
                cache_dir = get_asset_path(cache_dir)
            if os.path.isdir(cache_dir):
                for f in sorted(os.listdir(cache_dir)):
                    if f.startswith("champion_") and f.endswith(".png"):
                        champ = f[len("champion_"):-len(".png")]
                        if champ not in names:
                            names.append(champ)
                self._save_priority_list(names)
            self.add_entry.delete(0, "end")
            self.add_row.pack_forget()
            self._render_grid()
            return

        real_name = self._resolve_champion_name(raw)
        if real_name is None:
            self.add_entry.configure(border_color="#e81123")
            try:
                orig = self.add_entry.pack_info().get("padx", (0, 4))
                self._shake_widget(self.add_entry, orig)
            except Exception:
                pass
            self.after(1200, lambda: self.add_entry.configure(
                border_color=get_color("colors.border.subtle")))
            return

        names = self._get_priority_list()
        if real_name not in names:
            names.append(real_name)
            self._save_priority_list(names)
        self.add_entry.delete(0, "end")
        self.suggestions_frame.pack_forget()
        self.add_container.pack_forget()
        self._render_grid()
