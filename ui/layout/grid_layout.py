import customtkinter as ctk
from ui.theme.token_loader import TOKENS

class GridLayout(ctk.CTkFrame):
    def __init__(self, master, columns=2, padding=None, gap=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.cols = columns
        pad = padding if padding is not None else TOKENS.get("spacing.md", 16)
        self.gap = gap if gap is not None else TOKENS.get("spacing.sm", 8)

        # Configure columns
        for i in range(self.cols):
            self.grid_columnconfigure(i, weight=1, pad=self.gap)

    def add_widget(self, widget, row, col, **grid_kwargs):
        widget.grid(row=row, column=col, padx=self.gap//2, pady=self.gap//2, **grid_kwargs)
