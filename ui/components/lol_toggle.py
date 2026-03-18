import tkinter as tk
import customtkinter as ctk

class LolToggle(tk.Canvas):
    """Custom Riot-style animated sliding toggle switch using pure Canvas for maximum fidelity."""
    def __init__(self, master, width=32, height=16, variable=None, command=None, bg_color="#0A1428", **kwargs):
        super().__init__(master, width=width, height=height, highlightthickness=0, bg=bg_color, **kwargs)
        self.variable = variable
        self.command = command
        self._state = False
        if self.variable:
            self._state = self.variable.get()

        self.color_inactive = "#1E2328"
        self.color_active = "#A88A4E" # C8AA6E dimmed
        self.color_knob = "#F0E6D2"

        self.pos_off = 2
        self.pos_on = 18 # 32 - 12 - 2
        self._current_x = self.pos_on if self._state else self.pos_off
        
        self.bind("<Button-1>", self.toggle)
        self.bind("<Enter>", lambda e: self.configure(cursor="hand2"))
        self.bind("<Leave>", lambda e: self.configure(cursor=""))
        
        self._draw()

    def _draw(self):
        self.delete("all")
        bg_col = self.color_active if self._state else self.color_inactive
        
        # Track (Pill shape)
        self.create_oval(0, 0, 16, 16, fill=bg_col, outline=bg_col, tags="track")
        self.create_oval(16, 0, 32, 16, fill=bg_col, outline=bg_col, tags="track")
        self.create_rectangle(8, 0, 24, 16, fill=bg_col, outline=bg_col, tags="track")
        
        # Knob
        k_y = 2
        k_s = 12
        x = self._current_x
        self.knob_id = self.create_oval(x, k_y, x+k_s, k_y+k_s, fill=self.color_knob, outline=self.color_knob)

    def toggle(self, event=None):
        self._state = not self._state
        if self.variable:
            self.variable.set(self._state)
            
        if self.command:
            self.command()
            
        self._animate()

    def _animate(self):
        target_x = self.pos_on if self._state else self.pos_off
        
        bg_col = self.color_active if self._state else self.color_inactive
        self.itemconfig("track", fill=bg_col, outline=bg_col)
        
        def step_animation():
            if not self.winfo_exists(): return
            diff = target_x - self._current_x
            
            if abs(diff) < 0.5:
                self._current_x = target_x
                self.coords(self.knob_id, self._current_x, 2, self._current_x + 12, 14)
                return
                
            self._current_x += diff * 0.3
            self.coords(self.knob_id, self._current_x, 2, self._current_x + 12, 14)
            self.after(8, step_animation)
            
        step_animation()

