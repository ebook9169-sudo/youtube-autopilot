import os

def get_keys(prefix: str) -> list:
    keys = []
    for suffix in ["_1", "_2", ""]:
        val = os.environ.get(f"{prefix}{suffix}", "").strip()
        if val and val not in keys:
            keys.append(val)
    return keys

def run_with_failover(prefix: str, func, *args, **kwargs):
    keys = get_keys(prefix)
    if not keys:
        raise RuntimeError(f"No keys for {prefix}")
    last_err = None
    for idx, key in enumerate(keys, start=1):
        try:
            print(f"🔑 [{prefix}] Using Account #{idx}...")
            return func(key, *args, **kwargs)
        except Exception as e:
            print(f"⚠️ [{prefix}] Account #{idx} limit reached ({e}). Switching to Account #2...")
            last_err = e
    raise RuntimeError(f"All accounts exhausted: {last_err}")
