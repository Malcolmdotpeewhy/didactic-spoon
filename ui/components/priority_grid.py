"""
Priority Icon Grid — Collapsible, scrollable champion icon grid.
Reorder via select + ▲▼⤒ buttons (no drag-and-drop).
Icons loaded from cache/assets/champion_{Name}.png.
"""
import os
import tkinter as tk
import customtkinter as ctk
from PIL import Image

from utils.path_utils import resource_path
from ui.components.factory import get_color, get_font, get_radius, TOKENS


ICON_SIZE = 28
ICONS_PER_ROW = 6
GRID_PAD = 1

# Selection colours
SEL_BORDER = "#4da6ff"      # blue ring for single-select in edit mode
SEL_BG     = "#1a2a3e"      # dark blue tint
DEL_BORDER = "#ff4444"      # red for delete-marked
DEL_BG     = "#4d1111"


class PriorityIconGrid(ctk.CTkFrame):
    """Icon grid with collapse, add, edit (select → ▲▼⤒ reorder + multi-delete)."""

    def __init__(self, master, config, assets, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.config = config
        self.assets = assets

        self._expanded = True
        self._edit_mode = False
        self._active_index = None        # single-selected for reorder
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
        cache_dir = os.path.join("cache", "assets")
        if not os.path.isdir(cache_dir):
            cache_dir = resource_path(cache_dir)
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    known.add(f[len("champion_"):-len(".png")].lower())
        return known

    def _resolve_champion_name(self, raw):
        normalized = raw.replace(" ", "").replace("'", "").lower()
        cache_dir = os.path.join("cache", "assets")
        if not os.path.isdir(cache_dir):
            cache_dir = resource_path(cache_dir)
        if os.path.isdir(cache_dir):
            for f in os.listdir(cache_dir):
                if f.startswith("champion_") and f.endswith(".png"):
                    real = f[len("champion_"):-len(".png")]
                    if real.lower() == normalized:
                        return real
        return None

    def _get_priority_list(self):
        return self.config.get("priority_picker", {}).get("list", [])

    def _save_priority_list(self, lst):
        cfg = self.config.get("priority_picker", {})
        cfg["list"] = lst
        self.config.set("priority_picker", cfg)

    def _load_icon(self, champ_name):
        if champ_name in self._icon_cache:
            return self._icon_cache[champ_name]
        paths = [
            os.path.join("cache", "assets", f"champion_{champ_name}.png"),
            resource_path(os.path.join("cache", "assets", f"champion_{champ_name}.png")),
        ]
        for p in paths:
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
            text_color=get_color("colors.accent.primary"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_edit_mode,
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
        )
        self.btn_add.pack(side="right")

    # ───────────── body ─────────────
    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(4, 0))

        self.scroll = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=120,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
        )
        self.scroll.pack(fill="x")

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
        ).pack(side="left")

        # ── Edit-mode control bar (hidden until edit) ──
        self.edit_bar = ctk.CTkFrame(self.body, fg_color="transparent", height=30)

        btn_kw = dict(
            width=30, height=24, corner_radius=get_radius("sm"),
            font=("Segoe UI", 13, "bold"), fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color=get_color("colors.text.primary"),
        )

        self.btn_top = ctk.CTkButton(self.edit_bar, text="⤒", command=self._move_top, **btn_kw)
        self.btn_up  = ctk.CTkButton(self.edit_bar, text="▲", command=self._move_up,  **btn_kw)
        self.btn_down = ctk.CTkButton(self.edit_bar, text="▼", command=self._move_down, **btn_kw)

        self.btn_del = ctk.CTkButton(
            self.edit_bar, text="✕", width=30, height=24,
            corner_radius=get_radius("sm"), font=("Segoe UI", 13, "bold"),
            fg_color="transparent", hover_color="#4d1111",
            text_color="#ff4444", command=self._delete_active,
        )

        self.btn_top.pack(side="left", padx=1)
        self.btn_up.pack(side="left", padx=1)
        self.btn_down.pack(side="left", padx=1)
        self.btn_del.pack(side="right", padx=1)

    # ───────────── grid rendering ─────────────
    def _render_grid(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._icon_widgets.clear()

        names = self._get_priority_list()
        row_frame = None

        for i, name in enumerate(names):
            if i % ICONS_PER_ROW == 0:
                row_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=GRID_PAD)

            icon_img = self._load_icon(name)

            cell = ctk.CTkFrame(
                row_frame, width=ICON_SIZE + 4, height=ICON_SIZE + 4,
                fg_color="transparent", corner_radius=4,
            )
            cell.pack(side="left", padx=GRID_PAD)
            cell.pack_propagate(False)

            if icon_img:
                lbl = ctk.CTkLabel(cell, text="", image=icon_img, width=ICON_SIZE, height=ICON_SIZE)
            else:
                lbl = ctk.CTkLabel(
                    cell, text=name[:2], width=ICON_SIZE, height=ICON_SIZE,
                    font=("Arial", 10, "bold"),
                    fg_color=get_color("colors.background.card"),
                    corner_radius=4,
                    text_color=get_color("colors.text.primary"),
                )
            lbl.pack(expand=True)

            lbl.bind("<Enter>", lambda e, n=name: self._show_tooltip(e, n))
            lbl.bind("<Leave>", lambda e: self._hide_tooltip())
            lbl.bind("<Button-1>", lambda e, idx=i: self._on_cell_click(idx))

            self._icon_widgets.append((cell, lbl, i))

        self._refresh_visuals()

    # ───────────── tooltip ─────────────
    def _show_tooltip(self, event, name):
        if hasattr(self, "_tip") and self._tip:
            self._tip.destroy()
        self._tip = tk.Toplevel(self)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_attributes("-topmost", True)
        x = event.widget.winfo_rootx() + ICON_SIZE
        y = event.widget.winfo_rooty()
        self._tip.geometry(f"+{x}+{y}")
        tk.Label(self._tip, text=name, bg="#1a1a2e", fg="#e0e0e0",
                 font=("Segoe UI", 9), padx=6, pady=2).pack()

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
        self._active_index = None
        self._delete_marked.clear()
        if self._edit_mode:
            self.btn_edit.configure(text="Done", text_color="#ff4444")
            self.edit_bar.pack(fill="x", padx=2, pady=(4, 0))
        else:
            self.btn_edit.configure(text="Edit", text_color=get_color("colors.accent.primary"))
            self.edit_bar.pack_forget()
        self._refresh_visuals()

    def _on_cell_click(self, idx):
        if not self._edit_mode:
            return
        # Single-select toggle
        if self._active_index == idx:
            self._active_index = None
        else:
            self._active_index = idx
        self._refresh_visuals()

    def _refresh_visuals(self):
        for cell, lbl, idx in self._icon_widgets:
            if idx == self._active_index:
                cell.configure(fg_color=SEL_BG, border_width=2,
                               border_color=SEL_BORDER, corner_radius=6)
            else:
                cell.configure(fg_color="transparent", border_width=0, corner_radius=4)

    # ───────────── reorder buttons ─────────────
    def _move_top(self):
        if self._active_index is None or self._active_index == 0:
            return
        names = self._get_priority_list()
        item = names.pop(self._active_index)
        names.insert(0, item)
        self._save_priority_list(names)
        self._active_index = 0
        self._render_grid()

    def _move_up(self):
        if self._active_index is None or self._active_index == 0:
            return
        names = self._get_priority_list()
        i = self._active_index
        names[i], names[i - 1] = names[i - 1], names[i]
        self._save_priority_list(names)
        self._active_index = i - 1
        self._render_grid()

    def _move_down(self):
        names = self._get_priority_list()
        if self._active_index is None or self._active_index >= len(names) - 1:
            return
        i = self._active_index
        names[i], names[i + 1] = names[i + 1], names[i]
        self._save_priority_list(names)
        self._active_index = i + 1
        self._render_grid()

    def _delete_active(self):
        if self._active_index is None:
            return
        names = self._get_priority_list()
        if self._active_index < len(names):
            names.pop(self._active_index)
            self._save_priority_list(names)
        self._active_index = None
        self._render_grid()

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
                cache_dir = resource_path(cache_dir)
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
