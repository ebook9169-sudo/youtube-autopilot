import os
import asyncio
import subprocess
import requests
import edge_tts
from gtts import gTTS
from pipeline.key_rotator import rotator

def get_audio_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        out = subprocess.check_output(cmd).decode("utf-8").strip()
        return max(float(out), 4.0)
    except Exception:
        return 7.0

async def _edge_tts_save(text: str, out_file: str):
    # MoneyPrinterTurbo's Free Neural Voice tuned for Dark American Storytelling
    communicate = edge_tts.Communicate(
        text,
        voice="en-US-ChristopherNeural",
        rate="-4%",
        pitch="-8Hz"
    )
    await communicate.save(out_file)

def _synthesize_single_scene(text: str, out_file: str) -> bool:
    clean_text = text.strip()
    # 1. Try ElevenLabs Free API (Part-by-Part for high consistency)
    el_key = rotator.get_key("ELEVENLABS_KEY")
    if el_key:
        try:
            voice_id = "JBFqnCBsd6RMkjVDRZzb"  # George - Dark Suspense Storyteller
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {"xi-api-key": el_key, "Content-Type": "application/json"}
            payload = {
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.60, "similarity_boost": 0.82, "style": 0.35}
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                return True
        except Exception as e:
            print(f"[Voice] ElevenLabs scene fallback: {e}")

    # 2. Try MoneyPrinterTurbo's Free Edge-TTS (Deep Pitch)
    try:
        asyncio.run(_edge_tts_save(clean_text, out_file))
        if os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return True
    except Exception as e:
        print(f"[Voice] Edge-TTS fallback: {e}")

    # 3. Emergency gTTS Fallback
    tts = gTTS(text=clean_text, lang="en", slow=False)
    tts.save(out_file)
    return True

def generate_voiceover(scenes: list, output_audio_path: str) -> tuple:
    os.makedirs("output/voice_parts", exist_ok=True)
    os.makedirs(os.path.dirname(output_audio_path) or "output", exist_ok=True)

    part_files = []
    scene_durations = []

    print(f"[Voice] Generating Part-by-Part Voiceover across {len(scenes)} scenes...")
    for idx, scene in enumerate(scenes):
        part_path = f"output/voice_parts/scene_{idx+1}.mp3"
        narration = scene.get("narration", "Follow this rule carefully.")
        _synthesize_single_scene(narration, part_path)
        dur = get_audio_duration(part_path)
        scene["duration_sec"] = round(dur, 2)
        scene_durations.append(dur)
        part_files.append(part_path)

    # Concatenate all scene voice parts seamlessly using FFmpeg
    concat_list_path = "output/voice_parts/concat_list.txt"
    with open(concat_list_path, "w") as f:
        for p in part_files:
            f.write(f"file '{os.path.abspath(p)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list_path, "-c", "copy", output_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    total_duration = sum(scene_durations)
    return output_audio_path, total_duration
