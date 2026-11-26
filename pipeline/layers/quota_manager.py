from pipeline.key_rotator import get_keys
import requests

def check_elevenlabs_remaining_chars() -> int:
    total = 0
    for key in get_keys("ELEVENLABS_KEY"):
        try:
            r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": key}, timeout=15)
            if r.status_code == 200:
                sub = r.json()
                total += max(0, sub.get("character_limit", 0) - sub.get("character_count", 0))
        except Exception:
            pass
    return total

def decide_production_plan() -> dict:
    has_keys = len(get_keys("GEMINI_KEY")) > 0 or len(get_keys("ELEVENLABS_KEY")) > 0
    el_chars = check_elevenlabs_remaining_chars() if has_keys else 0
    return {
        "keyless_test_mode": not has_keys,
        "elevenlabs_remaining_chars": el_chars,
        "produce_long_16x9": True,
        "produce_short_9x16": True,
        "long_voice_tier": "ELEVENLABS_PRO" if el_chars >= 1800 else "STUDIO_NEURAL_FREE",
        "short_voice_tier": "ELEVENLABS_PRO" if el_chars >= 500 else "STUDIO_NEURAL_FREE"
    }
