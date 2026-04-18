# Shipment Checklist / TODO

## 1. Missing Features & Incomplete Implementations
*From comparing the planned features in `README.md` and planning documents to the current codebase.*
- **Priority Sniper**: Code exists in `automation.py`, but it appears incomplete or missing UI wiring (only fast-path optimization mentioned). Need to verify full implementation and UI connection.
- **Draft Assistant (Role Enforcer)**: Tool exists (`src/ui/components/game_tools/draft_tool.py`), but the "teammate respect algorithm" and full automation loop logic (`_perform_draft_assistant`) may be incomplete or lack test coverage.
- **Arena Synergy Picker (V2)**: Tool exists (`src/ui/components/game_tools/arena_tool.py`), but drag-and-drop fallback priority arrays logic and "intelligent global ban evasion" need thorough end-to-end verification.
- **Auto-Honor System**: `_handle_auto_honor` logic exists but needs verification that it successfully handles LCU API limits and correctly identifies friends/top performers.

## 2. Test Coverage Gaps
*Current overall test coverage is extremely low (~24%). The following areas need immediate attention before shipment:*
- **Background Services (`src/services/`)**:
  - `api_handler.py` (10% coverage)
  - `asset_manager.py` (20% coverage)
  - `automation.py` (20% coverage)
- **UI Components (`src/ui/`)**:
  - `app_sidebar.py` (8% coverage)
  - `priority_grid.py` (9% coverage)
  - `settings_modal.py` (10% coverage)
  - `friend_list.py` (10% coverage)
  - Various game tools (Arena Tool, Draft Tool) hover around 10-15% coverage.

## 3. Missing Documentation
*Numerous classes, modules, and public methods lack standard Python docstrings.*
- **`src/services/`**:
  - `automation.py` (Missing class docstring for `AutomationEngine`, missing docstrings for `start`, `stop`, `pause`, `resume`, `__init__`)
  - `asset_manager.py` (Missing module and `__init__` docstrings)
  - `stats_scraper.py` (Missing module and `__init__` docstrings)
  - `api_handler.py` (Missing `__init__` docstring)
- **`src/core/`**:
  - `main.py` (Missing module docstring, missing class docstring for `LeagueLoopApp`, and numerous event handler docstrings)
- **`src/ui/`**:
  - `app_sidebar.py` (Missing module docstring, missing class docstring for `SidebarWidget`)
  - `friend_list.py` (Missing class docstring for `FriendPriorityList` and `__init__`)
  - `toast.py` (Missing `get_instance` and `__init__` docstrings)
  - *Note: This is not an exhaustive list; a full sweep of the `src/ui` directory for docstrings is required.*

## 4. Unresolved Comments
- *No unresolved `TODO` or `FIXME` comments were found in the codebase.*
