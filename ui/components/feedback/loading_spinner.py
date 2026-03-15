import customtkinter as ctk
from ui.theme.token_loader import TOKENS
from ui.components.factory import get_color

class LoadingSpinner(ctk.CTkProgressBar):
    def __init__(self, master, width=100, height=10, mode="indeterminate", **kwargs):
        progress_color = get_color("colors.accent.primary", default="#0AC8B9")
        fg_color = get_color("colors.background.card", default="#1E2328")

        super().__init__(
            master,
            width=width,
            height=height,
            mode=mode,
            progress_color=progress_color,
            fg_color=fg_color,
            corner_radius=TOKENS.get("radius.sm", 4),
            **kwargs
        )
