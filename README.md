# LeagueLoop

A powerful, automated tool for your League of Legends client experience.
LeagueLoop sits in your system tray and interacts with the League Client Update (LCU) API to automate tedious pre-game tasks like accepting matches, calling roles, picking champions, and sending custom chat commands.

## Features

- **Auto-Join**: Automatically accepts friend requests or joins lobbies when invited by priority friends.
- **Auto-Accept Match**: Automatically clicks the "Accept" button when a match is found.
- **Champion Sniper**: Instantly hovers or locks in your preferred champion during Champion Select based on priority queues.
- **Spell & Rune Automation**: Equips preferred summoner spells automatically.
- **Omnibar (Ctrl+K)**: Quick, global command palette for interacting with the application.
- **Customizable UI**: Built with CustomTkinter for a sleek, dark-themed experience.

## Setup

1. **Requirements**: Python 3.10+
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

To run LeagueLoop in development mode:
```bash
launch_dev.bat
```
*(Or manually: `set PYTHONPATH=%CD%\src && python run.py`)*

## Building the Executable

To compile the application into a single standalone Windows executable using PyInstaller:
```bash
build.bat
```
*(The executable will be located in the `dist/LeagueLoop/` directory).*

## Creating the Installer

LeagueLoop uses **Inno Setup** to package the built executable into an installer.
1. Download and install [Inno Setup](https://jrsoftware.org/isinfo.php).
2. Right click `installer.iss` and click **Compile**.
3. The final installer will be located in the `dist/` directory as `LeagueLoop_Installer.exe`.

## Repository Structure

- `src/core/` - Core engine and application entry point
- `src/services/` - Subsystems like automation logic, LCU API handler, and asset manager
- `src/ui/` - The CustomTkinter graphical interface and layout modules
- `src/utils/` - Utility functions for environment paths and logging
- `tests/` - Application test suite
- `build.bat` - Script for compiling the executable
- `installer.iss` - Inno script for installer generation
