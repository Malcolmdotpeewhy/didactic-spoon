## 2024-05-24 - String manipulation overhead in UI event loops
**Learning:** High-frequency event handlers like keyboard typing (`_on_key`, `_on_search`) suffer from significant UI thread latency if they perform string manipulations (like `.lower()`) inside loops iterating over O(N) items.
**Action:** Pre-compute and cache normalized string lists or tuples during initialization or data-fetch to eliminate runtime string allocation overhead in these hot-paths.
