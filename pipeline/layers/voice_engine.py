import os, asyncio, requests, edge_tts
from gtts import gTTS
from pipeline.key_rotator import get_keys, run_with_failover

ADAM_VOICE_ID = "pNInz6obpgDQGcFmaJgB"

def _sec_to_ass(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def _build_ass_subtitles(words: list, out_ass: str, aspect="16:9"):
    res_x, res_y, f_size, margin_v, chunk = (1920, 1080, 58, 90, 5) if aspect == "16:9" else (1080, 1920, 82, 420, 2)
    header = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ProStyle,Liberation Sans,{f_size},&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,3,2,60,60,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines = [header.strip()]
    for i in range(0, len(words), chunk):
        grp = words[i:i+chunk]
        st_t = _sec_to_ass(grp[0]["start"])
        en_t = _sec_to_ass(max(grp[0]["start"] + 0.25, grp[-1]["end"]))
        txt = " ".join(w["word"].upper() for w in grp)
        anim = "{\fscx118\fscy118\t(0,110,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{st_t},{en_t},ProStyle,,0,0,0,,{anim}{txt}")
    open(out_ass, "w", encoding="utf-8").write("\n".join(lines))

async def _edge_studio_tts(text: str, out_audio: str):
    comm = edge_tts.Communicate(text, "en-US-ChristopherNeural", rate="+6%", pitch="-2Hz")
    words = []
    with open(out_audio, "wb") as f:
        async for ch in comm.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                st_s = ch["offset"] / 10_000_000
                dur_s = ch["duration"] / 10_000_000
                words.append({"word": ch["text"], "start": st_s, "end": st_s + dur_s})
    if not os.path.exists(out_audio) or os.path.getsize(out_audio) < 1000:
        raise RuntimeError("Edge TTS returned empty audio")
    return words

def generate_voice_and_subs(text: str, prefix: str, aspect="16:9", prefer_elevenlabs=True):
    os.makedirs("output", exist_ok=True)
    out_audio = f"output/{prefix}_voice.mp3"
    out_ass = f"output/{prefix}_subs.ass"
    words = []
    try:
        words = asyncio.run(_edge_studio_tts(text, out_audio))
    except Exception:
        gTTS(text=text, lang="en", slow=False).save(out_audio)

    if not words:
        raw_w = text.split()
        step = 24.0 / max(1, len(raw_w))
        words = [{"word": w, "start": i*step, "end": (i+1)*step} for i, w in enumerate(raw_w)]
    _build_ass_subtitles(words, out_ass, aspect=aspect)
    return out_audio, out_ass
