## 2024-05-24 - Faster Queue Polling
**Learning:** In high-frequency polling loops (like CustomTkinter's `after` events running at ~16ms), the EAFP pattern `try: queue.get_nowait() except queue.Empty:` is surprisingly slower than `if not queue.empty(): queue.get_nowait()`. Raising and catching the exception thousands of times a second adds unnecessary overhead when the queue is frequently empty. However, always retain the `try...except queue.Empty` block around `get_nowait()` as a fallback since `queue.empty()` does not guarantee thread safety against interleaving.
**Action:** Use `if not queue.empty():` check before `get_nowait()` in tight UI polling loops, but keep the `try...except queue.Empty` around `get_nowait()` itself.

## 2024-06-12 - Fast Theme Token Resolution
**Learning:** The UI extensively calls helper functions like `get_color(path)` and `get_font(type)` to resolve design tokens. Deep dictionary lookups `TOKENS.get(...)` coupled with string parsing (`path.split('.')`) multiple times per widget creation and during hover/focus events introduces measurable latency in the main UI thread.
**Action:** Apply `@functools.lru_cache` to UI styling helper functions (`get_color`, `get_font`, `get_radius`, `parse_border`) to avoid repetitive string manipulations and dict lookups.

## 2024-06-25 - Avoid Dynamic Event Colors
**Learning:** Computing visual effect states (like string hex code lighten/darken math in `apply_click_animation`) dynamically *inside* event handler callbacks like `on_click(_)` introduces measurable string manipulation latency on the main UI thread during every interaction.
**Action:** Precompute standard event colors in the closure scope of effect binders instead of computing them on the fly during the interaction event itself.

## 2026-03-19 - Precompute Helper Lookups for Hover States
**Learning:** Calling complex styling helper functions like `get_color` and `parse_border` directly inside high-frequency UI event handlers like `on_enter` and `on_leave` adds measurable performance overhead and main thread latency (~40% slower) due to unnecessary redundant calculations for a static token.
**Action:** Precompute static color/border values outside the event handler definitions and reference the cached values within the closure to improve responsiveness of mouse interactions.
