import unittest
from unittest.mock import patch
from services.session_tracker import SessionTracker

class TestSessionTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = SessionTracker()

    @patch('time.time', return_value=100)
    def test_start_time_initialized_on_first_in_progress(self, mock_time):
        self.assertIsNone(self.tracker.start_time)
        res = self.tracker.update_phase("InProgress")
        self.assertEqual(self.tracker.start_time, 100)
        self.assertEqual(res["games_played"], 0)
        self.assertEqual(res["time_elapsed"], 0.0)

    @patch('time.time')
    def test_start_time_not_overwritten(self, mock_time):
        mock_time.return_value = 100
        self.tracker.update_phase("InProgress")
        self.assertEqual(self.tracker.start_time, 100)

        mock_time.return_value = 200
        self.tracker.update_phase("InProgress")
        self.assertEqual(self.tracker.start_time, 100)

    @patch('time.time', return_value=150)
    def test_games_played_incremented_on_end_of_game(self, mock_time):
        # Set up an active game state
        self.tracker.start_time = 100
        self.tracker.last_phase = "InProgress"

        # Transition to EndOfGame
        res = self.tracker.update_phase("EndOfGame")

        self.assertEqual(self.tracker.games_played, 1)
        self.assertEqual(res["games_played"], 1)
        self.assertEqual(res["time_elapsed"], 50.0)

    def test_games_played_not_incremented_on_other_transitions(self):
        self.tracker.last_phase = "Lobby"
        self.tracker.update_phase("EndOfGame")
        self.assertEqual(self.tracker.games_played, 0)

        self.tracker.last_phase = "InProgress"
        self.tracker.update_phase("Lobby")
        self.assertEqual(self.tracker.games_played, 0)

if __name__ == '__main__':
    unittest.main()
