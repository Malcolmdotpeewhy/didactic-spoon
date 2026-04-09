"""Capture the current lobby's queue ID from the League Client."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from services.api_handler import LCUClient

lcu = LCUClient()
if not lcu.connect():
    print("ERROR: Could not connect to League Client. Is it running?")
    sys.exit(1)

print("Connected to LCU. Polling lobby for queue ID...")
print("Queue up for Brawl now! (polling every 2s for 60s)\n")

for i in range(30):
    try:
        resp = lcu.request("GET", "/lol-lobby/v2/lobby")
        if resp and resp.status_code == 200:
            data = resp.json()
            gc = data.get("gameConfig", {})
            q_id = gc.get("queueId")
            q_type = gc.get("gameMode", "?")
            q_name = gc.get("queueType", data.get("type", "?"))
            map_id = gc.get("mapId", "?")
            print(f"  LOBBY DETECTED:")
            print(f"    queueId  = {q_id}")
            print(f"    gameMode = {q_type}")
            print(f"    mapId    = {map_id}")
            print(f"    type     = {q_name}")
            print(f"\n  >>> Brawl Queue ID is: {q_id} <<<")
            sys.exit(0)
        else:
            print(f"  [{i+1}/30] No lobby yet...")
    except Exception as e:
        print(f"  [{i+1}/30] Error: {e}")
    time.sleep(2)

print("\nTimed out. No lobby detected in 60 seconds.")
