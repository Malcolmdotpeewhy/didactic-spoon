import threading
import tkinter as tk
import customtkinter as ctk

from ui.components.factory import get_color, get_font, get_radius
from ui.ui_shared import CTkTooltip
from ui.components.lol_toggle import LolToggle
from core.constants import SPACING_SM, SPACING_MD
from tkinterdnd2 import TkinterDnD, DND_TEXT

class SearchableDropdown(ctk.CTkFrame):
    def __init__(self, master, variable, command=None, **kwargs):
        # Remove pack_propagate to allow fluid width stretching based on expand=True
        super().__init__(master, fg_color="transparent", **kwargs)
        self.variable = variable
        self.command = command
        self._values = []
        self._filtered_values = []
        self._dropdown_frame = None
        
        self.entry = ctk.CTkEntry(
            self, textvariable=self.variable,
            height=28,
            font=get_font("body"),
            fg_color=get_color("colors.background.card"),
            border_color=get_color("colors.border.subtle"),
            
        )
        self.entry.pack(side="left", fill="both", expand=True)
        
        self.btn = ctk.CTkButton(
            self, text="▼", width=22, height=28,
            fg_color=get_color("colors.background.card"),
            hover_color=get_color("colors.state.hover"),
            command=self._toggle_dropdown,
            
        )
        self.btn.pack(side="right", fill="y", padx=(2, 0))
        
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<FocusIn>", self._on_focus)
        self.entry.bind("<Escape>", self._close_dropdown)
        
    def configure(self, values=None, **kwargs):
        if values is not None:
            self._values = values
            self._values_lower = [v.lower() for v in values]
            self._filtered_values = values
        super().configure(**kwargs)
        
    def _on_focus(self, event):
        if "name..." in self.variable.get():
            self.variable.set("")
            
    def _on_key(self, event):
        if event.keysym == "Return" and self.command:
            self._close_dropdown()
            self.command()
            return
            
        val = self.variable.get().lower()
        if hasattr(self, "_values_lower") and len(self._values_lower) == len(self._values):
            self._filtered_values = [v for v, v_lower in zip(self._values, self._values_lower) if val in v_lower]
        else:
            self._filtered_values = [v for v in self._values if val in v.lower()]

        if self._dropdown_frame:
            self._populate_dropdown()
        else:
            self._open_dropdown()
            
    def _toggle_dropdown(self):
        if self._dropdown_frame:
            self._close_dropdown()
        else:
            self._filtered_values = self._values
            self._open_dropdown()
            
    def _close_dropdown(self, event=None):
        if self._dropdown_frame:
            try:
                self._dropdown_frame.place_forget()
                self._dropdown_frame.destroy()
            except Exception:
                pass
            self._dropdown_frame = None
            try:
                if hasattr(self, "_click_id"):
                    root = self.winfo_toplevel()
                    root.unbind("<Button-1>", self._click_id)
            except Exception:
                pass
            
    def _open_dropdown(self):
        if self._dropdown_frame: return
        
        root = self.winfo_toplevel()
        # 20% max size calculation
        root_h = root.winfo_height()
        h = max(100, int(root_h * 0.2))
        
        w = self.winfo_width()
        x = self.winfo_rootx() - root.winfo_rootx()
        y = self.winfo_rooty() - root.winfo_rooty() + self.winfo_height() + 2
        
        self._dropdown_frame = ctk.CTkScrollableFrame(
            root, width=w - 5, height=h,
            fg_color=get_color("colors.background.app"),
            border_width=1, border_color=get_color("colors.border.subtle"),
            corner_radius=4
        )
        # Place it floating
        self._dropdown_frame.place(x=x, y=y)
        self._dropdown_frame.lift()
        
        self._populate_dropdown()
        
        # Register global click to close, stored so we can unbind it
        self._click_id = root.bind("<Button-1>", self._check_click_outside, add="+")
        
    def _check_click_outside(self, event):
        if not self._dropdown_frame: return
        try:
            x, y = event.x_root, event.y_root
            fx, fy = self._dropdown_frame.winfo_rootx(), self._dropdown_frame.winfo_rooty()
            fw, fh = self._dropdown_frame.winfo_width(), self._dropdown_frame.winfo_height()
            
            ex, ey = self.winfo_rootx(), self.winfo_rooty()
            ew, eh = self.winfo_width(), self.winfo_height()
            
            in_dropdown = (fx <= x <= fx+fw) and (fy <= y <= fy+fh)
            in_entry = (ex <= x <= ex+ew) and (ey <= y <= ey+eh)
            
            if not in_dropdown and not in_entry:
                self._close_dropdown()
                
                # Unbind the exact callback
                root = self.winfo_toplevel()
                root.unbind("<Button-1>", self._click_id)
        except Exception:
            self._close_dropdown()
        
    def _populate_dropdown(self):
        for w in self._dropdown_frame.winfo_children():
            w.destroy()
            
        if not self._filtered_values:
            lbl = ctk.CTkLabel(self._dropdown_frame, text="No matches", font=get_font("caption"), text_color="gray")
            lbl.pack(pady=4)
            return
            
        for val in self._filtered_values:
            btn = ctk.CTkButton(
                self._dropdown_frame, text=val,
                fg_color="transparent", anchor="w",
                hover_color=get_color("colors.state.hover"),
                height=28,
                command=lambda v=val: self._select_val(v),
                
            )
            btn.pack(fill="x", pady=1)
            
    def _select_val(self, val):
        self.variable.set(val)
        self._close_dropdown()
        if self.command:
            self.after(10, self.command)


class FriendPriorityList(ctk.CTkFrame):
    def __init__(self, master, config, lcu=None, **kw):
        super().__init__(master, fg_color="#0F1A24", corner_radius=8, **kw)

        # Add DnDWrapper capabilities safely without metaclass conflict
        if hasattr(TkinterDnD, 'DnDWrapper'):
            for name, func in TkinterDnD.DnDWrapper.__dict__.items():
                if callable(func) and not name.startswith("__") and not hasattr(self, name):
                    setattr(self, name, func.__get__(self, self.__class__))
        self.config = config
        self.lcu = lcu

        self._expanded = True
        self._friends_data = self._get_priority_list()
        self._lcu_friends_cache = []
        
        self._build_header()
        self._build_body()
        self._render_list()

        # Fetch friends once to populate the combobox
        if self.lcu:
            self.after(200, self._fetch_lcu_friends_async)

    def _get_priority_list(self):
        return self.config.get("auto_join_list", [])

    def _save_priority_list(self, lst):
        self.config.set("auto_join_list", lst)

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=24)
        self.header.pack(fill="x", padx=SPACING_MD, pady=(SPACING_MD, 0))

        self.lbl_section = ctk.CTkLabel(
            self.header, text="▼  FRIEND AUTO-JOIN",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
        )
        self.lbl_section.pack(side="left", padx=2)
        self.lbl_section.bind("<Button-1>", lambda e: self._toggle_collapse())

        # Master Toggle
        self.var_master_enabled = ctk.BooleanVar(value=self.config.get("auto_join_enabled", True))
        def _on_master_toggle():
            self.config.set("auto_join_enabled", self.var_master_enabled.get())
        
        self.sw_master = LolToggle(self.header, variable=self.var_master_enabled, command=_on_master_toggle)
        self.sw_master.pack(side="left", padx=(4, 0))
        CTkTooltip(self.sw_master, "Enable or disable global Friend Auto-Join")

        # Global Down Area
        self.btn_dn_global = ctk.CTkButton(
            self.header, text="▼", width=20, height=20,
            corner_radius=4,
            font=("Arial", 10), fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color="#0F1A24",
            command=self._move_down_global,
            state="disabled",
            cursor="hand2",
        )
        self.btn_dn_global.pack(side="right", padx=0)
        CTkTooltip(self.btn_dn_global, "Move Down")

        # Global Up Area
        self.btn_up_global = ctk.CTkButton(
            self.header, text="▲", width=20, height=20,
            corner_radius=4,
            font=("Arial", 10), fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            text_color="#0F1A24",
            command=self._move_up_global,
            state="disabled",
            cursor="hand2",
        )
        self.btn_up_global.pack(side="right", padx=(0, 2))
        CTkTooltip(self.btn_up_global, "Move Up")

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)

        # Add Input Row
        self.add_row = ctk.CTkFrame(self.body, fg_color="transparent")
        self.add_row.pack(fill="x", pady=(0, SPACING_SM))

        self.var_new_friend = ctk.StringVar()
        self.combo_add = SearchableDropdown(
            self.add_row,
            variable=self.var_new_friend,
            command=self._on_add_friend
            # Removed static width to allow fluid stretching
        )
        self.combo_add.pack(side="left", fill="x", expand=True, padx=(0, 6))
        # Default placeholder setup is handled inside logic

        self.btn_add = ctk.CTkButton(
            self.add_row, text="Add", width=36, height=28,
            font=get_font("body", "bold"),
            fg_color=get_color("colors.accent.primary"),
            hover_color="#005B99",
            text_color="#FFFFFF",
            command=self._on_add_friend,
            
        )
        self.btn_add.pack(side="right")

        # Scrollable list
        self.scroll = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=150,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
            scrollbar_fg_color="transparent",
        )
        try:
            self.scroll._scrollbar.configure(width=6)
        except Exception:
            pass
        self.scroll.pack(fill="x")

        self.list_parent = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.list_parent.pack(fill="x")

        # DND
        if hasattr(self, 'drop_target_register'):
            self.drop_target_register(DND_TEXT)
            self.dnd_bind('<<Drop>>', self._on_dnd_drop)

    def _fetch_lcu_friends_async(self):
        def task():
            try:
                res = self.lcu.request("GET", "/lol-chat/v1/friends")
                if res and res.status_code == 200:
                    friends = res.json()
                    names = []
                    for f in friends:
                        gn = f.get("gameName", "")
                        if gn:
                            names.append(gn)
                    names.sort(key=str.lower)
                    self._lcu_friends_cache = names
                    self.after(0, lambda: self.combo_add.configure(values=self._lcu_friends_cache))
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def _on_add_friend(self):
        name = self.var_new_friend.get().strip()
        if not name or "name..." in name: return
        
        # Check if already exists
        existing_names = [item.get("name", "").lower() for item in self._friends_data]
        if name.lower() not in existing_names:
            self._friends_data.append({"name": name, "enabled": True})
            self._save_priority_list(self._friends_data)
            self._render_list()
        
        self.var_new_friend.set("")

    def _on_dnd_drop(self, event):
        text = event.data
        if not text: return
        names = [n.strip() for n in text.replace('\r', '\n').split('\n') if n.strip()]
        if not names: return
        
        existing_names = [item.get("name", "").lower() for item in self._friends_data]
        added_any = False
        
        for name in names:
            if name.lower() not in existing_names:
                self._friends_data.append({"name": name, "enabled": True})
                existing_names.append(name.lower())
                added_any = True
                
        if added_any:
            self._save_priority_list(self._friends_data)
            self._render_list()

    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(4, 0))
            self.lbl_section.configure(text="▼  FRIEND AUTO-JOIN")
        else:
            self.body.pack_forget()
            self.lbl_section.configure(text="▶  FRIEND AUTO-JOIN")

    def _render_list(self):
        # We unpack directly into the scroll frame to avoid nest bloat as requested
        for w in self.list_parent.winfo_children():
            w.destroy()
            
        lst = self._friends_data
        if not lst:
            lbl = ctk.CTkLabel(self.list_parent, text="No friends configured.\nType a name and click Add.", font=get_font("caption"), text_color=get_color("colors.text.muted"))
            lbl.pack(pady=20)
            return

        for i, item in enumerate(lst):
            row = ctk.CTkFrame(self.list_parent, height=44, fg_color="transparent")
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            is_selected = (i == getattr(self, "_selected_index", -1))
            enabled = item.get("enabled", True)

            if is_selected:
                row.configure(fg_color="#182531")

            # Hover Feedback
            def on_enter(e, r=row, sel=is_selected):
                if not sel: r.configure(fg_color="#16202A")
            def on_leave(e, r=row, sel=is_selected):
                if not sel: r.configure(fg_color="transparent")

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

            # Left Icon / Toggle Switch Wrapper
            idx_var = ctk.BooleanVar(value=enabled)
            setattr(self, f"_var_friend_tog_{i}", idx_var) 
            def _on_tog(idx=i, var=idx_var):
                self._friends_data[idx]["enabled"] = var.get()
                self._save_priority_list(self._friends_data)

            # Use LolToggle as the left side icon indicator
            sw = LolToggle(row, variable=idx_var, command=_on_tog)
            sw.pack(side="left", padx=(6, 8))
            CTkTooltip(sw, "Toggle active state")

            # Name + Subtext (Centered Container)
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", expand=True, fill="x")

            lbl_name = ctk.CTkLabel(
                text_frame, text=item.get("name", ""),
                font=get_font("body", "bold"),
                text_color=get_color("colors.text.primary") if enabled else get_color("colors.text.disabled"),
            )
            lbl_name.pack(anchor="w")

            lbl_sub = ctk.CTkLabel(
                text_frame,
                text="Active" if enabled else "Ignored",
                text_color="#A0A7B0" if enabled else get_color("colors.text.disabled"),
                font=("Segoe UI", 10)
            )
            lbl_sub.pack(anchor="w")

            # Actions (Right side layout)
            action_frame = ctk.CTkFrame(row, fg_color="transparent")
            action_frame.pack(side="right", fill="y")
            
            # Status Indicator
            status_color = get_color("colors.state.success") if enabled else get_color("colors.border.subtle")
            status = ctk.CTkLabel(action_frame, text="●", text_color=status_color)
            status.pack(side="left", padx=(0, 6))

            btn_del = ctk.CTkButton(
                action_frame, text="✕", width=20, height=20,
                corner_radius=4, font=("Arial", 10), fg_color="transparent",
                hover_color="#e81123", text_color=get_color("colors.text.muted") if not is_selected else get_color("colors.background.app"),
                command=lambda idx=i: self._remove_item(idx),
                cursor="hand2",
            )
            btn_del.pack(side="left", padx=(0, 4))
            CTkTooltip(btn_del, "Remove friend")

            # Binding selection propagation safely
            def _select(event, idx=i):
                self._selected_index = idx
                self._render_list()

            row.bind("<Button-1>", _select)
            text_frame.bind("<Button-1>", _select)
            lbl_name.bind("<Button-1>", _select)
            lbl_sub.bind("<Button-1>", _select)
            
        # Update global arrows state
        sel = getattr(self, "_selected_index", -1)
        if hasattr(self, "btn_up_global"):
            if sel > 0:
                self.btn_up_global.configure(state="normal", text_color=get_color("colors.text.muted"))
            else:
                self.btn_up_global.configure(state="disabled", text_color="#0F1A24")
        if hasattr(self, "btn_dn_global"):
            if sel >= 0 and sel < len(lst) - 1:
                self.btn_dn_global.configure(state="normal", text_color=get_color("colors.text.muted"))
            else:
                self.btn_dn_global.configure(state="disabled", text_color="#0F1A24")

    def _move_up_global(self):
        idx = getattr(self, "_selected_index", -1)
        if idx <= 0: return
        self._friends_data[idx], self._friends_data[idx-1] = self._friends_data[idx-1], self._friends_data[idx]
        self._selected_index = idx - 1
        self._save_priority_list(self._friends_data)
        self._render_list()

    def _move_down_global(self):
        idx = getattr(self, "_selected_index", -1)
        if idx == -1 or idx >= len(self._friends_data) - 1: return
        self._friends_data[idx], self._friends_data[idx+1] = self._friends_data[idx+1], self._friends_data[idx]
        self._selected_index = idx + 1
        self._save_priority_list(self._friends_data)
        self._render_list()

    def _remove_item(self, idx):
        self._friends_data.pop(idx)

        sel = getattr(self, "_selected_index", -1)
        if sel == idx:
            self._selected_index = -1
        elif sel > idx:
            self._selected_index -= 1
                
        self._save_priority_list(self._friends_data)
        self._render_list()
