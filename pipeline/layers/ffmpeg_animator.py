import subprocess, os

def _sec_to_ass(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def _create_scene_subtitles(scene_audios: list, out_ass: str, aspect="16:9"):
    res_x, res_y, f_size, margin_v = (1920, 1080, 54, 55) if aspect == "16:9" else (1080, 1920, 74, 180)
    header = f'''[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: PictogramSub,Liberation Sans,{f_size},&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,5,3,2,50,50,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines = [header.strip()]
    cur_t = 0.0
    for item in scene_audios:
        words = item["text"].split()
        dur = item["duration"]
        chunk = 5 if aspect == "16:9" else 3
        groups = [words[i:i+chunk] for i in range(0, len(words), chunk)]
        step = dur / max(1, len(groups))
        for g_idx, grp in enumerate(groups):
            st_t = _sec_to_ass(cur_t + g_idx * step)
            en_t = _sec_to_ass(cur_t + (g_idx + 1) * step)
            txt = " ".join(grp).upper()
            lines.append(f"Dialogue: 0,{st_t},{en_t},PictogramSub,,0,0,0,,{{\fscx115\fscy115\t(0,100,\fscx100\fscy100)}}{txt}")
        cur_t += dur
    open(out_ass, "w", encoding="utf-8").write("\n".join(lines))

def render_pictogram_master_video(image_paths: list, scene_audios: list, aspect="16:9", out_mp4="output/long_video_16x9.mp4") -> str:
    os.makedirs("output", exist_ok=True)
    w, h = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    scale_w = 2200 if aspect == "16:9" else 1250
    clip_files = []

    for i, (img, aud_info) in enumerate(zip(image_paths, scene_audios)):
        clip_out = f"{img}_synced.mp4"
        dur = aud_info["duration"]
        aud_p = aud_info["audio_path"]
        frames = int(dur * 30)
        z_expr = "min(zoom+0.0014,1.18)" if i % 2 == 0 else "if(eq(on,1),1.18,max(1.0,zoom-0.0014))"
        vf = (
            f"scale={scale_w}:-2,zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30,"
            f"noise=alls=8:allf=t,format=yuv420p"
        )
        # Merge each scene's exact voiceover with its Creepy Pictogram animation + subtle eerie 55Hz dark drone
        subprocess.run([
            "ffmpeg", "-y",
            "-i", img,
            "-i", aud_p,
            "-f", "lavfi", "-i", f"sine=frequency=55:duration={dur}",
            "-filter_complex",
            f"[0:v]{vf}[v];[1:a]volume=1.0[va];[2:a]volume=0.05,lowpass=f=140[bg];[va][bg]amix=inputs=2:duration=first[a]",
            "-map", "[v]", "-map", "[a]",
            "-t", str(dur),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "192k", clip_out
        ], check=True)
        clip_files.append(clip_out)

    concat_txt = f"{out_mp4}_concat.txt"
    with open(concat_txt, "w") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c)}'\n")

    raw_merged = f"{out_mp4}_raw.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c", "copy", raw_merged
    ], check=True)

    ass_path = f"{out_mp4}.ass"
    _create_scene_subtitles(scene_audios, ass_path, aspect=aspect)

    subprocess.run([
        "ffmpeg", "-y", "-i", raw_merged,
        "-vf", f"subtitles={ass_path}",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", out_mp4
    ], check=True)
    return out_mp4
