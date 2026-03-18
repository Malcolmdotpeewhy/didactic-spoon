from utils.logger import Logger
import json
import os
import threading
import queue
import time
from typing import Any, Dict, Optional

import customtkinter as ctk
import requests
from PIL import Image

from utils.path_utils import get_asset_path

# Constants
CONFIG_FILE = "config.json"
CACHE_DIR = get_asset_path("assets")
ASSETS_DIR = get_asset_path("assets")

# Ensure cache directories exist (only works in dev mode, fails silently in exe mode)
try:
    os.makedirs(ASSETS_DIR, exist_ok=True)
except OSError:
    pass

DEFAULT_CONFIG = {
    "auto_accept": False,
    "auto_requeue": False,
    "auto_pick": "",  # Legacy/Global Fallback
    "auto_pick_backup": "",
    "auto_ban": "",
    "custom_status": "Using AutoLock",
    "auto_aram_swap": False,
    "auto_set_roles": False,
    "auto_hover": False,
    "auto_lock_in": False,
    "auto_random_skin": False,
    "auto_spells": True,
    "accept_delay": 2.0,
    "polling_rate_champ_select": 0.5,  # Default to Fast for CS
    # Role-Based Picks (3 slots per role)
    "pick_TOP_1": "",
    "pick_TOP_2": "",
    "pick_TOP_3": "",
    "pick_JUNGLE_1": "",
    "pick_JUNGLE_2": "",
    "pick_JUNGLE_3": "",
    "pick_MIDDLE_1": "",
    "pick_MIDDLE_2": "",
    "pick_MIDDLE_3": "",
    "pick_BOTTOM_1": "",
    "pick_BOTTOM_2": "",
    "pick_BOTTOM_3": "",
    "pick_UTILITY_1": "",
    "pick_UTILITY_2": "",
    "pick_UTILITY_3": "",
    # Role-Based Bans
    "ban_TOP": "",
    "ban_JUNGLE": "",
    "ban_MIDDLE": "",
    "ban_BOTTOM": "",
    "ban_UTILITY": "",
    "always_on_top": True,
}




DDRAGON_VER = "14.1.1"


class ConfigManager:
    """Manages application configuration."""

    def __init__(self):
        self.cfg = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.cfg.update(json.load(f))
            except Exception as e:  # pylint: disable=broad-exception-caught
                Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")

    def get(self, key, default=None):
        """Get a configuration value."""
        return self.cfg.get(key, default)

    def set(self, key, val, save=True):
        """Set a configuration value and optionally save to file."""
        self.cfg[key] = val
        if save:
            self.save()

    def set_batch(self, updates: dict, save=True):
        """Set multiple configuration values and optionally save to file."""
        self.cfg.update(updates)
        if save:
            self.save()

    def save(self):
        """Save configuration to file."""
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cfg, f, indent=4)




class AssetManager:
    """Manages application assets (images, data)."""

    def __init__(self, log_func=None):
        self._log_func = log_func
        # Create dir if not exists
        if not os.path.exists(ASSETS_DIR):
            try:
                os.makedirs(ASSETS_DIR)
            except Exception as e:  # pylint: disable=broad-exception-caught
                Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")

        self.champ_data: Dict[str, Any] = {}
        self.id_to_key: Dict[int, str] = {}  # ID (int) -> Key/DDragonID (str)
        self.id_to_tags: Dict[int, list] = {}  # ID (int) -> List[Tags]
        self.name_to_id: Dict[str, int] = {}  # Name/Key (lower) -> ID (int)
        self.champ_roles: Dict[int, list] = {}  # ID -> List[Positions]
        self.spell_data: Dict[int, str] = {}
        self.icons: Dict[str, ctk.CTkImage] = {}

        self._runes_cache = None

        self._pending_downloads = set()
        self._lock = threading.Lock()

        # Bolt: Use a Queue + Daemon Threads to prevent thread explosion during high load
        # (e.g., skin selector) while ensuring clean app exit.
        self._download_queue = queue.Queue()
        for _ in range(5):
            threading.Thread(target=self._download_worker, daemon=True).start()

        self.session = requests.Session()

        # Initialize version from cache if available, otherwise use default
        self.ddragon_ver = DDRAGON_VER
        v_path = os.path.join(CACHE_DIR, "version.txt")
        if os.path.exists(v_path):
            try:
                with open(v_path, "r", encoding="utf-8") as f:
                    self.ddragon_ver = f.read().strip()
            except Exception as e:
                Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")

    def _download_worker(self):
        """Worker thread for background downloads."""
        while True:
            func = self._download_queue.get()
            try:
                func()
            except Exception as e:  # pylint: disable=broad-exception-caught
                Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
            finally:
                self._download_queue.task_done()

    def log(self, msg):
        """Safe logging method that handles None log function."""
        if self._log_func:
            self._log_func(msg)
        else:
            print(f"[Assets] {msg}")

    def start_loading(self):
        """Start loading assets in a background thread."""
        threading.Thread(target=self._load_all, daemon=True).start()

    def _fetch_latest_version(self):
        """Fetches the latest Data Dragon version."""
        try:
            url = "https://ddragon.leagueoflegends.com/api/versions.json"
            response = self.session.get(url, timeout=5)
            if response.status_code == 200:
                versions = response.json()
                if versions and isinstance(versions, list):
                    latest = versions[0]
                    if latest != self.ddragon_ver:
                        self.log(f"Updated Data Dragon version to {latest}")
                        self.ddragon_ver = latest
                        v_path = os.path.join(CACHE_DIR, "version.txt")
                        with open(v_path, "w", encoding="utf-8") as f:
                            f.write(self.ddragon_ver)

                        # Invalidate stale data caches so they re-download
                        self._runes_cache = None
                        for filename in ("champion.json", "item.json", "summoner.json", "runesReforged.json"):
                            path = os.path.join(CACHE_DIR, filename)
                            if os.path.exists(path):
                                try:
                                    os.remove(path)
                                except Exception as e:
                                    Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
        except Exception as e:
            self.log(f"Failed to fetch latest version: {e}")

    def _load_all(self):
        self._fetch_latest_version()
        self.log("Downloading Data Assets...")

        # Preload Profile Background
        try:
            cfg = ConfigManager()
            bg_id = cfg.get("profile_bg_id")
            if bg_id:
                self.log(f"Preloading background {bg_id}...")
                self.get_splash_art(int(bg_id), width=1100, opacity=0.5)
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")

        self._load_champion_data()
        self._load_meraki_data()
        self._load_spell_data()
        self._load_rune_icons()
        self.log("Assets Loaded.")

    def _load_rune_icons(self):
        """Preloads all rune icons to cache (Download Only)."""
        runes = self.get_runes_data()
        if not runes:
            return

        count = 0
        for tree in runes:
            # Tree Icon
            self._ensure_rune_icon(tree.get("icon"))
            # Slots
            slots = tree.get("slots")
            if not slots:
                continue

            for slot in slots:
                slot_runes = slot.get("runes")
                if not slot_runes:
                    continue

                for rune in slot_runes:
                    self._ensure_rune_icon(rune.get("icon"))
                    count += 1
        self.log(f"Pre-checked {count} rune icons.")

    def _ensure_rune_icon(self, icon_path):
        """Downloads rune icon if missing, but DOES NOT create CTkImage."""
        if not icon_path:
            return
        safe_name = icon_path.replace("/", "_").replace("\\", "_")
        path = os.path.join(ASSETS_DIR, f"rune_{safe_name}")

        if not os.path.exists(path):
            url = f"https://ddragon.leagueoflegends.com/cdn/img/{icon_path}"
            self._start_download(url, path)

    def _load_champion_data(self):
        path = os.path.join(CACHE_DIR, "champion.json")
        try:
            if not os.path.exists(path):
                url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/data/en_US/champion.json"
                data = self.session.get(url, timeout=10).json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.champ_data = data["data"]

            # Populate Lookup Maps
            self.id_to_key = {}
            self.id_to_tags = {}
            self.name_to_id = {}
            for key_str, info in self.champ_data.items():
                try:
                    cid = int(info["key"])
                    name = info["name"]

                    self.id_to_key[cid] = key_str
                    self.id_to_tags[cid] = info.get("tags", [])

                    # Map both DDragon Key (e.g. "MonkeyKing") and Name (e.g. "Wukong")
                    self.name_to_id[key_str.lower()] = cid
                    self.name_to_id[name.lower()] = cid
                except (ValueError, KeyError):
                    continue

        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                Logger.warning("asset_manager.py", f"Failed to remove file {path}: {e}")

    def _load_meraki_data(self):
        """Load detailed champion data (including roles) from Meraki Analytics."""
        path = os.path.join(CACHE_DIR, "meraki_champions.json")
        try:
            # Download if missing or stale (simple check: if we just updated ddragon, update this too)
            if not os.path.exists(path):
                url = "https://cdn.merakianalytics.com/riot/lol/resources/latest/en-US/champions.json"
                r = self.session.get(url, timeout=15)
                if r.status_code == 200:
                    try:
                        data_to_write = r.json()
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(data_to_write, f)
                    except json.JSONDecodeError as e:
                        Logger.error("asset_manager.py", f"Failed to parse Meraki download: {e}")
                        return
            
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                     try:
                         data = json.load(f)
                     except json.JSONDecodeError as e:
                         Logger.error("asset_manager.py", f"Corrupted Meraki cache, deleting: {e}")
                         os.remove(path)
                         return
                     # Parse roles: ID -> [Positions]
                     self.champ_roles = {}
                     for _, info in data.items():
                         try:
                             cid = info.get("id", 0)
                             positions = info.get("positions", [])
                             if cid and positions:
                                 # Normalize "SUPPORT" -> "UTILITY" to match internal convention
                                 clean_pos = [
                                     "UTILITY" if p == "SUPPORT" else p 
                                     for p in positions
                                 ]
                                 self.champ_roles[int(cid)] = clean_pos
                         except Exception as e:
                             Logger.error("asset_manager.py", f"Handled exception: {e}")
                             continue
                self.log(f"Loaded Meraki role data for {len(self.champ_roles)} champions.")

        except Exception as e:
            Logger.error("asset_manager.py", f"Failed to load Meraki data: {type(e).__name__}: {e}")
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                Logger.warning("asset_manager.py", f"Failed to remove file {path}: {e}")

    def _load_spell_data(self):
        path = os.path.join(CACHE_DIR, "summoner.json")
        try:
            if not os.path.exists(path):
                url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/data/en_US/summoner.json"
                data = self.session.get(url, timeout=10).json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.spell_data = {}
                for id_name, info in data["data"].items():
                    self.spell_data[int(info["key"])] = id_name
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError as e:
                Logger.warning("asset_manager.py", f"Failed to remove file {path}: {e}")

    def get_champ_name(self, champ_id: int) -> str:
        """Get champion name by ID."""
        return self.id_to_key.get(champ_id, str(champ_id))








    def _simple_download(self, url, path):
        try:
            # Enable SSL verification for security
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                tmp_path = f"{path}.tmp"
                with open(tmp_path, "wb") as f:
                    f.write(r.content)
                # Atomic replace guarantees os.path.exists(path) is only true
                # when the file is 100% complete and valid for Image.open to read.
                os.replace(tmp_path, path)
            else:
                Logger.warning("asset_manager.py", f"Failed {url} -> {r.status_code}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("asset_manager.py", f"Exception {url} -> {e}")

    def _start_download(self, url, path):
        """Helper to start a download if not already in progress."""
        with self._lock:
            if path in self._pending_downloads:
                return
            self._pending_downloads.add(path)

        def _target():
            try:
                self._simple_download(url, path)
            finally:
                with self._lock:
                    self._pending_downloads.discard(path)

        self._download_queue.put(_target)










    def get_runes_data(self):
        """Get runes reforged data."""
        if self._runes_cache is not None:
            return self._runes_cache

        path = os.path.join(CACHE_DIR, "runesReforged.json")
        try:
            if not os.path.exists(path):
                url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/data/en_US/runesReforged.json"
                data = self.session.get(url, timeout=10).json()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
            with open(path, "r", encoding="utf-8") as f:
                self._runes_cache = json.load(f)
                return self._runes_cache
        except Exception as e:  # pylint: disable=broad-exception-caught
            Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
            return []

    def _download_and_cache_image(self, url, path, cache_key, size=None, opacity=1.0):
        if cache_key in self.icons:
            return self.icons[cache_key]

        # Check for pre-processed image on disk
        # We replace spaces and invalid characters in cache_key to be safe
        safe_key = cache_key.replace(" ", "_").replace(":", "").replace("/", "_")
        processed_fname = f"processed_{safe_key}.png"
        processed_path = os.path.join(ASSETS_DIR, processed_fname)
        
        if os.path.exists(processed_path):
            try:
                pil_img = Image.open(processed_path).convert("RGBA")
                # CTkImage size requires integer tuple, fallback to original if size contains None
                disp_size = size if size and size[1] is not None else pil_img.size
                img = ctk.CTkImage(pil_img, size=disp_size)
                self.icons[cache_key] = img
                return img
            except Exception:
                pass  # Fall back to regenerating if the cached file is corrupt
                
        if os.path.exists(path):
            try:
                pil_img = Image.open(path).convert("RGBA")
                
                # Resize
                if size and pil_img.size[:2] != size[:2]:
                    # If only width is provided or aspect ratio should be kept, handle it:
                    if size[1] is None:
                        aspect = pil_img.height / pil_img.width
                        height = int(size[0] * aspect)
                        size = (size[0], height)
                    pil_img = pil_img.resize(size, Image.Resampling.BICUBIC)
                else:
                    if size and size[1] is None:
                        aspect = pil_img.height / pil_img.width
                        size = (size[0], int(size[0] * aspect))

                # Opacity
                if opacity < 1.0:
                    alpha = pil_img.split()[3]
                    lut = [int(p * opacity) for p in range(256)]
                    alpha = alpha.point(lut)
                    pil_img.putalpha(alpha)

                # Save processed version to disk for future fast-loads
                try:
                    pil_img.save(processed_path, "PNG")
                except Exception:
                    pass

                img_size = size if size and size[1] is not None else pil_img.size
                img = ctk.CTkImage(pil_img, size=img_size)
                self.icons[cache_key] = img
                return img
            except Exception as e:
                Logger.error("asset_manager.py", f"Image load error: {e}")
                return None

        self._start_download(url, path)
        return None

    def get_icon(self, type_, key, size=(40, 40)) -> Optional[ctk.CTkImage]:
        """Synchronously get an icon if cached on disk, otherwise trigger a download and return None."""
        cache_key = f"{type_}_{key}_{size[0]}x{size[1]}"
        fname = ""
        url = ""
        
        # Clean the key to support 'MonkeyKing' vs 'Wukong' issues gracefully if needed
        if type_ == "champion":
            fname = f"champion_{key}.png"
            url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/img/champion/{key}.png"
        elif type_ == "spell":
            fname = f"spell_{key}.png"
            url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/img/spell/{key}.png"
        elif type_ == "item":
            fname = f"item_{key}.png"
            url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_ver}/img/item/{key}.png"
        elif type_ == "rune":
            # For runes, the key might be the relative path
            safe_name = key.replace("/", "_").replace("\\", "_")
            fname = f"rune_{safe_name}"
            url = f"https://ddragon.leagueoflegends.com/cdn/img/{key}"
        else:
            return None

        path = os.path.join(ASSETS_DIR, fname)
        return self._download_and_cache_image(url, path, cache_key, size=size)

    def get_icon_async(self, type_, key, callback, size=(40, 40), widget=None):
        """Helper to get an icon and call the callback when it's ready."""
        img = self.get_icon(type_, key, size=size)
        if img:
            callback(img)
            return

        def _wait():
            for _ in range(50):  # Wait up to 5 seconds
                if widget and not widget.winfo_exists():
                    return
                poll_img = self.get_icon(type_, key, size=size)
                if poll_img:
                    if widget and widget.winfo_exists():
                        widget.after(0, lambda: callback(poll_img))
                    return
                time.sleep(0.1)

        threading.Thread(target=_wait, daemon=True).start()

    def get_splash_art(
        self, skin_id: int, width=1280, opacity=1.0
    ) -> Optional[ctk.CTkImage]:
        """Get a CTkImage for the specified skin splash art."""
        cache_key = f"splash_{skin_id}_{width}_{opacity}"
        
        if cache_key in self.icons:
            return self.icons[cache_key]

        try:
            champ_id = skin_id // 1000
            skin_num = skin_id % 1000
            ddragon_id = self.get_champ_name(champ_id)
            if not ddragon_id or ddragon_id == str(champ_id):
                return None
        except Exception as e:
            Logger.error("asset_manager.py", f"Handled exception: {type(e).__name__}: {e}")
            return None

        fname = f"splash_{ddragon_id}_{skin_num}.jpg"
        path = os.path.join(ASSETS_DIR, fname)
        url = f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{ddragon_id}_{skin_num}.jpg"

        return self._download_and_cache_image(url, path, cache_key, size=(width, None), opacity=opacity)

