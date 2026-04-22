import threading
import tkinter as tk
import customtkinter as ctk

from ui.components.factory import get_color, get_font, get_radius, make_input
from ui.ui_shared import CTkTooltip
from core.constants import SPACING_SM, SPACING_MD

class FriendPriorityList(ctk.CTkFrame):
    def __init__(self, master, config, lcu=None, **kw):
        super().__init__(master, fg_color=get_color("colors.background.panel"), corner_radius=8, **kw)

        self.config = config
        self.lcu = lcu

        self._expanded = True
        self._friends_data = []  # Stores LCU friend objects
        self._auto_join_names = {f.get("name", "").lower(): f.get("enabled", True) for f in self.config.get("auto_join_list", [])}
        self._last_render_sig = None  # Dedup signature to avoid redundant re-renders
        
        self._build_header()
        self._build_body()

        # Start fetching loop
        if self.lcu:
            self.after(200, self._fetch_lcu_friends_loop)

    def _save_priority_list(self):
        # Convert dictionary back to list of dicts for config
        lst = [{"name": name, "enabled": enabled} for name, enabled in self._auto_join_names.items()]
        self.config.set("auto_join_list", lst)

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent", height=24)
        self.header.pack(fill="x", padx=SPACING_MD, pady=(SPACING_MD, 0))

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

        # Mass Invite button (right-aligned in header)
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

        # 🔮 Malcolm's Infusion: Export List Area
        self.btn_export = ctk.CTkButton(
            self.header, text="⎘", width=20, height=20,
            corner_radius=4, font=("Arial", 14),
            fg_color="transparent",
            text_color=get_color("colors.text.muted"),
            hover_color=get_color("colors.state.hover"),
            command=self._export_list, cursor="hand2",
            )
        self.btn_export.pack(side="right", padx=(0, 2))
        CTkTooltip(self.btn_export, "Export List to Clipboard")

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

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="x", pady=(SPACING_SM, SPACING_MD), padx=SPACING_MD)

        self.scroll = ctk.CTkScrollableFrame(
            self.body, fg_color="transparent", height=200,
            scrollbar_button_color=get_color("colors.text.disabled"),
            scrollbar_button_hover_color=get_color("colors.text.muted"),
            scrollbar_fg_color="transparent",
        )
        try:
            self.scroll._scrollbar.configure(width=6)
        except Exception:
            pass
        self.scroll.pack(fill="both", expand=True)

        self.list_parent = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.list_parent.pack(fill="x")

    def _fetch_lcu_friends_loop(self):
        if not self.winfo_exists() or not self.lcu:
            return

        def task():
            try:
                res = self.lcu.request("GET", "/lol-chat/v1/friends")
                if res and res.status_code == 200:
                    friends = res.json()
                    
                    # Sort active friends to top, then alphabetical
                    for f in friends:
                        f["_name_lower"] = f.get("gameName", "").lower()

                    def sort_key(f):
                        avail = f.get("availability", "offline")
                        gn = f.get("_name_lower", f.get("gameName", "").lower())
                        prio = 1 if avail == "offline" else 0
                        return (prio, gn)
                        
                    friends.sort(key=sort_key)
                    self._friends_data = friends
                    # Item #152: Schedule render AND next poll from main thread only
                    self.after(0, self._render_and_reschedule)
            except Exception:
                # Still reschedule on error
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

    def _toggle_collapse(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.body.pack(fill="x", pady=(4, 0))
            self.lbl_section.configure(text="▼  FRIEND LIST")
        else:
            self.body.pack_forget()
            self.lbl_section.configure(text="▶  FRIEND LIST")

    def _toggle_auto_join(self, name):
        name_lower = name.lower()
        self._auto_join_names[name_lower] = not self._auto_join_names.get(name_lower, False)
        self._save_priority_list()
        self._render_list()

    def _show_context_menu(self, event, friend_name):
        menu = tk.Menu(self, tearoff=0, bg=get_color("colors.background.card"), fg=get_color("colors.text.primary", "#F0E6D2"))
        
        name_lower = friend_name.lower()
        is_auto = self._auto_join_names.get(name_lower, False)
        
        label = "Disable Auto-Join" if is_auto else "Enable Auto-Join"
        menu.add_command(label=label, command=lambda: self._toggle_auto_join(friend_name))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

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

    def _focus_add_input(self):
        # We don't need to check if it's expanded, because the button is only
        # visible if the list is expanded.
        self.combo_add.entry.focus_set()

    def _render_list(self):
        if not self.winfo_exists(): return
        
        sig = self._get_render_signature()
        if self._last_render_sig == sig:
            return
        self._last_render_sig = sig
        
        for w in self.list_parent.winfo_children():
            w.destroy()
            
        if not self._friends_data:
            lbl = ctk.CTkLabel(self.list_parent, text="Checking friends...", font=get_font("caption"), text_color=get_color("colors.text.muted"))
            lbl.pack(pady=20)
            return

        # Item #157: Hoist root/assets lookup outside the per-friend loop
        root = self.winfo_toplevel()
        assets = getattr(root, "assets", None)

        for item in self._friends_data:
            name = item.get("gameName", "")
            if not name: continue
            
            avail = item.get("availability", "offline")
            status_msg = item.get("availabilityMessage", "Online") if avail != "offline" else "Offline"
            if avail in ("dnd", "away", "chat"):
                if not status_msg: status_msg = avail.capitalize()
                
            row = ctk.CTkFrame(self.list_parent, height=44, fg_color="transparent", cursor="hand2")
            row.pack(fill="x", pady=2)
            row.pack_propagate(False)

            # Hover Feedback
            def on_enter(e, r=row):
                r.configure(fg_color=get_color("colors.state.hover"))
            def on_leave(e, r=row):
                r.configure(fg_color="transparent")

            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

            # Profile Icon
            icon_frame = ctk.CTkFrame(row, fg_color="transparent", width=36, height=36)
            icon_frame.pack(side="left", padx=(8, 4), pady=4)
            icon_frame.pack_propagate(False)
            icon_lbl = ctk.CTkLabel(icon_frame, text="")
            icon_lbl.pack(expand=True, fill="both")
            if assets and hasattr(assets, "get_icon_async"):
                icon_id = str(item.get("icon", 1))
                assets.get_icon_async("profileicon", icon_id, lambda img, l=icon_lbl: l.configure(image=img) if l.winfo_exists() else None, size=(36, 36), widget=icon_lbl)

            # Online Status Dot (Green/Red)
            dot_color = get_color("colors.state.success") if avail != "offline" else get_color("colors.state.error")
            status_dot = ctk.CTkLabel(row, text="●", text_color=dot_color, font=("Arial", 14), cursor="hand2", width=14)
            status_dot.pack(side="left", padx=(2, 4))
            CTkTooltip(status_dot, f"Status: {avail}")

            # Name + Status
            text_frame = ctk.CTkFrame(row, fg_color="transparent", cursor="hand2")
            text_frame.pack(side="left", expand=True, fill="x")

            name_color = get_color("colors.accent.primary") if avail != "offline" else get_color("colors.text.disabled")
            lbl_name = ctk.CTkLabel(
                text_frame, text=name,
                font=get_font("body", "bold"),
                text_color=name_color,
                cursor="hand2"
            )
            lbl_name.pack(anchor="w", pady=(4, 0))

            lbl_sub = ctk.CTkLabel(
                text_frame,
                text=status_msg,
                text_color=get_color("colors.text.muted") if avail != "offline" else get_color("colors.text.disabled"),
                font=get_font("caption"),
                cursor="hand2"
            )
            lbl_sub.pack(anchor="w", pady=(0, 4))

            # Auto-Join Blue Indicator
            name_lower = item.get("_name_lower", name.lower())
            is_auto = self._auto_join_names.get(name_lower, False)
            
            if is_auto:
                auto_join_lbl = ctk.CTkLabel(row, text="⚭", font=("Arial", 20, "bold"), text_color="#00A2FF", cursor="hand2", width=24)
                auto_join_lbl.pack(side="right", padx=(4, 8))
                CTkTooltip(auto_join_lbl, "Auto-Join is Active")
            else:
                auto_join_lbl = ctk.CTkLabel(row, text="⚭", font=("Arial", 20, "bold"), text_color="#4A5568", cursor="hand2", width=24)
                auto_join_lbl.pack(side="right", padx=(4, 8))
                CTkTooltip(auto_join_lbl, "Auto-Join is Inactive (Right-click to toggle)")

            # Bind right click context menu
            def _popup(e, fn=name):
                self._show_context_menu(e, fn)

            row.bind("<Button-3>", _popup)
            text_frame.bind("<Button-3>", _popup)
            lbl_name.bind("<Button-3>", _popup)
            lbl_sub.bind("<Button-3>", _popup)
            status_dot.bind("<Button-3>", _popup)
            icon_lbl.bind("<Button-3>", _popup)
            auto_join_lbl.bind("<Button-3>", _popup)

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
