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

    def test_is_offline(self):
        # Test all combinations of _fetched and _fetching
        cases = [
            (False, False, True),
            (False, True, False),
            (True, False, False),
            (True, True, False)
        ]

        for fetched, fetching, expected in cases:
            with self.subTest(fetched=fetched, fetching=fetching):
                self.scraper._fetched = fetched
                self.scraper._fetching = fetching
                self.assertEqual(self.scraper.is_offline, expected)

if __name__ == '__main__':
    unittest.main()
