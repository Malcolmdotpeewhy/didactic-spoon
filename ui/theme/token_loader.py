import json
import os
import sys

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

    def get(self, *keys, default=None):
        keys = list(keys)
        # Handle cases where developers mistakenly pass the default as a positional argument
        if keys and (isinstance(keys[-1], (int, float, bool)) or 
                     (isinstance(keys[-1], str) and (keys[-1].startswith("#") or keys[-1] in ("transparent", "left", "right", "center", "bold", "normal", "medium")))):
            default = keys.pop()
            
        # Flatten keys if they contain dots
        flat_keys = []
        for k in keys:
            if isinstance(k, str) and "." in k:
                flat_keys.extend(k.split("."))
            else:
                flat_keys.append(k)

        data = self.tokens
        for k in flat_keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return default
        return data

TOKENS = DesignTokens()
