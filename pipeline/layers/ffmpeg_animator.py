import subprocess, os, mutagen.mp3

def render_master_video(image_paths: list, audio_path: str, ass_path: str, aspect="16:9", out_mp4="output/long_video_16x9.mp4") -> str:
    os.makedirs("output", exist_ok=True)
    w, h = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    scale_w = 2200 if aspect == "16:9" else 1250
    audio_len = max(6.0, mutagen.mp3.MP3(audio_path).info.length)
    per_scene = max(2.5, audio_len / len(image_paths))
    clip_files = []

    for i, img in enumerate(image_paths):
        clip_out = f"{img}_anim.mp4"
        frames = int(per_scene * 30)
        z_expr = "min(zoom+0.0015,1.20)" if i % 2 == 0 else "if(eq(on,1),1.20,max(1.0,zoom-0.0015))"
        vf = (
            f"scale={scale_w}:-2,zoompan=z='{z_expr}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30,"
            f"eq=contrast=1.12:brightness=-0.03:saturation=1.15,vignette=PI/5,format=yuv420p"
        )
        subprocess.run([
            "ffmpeg", "-y", "-i", img, "-vf", vf, "-t", str(per_scene),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", clip_out
        ], check=True)
        clip_files.append(clip_out)

    concat_txt = f"{out_mp4}_concat.txt"
    with open(concat_txt, "w") as f:
        for c in clip_files:
            f.write(f"file '{os.path.abspath(c)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", audio_path, "-vf", f"ass={ass_path}",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-shortest", out_mp4
    ], check=True)
    return out_mp4
