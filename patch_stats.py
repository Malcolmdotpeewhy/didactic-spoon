import sys
import os

with open("src/services/stats_scraper.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Imports
import_target = """import threading
from utils.logger import Logger"""
import_replacement = """import threading
import time
import requests
import re
from concurrent.futures import ThreadPoolExecutor
from utils.logger import Logger"""
content = content.replace(import_target, import_replacement)

# 2. Init
init_target = """    def __init__(self, mode="ARAM"):
        self.mode = mode
        self.win_rates = dict()
        self.set_mode(mode)"""
init_replacement = """    def __init__(self, mode="ARAM"):
        self.mode = mode
        self.win_rates = dict()
        self.live_winrates = dict()
        self._cache_timestamps = dict()
        self._executor = ThreadPoolExecutor(max_workers=2)
        self.set_mode(mode)

    def _fetch_live_data_background(self, mode):
        # 4.2 Auto-clearing cache validation
        now = time.time()
        if now - self._cache_timestamps.get(mode, 0) < 3600 * 24:
            return  # Cache is valid for 24 hours
            
        def fetch():
            try:
                # 4.1 Live Data Hook mapping
                req = requests.get(f"https://league-stats-api.example/v1/winrates?mode={mode}", timeout=3)
                if req.status_code == 200:
                    data = req.json()
                    sanitized = {}
                    for k, v in data.items():
                        # 4.4 Data sanitization regex
                        c_k = re.sub(r'[^a-zA-Z0-9]', '', k).lower()
                        sanitized[c_k] = float(v)
                    self.live_winrates[mode] = sanitized
                    self._cache_timestamps[mode] = time.time()
                else:
                    raise Exception(f"HTTP {req.status_code}")
            except Exception as e:
                # 4.3 Fallback to Local Assets on HTTP 500
                Logger.debug("Stats", f"Live scrape failed for {mode}, falling back to local. Error: {e}")
                self._cache_timestamps[mode] = time.time() - 3600 * 23  # Retry in 1 hour if failed

        # 4.5 Concurrent Scraper Threading
        self._executor.submit(fetch)"""
content = content.replace(init_target, init_replacement)

# 3. set_mode
set_mode_target = """        else:
            self.win_rates = dict(BASELINE_RANKED_WINRATES)"""
set_mode_replacement = """        else:
            self.win_rates = dict(BASELINE_RANKED_WINRATES)
        self._fetch_live_data_background(self.mode)"""
content = content.replace(set_mode_target, set_mode_replacement)

# 4. set_mode_by_queue_id
set_mode_queue_target = """    def set_mode_by_queue_id(self, queue_id):
        \"\"\"Switch active dataset by numeric queue ID for precise mode resolution.\"\"\"
        dataset = _QUEUE_DATASET_MAP.get(queue_id, BASELINE_ARAM_WINRATES)
        self.win_rates = dict(dataset)"""
set_mode_queue_replacement = """    def set_mode_by_queue_id(self, queue_id):
        \"\"\"Switch active dataset by numeric queue ID for precise mode resolution.\"\"\"
        dataset = _QUEUE_DATASET_MAP.get(queue_id, BASELINE_ARAM_WINRATES)
        self.win_rates = dict(dataset)
        self._fetch_live_data_background(self.mode)"""
content = content.replace(set_mode_queue_target, set_mode_queue_replacement)

# 5. get_winrate
get_win_target = """        clean = champ_name.translate(_CLEAN_TRANS).lower()
        return self.win_rates.get(clean, 50.0)"""
get_win_replacement = """        clean = champ_name.translate(_CLEAN_TRANS).lower()
        if self.mode in self.live_winrates and clean in self.live_winrates[self.mode]:
            return self.live_winrates[self.mode][clean]
        return self.win_rates.get(clean, 50.0)"""
content = content.replace(get_win_target, get_win_replacement)

# 6. is_offline
offline_target = """    @property
    def is_offline(self) -> bool:
        \"\"\"Always True as live scraping is disabled.\"\"\"
        return True"""
offline_replacement = """    @property
    def is_offline(self) -> bool:
        \"\"\"Dynamically returns True if operating on local fallback data.\"\"\"
        return self.mode not in self.live_winrates"""
content = content.replace(offline_target, offline_replacement)

with open("src/services/stats_scraper.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Modification complete")
