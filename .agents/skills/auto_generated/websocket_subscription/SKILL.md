---
name: Subscribe to LCU WebSocket Event
description: Auto-generated skill for registering and managing zero-overhead push notifications from the League Client via WebSockets instead of HTTP polling.
---

# Subscribe to LCU WebSocket Event

## Context
LeagueLoop uses a centralized `LCUClient` that maintains a background WAMP thread for WebSocket push notifications from the League UX API. Use this skill whenever a new LCU event must be tracked efficiently.

## Prerequisites
- Target API event URI must be a valid WAMP `OnJsonApiEvent_X` formatted string. 
- Example: `/lol-lobby/v2/lobby` becomes `OnJsonApiEvent_lol-lobby_v2_lobby` 

## Implementation Steps

### 1. In `api_handler.py` (Orchestrator)
Ensure `_server_subscribe` and the background thread can process the URI event array. This is already implemented.

### 2. In `automation.py` (`start` method)
Register the subscription immediately after `self.lcu.start_websocket()`:
```python
self.lcu.subscribe("OnJsonApiEvent_your_api_path_here", self._on_ws_event)
```

### 3. Handle Thread Wake-up
The `_on_ws_event` handler internally triggers `self._wake_event.set()`, instantly waking the main polling loop out of its sleep state so it can process the new data immediately with low UI frame blocking.

## Output
No return value. The system will now awake efficiently to track the event asynchronously.
