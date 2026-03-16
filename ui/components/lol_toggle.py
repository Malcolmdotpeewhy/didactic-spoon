import customtkinter as ctk

class LolToggle(ctk.CTkFrame):
    """Custom Riot-style animated sliding toggle switch."""
    def __init__(self, master, width=36, height=18,
                 fg_color="#1E2328", progress_color="#C8AA6E", knob_color="#F0E6D2",
                 variable=None, command=None, **kwargs):
        super().__init__(master, width=width, height=height, fg_color=fg_color, corner_radius=height//2, **kwargs)
        self.pack_propagate(False)

        self._variable = variable
        self._command = command
        self._state = False

        self._width = width
        self._height = height
        self._fg_color = fg_color
        self._progress_color = progress_color
        self._knob_color = knob_color

        if self._variable:
            self._state = self._variable.get()

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        # Draw the knob
        knob_size = self._height - 4
        self.knob = ctk.CTkFrame(self, width=knob_size, height=knob_size, 
                                 corner_radius=knob_size//2, fg_color=self._knob_color, bg_color="transparent")
        
        # Position logic
        self.pos_off = 2
        self.pos_on = self._width - knob_size - 2
        self._current_x = self.pos_on if self._state else self.pos_off
        
        self.knob.place(x=self._current_x, rely=0.5, anchor="w")
        self.configure(fg_color=self._progress_color if self._state else self._fg_color)

    def _bind_events(self):
        self.bind("<Button-1>", self.toggle)
        self.knob.bind("<Button-1>", self.toggle)
        
        def _on_enter(e):
            self.configure(cursor="hand2")
        def _on_leave(e):
            self.configure(cursor="")
            
        self.bind("<Enter>", _on_enter)
        self.bind("<Leave>", _on_leave)
        self.knob.bind("<Enter>", _on_enter)
        self.knob.bind("<Leave>", _on_leave)

    def toggle(self, event=None):
        self._state = not self._state
        if self._variable:
            self._variable.set(self._state)
            
        self._animate()
        
        if self._command:
            self._command()

    def _animate(self):
        target_x = self.pos_on if self._state else self.pos_off
        steps = 6
        step_time = 120 // steps # 120ms total duration
        
        start_x = self._current_x
        diff = target_x - start_x
        step_val = diff / steps
        
        def _anim_step(current_step):
            if not self.winfo_exists(): return
            if current_step >= steps:
                self._current_x = target_x
                self.knob.place(x=self._current_x, rely=0.5, anchor="w")
                self.configure(fg_color=self._progress_color if self._state else self._fg_color)
                return
            
            self._current_x = start_x + (step_val * current_step)
            self.knob.place(x=self._current_x, rely=0.5, anchor="w")
            self.after(step_time, _anim_step, current_step + 1)
            
        _anim_step(1)
