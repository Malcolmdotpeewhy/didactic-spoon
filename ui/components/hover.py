"""Hover animation utilities."""
from utils.logger import Logger
from .color_utils import lighten_color

def _apply_hover(widget, normal_fg, hover_fg, normal_border, hover_border):
    """Bind hover animation to a widget for brightness transition."""
    def on_enter(_):
        try:
            widget.configure(fg_color=hover_fg, border_color=hover_border)
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("hover.py", f"Handled exception: {e}")

    def on_leave(_):
        try:
            widget.configure(fg_color=normal_fg, border_color=normal_border)
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("hover.py", f"Handled exception: {e}")

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def apply_hover_brightness(widget, normal_color, boost_percent=8):
    """Simple hover brightness boost for any CTk widget with fg_color."""
    hover_color = lighten_color(normal_color, boost_percent)

    def on_enter(_):
        try:
            widget.configure(fg_color=hover_color)
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("hover.py", f"Handled exception: {e}")

    def on_leave(_):
        try:
            widget.configure(fg_color=normal_color)
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("hover.py", f"Handled exception: {e}")

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


def apply_click_animation(widget, normal_color, pulse_color=None, button_num=1):
    """
    🔮 Malcolm's Infusion: Global Click Pulse
    Applies a momentary gamified 'pulse' color flash to a widget upon clicking.
    Provides immediate haptic-like visual feedback that feels highly responsive.
    """
    from .color_utils import lighten_color
    from utils.logger import Logger

    def on_click(_):
        try:
            # Skip if widget is disabled
            if hasattr(widget, "cget") and widget.cget("state") == "disabled":
                return

            # Prevent overlapping animations from corrupting base colors on rapid double-clicks
            if getattr(widget, "_is_pulsing", False):
                return
            widget._is_pulsing = True

            # Stash original colors securely
            if not hasattr(widget, "_orig_pulse_fg"):
                widget._orig_pulse_fg = widget.cget("fg_color")
            if not hasattr(widget, "_orig_pulse_hover"):
                widget._orig_pulse_hover = widget.cget("hover_color")

            orig_fg = widget._orig_pulse_fg
            orig_hover = widget._orig_pulse_hover

            # Generate a bright pulse color
            if pulse_color:
                active_pulse = pulse_color
            elif orig_hover and orig_hover != "transparent":
                # Extract first color if it's a tuple
                hover_base = orig_hover[0] if isinstance(orig_hover, tuple) else orig_hover
                active_pulse = lighten_color(hover_base, 35)
            elif normal_color == "transparent":
                active_pulse = "#C8A45D"
            else:
                active_pulse = lighten_color(normal_color, 35)

            # CustomTkinter renders hover_color when the mouse is over the widget.
            # To show a pulse effect during a click, we must change both fg_color and hover_color.
            widget.configure(fg_color=active_pulse, hover_color=active_pulse)

            # Schedule reversion (feels like a quick satisfying snap)
            def _revert():
                if getattr(widget, "winfo_exists", lambda: False)():
                    widget.configure(fg_color=orig_fg, hover_color=orig_hover)
                    widget._is_pulsing = False

            if getattr(widget, "winfo_exists", lambda: False)():
                widget.after(150, _revert)
        except Exception as e:
            if hasattr(widget, "_is_pulsing"):
                widget._is_pulsing = False
            Logger.error("hover.py", f"Handled exception in click animation: {e}")

    # Add to ButtonPress-1 to align with press logic without removing existing handlers
    widget.bind(f"<ButtonPress-{button_num}>", on_click, add="+")

def apply_press_effect(widget, normal_color, press_color=None):
    """
    Bind press animation (click down/up).
    If press_color is None, it defaults to normal_color (no change) or could be calculated.
    For now, we will perform a slight darken if no press_color is provided.
    """
    from .color_utils import darken_color
    
    active_color = press_color or darken_color(normal_color, 10)

    def on_press(_):
        try:
            widget.configure(fg_color=active_color)
        except Exception as e:
            Logger.error("hover.py", f"Handled exception: {e}")

    def on_release(_):
        try:
            # We assume the mouse is still hovering, so we might want to return to 
            # hover state if possible, but simplest is return to normal and let hover re-trigger
            # or rely on the hover handler to fix it on next move.
            # Ideally, we restore normal, then let hover take over.
            widget.configure(fg_color=normal_color)
            # If the mouse is still inside, the hover handler <Enter> won't trigger again 
            # automatically unless we move. 
            # A robust system would track state. For now, we revert to normal.
        except Exception as e:
            Logger.error("hover.py", f"Handled exception: {e}")

    widget.bind("<ButtonPress-1>", on_press, add="+")
    widget.bind("<ButtonRelease-1>", on_release, add="+")

def apply_card_hover(widget):
    def on_enter(_):
        try:
            from ui.ui_shared import get_color
            widget.configure(border_color=get_color("colors.accent.primary", default="#0AC8B9"))
        except Exception as e:
            from utils.logger import Logger
            Logger.error("hover.py", f"Handled exception: {type(e).__name__}: {e}")

    def on_leave(_):
        try:
            from ui.components.factory import parse_border
            _, border_color = parse_border("subtle")
            widget.configure(border_color=border_color)
        except Exception as e:
            from utils.logger import Logger
            Logger.error("hover.py", f"Handled exception: {type(e).__name__}: {e}")

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")
