import os, math, random
from PIL import Image, ImageDraw, ImageFont

def _load_font(size: int, bold=True):
    try:
        name = "LiberationSans-Bold.ttf" if bold else "LiberationSans-Regular.ttf"
        return ImageFont.truetype(f"/usr/share/fonts/truetype/liberation/{name}", size)
    except Exception:
        return ImageFont.load_default()

def _draw_pictogram_person(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float, color: tuple, glowing_eyes=False):
    """Draws the iconic viral 'Creepy Pictogram' bathroom-sign style humanoid figure."""
    head_r = int(38 * scale)
    # Head
    draw.ellipse([cx - head_r, cy - int(150 * scale) - head_r, cx + head_r, cy - int(150 * scale) + head_r], fill=color)
    if glowing_eyes:
        er = max(4, int(7 * scale))
        draw.ellipse([cx - int(14*scale) - er, cy - int(154*scale) - er, cx - int(14*scale) + er, cy - int(154*scale) + er], fill=(255, 255, 255))
        draw.ellipse([cx + int(14*scale) - er, cy - int(154*scale) - er, cx + int(14*scale) + er, cy - int(154*scale) + er], fill=(255, 255, 255))
    # Torso (Rounded pillar)
    bw, bh = int(46 * scale), int(145 * scale)
    draw.rounded_rectangle([cx - bw, cy - int(95 * scale), cx + bw, cy + bh], radius=int(22 * scale), fill=color)
    # Arms
    aw = int(20 * scale)
    draw.rounded_rectangle([cx - bw - aw - 6, cy - int(88 * scale), cx - bw - 6, cy + int(35 * scale)], radius=10, fill=color)
    draw.rounded_rectangle([cx + bw + 6, cy - int(88 * scale), cx + bw + aw + 6, cy + int(35 * scale)], radius=10, fill=color)
    # Legs
    lw = int(20 * scale)
    draw.rounded_rectangle([cx - bw + 6, cy + bh - 10, cx - 6, cy + bh + int(135 * scale)], radius=10, fill=color)
    draw.rounded_rectangle([cx + 6, cy + bh - 10, cx + bw - 6, cy + bh + int(135 * scale)], radius=10, fill=color)

def _draw_creepy_pictogram_scene(sc: dict, idx: int, w: int, h: int, out_path: str):
    """Programmatically renders authentic 'Style #5: Creepy Pictogram' storyboard frames (Claude Code style)."""
    # Dark Slate VHS Analog Background (Visible charcoal grid, NEVER pure black!)
    img = Image.new("RGB", (w, h), (22, 24, 30))
    draw = ImageDraw.Draw(img)

    # 1. Analog Warning Grid & VHS Scanlines
    for x in range(0, w, 90):
        draw.line([(x, 0), (x, h)], fill=(34, 37, 46), width=2)
    for y in range(0, h, 90):
        draw.line([(0, y), (w, y)], fill=(34, 37, 46), width=2)

    # Outer Analog Hazard Border
    pad = 36
    draw.rectangle([pad, pad, w - pad, h - pad], outline=(210, 45, 45), width=5)
    draw.rectangle([pad + 12, pad + 12, w - pad - 12, h - pad - 12], outline=(90, 95, 110), width=2)

    # 2. Top Emergency Rule Header Banner
    banner_h = 95 if w > h else 110
    draw.rectangle([pad + 12, pad + 12, w - pad - 12, pad + 12 + banner_h], fill=(185, 25, 30))
    f_badge = _load_font(44 if w > h else 40, bold=True)
    draw.text((pad + 45, pad + 32), f"⚠  {sc.get('rule_badge', f'RULE 0{idx+1}')}", fill=(255, 255, 255), font=f_badge)

    cx, cy = w // 2, int(h * 0.48)
    scale = 1.05 if w > h else 0.92
    mode = sc.get("pictogram_mode", "family_plus_red_entity")

    # 3. Draw Scene-Specific Creepy Pictograms & Props (Block A + Block B)
    if mode == "family_plus_red_entity":
        # 4 White Family Pictograms + 5th Creepy Red Mystery Entity + Chat UI Card
        spacing = int(155 * scale)
        start_x = cx - int(2 * spacing)
        labels = ["MOM", "DAD", "LILY", "YOU", "???"]
        f_lbl = _load_font(28, bold=True)
        for j in range(5):
            px = start_x + j * spacing
            is_creepy = (j == 4)
            col = (235, 35, 40) if is_creepy else (238, 242, 248)
            _draw_pictogram_person(draw, px, cy + 20, scale * (1.12 if is_creepy else 0.88), col, glowing_eyes=is_creepy)
            draw.text((px - 32, cy - int(215 * scale)), labels[j], fill=col, font=f_lbl)

    elif mode == "phone_glitch":
        # Giant Smartphone UI with 5th Gray Circle & Countdown 1-2-3-4-5
        pw, ph = int(340 * scale), int(520 * scale)
        draw.rounded_rectangle([cx - pw//2, cy - ph//2, cx + pw//2, cy + ph//2], radius=32, fill=(14, 16, 22), outline=(235, 240, 245), width=8)
        f_ui = _load_font(28, bold=True)
        members = [("MOM", (220, 225, 235)), ("DAD", (220, 225, 235)), ("LILY", (220, 225, 235)), ("YOU", (220, 225, 235)), ("ADDED BY: [BLANK]", (240, 45, 45))]
        for k, (m_name, m_col) in enumerate(members):
            my = cy - ph//2 + 55 + k * int(82 * scale)
            draw.ellipse([cx - pw//2 + 30, my, cx - pw//2 + 78, my + 48], fill=m_col)
            draw.text((cx - pw//2 + 98, my + 8), m_name, fill=m_col, font=f_ui)

    elif mode == "crossed_exit":
        # White figure + Door Frame + Giant Red Forbidden X + Tall Red Shadow Figure
        _draw_pictogram_person(draw, cx - int(180 * scale), cy + 25, scale * 0.95, (240, 242, 248))
        _draw_pictogram_person(draw, cx + int(185 * scale), cy + 10, scale * 1.18, (225, 30, 35), glowing_eyes=True)
        # Red Forbidden Cross in center
        r_rad = int(95 * scale)
        draw.ellipse([cx - r_rad, cy - r_rad, cx + r_rad, cy + r_rad], outline=(255, 45, 45), width=14)
        draw.line([(cx - int(65*scale), cy - int(65*scale)), (cx + int(65*scale), cy + int(65*scale))], fill=(255, 45, 45), width=14)

    elif mode == "typing_eyes":
        # White figure + Typing Bubble [ • • • ] + Glowing Red Eyes in Dark Doorway
        _draw_pictogram_person(draw, cx - int(160 * scale), cy + 30, scale * 0.95, (240, 242, 248))
        # Doorway on right
        dx, dy = cx + int(80 * scale), cy - int(180 * scale)
        draw.rectangle([dx, dy, dx + int(190 * scale), dy + int(390 * scale)], fill=(10, 10, 14), outline=(220, 225, 235), width=6)
        # Red eyes inside doorway
        draw.ellipse([dx + 55, dy + 90, dx + 78, dy + 112], fill=(255, 30, 30))
        draw.ellipse([dx + 110, dy + 90, dx + 133, dy + 112], fill=(255, 30, 30))
        # Typing bubble
        draw.rounded_rectangle([cx - int(80*scale), cy - int(180*scale), cx + int(60*scale), cy - int(110*scale)], radius=20, fill=(220, 35, 40))
        for d in range(3):
            draw.ellipse([cx - int(45*scale) + d*35, cy - int(155*scale), cx - int(25*scale) + d*35, cy - int(135*scale)], fill=(255, 255, 255))

    else:
        # Twist / Shadow Looming Directly Behind White Pictogram
        _draw_pictogram_person(draw, cx + int(55 * scale), cy - int(15 * scale), scale * 1.25, (220, 25, 30), glowing_eyes=True)
        _draw_pictogram_person(draw, cx - int(25 * scale), cy + int(35 * scale), scale * 0.92, (242, 245, 250))

    # 4. Bottom Subtitle / Rule Title Box
    box_top = h - (215 if w > h else 340)
    draw.rectangle([pad + 20, box_top, w - pad - 20, box_top + 115], fill=(12, 14, 18), outline=(255, 215, 0), width=4)
    f_title = _load_font(44 if w > h else 36, bold=True)
    draw.text((pad + 50, box_top + 32), sc.get("caption_title", "FOLLOW THE RULES"), fill=(255, 225, 0), font=f_title)

    img.save(out_path, "JPEG", quality=95)

def generate_pictogram_scenes(scenes: list, aspect="16:9", prefix="long") -> list:
    w, h = (1920, 1080) if aspect == "16:9" else (1080, 1920)
    out_dir = f"output/scenes_{prefix}"
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, sc in enumerate(scenes):
        img_p = f"{out_dir}/scene_{i:02d}.jpg"
        _draw_creepy_pictogram_scene(sc, i, w, h, img_p)
        paths.append(img_p)
    return paths

def generate_pro_thumbnail(bg_image: str, hook_text: str, out_thumb="output/thumbnail_16x9.jpg") -> str:
    im = Image.open(bg_image).convert("RGB").resize((1280, 720))
    draw = ImageDraw.Draw(im)
    draw.rectangle([(0, 520), (1280, 720)], fill=(180, 15, 20))
    f_th = _load_font(78, bold=True)
    draw.text((65, 570), f"⚠ {hook_text.upper()}", fill=(255, 255, 255), font=f_th)
    im.save(out_thumb, "JPEG", quality=95)
    return out_thumb
