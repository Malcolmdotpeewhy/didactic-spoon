## 2024-05-15 - Missing hover affordances on buttons
**Learning:** In CustomTkinter applications, custom `CTkButton` components and elements acting as buttons often lack standard hover affordances. Without `cursor="hand2"`, users don't get immediate feedback that an element is clickable, leading to poor accessibility.
**Action:** Always apply `cursor="hand2"` to interactive elements to ensure clear click/drag usability.
## 2024-03-28 - CTkOptionMenu Affordances
**Learning:** In CustomTkinter, `CTkOptionMenu` components (dropdowns) do not automatically provide a change in the cursor (e.g., to a pointing hand) when hovered, unlike standard web buttons or links. This omission can make it slightly less obvious that the element is clickable and interactive, particularly when styled to blend into the application background.
**Action:** Always ensure `cursor="hand2"` is explicitly passed to `CTkOptionMenu` instances alongside other interactive widgets like `CTkButton` to maintain clear affordance and consistent visual UX cues across the application.
## 2024-05-18 - RiotButton Affordance
**Learning:** In CustomTkinter, custom components that behave as interactive buttons (like `RiotButton`, built by composing `CTkFrame` and `CTkLabel`) lack standard hover affordances. The mouse cursor does not naturally change to a pointing hand, which reduces the immediate visual cue that the element is clickable.
**Action:** Always manually apply `cursor="hand2"` to the parent frame and all its relevant inner composite components to maintain clear and accessible clickability affordances.
## 2026-03-29 - Interactive Label Affordances
**Learning:** In CustomTkinter, `CTkLabel` elements acting as buttons or toggles (like collapsible section headers) do not inherently provide hover affordances. Without explicitly setting `cursor="hand2"` and text color hover states, users lack the visual cue that the element is interactive.
**Action:** Always apply explicit cursor and hover color bindings to interactive labels to ensure accessibility and intuitive UX.
## 2024-05-19 - Keyboard Shortcut Discoverability
**Learning:** Users often miss global hotkeys because they are hidden within the settings menu. Adding dynamic keyboard shortcut hints directly to the tooltips of corresponding UI buttons significantly improves hotkey discoverability and overall keyboard accessibility without cluttering the main interface.
**Action:** Always append keyboard shortcut hints (e.g., `(CTRL+SHIFT+X)`) to the tooltips of interactive elements that are bound to global hotkeys.

## 2024-03-31 - Actionable Configuration Errors
**Learning:** Generic error states like "Invalid" in configuration inputs (like HotkeyRecorder) fail to provide guidance. Users need to know *why* it failed (e.g., only modifiers were pressed).
**Action:** Always provide actionable micro-copy (e.g., "! Needs a key") and sufficient display duration (1200ms) for temporary error states.
## 2026-03-31 - Keyboard Accessibility on CustomTkinter Settings
**Learning:** High-density configuration modals using CustomTkinter buttons for hotkey recording severely limit keyboard users because they lack default focus rings and space/enter activation.
**Action:** Explicitly bind <FocusIn>, <FocusOut>, <KeyPress-space>, and <KeyPress-Return> to interactive elements like HotkeyRecorder to guarantee WCAG-compliant keyboard operability.
