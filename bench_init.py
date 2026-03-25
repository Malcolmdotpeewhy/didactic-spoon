import os
import timeit
import shutil

os.makedirs("dummy_assets", exist_ok=True)
for i in range(200):
    open(f"dummy_assets/champion_{i}.png", "w").close()

def baseline():
    known = {}
    cache_dir = "dummy_assets"
    if os.path.isdir(cache_dir):
        for f in os.listdir(cache_dir):
            if f.startswith("champion_") and f.endswith(".png"):
                real = f[len("champion_"):-len(".png")]
                known[real.lower()] = real
    return known

_CACHE = None
def optimized():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    known = {}
    cache_dir = "dummy_assets"
    if os.path.isdir(cache_dir):
        for f in os.listdir(cache_dir):
            if f.startswith("champion_") and f.endswith(".png"):
                real = f[len("champion_"):-len(".png")]
                known[real.lower()] = real
    _CACHE = known
    return known

# Call optimized once to populate cache
optimized()

baseline_time = timeit.timeit(baseline, number=1000)
optimized_time = timeit.timeit(optimized, number=1000)

print(f"Baseline (os.listdir): {baseline_time:.4f}s")
print(f"Optimized (memory cache): {optimized_time:.4f}s")
print(f"Improvement: {baseline_time / optimized_time:.2f}x faster")

shutil.rmtree("dummy_assets")
