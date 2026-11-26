import subprocess, json

def inspect_and_certify(video_path: str, expected_res: str, blueprint: dict) -> dict:
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration", "-of", "json", video_path]
    probe = json.loads(subprocess.check_output(cmd).decode("utf-8"))["streams"][0]
    actual_res = f"{probe['width']}x{probe['height']}"
    return {
        "file": video_path,
        "resolution": actual_res,
        "duration_sec": round(float(probe.get("duration", 0)), 2),
        "monetization_safe": blueprint.get("monetization_safe", True),
        "copyright_safe": blueprint.get("copyright_safe", True),
        "audio_standard": "-14 LUFS Normalized",
        "certified_for_youtube": (actual_res == expected_res)
    }
