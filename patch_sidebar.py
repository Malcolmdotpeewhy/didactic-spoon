import sys
import re

with open("src/ui/app_sidebar.py", "r", encoding="utf-8") as f:
    text = f.read()

# 5.3 Unified Color Palette Integration
# Replace hardcoded hex colors with get_color where appropriate.
text = text.replace('fg_color="#0F1A24"', 'fg_color=get_color("colors.background.panel")')
text = text.replace('"#00C853"', 'get_color("colors.state.success", "#00C853")')
text = text.replace('fg_color="#1F2A36"', 'fg_color=get_color("colors.border.subtle", "#1F2A36")')
text = text.replace('fg_color="#1E2328"', 'fg_color=get_color("colors.border.subtle", "#1E2328")')
text = text.replace('border_color="#F0E6D2"', 'border_color=get_color("colors.accent.primary", "#F0E6D2")')
text = text.replace('text_color="#F0E6D2"', 'text_color=get_color("colors.text.primary", "#F0E6D2")')

# 5.1 Animated Tab Navigation
# We inject a Tab Bar right below self.main_body inside _setup_ui, and pack_forget logic.
tab_injection_target = """        # ── Status & Mode Selection ──
        status_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")"""
tab_injection = """        # ── 5.1 Tab Navigation ──
        self.tab_frame = ctk.CTkFrame(self.main_body, fg_color="transparent", height=30)
        self.tab_frame.pack(fill="x", pady=(0, 10))
        
        self._current_tab = "Play"
        
        def _switch_tab(tab_name):
            self._current_tab = tab_name
            # Update button colors for pseudo-animation
            btn_play.configure(fg_color=get_color("colors.accent.primary") if tab_name == "Play" else "transparent",
                               text_color=get_color("colors.background.app") if tab_name == "Play" else get_color("colors.text.muted"))
            btn_cfg.configure(fg_color=get_color("colors.accent.primary") if tab_name == "Configure" else "transparent",
                              text_color=get_color("colors.background.app") if tab_name == "Configure" else get_color("colors.text.muted"))
            btn_adv.configure(fg_color=get_color("colors.accent.primary") if tab_name == "Advanced" else "transparent",
                              text_color=get_color("colors.background.app") if tab_name == "Advanced" else get_color("colors.text.muted"))
            
            # Hide everything
            status_frame.pack_forget()
            self.session_frame.pack_forget()
            self.action_container.pack_forget()
            self.game_tool_container.pack_forget()
            if self.accounts_tool: self.accounts_tool.pack_forget()
            
            self.auto_container.pack_forget()
            self.friend_list.pack_forget()
            
            self.profile_container.pack_forget()
            self.stats_frame.pack_forget()
            
            # Pack based on tab
            if tab_name == "Play":
                status_frame.pack(fill="x", pady=(0, 8))
                self.session_frame.pack(fill="x", pady=(0, 8))
                self.action_container.pack(fill="x", pady=(0, 8))
                if getattr(self, "_game_tool_visible", False):
                    self.game_tool_container.pack(fill="x", pady=(0, 8))
                if getattr(self, "_accounts_tool_visible", False) and self.accounts_tool:
                    self.accounts_tool.pack(fill="x", pady=(0, 8))
            elif tab_name == "Configure":
                self.auto_container.pack(fill="x", pady=(0, 8))
                self.friend_list.pack(fill="x", pady=(0, 8))
            elif tab_name == "Advanced":
                self.profile_container.pack(fill="x", pady=(0, 8))
                if getattr(self, "_stats_visible", False):
                    self.stats_frame.pack(fill="x", pady=(0, 8))
                    
        self.switch_tab = _switch_tab
        
        btn_play = ctk.CTkButton(self.tab_frame, text="Play", width=60, height=24, fg_color=get_color("colors.accent.primary"), text_color=get_color("colors.background.app"), hover_color=get_color("colors.state.hover"), font=("Arial", 11, "bold"), command=lambda: self.switch_tab("Play"))
        btn_cfg = ctk.CTkButton(self.tab_frame, text="Configure", width=70, height=24, fg_color="transparent", text_color=get_color("colors.text.muted"), hover_color=get_color("colors.state.hover"), font=("Arial", 11, "bold"), command=lambda: self.switch_tab("Configure"))
        btn_adv = ctk.CTkButton(self.tab_frame, text="Advanced", width=70, height=24, fg_color="transparent", text_color=get_color("colors.text.muted"), hover_color=get_color("colors.state.hover"), font=("Arial", 11, "bold"), command=lambda: self.switch_tab("Advanced"))
        
        btn_play.pack(side="left", padx=2)
        btn_cfg.pack(side="left", padx=2)
        btn_adv.pack(side="left", padx=2)

        # ── Status & Mode Selection ──
        status_frame = ctk.CTkFrame(self.main_body, fg_color="transparent")"""
text = text.replace(tab_injection_target, tab_injection)

# 5.4 Form-field validation highlights
validation_target = """    def _on_status_submit(self, event=None):
        if not self.lcu or not self.lcu.is_connected:
            return
        status = self.entry_status.get()
        if not status:
            return"""
validation_replacement = """    def _on_status_submit(self, event=None):
        if not self.lcu or not self.lcu.is_connected:
            self.entry_status.configure(border_color=get_color("colors.state.error", "#E81123"))
            self.after(500, lambda: self.entry_status.configure(border_color=get_color("colors.border.subtle")))
            return
        status = self.entry_status.get()
        if not status:
            return
            
        # 5.4 Form-field validation highlights
        self.entry_status.configure(border_color=get_color("colors.state.success", "#00C853"))
        self.after(1000, lambda: self.entry_status.configure(border_color=get_color("colors.border.subtle")))"""
text = text.replace(validation_target, validation_replacement)

# 5.5 State-driven loading spinners
# We inject logic into _find_match and queue updating to animate the button or show states
spinner_target = """    def _find_match(self):
        if not self.lcu or not self.lcu.is_connected:
            self._log_action("Client not connected.")
            return

        if self._current_game_phase == "Matchmaking":"""
spinner_replacement = """    def _find_match(self):
        # 5.5 State-driven loading spinner
        self.btn_find_match.configure(text="⏳ Processing...")
        self.master.update_idletasks()
        
        if not self.lcu or not self.lcu.is_connected:
            self.btn_find_match.configure(text="▶ Find Match")
            self._log_action("Client not connected.")
            return

        if self._current_game_phase == "Matchmaking":"""
text = text.replace(spinner_target, spinner_replacement)

# Make sure buttons return to normal text if error occurs
spinner_end_target = """        else:
            queue_id = self._get_selected_queue_id()
            if not queue_id:
                self._log_action(f"Failed to resolve queue ID for {self.var_game_mode.get()}")
                return

            self._log_action(f"Matchmaking started for {self.var_game_mode.get()}")
            self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")"""
spinner_end_replacement = """        else:
            queue_id = self._get_selected_queue_id()
            if not queue_id:
                self.btn_find_match.configure(text="▶ Find Match")
                self._log_action(f"Failed to resolve queue ID for {self.var_game_mode.get()}")
                return

            self._log_action(f"Matchmaking started for {self.var_game_mode.get()}")
            self.lcu.request("POST", "/lol-lobby/v2/lobby/matchmaking/search")
            self.after(500, lambda: self.btn_find_match.configure(text="▶ Find Match") if self.winfo_exists() else None)"""
text = text.replace(spinner_end_target, spinner_end_replacement)

# Also need to re-invoke switch_tab dynamically so visibility stays true across game phase updates
update_acct_target = """        if should_show and not self._accounts_tool_visible:
            # Show — pack between friend list and profile section
            if hasattr(self, "profile_container"):
                self.accounts_tool.pack(fill="x", pady=(0, SPACING_MD), padx=0,
                                        before=self.profile_container)
            else:
                self.accounts_tool.pack(fill="x", pady=(0, SPACING_MD), padx=0)
            self._accounts_tool_visible = True
        elif not should_show and self._accounts_tool_visible:
            # Hide
            self.accounts_tool.pack_forget()
            self._accounts_tool_visible = False"""
update_acct_replacement = """        self._accounts_tool_visible = should_show
        if hasattr(self, "switch_tab"):
            self.switch_tab(self._current_tab)"""
text = text.replace(update_acct_target, update_acct_replacement)

# Apply same hook to game tool visibility
update_game_tool_target = """        if hasattr(self, 'game_tool_container'):
            # First, hide all existing tools
            self.arena_tool.pack_forget()
            self.draft_tool.pack_forget()
            self.priority_grid.pack_forget()
            
            self.game_tool_container.pack_forget()"""
update_game_tool_replacement = """        if hasattr(self, 'game_tool_container'):
            # First, hide all existing tools
            self.arena_tool.pack_forget()
            self.draft_tool.pack_forget()
            self.priority_grid.pack_forget()
            
            self.game_tool_container.pack_forget()
            self._game_tool_visible = False"""
text = text.replace(update_game_tool_target, update_game_tool_replacement)

with open("src/ui/app_sidebar.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Modification complete")
