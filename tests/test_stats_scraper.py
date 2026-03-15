import unittest
from unittest.mock import patch
from services.stats_scraper import StatsScraper

class TestStatsScraper(unittest.TestCase):

    @patch('services.stats_scraper.StatsScraper._fetch_stats')
    def setUp(self, mock_fetch):
        # Patching _fetch_stats prevents actual network requests during testing
        self.scraper = StatsScraper()

    def test_get_winrate_known_champion(self):
        # Aatrox is in BASELINE_ARAM_WINRATES as 49.5
        self.assertEqual(self.scraper.get_winrate("aatrox"), 49.5)

    def test_get_winrate_unknown_champion(self):
        self.assertEqual(self.scraper.get_winrate("UnknownChamp"), 50.0)

    def test_get_winrate_with_spaces(self):
        # Miss Fortune is "missfortune": 53.2
        self.assertEqual(self.scraper.get_winrate("Miss Fortune"), 53.2)
        # Aurelion Sol is "aurelionsol": 51.5
        self.assertEqual(self.scraper.get_winrate("Aurelion Sol"), 51.5)

    def test_get_winrate_with_apostrophes(self):
        # Kha'Zix is "khazix": 50.3
        self.assertEqual(self.scraper.get_winrate("Kha'Zix"), 50.3)
        # Rek'Sai is "reksai": 48.5
        self.assertEqual(self.scraper.get_winrate("Rek'Sai"), 48.5)

    def test_get_winrate_with_dots(self):
        # Dr. Mundo is "drmundo": 53.5
        self.assertEqual(self.scraper.get_winrate("Dr. Mundo"), 53.5)

    def test_get_winrate_case_insensitivity(self):
        # Ahri is "ahri": 52.1
        self.assertEqual(self.scraper.get_winrate("aHrI"), 52.1)
        self.assertEqual(self.scraper.get_winrate("AATROX"), 49.5)

if __name__ == '__main__':
    unittest.main()
