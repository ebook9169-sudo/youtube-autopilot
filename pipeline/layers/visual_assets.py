import os, subprocess, urllib.parse, requests
from pipeline.key_rotator import get_keys, run_with_failover

HF_FLUX_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

def _hf_flux(token: str, prompt: str, w: int, h: int, out_path: str):
    r = requests.post(HF_FLUX_URL, headers={"Authorization": f"Bearer {token}"}, json={"inputs": prompt, "parameters": {"width": w, "height": h}}, timeout=60)
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(f"HF {r.status_code}")
    open(out_path, "wb").write(r.content)

def _procedural_fallback_image(w: int, h: int, idx: int, out_path: str):
    colors = ["0x0d1b2a", "0x1b263b", "0x10002b", "0x212529"]
    c = colors[idx % len(colors)]
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={c}:s={w}x{h}:d=1",
        "-vf", "noise=alls=18:allf=t+u,vignette=PI/4", "-frames:v", "1", out_path
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

def generate_visuals(prompts: list, aspect="16:9", prefix="long") -> list:
    w, h = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    out_dir = f"output/scenes_{prefix}"
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, p in enumerate(prompts):
        img_p = f"{out_dir}/scene_{i:02d}.jpg"
        full_p = f"{p}, dark cinematic lighting, 8k photorealistic"
        try:
            if get_keys("HF_TOKEN"):
                run_with_failover("HF_TOKEN", _hf_flux, full_p, w, h, img_p)
            else:
                q = urllib.parse.quote(full_p)
                url = f"https://image.pollinations.ai/prompt/{q}?width={w}&height={h}&model=flux&nologo=true&seed={i+300}"
                r = requests.get(url, timeout=35)
                if r.status_code == 200 and len(r.content) > 5000:
                    open(img_p, "wb").write(r.content)
                else:
                    _procedural_fallback_image(w, h, i, img_p)
        except Exception:
            _procedural_fallback_image(w, h, i, img_p)
        paths.append(img_p)
    return paths

def generate_pro_thumbnail(bg_image: str, hook_text: str, out_thumb="output/thumbnail_16x9.jpg") -> str:
    safe_txt = hook_text.replace("'", "").upper()
    vf = (
        f"scale=1280:720,eq=contrast=1.25:brightness=-0.08:saturation=1.3,vignette=PI/4,"
        f"drawbox=x=0:y=480:w=1280:h=180:color=black@0.65:t=fill,"
        f"drawtext=text='{safe_txt}':fontcolor=yellow:fontsize=78:x=(w-text_w)/2:y=535:borderw=5:bordercolor=black"
    )
    subprocess.run(["ffmpeg", "-y", "-i", bg_image, "-vf", vf, "-frames:v", "1", out_thumb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_thumb
