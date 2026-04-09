import time
import sys
from unittest.mock import MagicMock

# Mock psutil
mock_psutil = MagicMock()
sys.modules['psutil'] = mock_psutil

# We just measure the mock overhead for the sake of the benchmark step
import psutil

class MockProcess:
    def __init__(self, name):
        self._name = name
        self.info = {'name': name}

    def name(self):
        # Simulate expensive call
        time.sleep(0.0001)
        return self._name

def process_iter_mock(attrs=None):
    return [MockProcess(f"proc_{i}") for i in range(1000)]

psutil.process_iter = process_iter_mock

client_procs = ["LeagueClientUx.exe", "LeagueClient.exe"]

def test_without_attrs():
    start = time.time()
    for p in psutil.process_iter():
        try:
            name = p.name()
            if name in client_procs:
                pass
        except Exception:
            continue
    return time.time() - start

def test_with_attrs():
    start = time.time()
    for p in psutil.process_iter(attrs=['name']):
        try:
            name = p.info['name']
            if name in client_procs:
                pass
        except Exception:
            continue
    return time.time() - start

t1 = test_without_attrs()
t2 = test_with_attrs()

print(f"Without attrs: {t1:.4f}s")
print(f"With attrs: {t2:.4f}s")
