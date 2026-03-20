
## 2024-05-20 - Frictionless Context Switching via Inline Modals and Macro Injection

**Learning:** When navigating between multiple digital identities (accounts) in a restrictive ecosystem (like Riot Client), creating a distinct "Login Screen" introduces cognitive friction and breaks application momentum. Inline credential management combined with asynchronous macro injection (e.g., auto-typing) bridges the gap between secure local storage and closed systems without requiring complex API circumventions.

**Action:** For closed-loop client launchers that lack API support, manage authentication state visually within the primary interaction context (e.g., the sidebar). Use simple, deterministic macro sequences executed on a background thread (`daemon=True`) to maintain the application's responsiveness (The 100ms Law) while bridging the systemic gap.
