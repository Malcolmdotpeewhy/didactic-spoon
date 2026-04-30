---
name: Extract UI Component
description: Auto-generated skill for extracting inline UI elements (like tab bars or dividers) from complex layouts into standalone reusable customtkinter components.
---

# Extract UI Component

## Inputs
- Complex parent UI file (e.g. `app_sidebar.py`)
- Inline UI logic to extract (e.g. `tab_frame` and `_switch_tab`)

## Outputs
- Standalone component file in `src/ui/components/`
- Refactored parent UI file utilizing the new component

## Steps
1. Identify the inline logic and state bindings in the parent file.
2. Create a new subclass of `ctk.CTkFrame` in `src/ui/components/`.
3. Move the internal widget creation (`ctk.CTkButton`, etc.) into the `__init__` of the new class.
4. Pass any necessary callbacks via a `command` argument.
5. In the parent file, replace the inline logic with the instantiation of the new component.
6. Verify layout via `.pack()` or `.grid()` methods.

## Dependencies
- `customtkinter`
- `ui.components.factory` (for token styling)
