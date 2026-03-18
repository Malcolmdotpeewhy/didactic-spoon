from services.api_handler import LCUApiHandler
import json

lcu = LCUApiHandler()
if not lcu.connect():
    print("Cannot connect.")
    exit(1)

tests = [
    {"queueId": 450},
    {"queueId": "450"},
    {"gameConfig": {"queueId": 450}},
    {"gameCustomization": {}, "isCustom": False, "queueId": 450}
]

for payload in tests:
    print(f"Testing payload: {payload}")
    res = lcu.request("POST", "/lol-lobby/v2/lobby", data=payload)
    if res:
        print(f"Status: {res.status_code}")
        try:
            print(f"Response: {res.json()}")
        except:
            print(f"Response: {res.text}")
    print("-" * 50)
