import customtkinter as ctk
import time
from ui.components.factory import get_color, get_font, make_button
from ui.ui_shared import CTkTooltip
from core.constants import SPACING_SM, SPACING_MD, SPACING_LG
import keyboard

class AccountSwitcher(ctk.CTkFrame):
    def __init__(self, master, config, on_launch_callback, **kwargs):
        super().__init__(
            master,
            fg_color="transparent",
            **kwargs
        )
        self.config = config
        self.on_launch_callback = on_launch_callback
        self.accounts = self.config.get("accounts", [])

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACING_SM))

        lbl = ctk.CTkLabel(
            header,
            text="Account Switcher",
            font=get_font("body", "bold"),
            text_color=get_color("colors.text.secondary")
        )
        lbl.pack(side="left")

        btn_add = ctk.CTkButton(
            header,
            text="+",
            width=20, height=20,
            corner_radius=10,
            font=("Arial", 12, "bold"),
            fg_color="transparent",
            hover_color=get_color("colors.state.hover"),
            command=self._show_add_modal
        )
        btn_add.pack(side="right")
        CTkTooltip(btn_add, "Add New Account")

        self.list_frame = ctk.CTkFrame(self, fg_color=get_color("colors.background.card"), corner_radius=6)
        self.list_frame.pack(fill="x")

        self._render_accounts()

    def _render_accounts(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        if not self.accounts:
            lbl = ctk.CTkLabel(
                self.list_frame,
                text="No accounts saved.",
                font=get_font("caption"),
                text_color=get_color("colors.text.muted")
            )
            lbl.pack(pady=SPACING_MD)
            return

        for idx, acc in enumerate(self.accounts):
            row = ctk.CTkFrame(self.list_frame, fg_color="transparent", height=32)
            row.pack(fill="x", padx=4, pady=2)
            row.pack_propagate(False)

            btn_launch = ctk.CTkButton(
                row,
                text=acc.get("name", f"Account {idx+1}"),
                font=get_font("body"),
                anchor="w",
                fg_color="transparent",
                text_color=get_color("colors.text.primary"),
                hover_color=get_color("colors.state.hover"),
                command=lambda a=acc: self._launch_account(a)
            )
            btn_launch.pack(side="left", fill="both", expand=True)
            CTkTooltip(btn_launch, "Launch Client with this Account")

            btn_del = ctk.CTkButton(
                row,
                text="✕",
                width=24,
                fg_color="transparent",
                hover_color="#e81123",
                text_color=get_color("colors.text.muted"),
                command=lambda i=idx: self._remove_account(i)
            )
            btn_del.pack(side="right", padx=(2, 0))
            CTkTooltip(btn_del, "Remove Account")

    def _launch_account(self, account):
        # Trigger client launch
        if self.on_launch_callback:
            self.on_launch_callback()

        # Very simple auto-type capability.
        # This is a bit hacky but Riot's architecture prevents direct CLI logins.
        # Wait 8 seconds for Riot Client to appear, then type user -> tab -> pass -> enter
        def auto_type():
            time.sleep(8)
            try:
                username = account.get("username", "")
                password = account.get("password", "")
                if username and password:
                    keyboard.write(username, delay=0.01)
                    time.sleep(0.1)
                    keyboard.send('tab')
                    time.sleep(0.1)
                    keyboard.write(password, delay=0.01)
                    time.sleep(0.1)
                    keyboard.send('enter')
            except Exception as e:
                from utils.logger import Logger
                Logger.error("SYS", f"Auto-type failed: {e}")

        import threading
        threading.Thread(target=auto_type, daemon=True).start()

    def _remove_account(self, idx):
        if 0 <= idx < len(self.accounts):
            self.accounts.pop(idx)
            self.config.set("accounts", self.accounts)
            self._render_accounts()

    def _show_add_modal(self):
        modal = ctk.CTkToplevel(self.winfo_toplevel())
        modal.title("Add Account")
        modal.geometry("300x260")
        modal.attributes("-topmost", True)
        modal.configure(fg_color=get_color("colors.background.app"))
        modal.resizable(False, False)

        # Center the modal
        modal.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - 150
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - 130
        modal.geometry(f"+{x}+{y}")

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=SPACING_LG, pady=SPACING_LG)

        ctk.CTkLabel(container, text="Display Name", font=get_font("caption")).pack(anchor="w")
        ent_name = ctk.CTkEntry(container, height=28, fg_color=get_color("colors.background.card"))
        ent_name.pack(fill="x", pady=(2, SPACING_MD))

        ctk.CTkLabel(container, text="Username", font=get_font("caption")).pack(anchor="w")
        ent_user = ctk.CTkEntry(container, height=28, fg_color=get_color("colors.background.card"))
        ent_user.pack(fill="x", pady=(2, SPACING_MD))

        ctk.CTkLabel(container, text="Password", font=get_font("caption")).pack(anchor="w")
        ent_pass = ctk.CTkEntry(container, height=28, show="*", fg_color=get_color("colors.background.card"))
        ent_pass.pack(fill="x", pady=(2, SPACING_LG))

        def save():
            n = ent_name.get().strip() or "Unnamed Account"
            u = ent_user.get().strip()
            p = ent_pass.get().strip()
            if u and p:
                self.accounts.append({"name": n, "username": u, "password": p})
                self.config.set("accounts", self.accounts)
                self._render_accounts()
            modal.destroy()

        make_button(container, text="Save Account", command=save).pack(fill="x")
