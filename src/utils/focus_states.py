"""
Keyboard Focus State System
────────────────────────────
Adds visible focus indicators for keyboard navigation.
Applies a colored ring to focused interactive elements.
"""

import customtkinter as ctk
from ui.components.factory import get_color


# Focus ring color
_FOCUS_COLOR = None  # Lazy-loaded


def _get_focus_color():
    global _FOCUS_COLOR
    if _FOCUS_COLOR is None:
        _FOCUS_COLOR = get_color("colors.accent.gold", "#C8AA6E")
    return _FOCUS_COLOR


def apply_focus_ring(widget, color=None, width=2):
    """
    Add visible focus ring to a CTkButton or CTkFrame widget.
    When the widget gains keyboard focus, a border highlight appears.
    When it loses focus, the original border is restored.

    Parameters
    ----------
    widget : ctk widget
        The widget to enhance.
    color : str or None
        Focus ring color. Defaults to accent gold.
    width : int
        Border width for the focus ring.
    """
    focus_color = color or _get_focus_color()

    # Store original border state
    orig_border_width = getattr(widget, "_orig_border_width", None)
    orig_border_color = getattr(widget, "_orig_border_color", None)

    if orig_border_width is None:
        try:
            orig_border_width = widget.cget("border_width") or 0
            orig_border_color = widget.cget("border_color") or "transparent"
        except Exception:
            orig_border_width = 0
            orig_border_color = "transparent"

    widget._orig_border_width = orig_border_width
    widget._orig_border_color = orig_border_color

    def _on_focus_in(event):
        try:
            widget.configure(border_width=width, border_color=focus_color)
        except Exception:
            pass

    def _on_focus_out(event):
        try:
            widget.configure(
                border_width=widget._orig_border_width,
                border_color=widget._orig_border_color
            )
        except Exception:
            pass

    widget.bind("<FocusIn>", _on_focus_in, add="+")
    widget.bind("<FocusOut>", _on_focus_out, add="+")

    # Make the widget focusable via Tab
    try:
        widget.configure(takefocus=True)
    except Exception:
        pass


def apply_focus_states_recursive(container, skip_types=None):
    """
    Walk a container's widget tree and apply focus rings to all
    interactive elements (buttons, switches, entries, etc.).

    Parameters
    ----------
    container : ctk widget
        The root container to walk.
    skip_types : set or None
        Widget types to skip.
    """
    skip = skip_types or set()

    interactive_types = (
        ctk.CTkButton,
        ctk.CTkSwitch,
        ctk.CTkCheckBox,
        ctk.CTkEntry,
        ctk.CTkOptionMenu,
        ctk.CTkComboBox,
    )

    def _walk(widget):
        if isinstance(widget, interactive_types) and type(widget).__name__ not in skip:
            apply_focus_ring(widget)
        for child in widget.winfo_children():
            _walk(child)

    _walk(container)
