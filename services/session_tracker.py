import time

class SessionTracker:
    def __init__(self):
        self.start_time = None
        self.games_played = 0
        self.last_phase = "None"

    def update_phase(self, current_phase: str) -> dict:
        if self.start_time is None and current_phase == "InProgress":
            self.start_time = time.time()

        if self.last_phase == "InProgress" and current_phase == "EndOfGame":
            self.games_played += 1

        self.last_phase = current_phase

        elapsed_time = 0.0
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time

        return {
            "games_played": self.games_played,
            "time_elapsed": elapsed_time
        }
