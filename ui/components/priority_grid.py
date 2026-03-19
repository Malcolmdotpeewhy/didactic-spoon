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
from ui.components.factory import get_color, get_font, get_radius, TOKENS
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


class PriorityIconGrid(ctk.CTkFrame):
    """Icon grid with collapse, add, edit (select → ▲▼⤒ reorder + multi-delete)."""

    def __init__(self, master, config, assets, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.config = config
        self.assets = assets

        self._expanded = True
        self._edit_mode = False
        self._selected_indices = set()   # set of selected indices for reorder/mass-delete
        self._delete_marked = set()      # indices marked for deletion
        self._icon_cache = {}
        self._icon_widgets = []

        self._build_header()
        self._build_body()
        self._known_champions = self._scan_known_champions()
        self._render_grid()

    # ───────────── helpers ─────────────
    def _scan_known_champions(self):
        known = set()
        cache_dir = get_asset_path("assets")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    known.add(f[len("champion_"):-len(".png")].lower())
        return known

    def _resolve_champion_name(self, raw):
        normalized = raw.replace(" ", "").replace("'", "").lower()
        cache_dir = get_asset_path("assets")
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    real = f[len("champion_"):-len(".png")]
                    if real.lower() == normalized:
                        return real
        return None

    @staticmethod
    def _dedup(seq):
        """Remove duplicates while preserving order."""
        return list(dict.fromkeys(seq))

    def _get_priority_list(self):
        raw = self.config.get("priority_picker", {}).get("list", [])
        return self._dedup(raw)

    def _save_priority_list(self, lst):
        cfg = self.config.get("priority_picker", {})
        cfg["list"] = self._dedup(lst)
        self.config.set("priority_picker", cfg)

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

    # ───────────── header ─────────────
    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=24)
        self.header.pack(fill="x")

        self.lbl_section = ctk.CTkLabel(
            self.header, text="▼  PRIORITY LIST",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
            cursor="hand2",
        )
        self.lbl_section.pack(side="left", padx=2)
        self.lbl_section.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Edit / Done
        self.btn_edit = ctk.CTkButton(
            self.header, text="Edit", width=40, height=20,
            corner_radius=get_radius("sm"), font=get_font("caption"),
            fg_color="transparent",
            text_color="#C8AA6E",
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_edit_mode,
            cursor="hand2"
        )
        self.btn_edit.pack(side="right", padx=2)

        # +
        self.btn_add = ctk.CTkButton(
            self.header, text="+", width=20, height=20,
            corner_radius=10, font=("Arial", 14, "bold"),
            fg_color="transparent",
            text_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._show_add_input,
            cursor="hand2"
        )
        self.btn_add.pack(side="right")
        CTkTooltip(self.btn_add, "Add Champion")

    # ───────────── body ─────────────
    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(4, 0))

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
        
        self.grid_parent.grid_propagate(False)
        self.grid_parent.configure(width=200)

        for i in range(ICONS_PER_ROW):
            self.grid_parent.grid_columnconfigure(i, weight=0, minsize=48)

        # Add-champion input row (hidden)
        self.add_row = ctk.CTkFrame(self.body, fg_color="transparent", height=28)
        self.add_entry = ctk.CTkEntry(
            self.add_row, placeholder_text="Champion name...",
            font=get_font("caption"), height=24, width=120,
            corner_radius=get_radius("sm"),
            fg_color=get_color("colors.background.card"),
            border_width=1,
            border_color=get_color("colors.border.subtle"),
            text_color=get_color("colors.text.primary"),
        )
        self.add_entry.pack(side="left", padx=(0, 4))
        self.add_entry.bind("<Return>", lambda e: self._commit_add())

        ctk.CTkButton(
            self.add_row, text="Add", width=36, height=24,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._commit_add,
            cursor="hand2"
        ).pack(side="left")

        # ── Edit-mode control bar (hidden until edit) ──
        self.edit_bar = ctk.CTkFrame(self.body, fg_color="transparent", height=30)

        btn_kw = dict(
            width=30, height=24, corner_radius=get_radius("sm"),
            font=("Segoe UI", 13, "bold"), fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color=get_color("colors.text.primary"),
            cursor="hand2"
        )

        self.btn_top = ctk.CTkButton(self.edit_bar, text="⤒", command=self._move_top, **btn_kw)
        self.btn_up  = ctk.CTkButton(self.edit_bar, text="▲", command=self._move_up,  **btn_kw)
        self.btn_down = ctk.CTkButton(self.edit_bar, text="▼", command=self._move_down, **btn_kw)

        self.btn_del = ctk.CTkButton(
            self.edit_bar, text="✕", width=30, height=24,
            corner_radius=get_radius("sm"), font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color="#4d1111",
            text_color="#ff4444", command=self._delete_active,
            cursor="hand2"
        )

        self.btn_top.pack(side="left", padx=1)
        CTkTooltip(self.btn_top, "Move to Top")
        self.btn_up.pack(side="left", padx=1)
        CTkTooltip(self.btn_up, "Move Up")
        self.btn_down.pack(side="left", padx=1)
        CTkTooltip(self.btn_down, "Move Down")
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
        self._move_entry = ctk.CTkEntry(
            self._move_to_frame, width=34, height=22,
            font=("Segoe UI", 11), corner_radius=4,
            fg_color=get_color("colors.background.card"),
            border_width=1,
            border_color=get_color("colors.border.subtle"),
            text_color=get_color("colors.text.primary"),
            placeholder_text="pos",
            justify="center",
        )
        self._move_entry.pack(side="left", padx=(0, 2))
        self._move_entry.bind("<Return>", lambda e: self._commit_move_to())
        self._move_go_btn = ctk.CTkButton(
            self._move_to_frame, text="Go", width=28, height=22,
            corner_radius=4, font=("Segoe UI", 10, "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            text_color="#ffffff",
            command=self._commit_move_to,
            cursor="hand2"
        )
        self._move_go_btn.pack(side="left")
        self._move_to_frame.pack(side="left", padx=(6, 0))

    # ───────────── grid rendering ─────────────
    def _render_grid(self):
        for w in self.grid_parent.winfo_children():
            w.destroy()
        self._icon_widgets.clear()

        names = self._get_priority_list()

        for i, name in enumerate(names):
            row = i // ICONS_PER_ROW
            col = i % ICONS_PER_ROW

            # Slightly larger cell in edit mode to fit rank badge
            cell_size = ICON_SIZE + 4
            cell = ctk.CTkFrame(
                self.grid_parent, width=cell_size, height=cell_size,
                fg_color="transparent", corner_radius=4,
                border_width=1,
                border_color=get_color("colors.border.subtle")
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
                fg_color=get_color("colors.background.card"),
                corner_radius=4,
                text_color=get_color("colors.text.primary"),
            )
            # Start with centered place for easy animation
            lbl.place(relx=0.5, rely=0.5, anchor="center")

            # Start async load
            self.after(10 * i, lambda n=name, l=lbl: self._load_icon_async(n, l))

            # Hover animations for grid
            def _on_enter(e, n=name, idx=i, c=cell):
                self._show_tooltip(e, n, idx)
                if not self._edit_mode and idx not in self._selected_indices and idx not in self._delete_marked:
                    c.configure(border_color=get_color("colors.accent.gold", "#C8AA6E"))

            def _on_leave(e, c=cell):
                self._hide_tooltip()
                if not self._edit_mode and c._border_color != SEL_BORDER and c._border_color != DEL_BORDER:
                    c.configure(border_color=get_color("colors.border.subtle"))

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
        # Show rank in tooltip (e.g. "#3 Brand")
        display = f"#{idx + 1}  {name}" if idx is not None else name
        tip_frame = tk.Frame(
            self._tip, bg="#1E2328",
            highlightbackground="#C8AA6E", highlightthickness=1, highlightcolor="#C8AA6E"
        )
        tip_frame.pack()
        tk.Label(tip_frame, text=display, bg="#1E2328", fg="#e0e0e0",
                 font=("Segoe UI", 9), padx=6, pady=2).pack(side="left")
        if self._edit_mode and len(self._selected_indices) == 1 and idx not in self._selected_indices:
            tk.Label(tip_frame, text="  ⇧Click to move here", bg="#1E2328",
                     fg="#4da6ff", font=("Segoe UI", 8), padx=2, pady=2).pack(side="left")

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

    # ───────────── add ─────────────
    def _show_add_input(self):
        if self.add_row.winfo_manager():
            self.add_row.pack_forget()
        else:
            self.add_row.pack(fill="x", padx=4, pady=(4, 0))
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
        self.add_row.pack_forget()
        self._render_grid()
