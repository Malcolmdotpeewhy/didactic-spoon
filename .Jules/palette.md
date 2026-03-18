## 2024-05-19 - Tooltips for CustomTkinter Apps
**Learning:** CustomTkinter apps don't support web-based verification tools like Playwright. Adding tooltips to icon-only buttons significantly improves accessibility but requires custom implementations or manual visual verification in this desktop environment.
**Action:** Always import `CTkTooltip` from `ui.ui_shared` instead of internal paths, and use Python unit tests for basic structural validation of UI enhancements rather than trying to use web tools.

## 2024-05-20 - CustomTkinter Button Interaction Cursors
**Learning:** CustomTkinter `CTkButton` components do not change the mouse cursor to a hand/pointer when hovered by default, unlike standard web behaviors. This leads to a lack of visual feedback for interactive elements.
**Action:** When implementing new `CTkButton` components or variants, always explicitly configure them with `cursor="hand2"` during initialization to ensure consistent and intuitive visual interaction cues for the user.