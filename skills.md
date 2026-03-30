# Target System: skills.md (User Capability Model)

## Python CustomTkinter UI Development
### Add UI Component
- **Description:** Create a new reusable customtkinter UI component following project conventions.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 8.3
  - Confidence: High
- **[Inference]** Strong grasp of extending `ctk.CTkFrame`, applying `get_color()`, and avoiding unsupported kwargs for stability.

### Add Toast Notification
- **Description:** Show a toast notification from anywhere in the application.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:5 x 0.25) + (R:8 x 0.15) = 7.1
  - Confidence: Medium
- **[Inference]** Understands asynchronous UI updates and background task notifications.

### Update Design Tokens
- **Description:** Modify the UI design token system (colors, fonts, radii).
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:5 x 0.2) + (C:4 x 0.25) + (R:6 x 0.15) = 5.7
  - Confidence: Low
- **[Inference]** Familiar with `ui/components/factory.py` design system structure.

## Automation & Background Processing
### Debug Champ Select
- **Description:** Diagnose issues with champion select automation (priority sniper, skin equip).
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:5 x 0.2) + (C:9 x 0.25) + (R:8 x 0.15) = 8.0
  - Confidence: High
- **[Inference]** Highly proficient at tracing API flows and debugging LCU session state updates.

### Add Automation Phase Handler
- **Description:** Add a new game phase handler to the automation engine.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:8 x 0.25) + (R:8 x 0.15) = 7.6
  - Confidence: High
- **[Inference]** Understands thread safety (`self.after()`) and decoupling UI from backend processes.

### Add Toggle Setting
- **Description:** Add a new boolean toggle to the sidebar automation panel and persist it in config.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:6 x 0.25) + (R:7 x 0.15) = 7.2
  - Confidence: Medium
- **[Inference]** Experienced in modifying `config.json` state representations and mapping them to UI interactions.

### Add Hotkey Binding
- **Description:** Register a new global hotkey in LeagueLoop.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:6 x 0.2) + (C:5 x 0.25) + (R:7 x 0.15) = 6.3
  - Confidence: Medium
- **[Inference]** Follows main thread safety practices for keyboard listener callbacks.

## LCU API Integration
### Add LCU API Endpoint
- **Description:** Make a new League Client API call from the automation engine.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 7.9
  - Confidence: High
- **[Inference]** Competent in RESTful interaction with the League Client endpoints using proper authentication headers.

### Test LCU Connection
- **Description:** Verify the League Client Update API connection and diagnose issues.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:6 x 0.2) + (C:6 x 0.25) + (R:7 x 0.15) = 6.5
  - Confidence: Medium
- **[Inference]** Understands the lockfile parsing process and SSL certificate validation bypass logic.

## Application Architecture & Data
### Edit Config
- **Description:** Safely modify config.json values with validation.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:9 x 0.2) + (C:4 x 0.25) + (R:9 x 0.15) = 7.8
  - Confidence: High
- **[Inference]** Uses `ConfigManager` properly to avoid race conditions.

### Read Crash Logs
- **Description:** Parse and diagnose LeagueLoop crash logs and error files.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.4
  - Confidence: Medium
- **[Inference]** Strong troubleshooting skills using localized traceback outputs.

### Add Stats Scraper Source
- **Description:** Add a new win rate data source to the stats scraper.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:5 x 0.2) + (C:7 x 0.25) + (R:7 x 0.15) = 7.0
  - Confidence: Medium
- **[Inference]** Familiar with external API requests, JSON parsing, and fallback/caching strategies.

### Add Omnibar Command
- **Description:** Register a new command in the Ctrl+K omnibar command palette.
- **Scoring Breakdown:**
  - Score: (E:6 x 0.4) + (F:4 x 0.2) + (C:5 x 0.25) + (R:6 x 0.15) = 5.3
  - Confidence: Low
- **[Inference]** Able to extend global command palette logic efficiently.

## DevOps & Environment Setup
### Run Tests
- **Description:** Run the LeagueLoop test suite and diagnose failures.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.8
  - Confidence: High
- **[Inference]** Competent with unittest, xvfb-run, and mocking Tkinter UI dependencies.

### Git Sync
- **Description:** Commit all changes and sync with the remote repository.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:9 x 0.2) + (C:3 x 0.25) + (R:9 x 0.15) = 7.5
  - Confidence: High
- **[Inference]** Uses Git effectively for version control.

### Launch Dev Server
- **Description:** Launch the LeagueLoop application in development mode with proper PYTHONPATH.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:10 x 0.2) + (C:2 x 0.25) + (R:9 x 0.15) = 7.4
  - Confidence: Medium
- **[Inference]** Configures environment paths correctly.

### Install Dependency
- **Description:** Install a new pip dependency into the project venv and update requirements.txt.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:3 x 0.25) + (R:8 x 0.15) = 6.4
  - Confidence: Medium
- **[Inference]** Manages Python package dependencies securely.

### Build Executable
- **Description:** Build the LeagueLoop PyInstaller executable in ONEDIR mode.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:3 x 0.2) + (C:8 x 0.25) + (R:5 x 0.15) = 6.2
  - Confidence: Medium
- **[Inference]** Understands spec file configurations and resource bundling for PyInstaller.

### Refresh Assets
- **Description:** Clear and rebuild the champion icon asset cache from DDragon.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:4 x 0.2) + (C:6 x 0.25) + (R:6 x 0.15) = 6.0
  - Confidence: Medium
- **[Inference]** Can manage external asset synchronization and storage.

### Build Installer
- **Description:** Compile the Inno Setup installer for LeagueLoop distribution.
- **Scoring Breakdown:**
  - Score: (E:6 x 0.4) + (F:3 x 0.2) + (C:6 x 0.25) + (R:5 x 0.15) = 5.2
  - Confidence: Low
- **[Inference]** Capable of generating deployment installers from build outputs.
## Gap Analysis
- **Missing CI/CD Automation:** While `Build Executable` and `Build Installer` skills exist, they are manual processes.
- **Limited Advanced Testing:** `Run Tests` shows capability with basic unit tests, but there's a gap in advanced mock integration testing.

## Skill Recommendations
- **Learn CI/CD Automation:** Implement GitHub Actions to automate the `Build Executable` and `Build Installer` steps to eliminate manual building and reduce friction in deployments.
- **Enhance Testing Skills:** Develop skills in advanced mock integration testing, especially for UI components and LCU API interactions, to improve overall code reliability and confidence in automated refactoring.
