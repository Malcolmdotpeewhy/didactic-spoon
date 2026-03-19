## 2024-05-18 - Tooltips for Context
**Learning:** Some custom UI widgets like `LolToggle` don't inherit basic accessibility properties naturally. Additionally, toggle descriptions like "Auto Accept" can be ambiguous without supplementary context. Binding `CTkTooltip` to adjacent label widgets provides a clean, native-feeling way to add descriptive hints without cluttering the visual layout.
**Action:** Always verify if newly added or custom toggles/switches require tooltips to explain their effects. Bind tooltips to both the interactive element and its descriptive label for better usability.
