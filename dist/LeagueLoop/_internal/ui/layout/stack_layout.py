import customtkinter as ctk
from ui.theme.token_loader import TOKENS

class StackLayout(ctk.CTkFrame):
    def __init__(self, master, direction="vertical", gap=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.direction = direction
        self.gap = gap if gap is not None else TOKENS.get("spacing.md", 16)
