import time
import psutil

client_procs = ["LeagueClientUx.exe", "LeagueClient.exe"]
highest_priority = client_procs[0]

def test_without_attrs():
    start = time.time()
    found_procs = {}
    for p in psutil.process_iter():
        try:
            name = p.name()
            if name in client_procs:
                found_procs[name] = p
                if name == highest_priority:
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return time.time() - start

def test_with_attrs():
    start = time.time()
    found_procs = {}
    for p in psutil.process_iter(attrs=['name']):
        try:
            name = p.info['name']
            if name in client_procs:
                found_procs[name] = p
                if name == highest_priority:
                    break
        except Exception:
            continue
    return time.time() - start

# warm up
test_without_attrs()
test_with_attrs()

# measure
t1 = sum(test_without_attrs() for _ in range(100)) / 100
t2 = sum(test_with_attrs() for _ in range(100)) / 100

print(f"Without attrs: {t1:.4f}s")
print(f"With attrs: {t2:.4f}s")
