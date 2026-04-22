"""
Friend Priority List — Rebuilt V2
──────────────────────────────────
Grid-based friend rows with proper scroll/input separation,
deterministic layout, and tokenized styling throughout.

Structure:
  ┌─────────────────────────┐
  │ ▼ FRIEND LIST   [actions]│  ← header (grid)
  ├─────────────────────────┤
  │ [SCROLLABLE FRIEND LIST]│  ← scroll area (pack, isolated)
  │  ┌ icon ┬ name  ┬ ⚭ ┐  │
  │  │      │ status│   │  │
  │  └──────┴───────┴───┘  │
  └─────────────────────────┘
"""
import threading
import tkinter as tk
import customtkinter as ctk

from ui.components.factory import get_color, get_font, get_radius
from ui.ui_shared import CTkTooltip
from core.constants import SPACING_SM, SPACING_MD, ROW_HEIGHT, ICON_SIZE, PADDING_X
from utils.logger import Logger


class FriendRow(ctk.CTkFrame):
    """A single friend entry using grid layout for deterministic column alignment."""

    def __init__(self, master, name, status_text, availability, icon_widget_cb=None,
                 is_auto_join=False, on_toggle_auto_join=None, on_context_menu=None, **kw):
        super().__init__(master, height=ROW_HEIGHT + 4, fg_color="transparent", cursor="hand2", **kw)
        self.grid_columnconfigure(2, weight=1)  # Name column expands
        self.grid_propagate(False)

        self._name = name
        self._on_toggle = on_toggle_auto_join
        self._on_context = on_context_menu

        # Hover feedback
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Col 0: Profile Icon
        self.icon_frame = ctk.CTkFrame(self, fg_color="transparent", width=ICON_SIZE, height=ICON_SIZE)
        self.icon_frame.grid(row=0, column=0, rowspan=2, padx=(PADDING_X, 6), pady=4, sticky="w")
        self.icon_frame.grid_propagate(False)
        self.icon_lbl = ctk.CTkLabel(self.icon_frame, text="")
        self.icon_lbl.pack(expand=True, fill="both")

        # Async icon loading callback
        if icon_widget_cb:
            icon_widget_cb(self.icon_lbl)

        # Col 1: Status Dot
        is_online = availability != "offline"
        dot_color = get_color("colors.state.success") if is_online else get_color("colors.state.error")
        self.status_dot = ctk.CTkLabel(
            self, text="●", text_color=dot_color,
            font=get_font("body"), width=14
        )
        self.status_dot.grid(row=0, column=1, rowspan=2, padx=(0, 4), sticky="w")
        CTkTooltip(self.status_dot, f"Status: {availability}")

        # Col 2: Name + Status Text (stacked)
        name_color = get_color("colors.accent.primary") if is_online else get_color("colors.text.disabled")
        self.lbl_name = ctk.CTkLabel(
            self, text=name,
            font=get_font("body", "bold"),
            text_color=name_color,
            anchor="w"
        )
        self.lbl_name.grid(row=0, column=2, sticky="ew", pady=(4, 0))

        status_color = get_color("colors.text.muted") if is_online else get_color("colors.text.disabled")
        self.lbl_status = ctk.CTkLabel(
            self, text=status_text,
            font=get_font("caption"),
            text_color=status_color,
            anchor="w"
        )
        self.lbl_status.grid(row=1, column=2, sticky="ew", pady=(0, 4))

        # Col 3: Auto-Join Indicator
        aj_color = "#00A2FF" if is_auto_join else get_color("colors.text.disabled")
        aj_tip = "Auto-Join Active — Click to toggle" if is_auto_join else "Auto-Join Inactive — Click to toggle"
        self.auto_join_lbl = ctk.CTkLabel(
            self, text="⚭", font=get_font("title", "bold"),
            text_color=aj_color, cursor="hand2", width=24
        )
        self.auto_join_lbl.grid(row=0, column=3, rowspan=2, padx=(4, PADDING_X), sticky="e")
        CTkTooltip(self.auto_join_lbl, aj_tip)

        # Left-click toggle on auto-join icon (Item #154)
        self.auto_join_lbl.bind("<Button-1>", lambda e: self._on_toggle(self._name) if self._on_toggle else None)

        # Right-click context menu on all widgets
        for w in [self, self.icon_lbl, self.status_dot, self.lbl_name, self.lbl_status, self.auto_join_lbl]:
            w.bind("<Button-3>", self._popup_context)
            # Propagate hover to parent row
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self.configure(fg_color=get_color("colors.state.hover"))

    def _on_leave(self, e):
        self.configure(fg_color="transparent")

    def _popup_context(self, e):
        if self._on_context:
            self._on_context(e, self._name)


class FriendPriorityList(ctk.CTkFrame):
    """Rebuilt friend list with grid-based rows and separated scroll/input areas."""

    def __init__(self, master, config, lcu=None, **kw):
        super().__init__(master, fg_color=get_color("colors.background.panel"), corner_radius=8, **kw)

        self.config = config
        self.lcu = lcu

        self._expanded = True
        self._friends_data = []
        self._auto_join_names = {
            f.get("name", "").lower(): f.get("enabled", True)
            for f in self.config.get("auto_join_list", [])
        }
        self._last_render_sig = None
        self._row_widgets = []  # Track FriendRow instances for cleanup

        self._build_header()
        self._build_body()

        if self.lcu:
            self.after(200, self._fetch_lcu_friends_loop)

    # ─────────── Config Persistence ───────────

    def _save_priority_list(self):
        lst = [{"name": name, "enabled": enabled} for name, enabled in self._auto_join_names.items()]
        self.config.set("auto_join_list", lst)

    # ─────────── Header ───────────

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=28)
        self.header.pack(fill="x", padx=SPACING_MD, pady=(SPACING_MD, 0))
        self.header.grid_columnconfigure(1, weight=1)

        self.lbl_section = ctk.CTkLabel(
            self.header, text="▼  FRIEND LIST",
            font=get_font("caption", "bold"),
            text_color=get_color("colors.text.muted"), anchor="w",
            cursor="hand2"
        )
        self.lbl_section.pack(side="left", padx=2)
        self.lbl_section.bind("<Button-1>", lambda e: self._toggle_collapse())
        self.lbl_section.bind("<Enter>", lambda e: self.lbl_section.configure(text_color=get_color("colors.text.primary")))
        self.lbl_section.bind("<Leave>", lambda e: self.lbl_section.configure(text_color=get_color("colors.text.muted")))

        # Online count badge
        self.lbl_online_count = ctk.CTkLabel(
            self.header, text="0", width=22, height=18,
            corner_radius=9, fg_color=get_color("colors.text.muted"),
            text_color=get_color("colors.background.app"),
            font=get_font("caption", "bold")
        )
        self.lbl_online_count.pack(side="left", padx=(4, 0))

        # Export button
        self.btn_export = ctk.CTkButton(
            self.header, text="⎘", width=20, height=20,
            corner_radius=4, font=get_font("body"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._export_list, cursor="hand2",
        )
        self.btn_export.pack(side="right", padx=(0, 2))
        CTkTooltip(self.btn_export, "Export List to Clipboard")

        # Mass Invite button
        self.btn_mass_invite = ctk.CTkButton(
            self.header, text="👥 Invite All", width=80, height=20,
            corner_radius=get_radius("sm"), font=get_font("caption", "bold"),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._on_mass_invite,
            cursor="hand2",
        )
        self.btn_mass_invite.pack(side="right")
        CTkTooltip(self.btn_mass_invite, "Invite all online friends (or VIPs) to your lobby")

    # ─────────── Body (Scroll Area) ───────────

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)

        self.scroll = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=220,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
            scrollbar_fg_color="transparent",
        )
        try:
            self.scroll._scrollbar.configure(width=6)
        except Exception:
            pass
        self.scroll.pack(fill="both", expand=True)

        # The list_parent lives inside the scroll frame
        self.list_parent = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.list_parent.pack(fill="x")

    # ─────────── Data Fetching ───────────

    def _fetch_lcu_friends_loop(self):
        if not self.winfo_exists() or not self.lcu:
            return

        def task():
            try:
                res = self.lcu.request("GET", "/lol-chat/v1/friends")
                if res and res.status_code == 200:
                    friends = res.json()

                    for f in friends:
                        f["_name_lower"] = f.get("gameName", "").lower()

                    def sort_key(f):
                        avail = f.get("availability", "offline")
                        gn = f.get("_name_lower", f.get("gameName", "").lower())
                        prio = 1 if avail == "offline" else 0
                        return (prio, gn)

                    friends.sort(key=sort_key)
                    self._friends_data = friends
                    self.after(0, self._render_and_reschedule)
            except Exception as e:
                Logger.debug("FriendList", f"Fetch error: {e}")
                self.after(0, self._schedule_next_fetch)

        threading.Thread(target=task, daemon=True).start()

    def _render_and_reschedule(self):
        """Called on main thread: render the list then schedule next fetch."""
        self._render_list()
        self._schedule_next_fetch()

    def _schedule_next_fetch(self):
        """Schedule next friend fetch from the main thread."""
        if self.winfo_exists():
            self.after(5000, self._fetch_lcu_friends_loop)

    # ─────────── Collapse ───────────

    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(4, 0))
            self.lbl_section.configure(text="▼  FRIEND LIST")
        else:
            self.body.pack_forget()
            self.lbl_section.configure(text="▶  FRIEND LIST")

    # ─────────── Auto-Join Toggle ───────────

    def _toggle_auto_join(self, name):
        name_lower = name.lower()
        self._auto_join_names[name_lower] = not self._auto_join_names.get(name_lower, False)
        self._save_priority_list()
        self._last_render_sig = None  # Force re-render
        self._render_list()

    # ─────────── Context Menu ───────────

    def _show_context_menu(self, event, friend_name):
        menu = tk.Menu(
            self, tearoff=0,
            bg=get_color("colors.background.card"),
            fg=get_color("colors.text.primary", "#F0E6D2"),
            activebackground=get_color("colors.state.hover"),
            activeforeground=get_color("colors.text.primary"),
            relief="flat",
            borderwidth=1,
        )

        name_lower = friend_name.lower()
        is_auto = self._auto_join_names.get(name_lower, False)
        label = "✕ Disable Auto-Join" if is_auto else "✓ Enable Auto-Join"
        menu.add_command(label=label, command=lambda: self._toggle_auto_join(friend_name))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ─────────── Render Signature (Dedup) ───────────

    def _get_render_signature(self):
        sig = []
        for f in self._friends_data:
            name = f.get("gameName", "")
            avail = f.get("availability", "offline")
            msg = f.get("availabilityMessage", "Online")
            name_lower = f.get("_name_lower", name.lower())
            is_auto = self._auto_join_names.get(name_lower, False)
            sig.append(f"{name}|{avail}|{msg}|{is_auto}")
        return "|".join(sig)

    # ─────────── Rendering ───────────

    def _render_list(self):
        if not self.winfo_exists():
            return

        sig = self._get_render_signature()
        if self._last_render_sig == sig:
            return
        self._last_render_sig = sig

        # Destroy old rows
        for w in self._row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._row_widgets.clear()

        for w in self.list_parent.winfo_children():
            w.destroy()

        # Update online count badge
        online_count = sum(1 for f in self._friends_data if f.get("availability", "offline") != "offline")
        total_count = len(self._friends_data)
        if hasattr(self, "lbl_online_count"):
            self.lbl_online_count.configure(text=str(online_count))
            if online_count > 0:
                self.lbl_online_count.configure(fg_color=get_color("colors.state.success"))
            else:
                self.lbl_online_count.configure(fg_color=get_color("colors.text.muted"))

        if not self._friends_data:
            lbl = ctk.CTkLabel(
                self.list_parent, text="Checking friends...",
                font=get_font("caption"),
                text_color=get_color("colors.text.muted")
            )
            lbl.pack(pady=20)
            return

        # Hoist assets lookup outside the loop
        root = self.winfo_toplevel()
        assets = getattr(root, "assets", None)

        for item in self._friends_data:
            name = item.get("gameName", "")
            if not name:
                continue

            avail = item.get("availability", "offline")
            status_msg = item.get("availabilityMessage", "Online") if avail != "offline" else "Offline"
            if avail in ("dnd", "away", "chat"):
                if not status_msg:
                    status_msg = avail.capitalize()

            name_lower = item.get("_name_lower", name.lower())
            is_auto = self._auto_join_names.get(name_lower, False)

            # Build icon loading callback
            def make_icon_cb(asset_mgr, icon_id):
                def cb(label_widget):
                    if asset_mgr and hasattr(asset_mgr, "get_icon_async"):
                        asset_mgr.get_icon_async(
                            "profileicon", str(icon_id),
                            lambda img, l=label_widget: l.configure(image=img) if l.winfo_exists() else None,
                            size=(ICON_SIZE, ICON_SIZE), widget=label_widget
                        )
                return cb

            icon_cb = make_icon_cb(assets, item.get("icon", 1))

            row = FriendRow(
                self.list_parent,
                name=name,
                status_text=status_msg,
                availability=avail,
                icon_widget_cb=icon_cb,
                is_auto_join=is_auto,
                on_toggle_auto_join=self._toggle_auto_join,
                on_context_menu=self._show_context_menu,
            )
            row.pack(fill="x", pady=1)
            self._row_widgets.append(row)

    # ─────────── Export ───────────

    def _export_list(self):
        """Copies the active Friend Auto-Join list to the clipboard."""
        from ui.components.toast import ToastManager
        if not self._friends_data:
            ToastManager.get_instance().show("Friend list is empty!", icon="⚠️", theme="error")
            return

        names = [f.get("name", "") for f in self._friends_data if f.get("name", "")]
        export_str = "\n".join(names)

        self.clipboard_clear()
        self.clipboard_append(export_str)
        self.update()

        ToastManager.get_instance().show(
            "Friend List Copied!",
            icon="📋",
            theme="success",
            confetti=True
        )

    # ─────────── Mass Invite ───────────

    def _on_mass_invite(self):
        """Delegate mass invite to the automation engine via the widget tree."""
        root = self.winfo_toplevel()
        engine = getattr(root, "automation", None)
        if engine:
            threading.Thread(target=engine.mass_invite_friends, daemon=True).start()
        else:
            try:
                from ui.components.toast import ToastManager
                ToastManager.get_instance().show("Automation engine not available.", icon="⚠️", theme="error")
            except Exception:
                pass
