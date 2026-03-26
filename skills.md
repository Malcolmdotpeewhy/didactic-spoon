# Target System: skills.md (User Capability Model)

## Python CustomTkinter UI Development
### Add UI Component
- **Description:** Create a new reusable customtkinter UI component following project conventions.
- **Scoring Breakdown:**
  - Evidence (E): 9
  - Frequency (F): 8
  - Complexity (C): 7
  - Recency (R): 9
  - Score: (9 x 0.4) + (8 x 0.2) + (7 x 0.25) + (9 x 0.15) = 8.3
- **[Inference]** Strong grasp of extending `ctk.CTkFrame`, applying `get_color()`, and avoiding unsupported kwargs for stability.

### Add Toast Notification
- **Description:** Show a toast notification from anywhere in the application.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 7
  - Complexity (C): 5
  - Recency (R): 8
  - Score: (8 x 0.4) + (7 x 0.2) + (5 x 0.25) + (8 x 0.15) = 7.05
- **[Inference]** Understands asynchronous UI updates and background task notifications.

### Update Design Tokens
- **Description:** Modify the UI design token system (colors, fonts, radii).
- **Scoring Breakdown:**
  - Evidence (E): 7
  - Frequency (F): 5
  - Complexity (C): 4
  - Recency (R): 6
  - Score: (7 x 0.4) + (5 x 0.2) + (4 x 0.25) + (6 x 0.15) = 5.7
- **[Inference]** Familiar with `ui/components/factory.py` design system structure.

## Automation & Background Processing
### Add Automation Phase Handler
- **Description:** Add a new game phase handler to the automation engine.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 6
  - Complexity (C): 8
  - Recency (R): 8
  - Score: (8 x 0.4) + (6 x 0.2) + (8 x 0.25) + (8 x 0.15) = 7.6
- **[Inference]** Understands thread safety (`self.after()`) and decoupling UI from backend processes.

### Add Hotkey Binding
- **Description:** Register a new global hotkey in LeagueLoop.
- **Scoring Breakdown:**
  - Evidence (E): 7
  - Frequency (F): 6
  - Complexity (C): 5
  - Recency (R): 7
  - Score: (7 x 0.4) + (6 x 0.2) + (5 x 0.25) + (7 x 0.15) = 6.3
- **[Inference]** Follows main thread safety practices for keyboard listener callbacks.

### Add Toggle Setting
- **Description:** Add a new boolean toggle to the sidebar automation panel and persist it in config.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 7
  - Complexity (C): 6
  - Recency (R): 7
  - Score: (8 x 0.4) + (7 x 0.2) + (6 x 0.25) + (7 x 0.15) = 7.15
- **[Inference]** Experienced in modifying `config.json` state representations and mapping them to UI interactions.

### Debug Champ Select
- **Description:** Diagnose issues with champion select automation (priority sniper, skin equip).
- **Scoring Breakdown:**
  - Evidence (E): 9
  - Frequency (F): 5
  - Complexity (C): 9
  - Recency (R): 8
  - Score: (9 x 0.4) + (5 x 0.2) + (9 x 0.25) + (8 x 0.15) = 8.05
- **[Inference]** Highly proficient at tracing API flows and debugging LCU session state updates.

## LCU API Integration
### Add LCU API Endpoint
- **Description:** Make a new League Client API call from the automation engine.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 8
  - Complexity (C): 7
  - Recency (R): 9
  - Score: (8 x 0.4) + (8 x 0.2) + (7 x 0.25) + (9 x 0.15) = 7.9
- **[Inference]** Competent in RESTful interaction with the League Client endpoints using proper authentication headers.

### Test LCU Connection
- **Description:** Verify the League Client Update API connection and diagnose issues.
- **Scoring Breakdown:**
  - Evidence (E): 7
  - Frequency (F): 6
  - Complexity (C): 6
  - Recency (R): 7
  - Score: (7 x 0.4) + (6 x 0.2) + (6 x 0.25) + (7 x 0.15) = 6.55
- **[Inference]** Understands the lockfile parsing process and SSL certificate validation bypass logic.

## Application Architecture & Data
### Add Omnibar Command
- **Description:** Register a new command in the Ctrl+K omnibar command palette.
- **Scoring Breakdown:**
  - Evidence (E): 6
  - Frequency (F): 4
  - Complexity (C): 5
  - Recency (R): 6
  - Score: (6 x 0.4) + (4 x 0.2) + (5 x 0.25) + (6 x 0.15) = 5.35
- **[Inference]** Able to extend global command palette logic efficiently.

### Add Stats Scraper Source
- **Description:** Add a new win rate data source to the stats scraper.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 5
  - Complexity (C): 7
  - Recency (R): 7
  - Score: (8 x 0.4) + (5 x 0.2) + (7 x 0.25) + (7 x 0.15) = 7.0
- **[Inference]** Familiar with external API requests, JSON parsing, and fallback/caching strategies.

### Edit Config
- **Description:** Safely modify config.json values with validation.
- **Scoring Breakdown:**
  - Evidence (E): 9
  - Frequency (F): 9
  - Complexity (C): 4
  - Recency (R): 9
  - Score: (9 x 0.4) + (9 x 0.2) + (4 x 0.25) + (9 x 0.15) = 7.75
- **[Inference]** Uses `ConfigManager` properly to avoid race conditions.

### Read Crash Logs
- **Description:** Parse and diagnose LeagueLoop crash logs and error files.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 6
  - Complexity (C): 7
  - Recency (R): 8
  - Score: (8 x 0.4) + (6 x 0.2) + (7 x 0.25) + (8 x 0.15) = 7.35
- **[Inference]** Strong troubleshooting skills using localized traceback outputs.

## DevOps & Environment Setup
### Build Executable
- **Description:** Build the LeagueLoop PyInstaller executable in ONEDIR mode.
- **Scoring Breakdown:**
  - Evidence (E): 7
  - Frequency (F): 3
  - Complexity (C): 8
  - Recency (R): 5
  - Score: (7 x 0.4) + (3 x 0.2) + (8 x 0.25) + (5 x 0.15) = 6.15
- **[Inference]** Understands spec file configurations and resource bundling for PyInstaller.

### Build Installer
- **Description:** Compile the Inno Setup installer for LeagueLoop distribution.
- **Scoring Breakdown:**
  - Evidence (E): 6
  - Frequency (F): 3
  - Complexity (C): 6
  - Recency (R): 5
  - Score: (6 x 0.4) + (3 x 0.2) + (6 x 0.25) + (5 x 0.15) = 5.25
- **[Inference]** Capable of generating deployment installers from build outputs.

### Git Sync
- **Description:** Commit all changes and sync with the remote repository.
- **Scoring Breakdown:**
  - Evidence (E): 9
  - Frequency (F): 9
  - Complexity (C): 3
  - Recency (R): 9
  - Score: (9 x 0.4) + (9 x 0.2) + (3 x 0.25) + (9 x 0.15) = 7.5
- **[Inference]** Uses Git effectively for version control.

### Install Dependency
- **Description:** Install a new pip dependency into the project venv and update requirements.txt.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 6
  - Complexity (C): 3
  - Recency (R): 8
  - Score: (8 x 0.4) + (6 x 0.2) + (3 x 0.25) + (8 x 0.15) = 6.35
- **[Inference]** Manages Python package dependencies securely.

### Launch Dev Server
- **Description:** Launch the LeagueLoop application in development mode with proper PYTHONPATH.
- **Scoring Breakdown:**
  - Evidence (E): 9
  - Frequency (F): 10
  - Complexity (C): 2
  - Recency (R): 9
  - Score: (9 x 0.4) + (10 x 0.2) + (2 x 0.25) + (9 x 0.15) = 7.45
- **[Inference]** Configures environment paths correctly.

### Refresh Assets
- **Description:** Clear and rebuild the champion icon asset cache from DDragon.
- **Scoring Breakdown:**
  - Evidence (E): 7
  - Frequency (F): 4
  - Complexity (C): 6
  - Recency (R): 6
  - Score: (7 x 0.4) + (4 x 0.2) + (6 x 0.25) + (6 x 0.15) = 6.0
- **[Inference]** Can manage external asset synchronization and storage.

### Run Tests
- **Description:** Run the LeagueLoop test suite and diagnose failures.
- **Scoring Breakdown:**
  - Evidence (E): 8
  - Frequency (F): 8
  - Complexity (C): 7
  - Recency (R): 8
  - Score: (8 x 0.4) + (8 x 0.2) + (7 x 0.25) + (8 x 0.15) = 7.75
- **[Inference]** Competent with unittest, xvfb-run, and mocking Tkinter UI dependencies.