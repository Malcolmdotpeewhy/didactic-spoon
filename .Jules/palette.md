## 2024-05-18 - Tooltips for Context
**Learning:** Some custom UI widgets like `LolToggle` don't inherit basic accessibility properties naturally. Additionally, toggle descriptions like "Auto Accept" can be ambiguous without supplementary context. Binding `CTkTooltip` to adjacent label widgets provides a clean, native-feeling way to add descriptive hints without cluttering the visual layout.
**Action:** Always verify if newly added or custom toggles/switches require tooltips to explain their effects. Bind tooltips to both the interactive element and its descriptive label for better usability.

## 2024-05-20 - Game Mode Selector Tooltip
**Learning:** Dropdowns without explicit labels or tooltips can leave users guessing their purpose. Adding a tooltip ensures clarity and accessibility.
**Action:** Add tooltips to all interactive elements, including option menus, to provide context and improve usability.

## 2024-05-24 - Tooltips for Icon-Only Buttons in Lists
**Learning:** Icon-only buttons (like an "✕" for delete or dynamic names for launch) within dynamically rendered lists, such as the Account Switcher, are not inherently accessible. Without tooltips, screen readers and users may struggle to understand their function.
**Action:** Ensure all icon-only buttons, especially those generated in loops or lists, have descriptive tooltips attached to clarify their specific action and context.

## 2024-05-25 - Tooltips for Contextual Buttons
**Learning:** Standard action buttons like "Requeue" and "Dodge" can have ambiguous outcomes or lack affordance, particularly when nested alongside unrelated functions. Furthermore, buttons using standard system styling may not inherently indicate their clickability.
**Action:** Add descriptive tooltips to action buttons to clarify their specific intent ("Force quit the client to dodge the lobby"). Always ensure interactive elements explicitly set `cursor="hand2"` to provide native-feeling hover affordance.
