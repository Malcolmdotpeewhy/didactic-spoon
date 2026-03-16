## 2024-05-19 - Tooltips for CustomTkinter Apps
**Learning:** CustomTkinter apps don't support web-based verification tools like Playwright. Adding tooltips to icon-only buttons significantly improves accessibility but requires custom implementations or manual visual verification in this desktop environment.
**Action:** Always import `CTkTooltip` from `ui.ui_shared` instead of internal paths, and use Python unit tests for basic structural validation of UI enhancements rather than trying to use web tools.
