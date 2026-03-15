import customtkinter as ctk
from ui.theme.token_loader import TOKENS

class StackLayout(ctk.CTkFrame):
    def __init__(self, master, direction="vertical", gap=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.direction = direction
        self.gap = gap if gap is not None else TOKENS.get("spacing.md", 16)

    def add_widget(self, widget, expand=False, fill="x", **pack_kwargs):
        side = "top" if self.direction == "vertical" else "left"
        padx = self.gap // 2 if self.direction == "horizontal" else 0
        pady = self.gap // 2 if self.direction == "vertical" else 0

        # Override pack_kwargs if provided
        final_kwargs = {"side": side, "padx": padx, "pady": pady, "expand": expand, "fill": fill}
        final_kwargs.update(pack_kwargs)

        widget.pack(**final_kwargs)
