import unittest
from unittest.mock import patch, MagicMock
import ssl

from services.stats_scraper import StatsScraper

class TestStatsScraper(unittest.TestCase):

    @patch('threading.Thread.start')
    def setUp(self, _mock_thread_start):
        self.scraper = StatsScraper()

    @patch('urllib.request.urlopen')
    def test_try_metasrc_strategy_1(self, mock_urlopen):
        mock_resp = MagicMock()

        # Simulate > 20 champions to ensure strategy 1 is fully populated
        # The regex pattern looks for '/build/championname" >ChampionName</a>'
        # followed by a percentage between 35.0 and 65.0.
        html_content = ""
        for i in range(25):
            # Using letters to match regex r'/build/([a-z\-]+)'
            name = f"champ{chr(97+i)}"
            html_content += f'<a href="/build/{name}" class="foo">{name.capitalize()}</a>\n'
            # Add some percentages that are ignored (e.g. pick rate, score)
            # and one valid win rate
            html_content += f'<div>99.99%</div> <div>10.00%</div> <div>52.{i:02d}%</div>\n'

        html_content += '<a href="/build/ahri" class="foo">Ahri</a> <div>53.42%</div>\n'

        mock_resp.read.return_value.decode.return_value = html_content
        mock_urlopen.return_value = mock_resp

        ctx = ssl.create_default_context()
        results = self.scraper._try_metasrc(ctx)

        self.assertIn("ahri", results)
        self.assertEqual(results["ahri"], 53.42)
        self.assertIn("champa", results)
        self.assertEqual(results["champa"], 52.00)
        self.assertGreaterEqual(len(results), 20)

    @patch('urllib.request.urlopen')
    def test_try_metasrc_strategy_2(self, mock_urlopen):
        mock_resp = MagicMock()

        # Simulate < 20 champions so Strategy 2 triggers
        # Strategy 2 looks for <tr data-champ="championname"> and then a percentage
        html_content = ""
        for i in range(5):
            name = f"champ{i}"
            html_content += f'<tr data-champ="{name}"><td>55.{i:02d}%</td></tr>\n'

        html_content += '<tr data-champ="ahri"><td>54.32%</td></tr>\n'

        mock_resp.read.return_value.decode.return_value = html_content
        mock_urlopen.return_value = mock_resp

        ctx = ssl.create_default_context()
        results = self.scraper._try_metasrc(ctx)

        self.assertIn("ahri", results)
        self.assertEqual(results["ahri"], 54.32)
        self.assertIn("champ0", results)
        self.assertEqual(results["champ0"], 55.00)

    @patch('threading.Thread.start')
    def test_get_winrate(self, _mock_thread_start):
        # Disable background fetch for clean state
        scraper = StatsScraper()

        # Test normal baseline retrieval
        self.assertEqual(scraper.get_winrate("aatrox"), 49.5)
        self.assertEqual(scraper.get_winrate("ahri"), 52.1)

        # Test string normalization (capitalization, spaces, punctuation)
        self.assertEqual(scraper.get_winrate("Aatrox"), 49.5)
        self.assertEqual(scraper.get_winrate("Kog'Maw"), 54.0)
        self.assertEqual(scraper.get_winrate("Lee Sin"), 49.0)
        self.assertEqual(scraper.get_winrate(" Dr. Mundo "), 53.5)

        # Test fallbacks (baseline is 50.0)
        self.assertEqual(scraper.get_winrate("UnknownChamp"), 50.0)
        self.assertEqual(scraper.get_winrate(""), 50.0)

        # Test with custom fetched data
        scraper.win_rates["testchamp"] = 60.5
        self.assertEqual(scraper.get_winrate("Test Champ"), 60.5)

if __name__ == '__main__':
    unittest.main()
