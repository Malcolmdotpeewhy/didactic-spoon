from utils.logger import Logger
"""
New UI Component Factory using Design Tokens.
Centralizes the creation of styled widgets (Panels, Cards, Buttons) ensuring visual consistency.
"""
import functools
import customtkinter as ctk
from ..theme.token_loader import TOKENS
from .hover import apply_hover_brightness, apply_press_effect

# ... (omitted)

# --- Token Parsing Helpers ---

@functools.lru_cache(maxsize=256)
def get_color(path, default="#000000"):
    """Retrieve color from tokens."""
    return TOKENS.get(*path.split("."), default=default)

@functools.lru_cache(maxsize=32)
def get_radius(size="md"):
    """Retrieve corner radius."""
    return TOKENS.get("radius", size, default=10)

@functools.lru_cache(maxsize=32)
def get_font(type="body", weight=None):
    """Retrieve font tuple. Weight can be 'bold', 'medium', or 'normal'."""
    if type == "header" or type == "title":
        family = "Cinzel"
        size = 14 if type == "header" else 16
        weight_val = "bold"
    elif type == "caption":
        family = "Inter"
        size = 11
        weight_val = "normal"
    else:
        family = "Inter"
        size = 12
        weight_val = "normal"
    
    if weight:
        weight_val = "normal" if weight == "medium" else weight
        
    return (family, size, weight_val)

@functools.lru_cache(maxsize=32)
def parse_border(token_key):
    """
    Parse a border token like '1px solid #RRGGBB'.
    Returns (width, color).
    """
    val = TOKENS.get("borders", token_key)
    if not val:
        return 0, None
    
    parts = val.split()
    try:
        width = int(parts[0].replace("px", ""))
        color = parts[2]
        if "rgba" in color:
             return width, "#3A4654" 
        return width, color
    except Exception as e:
        Logger.error("factory.py", f"Handled exception: {e}")
        return 0, None

# --- Components ---

class RiotButton(ctk.CTkFrame):
    """Custom button emulating Riot's 2-layer depth with top highlight."""
    def __init__(self, master, text, style="primary", width=120, height=30, command=None, font=None, **kwargs):
        # Extract text styling
        text_color = kwargs.pop("text_color", None)
        
        if style == "primary" or style == "success":
            outer_color = "#C8AA6E"
            inner_color = "#A98A48"
            hover_color = "#C8AA6E" # Brighten on hover
            base_text_color = text_color or "#091428"
        elif style == "ghost" or style == "danger":
            outer_color = "#1E2328" if style == "danger" else "transparent"
            inner_color = "transparent"
            hover_color = "#1C2630" if style == "ghost" else "#4d1111"
            base_text_color = text_color or ("#E74C3C" if style == "danger" else "#F0E6D2")
        else: # secondary
            outer_color = "#1E2328"
            inner_color = "#0A1428"
            hover_color = "#1E2328"
            base_text_color = text_color or "#C8AA6E"

        super().__init__(master, width=width, height=height, fg_color=outer_color, corner_radius=2, **kwargs)
        self.pack_propagate(False)
        self.command = command
        
        padding = 1 if style not in ("ghost",) else 0
        self.inner = ctk.CTkFrame(self, fg_color=inner_color, corner_radius=1)
        self.inner.pack(fill="both", expand=True, padx=padding, pady=padding)
        
        if style == "primary":
            self.highlight = ctk.CTkFrame(self.inner, height=1, fg_color="#D3B679", corner_radius=0)
            self.highlight.pack(fill="x", side="top")
            
        btn_font = font or get_font("body", "bold")
        self.lbl = ctk.CTkLabel(self.inner, text=text, font=btn_font, text_color=base_text_color)
        self.lbl.pack(expand=True)
        
        for w in (self, self.inner, self.lbl):
            w.bind("<Enter>", lambda e: self._on_enter(hover_color))
            w.bind("<Leave>", lambda e: self._on_leave(inner_color))
            w.bind("<Button-1>", self._on_click)
            
        self._inner_color = inner_color
        
    def _on_enter(self, h_color):
        self.configure(cursor="hand2")
        self.inner.configure(fg_color=h_color)
        
    def _on_leave(self, i_color):
        self.configure(cursor="")
        self.inner.configure(fg_color=i_color)
        
    def _on_click(self, e):
        # Optional: Add small press scale if desired
        if self.command:
            self.command()

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.lbl.configure(text=kwargs.pop("text"))
        if "text_color" in kwargs:
            self.lbl.configure(text_color=kwargs.pop("text_color"))
        if "command" in kwargs:
            self.command = kwargs.pop("command")
        if kwargs:
            super().configure(**kwargs)

def make_button(parent, text, style="primary", width=None, command=None, icon=None, **kw):
    """Factory wrapper for new RiotButton."""
    w = kw.pop("width", width or 120)
    h = kw.pop("height", 30)
    if "variant" in kw:
        style = kw.pop("variant")
    return RiotButton(parent, text=text, style=style, width=w, height=h, command=command, **kw)


def make_input(parent, placeholder="", width=None, **kw):
    """
    Create a standardized input field.
    """
    w = kw.pop("width", width or 200)
    font = kw.pop("font", get_font("body"))
    radius = kw.pop("corner_radius", get_radius("sm"))
    height = kw.pop("height", 32)
    
    bg_color = kw.pop("fg_color", get_color("colors.background.app"))
    def_border_w, def_border_c = parse_border("subtle")
    border_w = kw.pop("border_width", def_border_w)
    border_c = kw.pop("border_color", def_border_c)
    
    entry = ctk.CTkEntry(
        parent,
        width=w,
        height=height,
        corner_radius=radius,
        font=font,
        fg_color=bg_color, 
        border_color=border_c,
        border_width=border_w,
        placeholder_text=placeholder,
        placeholder_text_color=get_color("colors.text.muted"),
        text_color=get_color("colors.text.primary"),
        **kw
    )

    # ⚡ Bolt: Precompute static colors for focus handlers to avoid main thread latency
    # during high-frequency focus events.
    _focus_border = get_color("colors.accent.blue")
    _focus_bg = get_color("colors.background.card")
    _unfocus_border = border_c
    _unfocus_bg = bg_color

    def _on_focus(e):
        entry.configure(
            border_color=_focus_border,
            fg_color=_focus_bg
        )

    def _on_unfocus(e):
        entry.configure(
            border_color=_unfocus_border,
            fg_color=_unfocus_bg
        )

    entry.bind("<FocusIn>", _on_focus, add="+")
    entry.bind("<FocusOut>", _on_unfocus, add="+")

    return entry








