## 2024-05-23 - Custom Canvas Components Lack Default Accessibility
**Learning:** Custom interactive components built on low-level primitives like `tk.Canvas` lack standard button accessibility behaviors out of the box. They do not accept keyboard focus or respond to keyboard events (like Space or Enter) by default, completely blocking screen-reader and keyboard-only users.
**Action:** When using custom UI primitives (like `LolToggle` on a Canvas), explicitly enforce `takefocus=1`, implement `<FocusIn>` and `<FocusOut>` visual indicators, and map `<KeyPress-space>` and `<Return>` to the primary toggle/click handler to ensure full keyboard navigation parity with native buttons.

## 2024-05-24 - Input Cursor Usability
**Learning:** In Tkinter/CustomTkinter setups, custom text entry fields (`CTkEntry`) do not automatically inherit the standard "I-beam" text cursor upon hover. This creates a confusing experience as users expect clear visual feedback indicating that a field is interactive and ready for text input.
**Action:** When instantiating `CTkEntry` widgets, explicitly assign `cursor="xterm"` to ensure the correct OS-level I-beam cursor appears on hover, maintaining standard input affordance.
