import os
import io
import time
import random
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageEnhance, ImageFilter
from pipeline.key_rotator import rotator

LULLORIN_STYLE_PREFIX = (
    "2D dark minimalist creepy pictogram animation frame in the exact style of Lullorin and NightoraVideos, "
    "smooth pure-white 2D silhouette stick-figure character with expressive frightened eyes, "
    "inside a dark moody illustrated 2D interior environment at night, deep shadows, subtle crimson red horror accent lighting, "
    "clean full-screen composition, high contrast, no text, no watermark, no borders: "
)

def _get_font(size: int):
    candidates = [
        "resource/fonts/TitanOne-Regular.ttf",
        "resource/fonts/MicrosoftYaHeiBold.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _is_valid_image(img: Image.Image) -> bool:
    stat = ImageStat.Stat(img.convert("RGB"))
    mean_val = sum(stat.mean) / 3.0
    extrema = stat.extrema
    dyn_range = max(c[1] - c[0] for c in extrema)
    return mean_val > 8.0 and dyn_range > 50

def _generate_ai_pictogram_image(scene_prompt: str, width: int, height: int, seed: int) -> Image.Image:
    full_prompt = LULLORIN_STYLE_PREFIX + scene_prompt

    # 1. Try HuggingFace FLUX.1-schnell via Router & Inference Endpoints
    hf_token = rotator.get_key("HF_TOKEN")
    if hf_token:
        hf_urls = [
            "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        ]
        for api_url in hf_urls:
            try:
                headers = {
                    "Authorization": f"Bearer {hf_token}",
                    "Accept": "image/jpeg"
                }
                payload = {
                    "inputs": full_prompt,
                    "parameters": {"seed": seed}
                }
                r = requests.post(api_url, headers=headers, json=payload, timeout=35)
                if r.status_code == 200 and len(r.content) > 4000:
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    img = img.resize((width, height), Image.Resampling.LANCZOS)
                    if _is_valid_image(img):
                        return img
            except Exception as e:
                print(f"[Visuals] HF endpoint note: {e}")

    # 2. Try Pollinations FLUX Model (with concise URL + retries so it never times out)
    short_prompt = (
        "2D dark minimalist creepy pictogram style Lullorin Nightora, "
        "pure white smooth pictogram character in dark moody room at night, "
        "creepy shadow figure with glowing white eyes, high contrast, no text: "
        + scene_prompt[:220]
    )
    encoded = urllib.parse.quote(short_prompt)
    gen_w = 1280 if width > height else 720
    gen_h = 720 if width > height else 1280

    for attempt in range(3):
        try:
            cur_seed = seed + attempt * 17
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={gen_w}&height={gen_h}&seed={cur_seed}&model=flux&nologo=true"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}
            r = requests.get(url, headers=headers, timeout=30)
            if r.status_code == 200 and len(r.content) > 4000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                if _is_valid_image(img):
                    return img
        except Exception as e:
            print(f"[Visuals] Pollinations Flux retry {attempt+1}: {e}")
            time.sleep(1.5)

    # 3. High-Atmosphere Smooth 2D Dark Pictogram Fallback (No ugly grids or red borders!)
    return _render_clean_lullorin_fallback(width, height, seed)

def _render_clean_lullorin_fallback(width: int, height: int, seed: int) -> Image.Image:
    # Smooth dark atmospheric room gradient + glowing doorway + smooth white 2D pictogram + shadow entity
    img = Image.new("RGB", (width, height), (11, 13, 18))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2

    # Subtle perspective room walls
    draw.line([(0, 0), (cx - 260, cy - 180)], fill=(28, 32, 42), width=3)
    draw.line([(width, 0), (cx + 260, cy - 180)], fill=(28, 32, 42), width=3)
    draw.line([(0, height), (cx - 260, cy + 180)], fill=(28, 32, 42), width=3)
    draw.line([(width, height), (cx + 260, cy + 180)], fill=(28, 32, 42), width=3)
    draw.rectangle([cx - 260, cy - 180, cx + 260, cy + 180], outline=(34, 38, 48), width=3)

    # Dark doorway in background with tall shadow entity & glowing white pinhole eyes
    door_x = cx + 60
    door_y = cy - 110
    draw.rectangle([door_x - 65, door_y - 90, door_x + 65, door_y + 220], fill=(5, 6, 9), outline=(90, 18, 22), width=3)
    # Shadow entity head & glowing eyes
    draw.ellipse([door_x - 28, door_y - 45, door_x + 28, door_y + 11], fill=(18, 8, 10))
    draw.ellipse([door_x - 14, door_y - 22, door_x - 6, door_y - 14], fill=(255, 255, 255))
    draw.ellipse([door_x + 6, door_y - 22, door_x + 14, door_y - 14], fill=(255, 255, 255))

    # Foreground smooth white pictogram character (Lullorin style)
    px, py = cx - 130, cy + 60
    draw.ellipse([px - 48, py - 145, px + 48, py - 49], fill=(245, 245, 250))
    # Wide frightened dark eyes
    draw.ellipse([px - 22, py - 108, px - 6, py - 88], fill=(12, 14, 18))
    draw.ellipse([px + 6, py - 108, px + 22, py - 88], fill=(12, 14, 18))
    draw.rounded_rectangle([px - 42, py - 42, px + 42, py + 110], radius=22, fill=(245, 245, 250))
    return img

def _polish_cinema_look(img: Image.Image) -> Image.Image:
    # Clean contrast and sharpness boost - NO red borders, NO ugly top banners!
    img = ImageEnhance.Contrast(img).enhance(1.12)
    img = ImageEnhance.Sharpness(img).enhance(1.15)
    return img

def fetch_visual_scenes(storyboard: dict, orientation="16:9") -> list:
    os.makedirs("output/scenes", exist_ok=True)
    width, height = (1920, 1080) if orientation == "16:9" else (1080, 1920)
    scenes = storyboard.get("scenes", [])
    saved_paths = []

    print(f"[Visuals] Generating {len(scenes)} @Lullorin / @NightoraVideos AI scenes ({orientation})...")
    base_seed = random.randint(10000, 89999)

    for idx, scene in enumerate(scenes):
        out_path = f"output/scenes/scene_{orientation.replace(':', 'x')}_{idx+1}.jpg"
        v_prompt = scene.get("visual_prompt") or scene.get("block_b_visual_prompt") or scene.get("narration", "")
        raw_img = _generate_ai_pictogram_image(v_prompt, width, height, seed=base_seed + idx * 31)
        final_img = _polish_cinema_look(raw_img)
        final_img.save(out_path, "JPEG", quality=95)
        scene["image_path"] = out_path
        saved_paths.append(out_path)

    return saved_paths

def generate_viral_thumbnail(storyboard: dict, out_path="output/thumbnail_16x9.jpg"):
    os.makedirs(os.path.dirname(out_path) or "output", exist_ok=True)
    thumb_prompt = storyboard.get(
        "thumbnail_prompt",
        "Close-up 2D dark minimalist creepy pictogram illustration in the style of Lullorin and NightoraVideos, "
        "a pure white smooth pictogram character frozen in terror in bed at night while a tall pitch-black shadow figure "
        "with glowing white pinhole eyes stands in the red-lit bedroom doorway behind them, ultra high contrast, no text"
    )
    thumb_text = (storyboard.get("thumbnail_text") or "DON'T LOOK BACK").upper()[:20]

    print("[Thumbnail] Generating Real AI @Lullorin / @NightoraVideos Thumbnail via FLUX...")
    img = _generate_ai_pictogram_image(thumb_prompt, 1280, 720, seed=random.randint(1000, 9999))
    img = ImageEnhance.Contrast(img).enhance(1.22)

    draw = ImageDraw.Draw(img)

    # Subtle glowing red attention circle (classic @Lullorin / @NightoraVideos thumbnail cue)
    cx, cy = 880, 310
    for offset in range(6):
        draw.ellipse([cx - 115 - offset, cy - 115 - offset, cx + 115 + offset, cy + 115 + offset], outline=(235, 20, 25))

    # Clean, massive, shadow-backed bold text (NO ugly MS-Paint rectangle box!)
    font_huge = _get_font(86)
    tx, ty = 55, 565
    # Deep black drop-shadow stroke for readability over any AI artwork
    for dx in (-5, -3, 0, 3, 5):
        for dy in (-5, -3, 0, 3, 5):
            if dx != 0 or dy != 0:
                draw.text((tx + dx, ty + dy), thumb_text, font=font_huge, fill=(0, 0, 0))
    draw.text((tx, ty), thumb_text, font=font_huge, fill=(255, 255, 255))

    img.save(out_path, "JPEG", quality=96)
    return out_path
