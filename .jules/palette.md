## 2024-03-27 - Centralize Focus States with Factory Inputs
**Learning:** Hardcoding standard styling arguments (like `border_width`, `fg_color`) or instantiating core widgets directly (e.g., `ctk.CTkEntry` instead of `make_input`) bypasses the centralized design system. This leads to missing accessibility features, such as consistent focus-visible rings for keyboard navigation.
**Action:** When implementing new inputs, always prefer the `make_input` factory and omit hardcoded low-level styles to inherit standard focus handlers and UX defaults.
## 2024-05-15 - Add Hand Cursor Affordance to Custom Components
**Learning:** Custom interactive elements built on `tk.Canvas` or heavily styled `CTkFrame`/`CTkLabel` do not inherit standard OS cursor changes on hover, which removes critical affordance that an element is clickable/draggable.
**Action:** When creating custom interactive UI elements, explicitly bind `<Enter>` and `<Leave>` events to configure `cursor="hand2"` and `cursor=""` to restore this visual feedback.
