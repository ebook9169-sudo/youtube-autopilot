import os
import io
import re
import time
import json
import copy
import random
import asyncio
import urllib.parse
import subprocess
import requests
import edge_tts
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageStat, ImageEnhance, ImageFilter

# ==============================================================================
# 0. DUAL-ACCOUNT API KEY ROTATOR
# ==============================================================================
class DualAccountKeyRotator:
    def __init__(self):
        self.counters = {}

    def get_key(self, prefix: str) -> str:
        k1 = os.environ.get(f"{prefix}_1", "").strip()
        k2 = os.environ.get(f"{prefix}_2", "").strip()
        single = os.environ.get(prefix, "").strip()
        valid = [k for k in [k1, k2, single] if k and not k.startswith("YOUR_")]
        if not valid:
            return ""
        idx = self.counters.get(prefix, 0)
        chosen = valid[idx % len(valid)]
        self.counters[prefix] = idx + 1
        return chosen

rotator = DualAccountKeyRotator()

def check_connected_keys() -> dict:
    status = {
        "GEMINI_KEY": bool(rotator.get_key("GEMINI_KEY")),
        "HF_TOKEN": bool(rotator.get_key("HF_TOKEN")),
        "GROQ_KEY": bool(rotator.get_key("GROQ_KEY")),
        "ELEVENLABS_KEY": bool(rotator.get_key("ELEVENLABS_KEY")),
    }
    print("-----------------------------------------------------------------")
    print("🔑 API KEYS CONNECTION STATUS:")
    for k, is_set in status.items():
        badge = "✅ CONNECTED (Real AI Active)" if is_set else "⚪ NOT SET"
        print(f"   • {k}: {badge}")
    print("-----------------------------------------------------------------")
    return status

# ==============================================================================
# 1. @LULLORIN / @NIGHTSILL-U2N / @NIGHTORAVIDEOS STORY ENGINE (100% NEW STORIES)
# ==============================================================================
STORY_PREMISES = [
    {
        "seed": "waking up at 3:14 AM because all of your shoes have been neatly lined up pointing toward your bed",
        "hook_title": "DO NOT Touch Your Shoes At 3:14 AM (7 Rules To Survive)",
        "thumb_text": "DON'T LEAVE BED",
        "location": "dark moody bedroom at 3:14 AM",
        "object": "a neat row of shoes on the bedroom floor pointing directly at the bed",
        "entity": "tall pitch-black shadow figure with glowing white pinhole eyes standing inside the cracked closet door"
    },
    {
        "seed": "hearing four slow polite knocks on your bedroom window even though your room is on the third floor",
        "hook_title": "If Something Knocks On Your 3rd Floor Window At 3AM, Follow These 7 Rules",
        "thumb_text": "DON'T OPEN THE CURTAIN",
        "location": "moonlit third-floor bedroom at night",
        "object": "a foggy third-floor glass window with a pale handprint pressed against the outside",
        "entity": "elongated dark silhouette figure with glowing white pinhole eyes crouching outside on the narrow window ledge"
    },
    {
        "seed": "stepping into your apartment elevator at 2:30 AM and realizing the mirror shows only you, not the person standing beside you",
        "hook_title": "DO NOT Look In The Elevator Mirror After 2:00 AM (7 Survival Rules)",
        "thumb_text": "IT HAS NO REFLECTION",
        "location": "dimly lit metallic apartment elevator late at night",
        "object": "an elevator wall mirror showing only one person while two figures stand in the cabin",
        "entity": "tall faceless dark shadow figure with glowing white eyes standing right behind your shoulder"
    },
    {
        "seed": "finding your dog sitting completely frozen in the hallway at 3:00 AM staring at an empty ceiling corner",
        "hook_title": "If Your Dog Stares At The Ceiling Corner At 3AM, Follow These 7 Rules",
        "thumb_text": "DON'T LOOK UP",
        "location": "dark suburban hallway at 3:00 AM",
        "object": "a terrified dog frozen stiff on the hallway rug staring up at the dark ceiling",
        "entity": "contorted pitch-black shadow figure with glowing white pinhole eyes clinging to the ceiling corner"
    },
    {
        "seed": "driving home alone at night when your car dashboard suddenly warns that a backseat seatbelt was just unbuckled",
        "hook_title": "If Your Car Says A Backseat Passenger Unbuckled At Night, Follow These 7 Rules",
        "thumb_text": "DON'T CHECK THE MIRROR",
        "location": "inside a dark car driving on an empty rain-soaked highway at night",
        "object": "a glowing red backseat seatbelt warning icon on the car dashboard",
        "entity": "pair of glowing white pinhole eyes visible in the rearview mirror rising slowly from the dark backseat"
    },
    {
        "seed": "waking up at 2:48 AM to a phone notification saying an AirDrop photo was just shared from inside your own bedroom",
        "hook_title": "DO NOT Accept An AirDrop At 3:00 AM When You Are Home Alone (7 Rules)",
        "thumb_text": "IT'S IN THE ROOM",
        "location": "dark bedroom lit only by a glowing smartphone screen",
        "object": "a smartphone screen showing a photo of you sleeping taken from the bedroom doorway",
        "entity": "tall pitch-black shadow figure with glowing white eyes leaning out from the dark hallway door"
    }
]

LULLORIN_LLM_PROMPT = """You are the head scriptwriter for the viral USA YouTube channels @Lullorin, @Nightsill-u2n, and @NightoraVideos.
Write a 100% BRAND NEW, chilling second-person ("You...") psychological survival rules story based on this exact premise:
Premise: {seed}

Rules for output:
- Start immediately in the tense late-night situation.
- Include 7 specific, eerie survival rules and a chilling final twist.
- Every `visual_prompt` must describe a 2D dark minimalist creepy pictogram frame in the style of @Lullorin and @NightoraVideos (pure white smooth 2D pictogram character with frightened eyes, dark moody illustrated room, and a pitch-black shadow entity with glowing white pinhole eyes).
- Provide between 8 and 10 scenes.

Return ONLY valid JSON in this exact format:
{{
  "title": "{hook_title}",
  "thumbnail_text": "{thumb_text}",
  "thumbnail_prompt": "2D dark minimalist creepy pictogram illustration in the style of Lullorin and NightoraVideos, close-up of a pure white smooth pictogram character frozen in terror in {location}, while a {entity}, high contrast, no text",
  "seo_description": "Suspenseful description with #lullorin #nightora #survivalrules #creepy #donot #whatif",
  "tags": ["do not", "7 rules to survive", "lullorin", "nightora", "creepy pictogram", "scary rules", "what if"],
  "publishing_package": {{
    "title_ideas": ["5 viral titles in @Lullorin style..."],
    "thumbnail_prompts": ["3 thumbnail prompts in @NightoraVideos style..."]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "1 to 2 tense spoken sentences for this scene...",
      "visual_prompt": "2D dark minimalist creepy pictogram illustration style of Lullorin and NightoraVideos, pure white smooth pictogram character in {location}, {object}, dark shadows, no text",
      "motion": "zoom_in_slow"
    }}
  ]
}}"""

def _extract_json(raw_text: str) -> dict:
    cleaned = re.sub(r"```(?:json)?", "", raw_text).replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        return json.loads(cleaned[start:end+1])
    raise ValueError("No valid JSON block found")

def _build_fallback_lullorin_story(item: dict) -> dict:
    loc = item["location"]
    obj = item["object"]
    ent = item["entity"]
    seed = item["seed"]
    return {
        "title": item["hook_title"],
        "thumbnail_text": item["thumb_text"],
        "thumbnail_prompt": f"2D dark minimalist creepy pictogram illustration in the style of Lullorin and NightoraVideos, close-up of a pure white smooth pictogram character terrified in {loc}, {obj}, while a {ent}, high contrast, no text",
        "seo_description": f"Imagine {seed}. Follow these 7 survival rules immediately if you want to make it to sunrise.\n\n#lullorin #nightora #survivalrules #creepy #donot #whatif",
        "tags": ["do not", "7 rules to survive", "lullorin", "nightora", "creepy pictogram", "scary rules", "what if"],
        "publishing_package": {
            "title_ideas": [
                item["hook_title"],
                "DO NOT Ignore This Warning At 3:00 AM (7 Rules To Survive)",
                "7 Survival Rules When Something Is Watching You In The Dark",
                "NEVER Turn Around If You Notice This At 3:14 AM",
                "What If You Break Rule #1 When You Are Home Alone?"
            ],
            "thumbnail_prompts": [
                f"Lullorin style 2D dark pictogram: white character frozen in {loc}, {ent} behind them, red circle on the shadow",
                f"NightoraVideos style 2D dark pictogram: close up of terrified white pictogram looking at {obj}"
            ]
        },
        "scenes": [
            {
                "scene_id": 1,
                "narration": f"It is 3:14 in the morning when you suddenly wake up, and the first thing you notice is {seed}.",
                "visual_prompt": f"Wide cinematic 2D dark minimalist pictogram illustration, pure white smooth pictogram character in {loc}, noticing {obj}, deep atmospheric shadows, style of Lullorin and NightoraVideos",
                "motion": "zoom_in_slow"
            },
            {
                "scene_id": 2,
                "narration": "The air around you turns freezing cold, and the normal background hum of the building goes dead silent. Whatever did this is still nearby, watching for your reaction.",
                "visual_prompt": f"Close-up 2D dark minimalist pictogram illustration, white pictogram character with wide frightened eyes frozen still in {loc}, eerie dark lighting, style of Lullorin",
                "motion": "zoom_out_slow"
            },
            {
                "scene_id": 3,
                "narration": "Rule Number One: Do not make any sudden movement or turn on the main light. Sudden light lets it lock onto your exact position.",
                "visual_prompt": f"Over-the-shoulder POV 2D dark pictogram shot, white pictogram hand trembling near a dark wall switch in {loc}, dim red rim light, style of NightoraVideos",
                "motion": "zoom_in_slow"
            },
            {
                "scene_id": 4,
                "narration": "Rule Number Two: Keep your breathing slow and steady. If your breathing speeds up, it will know you are awake and step closer.",
                "visual_prompt": f"Side profile 2D dark pictogram illustration, white character motionless in {loc} while a long pitch-black shadow stretches across the floor toward them",
                "motion": "zoom_out_slow"
            },
            {
                "scene_id": 5,
                "narration": "Rule Number Three: Never stare directly into the darkest corner for more than two seconds. It can feel when your eyes focus on its silhouette.",
                "visual_prompt": f"Low-angle 2D dark minimalist pictogram shot in {loc}, showing a {ent} lurking in the deep shadows",
                "motion": "zoom_in_slow"
            },
            {
                "scene_id": 6,
                "narration": "Rule Number Four: If you hear a quiet voice repeating your own name from the next doorway, do not answer it. It is mimicking someone you trust.",
                "visual_prompt": f"Extreme close-up 2D dark pictogram art, a slightly open dark doorway in {loc} with two glowing white pinhole eyes peeking through the gap",
                "motion": "zoom_out_slow"
            },
            {
                "scene_id": 7,
                "narration": "Rule Number Five: Hide your hands and phone screen out of sight. Even a tiny reflection of light on your face will give you away.",
                "visual_prompt": f"2D dark minimalist pictogram illustration, white character slowly hiding a dim phone screen in {loc} while {obj} remains in the foreground shadow",
                "motion": "zoom_in_slow"
            },
            {
                "scene_id": 8,
                "narration": "Rule Number Six: If the floor creaks right behind you, close your eyes tightly and count backward from thirty. Do not open them until the cold air fades.",
                "visual_prompt": f"Dramatic top-down 2D dark pictogram shot, a tall {ent} standing inches behind the motionless white pictogram character in {loc}",
                "motion": "zoom_out_slow"
            },
            {
                "scene_id": 9,
                "narration": "Rule Number Seven: Wait until 6:00 AM sunlight hits the floor before you move, and walk out without looking back once.",
                "visual_prompt": f"Wide 2D dark minimalist pictogram shot, pale morning light entering {loc} as the white character steps toward the exit without turning around",
                "motion": "zoom_in_slow"
            },
            {
                "scene_id": 10,
                "narration": "You might think surviving until sunrise means you are safe. But look closely at the floor. Those marks did not come from outside. Whatever was watching you never left.",
                "visual_prompt": f"Chilling final twist 2D dark pictogram illustration, white character looking down at dark footprints leading from {obj} straight into the shadows where two glowing white eyes stare back",
                "motion": "zoom_in_slow"
            }
        ]
    }

def generate_pro_storyboard(video_format="16:9") -> dict:
    chosen_item = random.choice(STORY_PREMISES)
    custom_topic = os.environ.get("NICHE_OVERRIDE", "").strip()
    if custom_topic:
        chosen_item = {
            "seed": custom_topic,
            "hook_title": f"DO NOT Ignore This At 3:00 AM: {custom_topic[:35]}",
            "thumb_text": "DON'T LOOK BACK",
            "location": "dark moody bedroom at 3:00 AM",
            "object": "an unsettling object in the dim room",
            "entity": "tall pitch-black shadow figure with glowing white pinhole eyes"
        }

    prompt = LULLORIN_LLM_PROMPT.format(**chosen_item)
    ua_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}
    print(f"[Brain] Generating 100% NEW @Lullorin / @NightoraVideos story: {chosen_item['seed']}")

    # 1. Try Groq API (accepts >= 4 scenes so valid 7-rule stories are NEVER rejected!)
    groq_key = rotator.get_key("GROQ_KEY")
    if groq_key:
        for groq_model in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                resp = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {groq_key}",
                        "Content-Type": "application/json",
                        "User-Agent": ua_headers["User-Agent"]
                    },
                    json={
                        "model": groq_model,
                        "messages": [
                            {"role": "system", "content": "You output only valid JSON objects."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.8,
                        "max_tokens": 3500,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=40
                )
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"]
                    data = _extract_json(raw)
                    if len(data.get("scenes", [])) >= 4:
                        print(f"[Brain] ✅ Generated Fresh AI Story via Groq ({groq_model}): {data.get('title')}")
                        return data
                else:
                    print(f"[Brain] Groq ({groq_model}) HTTP {resp.status_code}")
            except Exception as e:
                print(f"[Brain] Groq ({groq_model}) note: {e}")

    # 2. Try Gemini API
    gemini_key = rotator.get_key("GEMINI_KEY")
    if gemini_key:
        for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": 3500}
                }
                resp = requests.post(url, headers=ua_headers, json=payload, timeout=40)
                if resp.status_code == 200:
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = _extract_json(raw)
                    if len(data.get("scenes", [])) >= 4:
                        print(f"[Brain] ✅ Generated Fresh AI Story via Gemini ({model_name}): {data.get('title')}")
                        return data
                else:
                    print(f"[Brain] Gemini ({model_name}) HTTP {resp.status_code}")
            except Exception as e:
                print(f"[Brain] Gemini ({model_name}) note: {e}")

    print("[Brain] Using Built-in Dynamic @Lullorin 10-Scene Story Generator...")
    return _build_fallback_lullorin_story(chosen_item)

# ==============================================================================
# 2. PART-BY-PART VOICEOVER ENGINE (ELEVENLABS + DEEP EDGE-TTS)
# ==============================================================================
def _get_audio_duration(file_path: str) -> float:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        out = subprocess.check_output(cmd).decode("utf-8").strip()
        return max(float(out), 3.5)
    except Exception:
        return 6.0

async def _edge_tts_save(text: str, out_file: str):
    communicate = edge_tts.Communicate(text, voice="en-US-ChristopherNeural", rate="-4%", pitch="-8Hz")
    await communicate.save(out_file)

def _synthesize_scene_voice(text: str, out_file: str) -> bool:
    clean_text = text.strip()
    el_key = rotator.get_key("ELEVENLABS_KEY")
    if el_key:
        try:
            voice_id = "JBFqnCBsd6RMkjVDRZzb"
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {"xi-api-key": el_key, "Content-Type": "application/json"}
            payload = {
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.60, "similarity_boost": 0.82, "style": 0.35}
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(out_file, "wb") as f:
                    f.write(r.content)
                return True
        except Exception as e:
            print(f"[Voice] ElevenLabs note: {e}")

    try:
        asyncio.run(_edge_tts_save(clean_text, out_file))
        if os.path.exists(out_file) and os.path.getsize(out_file) > 500:
            return True
    except Exception as e:
        print(f"[Voice] Edge-TTS note: {e}")

    tts = gTTS(text=clean_text, lang="en", slow=False)
    tts.save(out_file)
    return True

def generate_voiceover(scenes: list, output_audio_path: str) -> tuple:
    os.makedirs("output/voice_parts", exist_ok=True)
    os.makedirs(os.path.dirname(output_audio_path) or "output", exist_ok=True)
    part_files = []
    durations = []

    for idx, scene in enumerate(scenes):
        part_path = f"output/voice_parts/part_{idx+1}.mp3"
        narration = scene.get("narration", "Follow this rule carefully.")
        _synthesize_scene_voice(narration, part_path)
        dur = _get_audio_duration(part_path)
        scene["duration_sec"] = round(dur, 2)
        durations.append(dur)
        part_files.append(part_path)

    concat_txt = "output/voice_parts/concat_list.txt"
    with open(concat_txt, "w") as f:
        for p in part_files:
            f.write(f"file '{os.path.abspath(p)}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_txt, "-c", "copy", output_audio_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return output_audio_path, sum(durations)

# ==============================================================================
# 3. @LULLORIN / @NIGHTORAVIDEOS AI VISUALS & THUMBNAIL ENGINE
# ==============================================================================
LULLORIN_STYLE_PROMPT = (
    "2D dark minimalist creepy pictogram animation frame in the exact style of Lullorin and NightoraVideos, "
    "smooth pure-white 2D silhouette stick-figure character with expressive frightened eyes, "
    "inside a dark moody illustrated 2D room at night, deep atmospheric shadows, subtle crimson red horror accent lighting, "
    "clean full-screen composition, high contrast, no text, no watermark, no borders: "
)

def _get_font(size: int):
    for p in [
        "resource/fonts/TitanOne-Regular.ttf",
        "resource/fonts/MicrosoftYaHeiBold.ttc",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]:
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
    return mean_val > 7.0 and dyn_range > 45

def _render_lullorin_2d_scene_canvas(width: int, height: int, idx: int) -> Image.Image:
    # Rich atmospheric 2D dark room illustration in @Lullorin style (No grids or red boxes!)
    img = Image.new("RGB", (width, height), (10, 12, 18))
    draw = ImageDraw.Draw(img)
    cx, cy = width // 2, height // 2
    sc = 1.0 if width > height else 0.78

    # Atmospheric dark room perspective walls & floor
    rx1, ry1 = cx - int(380 * sc), cy - int(220 * sc)
    rx2, ry2 = cx + int(380 * sc), cy + int(220 * sc)
    draw.polygon([(0, height), (rx1, ry2), (rx2, ry2), (width, height)], fill=(16, 19, 27))
    draw.line([(0, 0), (rx1, ry1)], fill=(30, 35, 48), width=3)
    draw.line([(width, 0), (rx2, ry1)], fill=(30, 35, 48), width=3)
    draw.line([(0, height), (rx1, ry2)], fill=(30, 35, 48), width=3)
    draw.line([(width, height), (rx2, ry2)], fill=(30, 35, 48), width=3)
    draw.rectangle([rx1, ry1, rx2, ry2], outline=(35, 40, 54), width=3)

    # Dark cracked doorway with crimson rim light & tall shadow entity with glowing white pinhole eyes
    dx = cx + int((120 if idx % 2 == 0 else -120) * sc)
    dy = ry2
    dw, dh = int(140 * sc), int(330 * sc)
    draw.rectangle([dx - dw // 2, dy - dh, dx + dw // 2, dy], fill=(4, 5, 8), outline=(115, 20, 26), width=3)
    # Tall shadow entity inside doorway
    ex, ey = dx, dy - int(220 * sc)
    draw.ellipse([ex - int(32 * sc), ey - int(32 * sc), ex + int(32 * sc), ey + int(32 * sc)], fill=(15, 8, 12))
    draw.rounded_rectangle([ex - int(36 * sc), ey + int(28 * sc), ex + int(36 * sc), dy], radius=16, fill=(12, 7, 10))
    # Glowing white pinhole eyes
    er = max(4, int(6 * sc))
    draw.ellipse([ex - int(14 * sc) - er, ey - er, ex - int(14 * sc) + er, ey + er], fill=(255, 255, 255))
    draw.ellipse([ex + int(14 * sc) - er, ey - er, ex + int(14 * sc) + er, ey + er], fill=(255, 255, 255))

    # Foreground smooth pure-white 2D @Lullorin pictogram character
    px = cx - int((150 if idx % 2 == 0 else -150) * sc)
    py = cy + int(95 * sc)
    hr = int(52 * sc)
    draw.ellipse([px - hr, py - int(150 * sc) - hr, px + hr, py - int(150 * sc) + hr], fill=(246, 246, 252))
    # Frightened dark eyes looking toward the shadow entity
    look_shift = int(10 * sc) if idx % 2 == 0 else -int(10 * sc)
    draw.ellipse([px - int(22 * sc) + look_shift, py - int(162 * sc), px - int(6 * sc) + look_shift, py - int(138 * sc)], fill=(12, 14, 20))
    draw.ellipse([px + int(6 * sc) + look_shift, py - int(162 * sc), px + int(22 * sc) + look_shift, py - int(138 * sc)], fill=(12, 14, 20))
    draw.rounded_rectangle([px - int(46 * sc), py - int(92 * sc), px + int(46 * sc), py + int(110 * sc)], radius=int(24 * sc), fill=(246, 246, 252))
    return img

def _generate_ai_pictogram_image(scene_prompt: str, width: int, height: int, seed: int, idx: int = 0) -> Image.Image:
    full_prompt = LULLORIN_STYLE_PROMPT + scene_prompt

    # 1. Try HuggingFace Free FLUX.1-schnell
    hf_token = rotator.get_key("HF_TOKEN")
    if hf_token:
        for api_url in [
            "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell",
            "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        ]:
            try:
                headers = {"Authorization": f"Bearer {hf_token}", "Accept": "image/jpeg"}
                r = requests.post(api_url, headers=headers, json={"inputs": full_prompt}, timeout=35)
                if r.status_code == 200 and len(r.content) > 4000:
                    img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                    if _is_valid_image(img):
                        print(f"[Visuals] ✅ Scene {idx+1} generated via HuggingFace FLUX.1-schnell")
                        return img
            except Exception as e:
                print(f"[Visuals] HF note: {e}")

    # 2. Try Pollinations FLUX
    short_p = (
        "2D dark minimalist creepy pictogram style Lullorin NightoraVideos, "
        "pure white smooth pictogram character in dark room at night, "
        "shadow figure with glowing white eyes, high contrast, no text: " + scene_prompt[:200]
    )
    encoded = urllib.parse.quote(short_p)
    gen_w = 1280 if width > height else 720
    gen_h = 720 if width > height else 1280
    for attempt in range(2):
        try:
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={gen_w}&height={gen_h}&seed={seed + attempt*19}&model=flux&nologo=true"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}
            r = requests.get(url, headers=headers, timeout=28)
            if r.status_code == 200 and len(r.content) > 4000:
                img = Image.open(io.BytesIO(r.content)).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                if _is_valid_image(img):
                    print(f"[Visuals] ✅ Scene {idx+1} generated via Pollinations FLUX")
                    return img
        except Exception:
            time.sleep(1)

    print(f"[Visuals] Using @Lullorin 2D Dark Room Renderer for Scene {idx+1}")
    return _render_lullorin_2d_scene_canvas(width, height, idx)

def fetch_visual_scenes(storyboard: dict, orientation="16:9") -> list:
    os.makedirs("output/scenes", exist_ok=True)
    width, height = (1920, 1080) if orientation == "16:9" else (1080, 1920)
    scenes = storyboard.get("scenes", [])
    saved_paths = []
    base_seed = random.randint(10000, 89999)

    for idx, scene in enumerate(scenes):
        out_path = f"output/scenes/scene_{orientation.replace(':', 'x')}_{idx+1}.jpg"
        v_prompt = scene.get("visual_prompt") or scene.get("narration", "")
        img = _generate_ai_pictogram_image(v_prompt, width, height, seed=base_seed + idx * 37, idx=idx)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img.save(out_path, "JPEG", quality=95)
        scene["image_path"] = out_path
        saved_paths.append(out_path)

    return saved_paths

def generate_viral_thumbnail(storyboard: dict, out_path="output/thumbnail_16x9.jpg") -> str:
    os.makedirs(os.path.dirname(out_path) or "output", exist_ok=True)
    thumb_prompt = storyboard.get(
        "thumbnail_prompt",
        "Close-up 2D dark minimalist creepy pictogram illustration in the style of Lullorin and NightoraVideos, "
        "pure white smooth pictogram character frozen in terror in dark bedroom while a pitch-black shadow figure "
        "with glowing white pinhole eyes leans out from the doorway behind them, high contrast, no text"
    )
    thumb_text = (storyboard.get("thumbnail_text") or "DON'T LOOK BACK").upper()[:20]

    img = _generate_ai_pictogram_image(thumb_prompt, 1280, 720, seed=random.randint(1000, 9999), idx=99)
    img = ImageEnhance.Contrast(img).enhance(1.20)
    draw = ImageDraw.Draw(img)

    # Classic @Lullorin / @NightoraVideos red highlight circle around the anomaly
    cx, cy = 830, 290
    for off in range(6):
        draw.ellipse([cx - 110 - off, cy - 110 - off, cx + 110 + off, cy + 110 + off], outline=(235, 20, 25))

    # Clean, massive bold typography with deep black drop-shadow (NO ugly rectangle banner!)
    font_huge = _get_font(84)
    tx, ty = 55, 565
    for dx in (-5, -3, 0, 3, 5):
        for dy in (-5, -3, 0, 3, 5):
            if dx != 0 or dy != 0:
                draw.text((tx + dx, ty + dy), thumb_text, font=font_huge, fill=(0, 0, 0))
    draw.text((tx, ty), thumb_text, font=font_huge, fill=(255, 255, 255))

    img.save(out_path, "JPEG", quality=96)
    return out_path

# ==============================================================================
# 4. FFMPEG CINEMA ANIMATOR & SUBTITLES (CLEAN OUTLINE, NO BEEPS)
# ==============================================================================
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
        words = sc.get("narration", "").split()
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

def render_master_video(scenes: list, audio_path: str, total_duration: float, output_mp4: str, orientation="16:9") -> str:
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
        z_expr = "min(zoom+0.0008,1.16)" if idx % 2 == 0 else "if(eq(on,1),1.16,max(1.0,zoom-0.0008))"

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

# ==============================================================================
# 5. MASTER ORCHESTRATOR
# ==============================================================================
def verify_video_stream(mp4_path: str) -> dict:
    try:
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-show_entries", "format=duration,size", "-of", "json", mp4_path
        ]
        info = json.loads(subprocess.check_output(cmd).decode("utf-8"))
        stream = info.get("streams", [{}])[0]
        fmt = info.get("format", {})
        return {
            "passed": True,
            "width": stream.get("width"),
            "height": stream.get("height"),
            "codec": stream.get("codec_name"),
            "duration_sec": round(float(fmt.get("duration", 0)), 2),
            "size_kb": round(int(fmt.get("size", 0)) / 1024, 1)
        }
    except Exception as e:
        return {"passed": False, "error": str(e)}

def main():
    os.makedirs("output", exist_ok=True)
    print("=================================================================")
    print("🚀 STARTING UNIFIED @LULLORIN & @NIGHTORAVIDEOS AI FACTORY")
    print("=================================================================")

    key_status = check_connected_keys()

    long_story = generate_pro_storyboard(video_format="16:9")
    print(f"[1/5] Brand New Storyboard Ready: {long_story.get('title')}")

    print("[2/5] Producing 16:9 Long-Form Video & AI Thumbnail...")
    long_audio, long_dur = generate_voiceover(long_story["scenes"], "output/long_16x9_voice.mp3")
    fetch_visual_scenes(long_story, orientation="16:9")
    long_mp4 = render_master_video(
        long_story["scenes"], long_audio, long_dur, "output/long_video_16x9.mp4", orientation="16:9"
    )
    thumb_jpg = generate_viral_thumbnail(long_story, "output/thumbnail_16x9.jpg")
    print(f"✅ Long Video & AI Thumbnail Ready: {long_mp4} ({long_dur:.1f}s)")

    print("[3/5] Producing 9:16 Viral YouTube Short...")
    short_story = copy.deepcopy(long_story)
    all_scenes = short_story.get("scenes", [])
    if len(all_scenes) > 5:
        short_story["scenes"] = [all_scenes[0], all_scenes[2], all_scenes[4], all_scenes[6], all_scenes[-1]]
    short_audio, short_dur = generate_voiceover(short_story["scenes"], "output/short_9x16_voice.mp3")
    fetch_visual_scenes(short_story, orientation="9:16")
    short_mp4 = render_master_video(
        short_story["scenes"], short_audio, short_dur, "output/short_video_9x16.mp4", orientation="9:16"
    )
    print(f"✅ Viral Short Ready: {short_mp4} ({short_dur:.1f}s)")

    pub = long_story.get("publishing_package", {})
    with open("output/publishing_package.txt", "w", encoding="utf-8") as pf:
        pf.write("=== SELECTED ORIGINAL STORY ===\n")
        pf.write(f"{long_story.get('title')}\n\n")
        pf.write("=== VIRAL TITLE IDEAS ===\n")
        for idx, t in enumerate(pub.get("title_ideas", []), 1):
            pf.write(f"{idx}. {t}\n")
        pf.write("\n=== SEO DESCRIPTION ===\n")
        pf.write(long_story.get("seo_description", "") + "\n")
        pf.write("\n=== TAGS ===\n")
        pf.write(", ".join(long_story.get("tags", [])) + "\n")

    audit = {
        "style_reference": "@Lullorin / @Nightsill-u2n / @NightoraVideos",
        "api_keys_connected": key_status,
        "title": long_story.get("title"),
        "scenes_count": len(long_story.get("scenes", [])),
        "long_video_16x9": verify_video_stream(long_mp4),
        "short_video_9x16": verify_video_stream(short_mp4),
        "thumbnail": thumb_jpg
    }
    with open("output/audit_report.json", "w", encoding="utf-8") as af:
        json.dump(audit, af, indent=2)

    print("🎉 ALL COMPLETED IN 1 SINGLE RUN!")

if __name__ == "__main__":
    main()
