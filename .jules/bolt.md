## 2024-05-24 - String manipulation overhead in UI event loops
**Learning:** High-frequency event handlers like keyboard typing (`_on_key`, `_on_search`) suffer from significant UI thread latency if they perform string manipulations (like `.lower()`) inside loops iterating over O(N) items.
**Action:** Pre-compute and cache normalized string lists or tuples during initialization or data-fetch to eliminate runtime string allocation overhead in these hot-paths.

## 2024-06-03 - O(N^2) list membership checks during drag-and-drop
**Learning:** Checking membership against a list during drag-and-drop operations causes O(N^2) time complexity, leading to severe UI thread stalls when dropping large lists.
**Action:** Pre-convert list comprehensions into sets (Hash Maps) before iterating over dropped items to achieve O(1) membership checks.

## 2024-06-15 - Loop Invariant Code Motion (LICM) for CustomTkinter Render Loops
**Learning:** In CustomTkinter applications, repetitive static token lookups like `get_color` or `get_font` inside UI render loops (e.g., populating a dropdown or rendering a list) cause unnecessary string parsing overhead and micro-allocations on the main thread, leading to potential stuttering.
**Action:** Apply Loop Invariant Code Motion (LICM) to hoist static function calls and repetitive string manipulations outside of iteration loops to avoid redundant recalculations for every rendered element.
## 2026-03-29 - O(1) Tkinter Widget Updates
**Learning:** Iterating over O(N) widgets to call `.configure()` or forcing synchronous layout recalculations with `update_idletasks()` during high-frequency keyboard navigation causes severe UI thread blocking in Tkinter/CustomTkinter.
**Action:** Pass an `old_index` to update only the specific delta (O(1)) and defer `update_idletasks()` away from hot-paths.
## 2024-06-25 - Eager Initialization vs Lazy Caching in Event Loops
**Learning:** Lazy initialization of string caches (like `if "_search_target" not in cmd:`) inside UI event loops still incurs dictionary check and mutation overhead on the hot path, causing micro-stutters during rapid typing.
**Action:** Move cache normalization entirely upstream to the data-fetch or UI initialization phase to achieve pure O(1) lookups in the hot path.
