import os, asyncio, subprocess, edge_tts, mutagen.mp3
from gtts import gTTS

async def _tts_chunk(text: str, out_mp3: str):
    comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="-4%", pitch="-6Hz")
    with open(out_mp3, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
    if not os.path.exists(out_mp3) or os.path.getsize(out_mp3) < 1000:
        raise RuntimeError("Empty chunk")

def generate_section_by_section_voice(scenes: list, prefix: str) -> list:
    """Generates voiceover PART-BY-PART (Scene by Scene) for maximum suspense & exact visual sync!"""
    os.makedirs(f"output/audio_{prefix}", exist_ok=True)
    scene_audio_info = []
    for i, sc in enumerate(scenes):
        chunk_mp3 = f"output/audio_{prefix}/part_{i:02d}.mp3"
        txt = sc["voice"]
        try:
            asyncio.run(_tts_chunk(txt, chunk_mp3))
        except Exception:
            gTTS(text=txt, lang="en", slow=False).save(chunk_mp3)
        dur = max(4.0, mutagen.mp3.MP3(chunk_mp3).info.length + 0.45)
        scene_audio_info.append({"audio_path": chunk_mp3, "duration": dur, "text": txt})
    return scene_audio_info
