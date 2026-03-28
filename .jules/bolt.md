## 2024-05-24 - String manipulation overhead in UI event loops
**Learning:** High-frequency event handlers like keyboard typing (`_on_key`, `_on_search`) suffer from significant UI thread latency if they perform string manipulations (like `.lower()`) inside loops iterating over O(N) items.
**Action:** Pre-compute and cache normalized string lists or tuples during initialization or data-fetch to eliminate runtime string allocation overhead in these hot-paths.

## 2024-06-03 - O(N^2) list membership checks during drag-and-drop
**Learning:** Checking membership against a list during drag-and-drop operations causes O(N^2) time complexity, leading to severe UI thread stalls when dropping large lists.
**Action:** Pre-convert list comprehensions into sets (Hash Maps) before iterating over dropped items to achieve O(1) membership checks.
