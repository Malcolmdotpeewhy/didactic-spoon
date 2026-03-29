"""
🔮 Malcolm's Infusion: Omnibar (Command Palette)
A frictionless, keyboard-first command palette triggered by Ctrl+K.
Allows quick navigation, toggling settings, and executing actions without touching the mouse.

UX Rationale:
- Power users need a fast way to jump between views or trigger actions (like 'Clear Cache' or 'Launch Client')
  without hunting through menus.
- The Omnibar provides instant, predictive search across all app capabilities.

Accessibility:
- Fully keyboard-navigable (Up/Down, Enter to execute, Escape to dismiss).
"""
import customtkinter as ctk
from .factory import get_color, get_font, get_radius, parse_border, TOKENS, make_input
from ui.components.toast import ToastManager


class Omnibar(ctk.CTkFrame):
    """
    A floating command palette overlay.
    """

    def __init__(self, parent, command_provider):
        """
        Args:
            parent: The parent CTk widget (usually the root or content_area).
            command_provider: A callable that returns a list of dicts:
                              [{"title": "...", "subtitle": "...", "icon": "...", "action": func}, ...]
        """
        super().__init__(
            parent,
            fg_color=get_color("colors.background.panel"),
            corner_radius=get_radius("lg"),
            border_width=1,
            border_color=get_color("colors.accent.gold"),
        )
        self.command_provider = command_provider
        self._visible = False

        # State
        self._all_commands = ()
        self._filtered_commands = []
        self._selected_index = 0
        self._result_widgets = []

        # ⚡ Bolt: Precompute standard theme colors to avoid dynamic token resolution
        # overhead during high-frequency list navigation (_on_up, _on_down).
        self._color_bg_selected = get_color("colors.accent.primary")
        self._color_text_selected = get_color("colors.background.app")
        self._color_sub_selected = get_color("colors.background.card")
        self._color_text_normal = get_color("colors.text.primary")
        self._color_sub_normal = get_color("colors.text.muted")
        self._animation_id = None
        self._current_rely = 0.0

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        """Construct the Omnibar layout."""
        # ── Search Input ──
        input_container = ctk.CTkFrame(self, fg_color="transparent")
        input_container.pack(fill="x", padx=TOKENS.get("spacing.md", 12), pady=(TOKENS.get("spacing.md", 12), TOKENS.get("spacing.sm", 8)))

        self.search_input = make_input(
            input_container,
            placeholder="Search commands... (e.g. 'Launch', 'Dashboard')",
            width=500,
            height=40,
            font=get_font("title", "medium"),
            fg_color=get_color("colors.background.card"),
        )
        self.search_input.pack(fill="x", expand=True)

        # ── Divider ──
        ctk.CTkFrame(
            self, height=1, fg_color=parse_border("subtle")[1],
        ).pack(fill="x")

        # ── Results Area ──
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            height=300,
            scrollbar_button_color="#1E2328",
            scrollbar_button_hover_color="#3A4654",
        )
        self.results_frame.pack(fill="both", expand=True, padx=TOKENS.get("spacing.xs", 4), pady=TOKENS.get("spacing.sm", 8))

    def _bind_events(self):
        self.search_input.bind("<KeyRelease>", self._on_search)
        self.search_input.bind("<Down>", self._on_down)
        self.search_input.bind("<Up>", self._on_up)
        self.search_input.bind("<Return>", self._on_enter)
        self.search_input.bind("<Escape>", lambda e: self.hide())

    # --- Visibility ---

    def show(self):
        """Display the Omnibar with a slide-in animation."""
        if self._visible:
            return
        self._visible = True

        # Refresh commands on open
        self._all_commands = tuple(self.command_provider())
        self.search_input.delete(0, "end")
        self._filter_results("")

        if self._animation_id:
            self.after_cancel(self._animation_id)
            
        self._current_rely = 0.20
        self.place(relx=0.5, rely=self._current_rely, anchor="center")
        self.lift()
        self.after(10, self.search_input.focus_set)
        
        self._animate(target_rely=0.30, step=0.015)

    def hide(self):
        """Dismiss the Omnibar with a slide-out animation."""
        if not self._visible:
            return
        self._visible = False
        
        if self._animation_id:
            self.after_cancel(self._animation_id)
            
        self._animate(target_rely=0.20, step=-0.02, on_complete=self.place_forget)

    def _animate(self, target_rely, step, on_complete=None):
        """Internal animator for rely property."""
        if (step > 0 and self._current_rely >= target_rely) or (step < 0 and self._current_rely <= target_rely):
            self._current_rely = target_rely
            self.place(relx=0.5, rely=self._current_rely, anchor="center")
            if on_complete:
                on_complete()
            return
            
        self._current_rely += step
        
        # Add friction mapping for ease-out effect
        distance = abs(target_rely - self._current_rely)
        adjusted_step = max(0.002, abs(step) * (distance * 10)) if step > 0 else step
        if step > 0: step = adjusted_step

        self.place(relx=0.5, rely=self._current_rely, anchor="center")
        self._animation_id = self.after(16, lambda: self._animate(target_rely, step, on_complete))

    # --- Logic ---

    def _on_search(self, event):
        # Ignore navigation keys
        if event.keysym in ("Up", "Down", "Return", "Escape"):
            return
        query = self.search_input.get().strip().lower()
        self._filter_results(query)

    def _filter_results(self, query):
        if not query:
            self._filtered_commands = list(self._all_commands)
        else:
            # Simple fuzzy/substring search
            exact_matches = []
            other_matches = []

            for cmd in self._all_commands:
                # ⚡ Bolt: Fast-path by caching normalized title and subtitle per command to avoid
                # redundant .lower() calls and string concatenations on every keystroke loop.
                if "_search_target" not in cmd:
                    title = cmd.get("title", "")
                    cmd["_title_lower"] = title.lower()
                    cmd["_search_target"] = f"{title} {cmd.get('subtitle', '')}".lower()

                if query in cmd["_search_target"]:
                    if cmd["_title_lower"].startswith(query):
                        exact_matches.append(cmd)
                    else:
                        other_matches.append(cmd)

            self._filtered_commands = exact_matches + other_matches

        self._selected_index = 0
        self._render_results()

    def _render_results(self):
        # Clear old
        for w in self._result_widgets:
            w.destroy()
        self._result_widgets.clear()

        if not self._filtered_commands:
            lbl = ctk.CTkLabel(
                self.results_frame,
                text="No commands found.",
                text_color=get_color("colors.text.muted"),
                font=get_font("body")
            )
            lbl.pack(pady=TOKENS.get("spacing.xl", 24))
            self._result_widgets.append(lbl)
            return

        for i, cmd in enumerate(self._filtered_commands):
            is_selected = (i == self._selected_index)

            bg_color = self._color_bg_selected if is_selected else "transparent"
            text_color = self._color_text_selected if is_selected else self._color_text_normal
            sub_color = self._color_sub_selected if is_selected else self._color_sub_normal

            row = ctk.CTkFrame(
                self.results_frame,
                fg_color=bg_color,
                corner_radius=get_radius("sm"),
                height=48
            )
            row.pack(fill="x", padx=TOKENS.get("spacing.sm", 8), pady=2)
            row.pack_propagate(False)

            # Icon
            ctk.CTkLabel(
                row,
                text=cmd.get("icon", "⚡"),
                font=get_font("body"),
                text_color=text_color,
                width=30
            ).pack(side="left", padx=(TOKENS.get("spacing.sm", 8), TOKENS.get("spacing.xs", 4)))

            # Text Container
            text_cont = ctk.CTkFrame(row, fg_color="transparent")
            text_cont.pack(side="left", fill="both", expand=True)

            ctk.CTkLabel(
                text_cont,
                text=cmd.get("title", ""),
                font=get_font("body", "bold"),
                text_color=text_color,
                anchor="w"
            ).pack(fill="x", side="top", pady=(4, 0))

            if cmd.get("subtitle"):
                ctk.CTkLabel(
                    text_cont,
                    text=cmd.get("subtitle", ""),
                    font=get_font("caption"),
                    text_color=sub_color,
                    anchor="w"
                ).pack(fill="x", side="top")

            # Click binding
            def make_cmd(idx):
                return lambda e: self._execute_command(idx)

            row.bind("<Button-1>", make_cmd(i))
            for child in row.winfo_children():
                child.bind("<Button-1>", make_cmd(i))
                if isinstance(child, ctk.CTkFrame):
                    for grandchild in child.winfo_children():
                        grandchild.bind("<Button-1>", make_cmd(i))

            self._result_widgets.append(row)

    def _update_selection_visuals(self, old_index=None):
        """Update the visual state of the existing result widgets and ensure visibility."""
        if not self._result_widgets or not self._filtered_commands:
            return

        def _update_row(i):
            if i < 0 or i >= len(self._result_widgets):
                return
            row = self._result_widgets[i]
            # Skip the "No commands found" label if that's what's rendering
            if isinstance(row, ctk.CTkLabel):
                return

            is_selected = (i == self._selected_index)

            bg_color = self._color_bg_selected if is_selected else "transparent"
            text_color = self._color_text_selected if is_selected else self._color_text_normal
            sub_color = self._color_sub_selected if is_selected else self._color_sub_normal

            # 1. Update row background
            row.configure(fg_color=bg_color)

            # 2. Update children (Icon, text container, labels)
            children = row.winfo_children()
            if len(children) >= 2:
                # Icon is first child
                children[0].configure(text_color=text_color)

                # Text container is second child
                text_cont = children[1]
                text_children = text_cont.winfo_children()
                if len(text_children) >= 1:
                    text_children[0].configure(text_color=text_color) # Title
                if len(text_children) >= 2:
                    text_children[1].configure(text_color=sub_color)  # Subtitle

        # ⚡ Bolt: Fast-path O(1) visual updates during keyboard navigation
        if old_index is not None:
            _update_row(old_index)
            _update_row(self._selected_index)
        else:
            for i in range(len(self._result_widgets)):
                _update_row(i)

        # Ensure the selected item is visible by manipulating the canvas yview
        if hasattr(self.results_frame, "_parent_canvas"):
            canvas = self.results_frame._parent_canvas
            # ⚡ Bolt: Prevent synchronous layout calculation overhead during high-frequency
            # scrolling. Only force an update if rendering from scratch.
            if old_index is None:
                canvas.update_idletasks()

            # A row is height=48 + pady=2 (top+bottom) = ~52px total per row
            # Results frame height is 300px
            row_h = 52.0
            visible_rows = 300.0 / row_h
            total_rows = len(self._filtered_commands)

            if total_rows > visible_rows:
                # Calculate scroll fraction (0.0 to 1.0)
                # If we are near the top, scroll to 0
                if self._selected_index <= 1:
                    canvas.yview_moveto(0.0)
                # If we are near the bottom, scroll to 1
                elif self._selected_index >= total_rows - 2:
                    canvas.yview_moveto(1.0)
                else:
                    # Try to center the item
                    fraction = (self._selected_index - (visible_rows / 2.0)) / total_rows
                    canvas.yview_moveto(max(0.0, min(1.0, fraction)))

    def _on_down(self, event):
        if self._filtered_commands:
            old_index = self._selected_index
            self._selected_index = (self._selected_index + 1) % len(self._filtered_commands)
            self._update_selection_visuals(old_index)
        return "break"

    def _on_up(self, event):
        if self._filtered_commands:
            old_index = self._selected_index
            self._selected_index = (self._selected_index - 1) % len(self._filtered_commands)
            self._update_selection_visuals(old_index)
        return "break"

    def _on_enter(self, event):
        self._execute_command(self._selected_index)
        return "break"

    def _execute_command(self, index):
        if 0 <= index < len(self._filtered_commands):
            cmd = self._filtered_commands[index]
            action = cmd.get("action")
            if action:
                # Malcolm's Infusion: Pre-execution micro-animation and contextual feedback

                # 1. Show global success toast
                title = cmd.get("title", "Command")
                try:
                    ToastManager.get_instance(self.winfo_toplevel()).show(
                        message=f"Executed: {title}",
                        icon="✨",
                        theme="success",
                        duration=2000
                    )
                except Exception as e:
                    pass

                # 2. Pulse the selected row before hiding
                row_widget = None
                # Skip the "No commands found" label if it somehow got triggered
                for i, w in enumerate(self._result_widgets):
                    if not isinstance(w, ctk.CTkLabel) and i == index:
                        row_widget = w
                        break

                if row_widget and row_widget.winfo_exists():
                    orig_color = row_widget.cget("fg_color")
                    pulse_color = get_color("colors.accent.gold", "#C8AA6E")
                    row_widget.configure(fg_color=pulse_color)

                    def finish_execution():
                        if row_widget.winfo_exists():
                            row_widget.configure(fg_color=orig_color)
                        self.hide()
                        self.after(50, action)

                    self.after(80, finish_execution)
                else:
                    self.hide()
                    self.after(50, action)
