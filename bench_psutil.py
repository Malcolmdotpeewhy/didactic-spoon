import time
import psutil
import sys

def bench_without_attrs():
    start = time.time()
    for _ in range(100):
        found = 0
        for p in psutil.process_iter():
            try:
                name = p.name()
                if name == "LeagueClient.exe":
                    found += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    return time.time() - start

def bench_with_attrs():
    start = time.time()
    for _ in range(100):
        found = 0
        for p in psutil.process_iter(attrs=['name']):
            try:
                name = p.info['name']
                if name == "LeagueClient.exe":
                    found += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, KeyError):
                continue
    return time.time() - start

print(f"Without attrs (p.name()): {bench_without_attrs():.4f}s")
print(f"With attrs (p.info['name']): {bench_with_attrs():.4f}s")
