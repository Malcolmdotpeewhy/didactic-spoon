import customtkinter as ctk
from ui.theme.token_loader import TOKENS
from ui.components.factory import get_color, get_font, parse_border
from ui.components.hover import apply_hover_brightness, apply_press_effect
from ui.components.tooltip import CTkTooltip

class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, text="", command=None, width=120, height=32, tooltip=None, **kwargs):
        # Pop all non-CTkButton custom kwargs
        kwargs.pop('style', None)
        icon = kwargs.pop('icon', None)
        if icon:
            kwargs['image'] = icon

        # Resolve defaults, allowing kwargs overrides
        border_width_def, border_color_def = parse_border("subtle")
        bg_color = kwargs.pop('fg_color', get_color("buttons.secondary.bg", default="#1E2328"))
        text_color = kwargs.pop('text_color', get_color("colors.text.primary", default="#F0E6D2"))
        hover_color = kwargs.pop('hover_color', get_color("colors.state.hover", default="#1E282D"))
        border_width = kwargs.pop('border_width', border_width_def)
        border_color = kwargs.pop('border_color', border_color_def)
        font = kwargs.pop('font', get_font("body", "medium"))
        corner_radius = kwargs.pop('corner_radius', TOKENS.get("radius.sm", default=4))

        super().__init__(
            master,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color=bg_color,
            hover_color=hover_color,
            text_color=text_color,
            border_width=border_width,
            border_color=border_color,
            font=font,
            corner_radius=corner_radius,
            cursor="hand2",
            **kwargs
        )
        apply_hover_brightness(self, bg_color)
        apply_press_effect(self, bg_color)

        if tooltip:
            self.tooltip = CTkTooltip(self, tooltip)
