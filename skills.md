# Target System: skills.md (User Capability Model)

## Python CustomTkinter UI Development
### Add UI Component
- **Description:** Create a new reusable customtkinter UI component following project conventions.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 8.30
  - Confidence: High
- **[Inference]** Strong grasp of extending `ctk.CTkFrame`, applying `get_color()`, and avoiding unsupported kwargs for stability.

### Implement UI Affordances
- **Description:** Add interactive visual cues like pointer cursors and hover states to CustomTkinter components.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:8 x 0.2) + (C:6 x 0.25) + (R:9 x 0.15) = 8.05
  - Confidence: High
- **[Inference]** Strong understanding of event binding (`<Enter>`, `<Leave>`) and cursor configuration to improve usability.

### Debug Champ Select
- **Description:** Diagnose issues with champion select automation (priority sniper, skin equip).
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:5 x 0.2) + (C:9 x 0.25) + (R:8 x 0.15) = 8.05
  - Confidence: High
- **[Inference]** Highly proficient at tracing API flows and debugging LCU session state updates.

### UI State Management & Animation
- **Description:** Implement robust state removal and event cleanup for animated CustomTkinter widgets.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:8 x 0.25) + (R:8 x 0.15) = 7.80
  - Confidence: High
- **[Inference]** Competent at binding cleanup logic to `<Destroy>` events using closure guard flags to prevent race conditions during rapid re-renders.

### Event Loop Optimization
- **Description:** Eliminate main thread latency by precomputing static variables for high-frequency event handlers.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 7.70
  - Confidence: High
- **[Inference]** Understands how to prevent micro-stuttering in Tkinter/CustomTkinter by moving O(N) operations and variable initializations out of the hot path.

### Implement Drag-and-Drop Wrappers
- **Description:** Add drag-and-drop capabilities to CustomTkinter components using TkinterDnD.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:8 x 0.25) + (R:8 x 0.15) = 7.60
  - Confidence: High
- **[Inference]** Understands how to avoid multiple inheritance metaclass conflicts by dynamically binding methods to instances during initialization.

### Add Automation Phase Handler
- **Description:** Add a new game phase handler to the automation engine.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:8 x 0.25) + (R:8 x 0.15) = 7.60
  - Confidence: High
- **[Inference]** Understands thread safety (`self.after()`) and decoupling UI from backend processes.

### Hover State Normalization
- **Description:** Implement automated recursive checks and fixes for missing interactive hover affordances across UI modules.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:5 x 0.25) + (R:9 x 0.15) = 7.20
  - Confidence: Medium
- **[Inference]** Understands Abstract Syntax Trees (AST) or text parsing to enforce CustomTkinter cursor best practices globally.
### Add Toggle Setting
- **Description:** Add a new boolean toggle to the sidebar automation panel and persist it in config.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:6 x 0.25) + (R:7 x 0.15) = 7.15
  - Confidence: Medium
- **[Inference]** Experienced in modifying `config.json` state representations and mapping them to UI interactions.

### Add Toast Notification
- **Description:** Show a toast notification from anywhere in the application.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:5 x 0.25) + (R:8 x 0.15) = 7.05
  - Confidence: Medium
- **[Inference]** Understands asynchronous UI updates and background task notifications.

### Add Hotkey Binding
- **Description:** Register a new global hotkey in LeagueLoop.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:6 x 0.2) + (C:5 x 0.25) + (R:7 x 0.15) = 6.30
  - Confidence: Medium
- **[Inference]** Follows main thread safety practices for keyboard listener callbacks.

### Update Design Tokens
- **Description:** Modify the UI design token system (colors, fonts, radii).
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:5 x 0.2) + (C:4 x 0.25) + (R:6 x 0.15) = 5.70
  - Confidence: Low
- **[Inference]** Familiar with `ui/components/factory.py` design system structure.

## Automation & Background Processing

## LCU API Integration
### Add LCU API Endpoint
- **Description:** Make a new League Client API call from the automation engine.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 7.90
  - Confidence: High
- **[Inference]** Competent in RESTful interaction with the League Client endpoints using proper authentication headers.

### Test LCU Connection
- **Description:** Verify the League Client Update API connection and diagnose issues.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:6 x 0.2) + (C:6 x 0.25) + (R:7 x 0.15) = 6.55
  - Confidence: Medium
- **[Inference]** Understands the lockfile parsing process and SSL certificate validation bypass logic.


## Application Architecture & Data
### Advanced UI Mock Testing
- **Description:** Test CustomTkinter logic using `sys.modules` patching and headless xvfb environments.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:6 x 0.2) + (C:8 x 0.25) + (R:9 x 0.15) = 8.15
  - Confidence: High
- **[Inference]** Capable of testing UI components dynamically by bypassing strict CustomTkinter instantiation limits.

### Robust Path Resolution in Tests
- **Description:** Write tests that dynamically construct absolute paths relative to the test file.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:8 x 0.2) + (C:6 x 0.25) + (R:9 x 0.15) = 8.05
  - Confidence: High
- **[Inference]** Consistently avoids hardcoded relative paths to ensure tests run reliably regardless of execution directory.

### UI Instantiation Testing
- **Description:** Test robust instantiation of complex CustomTkinter widgets to prevent invalid kwargs crashes.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:8 x 0.2) + (C:6 x 0.25) + (R:9 x 0.15) = 8.05
  - Confidence: High
- **[Inference]** Effectively validates dynamic UI factories and layout components independently of active rendering contexts.
### Resolve Git Merge Conflicts
- **Description:** Resolve raw Git merge markers (e.g., `<<<<<<< HEAD`, `=======`, `>>>>>>>`) left in Python source code to restore correct syntax and functionality.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:6 x 0.2) + (C:7 x 0.25) + (R:9 x 0.15) = 7.90
  - Confidence: High
- **[Inference]** Understands how to properly clean up and merge conflicting code blocks using manual text editing or regex rather than blindly deleting markers.

## Testing & Quality Assurance
### Edit Config
- **Description:** Safely modify config.json values with validation.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:9 x 0.2) + (C:4 x 0.25) + (R:9 x 0.15) = 7.75
  - Confidence: High
- **[Inference]** Uses `ConfigManager` properly to avoid race conditions.

### Prevent Command Injection
- **Description:** Safely launch background processes like the Riot Client.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:6 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.75
  - Confidence: High
- **[Inference]** Understands how to pass command arguments as a list using the `subprocess` module to prevent shell injection vulnerabilities.

### Run Tests
- **Description:** Run the LeagueLoop test suite and diagnose failures.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:8 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.75
  - Confidence: High
- **[Inference]** Competent with unittest, xvfb-run, and mocking Tkinter UI dependencies.

### Test Background Tasks
- **Description:** Test classes that initiate background threads on instantiation.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:7 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.55
  - Confidence: High
- **[Inference]** Competent at patching `threading.Thread.start` to prevent background tasks from running, ensuring clean and isolated test states.

## DevOps & Environment Setup
### Git Sync
- **Description:** Commit all changes and sync with the remote repository.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:9 x 0.2) + (C:3 x 0.25) + (R:9 x 0.15) = 7.50
  - Confidence: High
- **[Inference]** Uses Git effectively for version control.

### Launch Dev Server
- **Description:** Launch the LeagueLoop application in development mode with proper PYTHONPATH.
- **Scoring Breakdown:**
  - Score: (E:9 x 0.4) + (F:10 x 0.2) + (C:2 x 0.25) + (R:9 x 0.15) = 7.45
  - Confidence: Medium
- **[Inference]** Configures environment paths correctly.

### Read Crash Logs
- **Description:** Parse and diagnose LeagueLoop crash logs and error files.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:7 x 0.25) + (R:8 x 0.15) = 7.35
  - Confidence: Medium
- **[Inference]** Strong troubleshooting skills using localized traceback outputs.

### Add Stats Scraper Source
- **Description:** Add a new win rate data source to the stats scraper.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:5 x 0.2) + (C:7 x 0.25) + (R:7 x 0.15) = 7.00
  - Confidence: Medium
- **[Inference]** Familiar with external API requests, JSON parsing, and fallback/caching strategies.

### Install Dependency
- **Description:** Install a new pip dependency into the project venv and update requirements.txt.
- **Scoring Breakdown:**
  - Score: (E:8 x 0.4) + (F:6 x 0.2) + (C:3 x 0.25) + (R:8 x 0.15) = 6.35
  - Confidence: Medium
- **[Inference]** Manages Python package dependencies securely.

### Build Executable
- **Description:** Build the LeagueLoop PyInstaller executable in ONEDIR mode.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:3 x 0.2) + (C:8 x 0.25) + (R:5 x 0.15) = 6.15
  - Confidence: Medium
- **[Inference]** Understands spec file configurations and resource bundling for PyInstaller.

### Refresh Assets
- **Description:** Clear and rebuild the champion icon asset cache from DDragon.
- **Scoring Breakdown:**
  - Score: (E:7 x 0.4) + (F:4 x 0.2) + (C:6 x 0.25) + (R:6 x 0.15) = 6.00
  - Confidence: Medium
- **[Inference]** Can manage external asset synchronization and storage.

### Add Omnibar Command
- **Description:** Register a new command in the Ctrl+K omnibar command palette.
- **Scoring Breakdown:**
  - Score: (E:6 x 0.4) + (F:4 x 0.2) + (C:5 x 0.25) + (R:6 x 0.15) = 5.35
  - Confidence: Low
- **[Inference]** Able to extend global command palette logic efficiently.

### Build Installer
- **Description:** Compile the Inno Setup installer for LeagueLoop distribution.
- **Scoring Breakdown:**
  - Score: (E:6 x 0.4) + (F:3 x 0.2) + (C:6 x 0.25) + (R:5 x 0.15) = 5.25
  - Confidence: Low
- **[Inference]** Capable of generating deployment installers from build outputs.
## Gap Analysis
- **Missing CI/CD Automation:** While `Build Executable` and `Build Installer` skills exist, they are manual processes.
- **Limited Cross-Platform Testing:** Advanced UI Mock testing focuses on Linux via `xvfb-run`; capability on Windows `windnd` and macOS is untested.
- **Accessibility Support:** The project requires explicit WCAG checks and structural keyboard-first paradigms.
- **UI State Snapshot Testing:** While kwargs instantiation is tested, verifying deep UI state correctness after complex interactions remains a gap.

## Skill Recommendations
- **Learn CI/CD Automation:** Implement GitHub Actions to automate the `Build Executable` and `Build Installer` steps to eliminate manual building and reduce friction in deployments.
- **Expand Test Matrix:** Add multi-os test matrices to GitHub Actions to verify CustomTkinter implementations across diverse environments.
- **Study CustomTkinter Accessibility:** Explore capabilities to implement screen-reader support and improve semantic layout.
- **Implement Snapshot Testing:** Add capabilities to capture and verify CustomTkinter widget hierarchies and visual states during automated tests.
