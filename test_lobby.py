from services.api_handler import LCUApiHandler
import json

lcu = LCUApiHandler()
if lcu.connect():
    print("Connected")
    res = lcu.request("POST", "/lol-lobby/v2/lobby", data={"queueId": 450})
    if res:
        print(f"Status: {res.status_code}")
        print(f"Text: {res.text}")
    else:
        print("No response")
else:
    print("Not connected")
