import os
import io
import math
import urllib.parse
import requests
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageEnhance
from pipeline.key_rotator import rotator

def _get_font(size: int):
    # Prioritize MoneyPrinterTurbo's built-in bold fonts first!
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

def _is_valid_non_black_image(img: Image.Image) -> bool:
    stat = ImageStat.Stat(img.convert("RGB"))
    mean_brightness = sum(stat.mean) / 3.0
    extrema = stat.extrema
    # Ensure image has real contrast and isn't a solid black/blank frame
    dynamic_range = max( c[1] - c[0] for c in extrema )
    return mean_brightness > 14.0 and dynamic_range > 60

def _try_flux_ai_generation(full_prompt: str, width: int, height: int):
    # 1. Try HuggingFace Free Serverless API (FLUX.1-schnell) if HF_TOKEN is provided
    hf_token = rotator.get_key("HF_TOKEN")
    if hf_token:
        try:
            api_url = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
            headers = {"Authorization": f"Bearer {hf_token}"}
            r = requests.post(api_url, headers=headers, json={"inputs": full_prompt}, timeout=25)
            if r.status_code == 200 and len(r.content) > 5000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                if _is_valid_non_black_image(img):
                    print("[Visuals] Generated scene via HuggingFace Free FLUX.1-schnell!")
                    return img
        except Exception as e:
            print(f"[Visuals] HF Flux fallback: {e}")

    # 2. Try MoneyPrinterTurbo's 100% Free Keyless Pollinations Flux Engine
    try:
        encoded = urllib.parse.quote(full_prompt)
        gen_w = 1280 if width > height else 720
        gen_h = 720 if width > height else 1280
        seed = abs(hash(full_prompt)) % 99999
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={gen_w}&height={gen_h}&seed={seed}&model=flux&nologo=true"
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/122.0.0.0 Safari/537.36"}
        r = requests.get(url, headers=headers, timeout=22)
        if r.status_code == 200 and len(r.content) > 5000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
            if _is_valid_non_black_image(img):
                print("[Visuals] Generated scene via Keyless Pollinations Flux AI!")
                return img
    except Exception as e:
        print(f"[Visuals] Pollinations Flux fallback: {e}")

    return None

def _draw_pictogram_person(draw, cx, cy, scale=1.0, color=(245, 245, 250), is_anomaly=False, glowing_eyes=False):
    r = int(34 * scale)
    draw.ellipse([cx - r, cy - int(115 * scale) - r, cx + r, cy - int(115 * scale) + r], fill=color)
    if glowing_eyes:
        eye_color = (255, 25, 25) if not is_anomaly else (255, 255, 255)
        er = max(4, int(6 * scale))
        draw.ellipse([cx - int(13 * scale) - er, cy - int(118 * scale) - er, cx - int(13 * scale) + er, cy - int(118 * scale) + er], fill=eye_color)
        draw.ellipse([cx + int(13 * scale) - er, cy - int(118 * scale) - er, cx + int(13 * scale) + er, cy - int(118 * scale) + er], fill=eye_color)
    body_w = int(30 * scale)
    draw.rounded_rectangle([cx - body_w, cy - int(72 * scale), cx + body_w, cy + int(45 * scale)], radius=int(14 * scale), fill=color)
    limb_w = max(6, int(13 * scale))
    draw.line([(cx - body_w, cy - int(55 * scale)), (cx - int(62 * scale), cy + int(15 * scale))], fill=color, width=limb_w)
    draw.line([(cx + body_w, cy - int(55 * scale)), (cx + int(62 * scale), cy + int(15 * scale))], fill=color, width=limb_w)
    draw.line([(cx - int(15 * scale), cy + int(42 * scale)), (cx - int(22 * scale), cy + int(130 * scale))], fill=color, width=limb_w)
    draw.line([(cx + int(15 * scale), cy + int(42 * scale)), (cx + int(22 * scale), cy + int(130 * scale))], fill=color, width=limb_w)

def _render_procedural_pictogram(archetype: str, width: int, height: int) -> Image.Image:
    img = Image.new("RGB", (width, height), (20, 22, 28))
    draw = ImageDraw.Draw(img)
    # Gritty VHS Grid
    step = 60
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=(32, 35, 44), width=1)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=(32, 35, 44), width=1)

    cx, cy = width // 2, height // 2 + 20
    sc = 1.15 if width > height else 0.92
    f_med = _get_font(int(30 * sc))
    f_sm = _get_font(int(22 * sc))

    if archetype == "phone_chat_5th":
        pw, ph = int(380 * sc), int(530 * sc)
        px1, py1 = cx - pw // 2, cy - ph // 2
        draw.rounded_rectangle([px1, py1, px1 + pw, py1 + ph], radius=32, fill=(28, 32, 42), outline=(235, 235, 245), width=6)
        draw.rectangle([px1 + 20, py1 + 25, px1 + pw - 20, py1 + 85], fill=(180, 20, 25))
        draw.text((px1 + 38, py1 + 38), "FAMILY CHAT (5)", font=f_med, fill=(255, 255, 255))
        members = [("MOM", False), ("DAD", False), ("LILY", False), ("YOU", False), ("??? [ADDED BY BLANK]", True)]
        for i, (m_name, is_bad) in enumerate(members):
            ry = py1 + 105 + i * int(78 * sc)
            bg = (85, 15, 20) if is_bad else (44, 48, 60)
            ol = (255, 45, 45) if is_bad else (140, 145, 160)
            draw.rounded_rectangle([px1 + 24, ry, px1 + pw - 24, ry + int(64 * sc)], radius=12, fill=bg, outline=ol, width=3)
            ic_col = (240, 30, 35) if is_bad else (240, 240, 248)
            draw.ellipse([px1 + 38, ry + 10, px1 + 38 + int(44 * sc), ry + 10 + int(44 * sc)], fill=ic_col)
            draw.text((px1 + 100, ry + 18), m_name, font=f_sm, fill=(255, 220, 220) if is_bad else (245, 245, 250))

    elif archetype == "counting_five":
        spacing = int(165 * sc) if width > height else int(125 * sc)
        start_x = cx - 2 * spacing
        for i in range(5):
            px = start_x + i * spacing
            is_fifth = (i == 4)
            col = (225, 25, 30) if is_fifth else (242, 242, 248)
            _draw_pictogram_person(draw, px, cy + 25, scale=0.88 * sc, color=col, is_anomaly=is_fifth, glowing_eyes=is_fifth)
            draw.text((px - 15, cy - int(195 * sc)), f"#{i+1}", font=f_med, fill=col)

    elif archetype == "do_not_delete":
        _draw_pictogram_person(draw, cx - int(160 * sc), cy + 30, scale=1.05 * sc, color=(242, 242, 248))
        bx, by = cx + int(110 * sc), cy
        draw.rounded_rectangle([bx - int(160 * sc), by - int(75 * sc), bx + int(160 * sc), by + int(75 * sc)], radius=18, fill=(55, 18, 22), outline=(255, 45, 45), width=5)
        draw.text((bx - int(130 * sc), by - int(22 * sc)), "REMOVE #5?", font=f_med, fill=(255, 255, 255))
        draw.line([(bx - int(140 * sc), by - int(100 * sc)), (bx + int(140 * sc), by + int(100 * sc))], fill=(255, 30, 30), width=14)
        draw.line([(bx + int(140 * sc), by - int(100 * sc)), (bx - int(140 * sc), by + int(100 * sc))], fill=(255, 30, 30), width=14)

    elif archetype == "doorway_eyes":
        dw, dh = int(250 * sc), int(430 * sc)
        draw.rectangle([cx - dw // 2, cy - dh // 2, cx + dw // 2, cy + dh // 2], fill=(10, 12, 16), outline=(235, 235, 245), width=6)
        _draw_pictogram_person(draw, cx, cy + 35, scale=1.05 * sc, color=(190, 20, 25), is_anomaly=True, glowing_eyes=True)

    elif archetype == "final_twist_table":
        draw.rectangle([cx - int(270 * sc), cy + int(35 * sc), cx + int(270 * sc), cy + int(65 * sc)], fill=(235, 235, 245))
        offsets = [-int(210 * sc), -int(70 * sc), int(70 * sc), int(210 * sc)]
        for idx, off in enumerate(offsets):
            traitor = (idx == 2)
            col = (230, 25, 30) if traitor else (242, 242, 248)
            _draw_pictogram_person(draw, cx + off, cy - int(20 * sc), scale=0.82 * sc, color=col, is_anomaly=traitor, glowing_eyes=traitor)
    else:
        _draw_pictogram_person(draw, cx - int(120 * sc), cy + 25, scale=1.0 * sc, color=(242, 242, 248))
        _draw_pictogram_person(draw, cx + int(120 * sc), cy + 25, scale=1.05 * sc, color=(225, 25, 30), is_anomaly=True, glowing_eyes=True)

    return img

def _apply_analog_horror_hud(img: Image.Image, rule_badge: str, scene_num: int, total_scenes: int) -> Image.Image:
    width, height = img.size
    # Boost contrast so the video is crisp and never dark/murky
    img = ImageEnhance.Contrast(img).enhance(1.18)
    draw = ImageDraw.Draw(img)

    # Scanlines
    for y in range(0, height, 6):
        draw.line([(0, y), (width, y)], fill=(12, 14, 18), width=1)

    # Bold Red Hazard Frame
    draw.rectangle([10, 10, width - 10, height - 10], outline=(215, 25, 30), width=6)
    draw.rectangle([20, 20, width - 20, height - 20], outline=(240, 240, 248), width=2)

    # Top Rule Banner
    sc = 1.0 if width > height else 0.82
    f_badge = _get_font(int(36 * sc))
    banner_w = min(width - 80, int(520 * sc))
    banner_h = int(68 * sc)
    bx1 = (width - banner_w) // 2
    by1 = 34
    draw.rounded_rectangle([bx1, by1, bx1 + banner_w, by1 + banner_h], radius=12, fill=(205, 20, 25), outline=(255, 255, 255), width=3)
    draw.text((bx1 + 28, by1 + 12), f"⚠ {rule_badge.upper()}", font=f_badge, fill=(255, 255, 255))

    return img

def fetch_visual_scenes(storyboard: dict, orientation="16:9") -> list:
    os.makedirs("output/scenes", exist_ok=True)
    width, height = (1920, 1080) if orientation == "16:9" else (1080, 1920)

    block_a = storyboard.get("block_a_assets", {})
    style_lock = block_a.get("style_lock", "2D minimalist creepy pictogram, white stick figure on dark charcoal background, blood red accents")
    char_desc = block_a.get("main_character", "white stick-figure pictogram")
    anom_desc = block_a.get("anomaly_entity", "blood-red shadow pictogram figure with glowing eyes")

    scenes = storyboard.get("scenes", [])
    saved_paths = []

    for idx, scene in enumerate(scenes):
        out_path = f"output/scenes/scene_{orientation.replace(':', 'x')}_{idx+1}.jpg"
        block_b_prompt = scene.get("block_b_visual_prompt", "")
        full_prompt = f"{style_lock}. Characters: {char_desc}, {anom_desc}. Scene: {block_b_prompt}"

        # Try AI Flux Generation (HF_TOKEN or Pollinations Flux)
        base_img = _try_flux_ai_generation(full_prompt, width, height)
        if base_img is None:
            # Guaranteed Procedural Creepy Pictogram
            archetype = scene.get("scene_archetype", "phone_chat_5th")
            base_img = _render_procedural_pictogram(archetype, width, height)

        # Apply Vinsa Style #5 Analog Horror HUD & Rule Banner
        rule_badge = scene.get("rule_badge", f"RULE #{idx+1}")
        final_img = _apply_analog_horror_hud(base_img, rule_badge, idx + 1, len(scenes))
        final_img.save(out_path, "JPEG", quality=95)
        scene["image_path"] = out_path
        saved_paths.append(out_path)

    return saved_paths

def generate_viral_thumbnail(title_text: str, out_path="output/thumbnail_16x9.jpg"):
    os.makedirs(os.path.dirname(out_path) or "output", exist_ok=True)
    img = _render_procedural_pictogram("phone_chat_5th", 1280, 720)
    draw = ImageDraw.Draw(img)
    draw.rectangle([8, 8, 1272, 712], outline=(235, 20, 25), width=12)
    f_big = _get_font(62)
    draw.rectangle([40, 565, 1240, 685], fill=(205, 15, 20), outline=(255, 255, 255), width=5)
    hook = (title_text or "DO NOT DELETE #5")[:28].upper()
    draw.text((75, 592), f"⚠ {hook}", font=f_big, fill=(255, 255, 255))
    img.save(out_path, "JPEG", quality=95)
    return out_path
