## 2024-05-24 - Faster Queue Polling
**Learning:** In high-frequency polling loops (like CustomTkinter's `after` events running at ~16ms), the EAFP pattern `try: queue.get_nowait() except queue.Empty:` is surprisingly slower than `if not queue.empty(): queue.get_nowait()`. Raising and catching the exception thousands of times a second adds unnecessary overhead when the queue is frequently empty.
**Action:** Use `if not queue.empty():` check before `get_nowait()` in tight UI polling loops.
