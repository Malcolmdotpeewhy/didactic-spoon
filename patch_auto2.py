import sys

with open("src/services/automation.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace _handle_ready_check
ready_target = """    def _handle_ready_check(self, phase):
        if phase != "ReadyCheck":
            self.ready_check_start = None
            self.ready_check_delay = None
            self.ready_check_accepted = False
            self._last_countdown_log = None
            return

        if not self.config.get("auto_accept"): return
        if self.ready_check_accepted: return

        if self.ready_check_start is None:
            self.ready_check_start = time.time()
            base_delay = self.config.get("accept_delay", 2.0)
            self.ready_check_delay = base_delay + random.uniform(0.0, 1.5) if base_delay > 0 else 0.0
            return

        target_delay = self.ready_check_delay if self.ready_check_delay is not None else 2.0
        
        if self.ready_check_start is None:
            return
            
        elapsed = time.time() - self.ready_check_start  # type: ignore

        if elapsed >= target_delay:  # type: ignore
            self.lcu.request("POST", "/lol-matchmaking/v1/ready-check/accept")
            self.ready_check_accepted = True
            self._log("Ready Check Accepted!")"""
            
ready_replacement = """    def _handle_ready_check(self, phase):
        if phase != "ReadyCheck":
            if getattr(self, "_accept_timer", None):
                self._accept_timer.cancel()
                self._accept_timer = None
            self.ready_check_start = None
            self.ready_check_delay = None
            self.ready_check_accepted = False
            self._last_countdown_log = None
            return

        if not self.config.get("auto_accept"): return
        if getattr(self, "_accept_timer", None) or self.ready_check_accepted: return

        self.ready_check_start = time.time()
        base_delay = self.config.get("accept_delay", 2.0)
        delay = base_delay + random.uniform(0.0, 1.5) if base_delay > 0 else 0.0
        self.ready_check_delay = delay
        
        def _do_accept():
            self.lcu.request("POST", "/lol-matchmaking/v1/ready-check/accept")
            self.ready_check_accepted = True
            self._log("Ready Check Accepted!")
            
        self._accept_timer = threading.Timer(delay, _do_accept)
        self._accept_timer.daemon = True
        self._accept_timer.start()"""

if ready_target in content:
    content = content.replace(ready_target, ready_replacement)
else:
    print("Ready target not found")

with open("src/services/automation.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Modification complete")
