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

## 2026-04-10 - Fast-Path Dictionary Lookups
**Learning:** For tight-loop string-based dictionary lookups (e.g., parsing UI design tokens), checking for dots and unconditionally splitting (`.split('.')`) allocates lists unnecessarily.
**Action:** Provide an EAFP (`try...except (KeyError, TypeError)`) fast-path for the most common input format that attempts direct lookup first, skipping intermediate list allocations and heavy string parsing to significantly reduce execution overhead.

## 2026-04-15 - Token Loader Inner Loop
**Learning:** The core token loader resolution function `_get_memoized` previously fell back to iterating a `keys` tuple with `isinstance` checks, even when most keys were single strings like `"colors.background.app"`. Also, `isinstance` is slower than `type() is`.
**Action:** Created an EAFP fast path for single-string key tuples `if len(keys) == 1 and type(keys[0]) is str:`, skipping the general loop and avoiding double dictionary lookups. This improves cold-path token lookups by nearly 2x (from 0.28s to 0.15s per 100k hits).

## 2024-06-25 - O(1) early-return optimization in Champ Select sniper
**Learning:** The `_perform_priority_sniper` function previously iterated over the bench champions and checked their index in the priority list. Building the priority list lookup map and evaluating every bench champion was slower than indexing the small bench and walking down the sorted priority list.
**Action:** Reverse the lookup relationship: index the small bench (O(1) lookup), then iterate down the sorted priority list. The first priority champion found on the bench is mathematically guaranteed to be the best, allowing an instant early-return break without further iteration.
