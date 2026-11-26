import os
import glob
import subprocess

def _generate_scene_sfx(sfx_type: str, out_wav: str, duration: float):
    # Generates 100% Copyright-Free Horror SFX impulses matched to scene start
    if sfx_type == "deep_boom":
        filter_str = f"sine=f=62:d=0.9,afade=t=out:st=0.1:d=0.8,volume=0.35,apad=whole_dur={duration:.2f}"
    elif sfx_type == "phone_buzz":
        filter_str = f"sine=f=135:d=0.45,tremolo=f=16:d=0.9,volume=0.25,apad=whole_dur={duration:.2f}"
    elif sfx_type == "heartbeat":
        filter_str = f"sine=f=48:d=1.2,tremolo=f=2.2:d=0.95,volume=0.35,apad=whole_dur={duration:.2f}"
    else:  # static_glitch
        filter_str = f"anoisesrc=d=0.35:c=pink:a=0.18,afade=t=out:st=0.05:d=0.3,apad=whole_dur={duration:.2f}"

    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", filter_str,
        "-ar", "44100", "-ac", "2", out_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def _create_synced_ass_subtitles(scenes: list, ass_path: str, is_short: bool):
    play_x, play_y = (1080, 1920) if is_short else (1920, 1080)
    font_size = 58 if is_short else 50
    margin_v = 240 if is_short else 85

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {play_x}
PlayResY: {play_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Liberation Sans,{font_size},&H00FFFFFF,&H000000FF,&H00101090,&H90000000,-1,0,0,0,100,100,1,0,3,4,2,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    cursor = 0.0
    for sc in scenes:
        dur = float(sc.get("duration_sec", 6.0))
        narration = sc.get("narration", "")
        words = narration.split()
        # Split narration into 4-5 word viral chunks synced across the scene duration
        chunks = [" ".join(words[i:i+5]) for i in range(0, len(words), 5)] or [sc.get("subtitle_caption", "FOLLOW THE RULES")]
        chunk_dur = dur / len(chunks)
        for ch in chunks:
            st = _format_ass_time(cursor)
            et = _format_ass_time(cursor + chunk_dur)
            safe_txt = ch.replace("{", "").replace("}", "").upper()
            lines.append(f"Dialogue: 0,{st},{et},Default,,0,0,0,,{{\fad(80,80)}}{safe_txt}")
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
    sfx_files = []

    for idx, sc in enumerate(scenes):
        img_path = sc["image_path"]
        dur = max(float(sc.get("duration_sec", 6.0)), 3.0)
        frames = int(dur * fps)
        clip_out = f"output/clips/clip_{orientation.replace(':', 'x')}_{idx+1}.mp4"
        sfx_out = f"output/clips/sfx_{orientation.replace(':', 'x')}_{idx+1}.wav"

        motion = sc.get("block_c_motion", "zoom_in_slow")
        if motion == "zoom_in_slow":
            z_expr = f"min(zoom+0.0007,1.18)"
        else:
            z_expr = f"if(eq(on,1),1.18,max(1.0,zoom-0.0007))"

        vf = (
            f"scale={scale_w}:-2,"
            f"zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={fps},"
            f"eq=contrast=1.06:brightness=0.02:saturation=1.08,format=yuv420p"
        )
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-vf", vf, "-t", f"{dur:.2f}",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", clip_out
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clip_files.append(clip_out)

        _generate_scene_sfx(sc.get("sfx_cue", "deep_boom"), sfx_out, dur)
        sfx_files.append(sfx_out)

    # Concatenate video clips
    v_list = f"output/clips/v_list_{orientation.replace(':', 'x')}.txt"
    with open(v_list, "w") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c)}'\n")
     stitched_v = f"output/clips/stitched_{orientation.replace(':', 'x')}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", v_list, "-c", "copy", stitched_v
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Concatenate scene SFX track
    sfx_list = f"output/clips/sfx_list_{orientation.replace(':', 'x')}.txt"
    with open(sfx_list, "w") as f:
        for s in sfx_files:
            f.write(f"file '{os.path.abspath(s)}'\n")
    stitched_sfx = f"output/clips/stitched_sfx_{orientation.replace(':', 'x')}.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", sfx_list, "-c", "copy", stitched_sfx
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Create synced word-chunk ASS Subtitles
    ass_path = f"output/clips/subs_{orientation.replace(':', 'x')}.ass"
    _create_synced_ass_subtitles(scenes, ass_path, is_short)

    # Mix Voiceover + Eerie 55Hz Dark Ambient Drone + Scene Horror SFX + Subtitles
    subprocess.run([
        "ffmpeg", "-y",
        "-i", stitched_v,
        "-i", audio_path,
        "-i", stitched_sfx,
        "-f", "lavfi", "-i", f"sine=frequency=55:duration={total_duration:.2f}",
        "-filter_complex",
        f"[3:a]volume=0.05[drone];[1:a][2:a][drone]amix=inputs=3:duration=first:dropout_transition=2,loudnorm=I=-14:TP=-1.5:LRA=11[aout];[0:v]ass={ass_path}[vout]",
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "21",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", output_mp4
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_mp4
