import urllib.request
import json
import re
import threading
import socket
import ssl
from utils.logger import Logger

# Baseline ARAM win rates (approximate, sourced from public tier lists).
# The scraper will attempt to refresh these at startup from lolalytics.
# If the fetch fails, these serve as the fallback for the whole session.
BASELINE_ARAM_WINRATES = {
    "aatrox": 49.5, "ahri": 52.1, "akali": 49.0, "akshan": 52.8, "alistar": 50.5,
    "amumu": 53.2, "anivia": 51.8, "annie": 50.9, "aphelios": 47.8, "ashe": 52.4,
    "aurelionsol": 51.5, "azir": 46.5, "bard": 50.2, "belveth": 48.0, "blitzcrank": 51.6,
    "brand": 53.0, "braum": 49.0, "briar": 49.8, "caitlyn": 50.3, "camille": 48.5,
    "cassiopeia": 50.6, "chogath": 52.0, "corki": 49.2, "darius": 50.8, "diana": 52.5,
    "draven": 49.4, "drmundo": 53.5, "ekko": 50.0, "elise": 48.3, "evelynn": 47.5,
    "ezreal": 49.8, "fiddlesticks": 52.8, "fiora": 47.6, "fizz": 50.2, "galio": 52.3,
    "gangplank": 49.0, "garen": 52.1, "gnar": 49.5, "gragas": 51.2, "graves": 49.8,
    "gwen": 48.7, "hecarim": 51.0, "heimerdinger": 52.5, "illaoi": 52.8, "irelia": 48.5,
    "ivern": 48.0, "janna": 51.5, "jarvaniv": 50.8, "jax": 50.5, "jayce": 50.0,
    "jhin": 51.2, "jinx": 52.0, "kaisa": 50.5, "kalista": 48.2, "karma": 51.0,
    "karthus": 54.5, "kassadin": 49.8, "katarina": 50.5, "kayle": 51.8, "kayn": 48.5,
    "kennen": 50.0, "khazix": 50.3, "kindred": 49.2, "kled": 50.5, "kogmaw": 54.0,
    "ksante": 47.5, "leblanc": 48.5, "leesin": 49.0, "leona": 51.5, "lillia": 51.0,
    "lissandra": 51.8, "lucian": 50.0, "lulu": 52.0, "lux": 53.0, "malphite": 52.5,
    "malzahar": 52.0, "maokai": 54.0, "masteryi": 50.5, "milio": 52.5, "missfortune": 53.2,
    "mordekaiser": 50.8, "morgana": 52.0, "nami": 52.8, "nasus": 51.5, "nautilus": 50.5,
    "neeko": 52.0, "nidalee": 49.0, "nilah": 51.0, "nocturne": 50.0, "nunu": 49.5,
    "olaf": 50.0, "orianna": 51.5, "ornn": 50.2, "pantheon": 49.8, "poppy": 51.0,
    "pyke": 49.5, "qiyana": 47.0, "quinn": 50.8, "rakan": 49.5, "rammus": 50.0,
    "reksai": 48.5, "rell": 49.0, "renata": 51.5, "renekton": 49.5, "rengar": 48.0,
    "riven": 48.5, "rumble": 52.0, "ryze": 47.0, "samira": 50.5, "sejuani": 51.5,
    "senna": 52.5, "seraphine": 54.0, "sett": 51.0, "shaco": 48.5, "shen": 50.5,
    "shyvana": 51.0, "singed": 50.5, "sion": 53.5, "sivir": 52.0, "skarner": 50.0,
    "smolder": 50.8, "sona": 55.0, "soraka": 53.5, "swain": 53.8, "sylas": 50.0,
    "syndra": 49.5, "tahmkench": 51.0, "taliyah": 50.5, "talon": 49.0, "taric": 52.0,
    "teemo": 53.0, "thresh": 49.5, "tristana": 50.5, "trundle": 51.5, "tryndamere": 49.0,
    "twistedfate": 49.5, "twitch": 51.0, "udyr": 49.5, "urgot": 51.5, "varus": 52.0,
    "vayne": 49.0, "veigar": 54.0, "velkoz": 53.5, "vex": 51.5, "vi": 50.5,
    "viego": 49.5, "viktor": 50.5, "vladimir": 49.8, "volibear": 51.0, "warwick": 51.5,
    "wukong": 50.5, "xayah": 49.5, "xerath": 53.0, "xinzhao": 50.0, "yasuo": 49.0,
    "yone": 49.5, "yorick": 51.5, "yuumi": 48.0, "zac": 52.5, "zed": 48.0,
    "zeri": 47.0, "ziggs": 54.5, "zilean": 53.0, "zoe": 50.0, "zyra": 53.5,
    "aurora": 51.0, "hwei": 50.0, "naafiri": 49.0,
}


class StatsScraper:
    """Fetches ARAM win rates once at startup. Falls back to baseline data on failure."""

    def __init__(self, mode="ARAM"):
        self.mode = mode
        self.win_rates = dict(BASELINE_ARAM_WINRATES)  # Start with known data
        self._fetching = False
        self._fetched = False
        self._fetch_thread = threading.Thread(target=self._fetch_stats, daemon=True)
        self._fetch_thread.start()

    def set_mode(self, mode):
        """Switch between ARAM / ARAM Mayhem. Re-fetches if mode actually changes."""
        if self.mode != mode:
            self.mode = mode
            # Reset to baseline and attempt re-fetch for the new mode
            self.win_rates = dict(BASELINE_ARAM_WINRATES)
            self._fetched = False
            self._try_fetch()

    def _try_fetch(self):
        if self._fetching:
            return
        self._fetching = True
        threading.Thread(target=self._fetch_stats, daemon=True).start()

    def _fetch_stats(self):
        """Try multiple sources. On any success, overwrite baseline. On failure, keep baseline."""
        try:
            socket.setdefaulttimeout(12)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            sources = [
                self._try_lolalytics,
                self._try_metasrc,
            ]
            for source_fn in sources:
                try:
                    results = source_fn(ctx)
                    if results and len(results) > 20:
                        self.win_rates.update(results)
                        self._fetched = True
                        Logger.info("Stats", f"Scraped {len(results)} {self.mode} win rates from {source_fn.__name__}.")
                        return
                except Exception as e:
                    Logger.debug("Stats", f"{source_fn.__name__} failed: {e}")
                    continue

            # All sources failed — baseline data is already loaded
            Logger.warning("Stats", f"All stat sources failed for {self.mode}. Using baseline win rates.")

        except Exception as e:
            Logger.error("Stats", f"Critical stats error: {e}")
        finally:
            self._fetching = False

    def _try_lolalytics(self, ctx):
        """Attempt to scrape lolalytics tier list page."""
        url = "https://lolalytics.com/lol/tierlist/?lane=aram"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
        })
        resp = urllib.request.urlopen(req, timeout=12, context=ctx)
        html = resp.read().decode("utf-8", errors="ignore")

        results = {}
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if script_tag and script_tag.string:
                nd = json.loads(script_tag.string)
                # Navigate the nested structure
                props = nd.get("props", {}).get("pageProps", {})
                champs = props.get("data", props.get("champions", {}))
                if isinstance(champs, dict):
                    for cdata in champs.values():
                        if type(cdata) is dict:
                            try:
                                name = cdata["name"]
                                wr = cdata["wr"]
                            except KeyError:
                                name = cdata.get("name", "")
                                wr = cdata.get("wr") or cdata.get("winRate")

                            if wr and name:
                                clean = name.replace("'", "").replace(" ", "").replace(".", "").lower()
                                results[clean] = float(wr)
        except Exception as e:
            Logger.debug("Stats", f"BS4 parsing failed for lolalytics: {e}")

        # Also try regex fallback for win rate data in the HTML
        if not results:
            # Pattern: champion name followed by win rate percentage
            rows = re.findall(r'champion/([a-z]+).*?(\d{2}\.\d+)%', html, re.IGNORECASE)
            for name, wr in rows:
                results[name.lower()] = float(wr)

        return results

    def _try_metasrc(self, ctx):
        """Attempt to scrape metasrc stats page for ARAM or Mayhem."""
        if self.mode == "ARAM Mayhem":
            url = "https://www.metasrc.com/lol/mayhem/na/stats"
        else:
            url = "https://www.metasrc.com/lol/aram/na/stats"

        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "identity",
            "Referer": "https://www.metasrc.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
        })
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode("utf-8", errors="ignore")

        results = {}
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # Metasrc typically uses a table where rows have data-champ
            rows = soup.find_all("tr", attrs={"data-champ": True})
            for row in rows:
                champ = row["data-champ"].replace("'", "").replace(" ", "").replace(".", "").lower()
                # Find all percentages in text
                text = row.get_text()
                pcts = re.findall(r'([\d.]+)%', text)
                if pcts:
                    try:
                        results[champ] = float(pcts[0])
                    except ValueError:
                        pass
                        
            # If the table structure changed, look for build links
            if len(results) < 20:
                links = soup.find_all("a", href=re.compile(r'/build/'))
                for link in links:
                    name_el = link.string
                    if not name_el: continue
                    champ = name_el.strip().replace("'", "").replace(" ", "").replace(".", "").lower()
                    parent = link.find_parent(["tr", "div"])
                    if parent:
                        pcts = re.findall(r'(\d{2}\.\d{2})%', parent.get_text())
                        for pct_str in pcts:
                            wr = float(pct_str)
                            if 35.0 <= wr <= 65.0:
                                results[champ] = wr
                                break
        except Exception as e:
            Logger.debug("Stats", f"BS4 parsing failed for metasrc: {e}")

        # Strategy 2 Fallback: Regex
        if len(results) < 20:
            build_matches = re.finditer(r'/build/([a-z\-]+)"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
            for match in build_matches:
                display_name = match.group(2).strip()
                after_text = html[match.end():match.end() + 800]
                pcts = re.findall(r'(\d{2}\.\d{2})%', after_text)
                if pcts:
                    try:
                        for pct_str in pcts:
                            wr = float(pct_str)
                            if 35.0 <= wr <= 65.0:
                                clean_name = display_name.replace("'", "").replace(" ", "").replace(".", "").lower()
                                results[clean_name] = wr
                                break
                    except ValueError:
                        pass

        return results

    def get_winrate(self, champ_name):
        """Look up a champion's ARAM win rate. Returns baseline 50.0 if completely unknown."""
        # ⚡ Bolt: Fast-path string manipulation.
        # Calling .lower() before running .replace() chain is slightly faster.
        clean = champ_name.lower().replace("'", "").replace(" ", "").replace(".", "")
        return self.win_rates.get(clean, 50.0)

    @property
    def is_offline(self) -> bool:
        """True when all fetch sources failed and we're using pure baseline data."""
        return not self._fetched and not self._fetching
