import os

class DualAccountKeyRotator:
    def __init__(self):
        self.counters = {}

    def get_key(self, prefix: str) -> str:
        k1 = os.environ.get(f"{prefix}_1", "").strip()
        k2 = os.environ.get(f"{prefix}_2", "").strip()
        single = os.environ.get(prefix, "").strip()

        valid_keys = [k for k in [k1, k2, single] if k and not k.startswith("YOUR_")]
        if not valid_keys:
            return ""

        idx = self.counters.get(prefix, 0)
        chosen = valid_keys[idx % len(valid_keys)]
        self.counters[prefix] = idx + 1
        return chosen

rotator = DualAccountKeyRotator()

def get_rotated_key(prefix: str) -> str:
    return rotator.get_key(prefix)
