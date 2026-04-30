import customtkinter as ctk  # type: ignore
from ui.components.factory import get_color, get_font
from ui.components.lol_toggle import LolToggle  # type: ignore
from ui.ui_shared import CTkTooltip  # type: ignore

class ToggleRow(ctk.CTkFrame):
    """A reusable component for a toggle row with an icon and label."""
    def __init__(self, master, label_text, variable, command, tooltip_text="", icon_item_id=None, assets=None, height=28, **kwargs):
        super().__init__(master, fg_color="transparent", height=height, **kwargs)
        self.pack_propagate(False)
        
        self.icon_label = ctk.CTkLabel(self, text="", width=24)
        self.icon_label.pack(side="left")
        
        if assets and icon_item_id:
            assets.get_icon_async(
                "item", 
                icon_item_id, 
                lambda img, l=self.icon_label: l.configure(image=img) if l.winfo_exists() else None, 
                size=(24, 24), 
                widget=self.icon_label
            )
            
        self.text_label = ctk.CTkLabel(
            self, 
            text=label_text, 
            font=get_font("body"), 
            width=90, 
            anchor="w", 
            text_color=get_color("colors.text.primary", "#F0E6D2")
        )
        self.text_label.pack(side="left", padx=(6, 0))
        
        if tooltip_text:
            CTkTooltip(self.text_label, tooltip_text)
            
        self.toggle = LolToggle(self, variable=variable, command=command)
        self.toggle.pack(side="right")
        
        if tooltip_text:
            CTkTooltip(self.toggle, tooltip_text)
