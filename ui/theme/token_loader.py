import json
import os
import sys
import functools

def _resolve_token_path():
    """Resolve design_tokens.json for both dev and PyInstaller frozen builds."""
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath(os.path.dirname(__file__))
        return os.path.join(base, "design_tokens.json")
    return os.path.join(base, "ui", "theme", "design_tokens.json")

TOKEN_PATH = _resolve_token_path()

DEFAULT_TOKENS = {}

class DesignTokens:
    def __init__(self):
        try:
            with open(TOKEN_PATH, "r") as f:
                self.tokens = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tokens = DEFAULT_TOKENS

    @functools.lru_cache(maxsize=1024)
    def _get_memoized(self, keys):
        """Memoized helper to avoid repeated dict traversal and string splitting overhead."""
        data = self.tokens
        try:
            for k in keys:
                if isinstance(k, str) and "." in k:
                    # Single dot-separated string fast path
                    for part in k.split("."):
                        data = data[part]
                else:
                    data = data[k]
            return data
        except (KeyError, TypeError, IndexError):
            return None

    def get(self, *keys, default=None):
        if not keys:
            return default

        # Handle cases where developers mistakenly pass the default as a positional argument
        last = keys[-1]
        if isinstance(last, str):
            if last and last[0] == "#" or last in ("transparent", "left", "right", "center", "bold", "normal", "medium"):
                default = last
                keys = keys[:-1]
        elif isinstance(last, (int, float, bool)):
            default = last
            keys = keys[:-1]

        # ⚡ Bolt: Offload dictionary access and string parsing to the memoized backend.
        result = self._get_memoized(keys)
        return result if result is not None else default

TOKENS = DesignTokens()
