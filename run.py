import sys
import os

# Ensure the root project directory is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    from core.main import LeagueLoopApp
    app = LeagueLoopApp()
    app.mainloop()
