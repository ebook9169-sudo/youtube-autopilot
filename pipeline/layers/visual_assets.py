import os, urllib.parse, requests
from PIL import Image, ImageDraw, ImageFont
from pipeline.key_rotator import get_keys, run_with_failover

HF_FLUX_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"

def _hf_flux(token: str, prompt: str, w: int, h: int, out_path: str):
    r = requests.post(HF_FLUX_URL, headers={"Authorization": f"Bearer {token}"}, json={"inputs": prompt, "parameters": {"width": w, "height": h}}, timeout=45)
    if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
        raise RuntimeError(f"HF {r.status_code}")
    open(out_path, "wb").write(r.content)

def _create_cinematic_canvas(w: int, h: int, idx: int, label: str, out_path: str):
    palettes = [(12, 20, 38), (24, 15, 36), (15, 28, 30), (28, 18, 18)]
    base = palettes[idx % len(palettes)]
    img = Image.new("RGB", (w, h), base)
    draw = ImageDraw.Draw(img)
    for y in range(0, h, 4):
        factor = 1.0 - (abs(y - h / 2) / (h / 1.5))
        col = tuple(max(0, min(255, int(c * factor + 15))) for c in base)
        draw.line([(0, y), (w, y)], fill=col, width=4)
    img.save(out_path, "JPEG", quality=92)

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
                r = requests.get(url, timeout=25)
                if r.status_code == 200 and len(r.content) > 10000:
                    open(img_p, "wb").write(r.content)
                    # Verify & normalize image size
                    im = Image.open(img_p).convert("RGB").resize((w, h))
                    im.save(img_p, "JPEG", quality=92)
                else:
                    _create_cinematic_canvas(w, h, i, p[:30], img_p)
        except Exception:
            _create_cinematic_canvas(w, h, i, p[:30], img_p)
        paths.append(img_p)
    return paths

def generate_pro_thumbnail(bg_image: str, hook_text: str, out_thumb="output/thumbnail_16x9.jpg") -> str:
    im = Image.open(bg_image).convert("RGB").resize((1280, 720))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(0, 490), (1280, 670)], fill=(0, 0, 0))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 72)
    except Exception:
        font = ImageFont.load_default()
    draw.text((80, 540), hook_text.upper(), fill=(255, 230, 0), font=font)
    im.save(out_thumb, "JPEG", quality=95)
    return out_thumb
