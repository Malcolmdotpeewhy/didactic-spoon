"""
Constants module for LeagueLoop.
Centralizes magic numbers and configuration defaults.
"""

# --- Queue IDs ---
QUEUE_DRAFT = 400
QUEUE_RANKED_SOLO = 420
QUEUE_RANKED_FLEX = 440
QUEUE_ARAM = 450
QUEUE_ARENA = 1700

# --- Polling & Timing ---
DOCKING_POLL_INTERVAL = 0.05       # seconds between docking geometry checks
DOCKING_IDLE_INTERVAL = 0.5        # seconds when no client window found
CONNECTION_POLL_INTERVAL = 2.0     # seconds between LCU connection attempts
CONNECTION_ERROR_INTERVAL = 5.0    # seconds to wait after connection error
TICK_SLEEP_DEFAULT = 3.0
TICK_SLEEP_CHAMPSELECT = 1.0
TICK_SLEEP_READYCHECK = 1.0
TICK_SLEEP_LOBBY = 2.0
TICK_SLEEP_INGAME = 30.0
GEOMETRY_THRESHOLD = 2             # pixels of movement before triggering geometry update
PRIORITY_SWAP_COOLDOWN = 1.0       # seconds between priority sniper swaps

# --- UI Dimensions ---
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24

SIDEBAR_WIDTH = 300
SIDEBAR_HEIGHT = 500
COMPACT_SIZE = 90
COMPACT_BUTTON_SIZE = 72
COMPACT_GLOW_SIZE = 80

# --- LCU Request ---
LCU_REQUEST_TIMEOUT = 2            # seconds

# --- Asset Manager ---
DDRAGON_DEFAULT_VERSION = "14.1.1"
DOWNLOAD_WORKER_COUNT = 5
PROCESS_SCAN_WARN_THRESHOLD = 0.5  # seconds; log warning if scan is slower
