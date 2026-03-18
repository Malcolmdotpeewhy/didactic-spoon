url = f\\" https://127.0.0.1: -encodedCommand cABvAHIAdAA= "/lol-lobby/v2/lobby\  
import base64
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOCKFILE = r"C:\Users\Administrator\Riot Games\League of Legends\lockfile"
try:
    with open(LOCKFILE, 'r') as f:
        data = f.read().split(':')
    port = data[2]
    token = data[3]
except Exception as e:
    exit(1)

auth = base64.b64encode(f"riot:{token}".encode()).decode()
headers = {
url = f"https://127.0.0.1:{port}/lol-lobby/v2/lobby"
import time

print("\n--- Phase 1: Clear Search ---")
res = requests.delete(f"https://127.0.0.1:{port}/lol-lobby/v2/lobby/matchmaking/search", headers=headers, verify=False)
print("Status:", res.status_code)

print("\n--- Phase 2: Check & Delete Lobby ---")
lobby_req = requests.get(url, headers=headers, verify=False)
print("GET Lobby:", lobby_req.status_code)
in_lobby = lobby_req.status_code == 200

if in_lobby:
    print("Deleting lobby...")
    res = requests.delete(url, headers=headers, verify=False)
    print("DEL Lobby:", res.status_code)
    time.sleep(0.5)

print("\n--- Phase 3: Create Lobby ---")
res = requests.post(url, json={"queueId": 2400}, headers=headers, verify=False)
print("POST Lobby Status:", res.status_code)
print("Response:", res.text)

print("\n--- Phase 4: Start Search ---")
search_url = f"https://127.0.0.1:{port}/lol-lobby/v2/lobby/matchmaking/search"
res2 = requests.post(search_url, headers=headers, verify=False)
print("POST Search Status:", res2.status_code)
print("Response:", res2.text)
