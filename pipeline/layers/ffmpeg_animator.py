import os
import subprocess

def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def _create_synced_ass_subtitles(scenes: list, ass_path: str, is_short: bool):
    play_x, play_y = (1080, 1920) if is_short else (1920, 1080)
    font_size = 56 if is_short else 46
    margin_v = 260 if is_short else 75

    # BorderStyle=1 (Clean cinema outline + drop shadow, NO ugly solid black rectangle box behind text!)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Liberation Sans,{font_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,3,2,50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    cursor = 0.0
    for sc in scenes:
        dur = float(sc.get("duration_sec", 5.0))
        narration = sc.get("narration", "")
        words = narration.split()
        # 4 words at a time for crisp, fast @Lullorin / @NightoraVideos pacing
        chunks = [" ".join(words[i:i+4]) for i in range(0, len(words), 4)] or ["FOLLOW THE RULES"]
        chunk_dur = dur / len(chunks)
        for ch in chunks:
            st = _format_ass_time(cursor)
            et = _format_ass_time(cursor + chunk_dur)
            safe_txt = ch.replace("{", "").replace("}", "")
            lines.append(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{{\\fad(60,60)}}{safe_txt}")
            cursor += chunk_dur

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def render_master_video(scenes: list, audio_path: str, total_duration: float, output_mp4: str, orientation="16:9"):
    os.makedirs("output/clips", exist_ok=True)
    os.makedirs(os.path.dirname(output_mp4) or "output", exist_ok=True)
    is_short = (orientation == "9:16")
    w, h = (1080, 1920) if is_short else (1920, 1080)
    scale_w = 1400 if is_short else 2400
    fps = 24

    clip_files = []

    for idx, sc in enumerate(scenes):
        img_path = sc["image_path"]
        dur = max(float(sc.get("duration_sec", 5.0)), 2.5)
        frames = int(dur * fps)
        clip_out = f"output/clips/clip_{orientation.replace(':', 'x')}_{idx+1}.mp4"

        motion = sc.get("motion", "zoom_in_slow" if idx % 2 == 0 else "zoom_out_slow")
        if "in" in motion:
            z_expr = "min(zoom+0.0008,1.16)"
        else:
            z_expr = "if(eq(on,1),1.16,max(1.0,zoom-0.0008))"

        vf = (
            f"scale={scale_w}:-2,"
            f"zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},"
            f"format=yuv420p"
        )
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-vf", vf, "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", clip_out
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_files.append(clip_out)

    v_list = f"output/clips/v_list_{orientation.replace(':', 'x')}.txt"
    with open(v_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c)}'\n")
    stitched_v = f"output/clips/stitched_{orientation.replace(':', 'x')}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_list, "-c", "copy", stitched_v
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ass_path = f"output/clips/subs_{orientation.replace(':', 'x')}.ass"
    _create_synced_ass_subtitles(scenes, ass_path, is_short)

    # Pure deep dark ambient sub-bass pad (42Hz + 63Hz) + Crisp Voiceover (NO cheesy electronic beeps!)
    subprocess.run([
        "ffmpeg", "-y",
        "-i", stitched_v,
        "-i", audio_path,
        "-f", "lavfi", "-i", f"sine=frequency=42:duration={total_duration:.2f}",
        "-f", "lavfi", "-i", f"sine=frequency=63:duration={total_duration:.2f}",
        "-filter_complex",
        f"[2:a]volume=0.04[sub1];[3:a]volume=0.025[sub2];[1:a][sub1][sub2]amix=inputs=3:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout];[0:v]ass={ass_path}[vout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", output_mp4
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_mp4
