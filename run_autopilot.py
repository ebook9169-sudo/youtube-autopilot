#!/usr/bin/env python3
"""
AUTONOMOUS 2D DARK-MINIMALIST HORROR ANIMATION FACTORY
======================================================
- Inspired by @Lullorin's visual style, pacing, and editing — NEVER copies the same story/script.
- Generates 100% ORIGINAL viral "Household Survival Rules" horror stories via GEMINI_KEY_1 / GROQ_KEY_1.
- No third-party channel watermark (uses 'REC // NIGHT 01 | RULE X' HUD).
- True SVG Cubic-Bezier Vector Renderer (cairosvg) with real Gaussian Glow filters & gradients.
- Real Studio Voice Pipeline: ELEVENLABS_KEY_1 -> GEMINI_KEY_1 (Gemini 2.5 Native TTS) -> Mastered Fallback.
- Outputs 16:9 Long Video, 9:16 Viral Short, 16:9 Custom Split-Door Thumbnail, Contact Sheet & Audit Report.
"""

import os
import sys
import json
import math
import time
import wave
import base64
import random
import shutil
import asyncio
import subprocess
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Ensure cairosvg is installed for true Cubic-Bezier SVG vector rendering
try:
    import cairosvg
    HAS_CAIRO = True
except Exception:
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "cairosvg"], check=True)
        import cairosvg
        HAS_CAIRO = True
    except Exception:
        HAS_CAIRO = False

try:
    import edge_tts
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "edge-tts"], check=True)
    import edge_tts

# ==============================================================================
# OUTPUT & CANVAS CONFIGURATION
# ==============================================================================
OUTPUT_DIR = Path("output")
WORK_DIR = Path("work_frames")
AUDIO_DIR = Path("work_audio")

W, H = 1920, 1080
FLOOR_Y = 895
FPS = 24

# Never put any other creator's channel name on the HUD
HUD_PREFIX = os.environ.get("CHANNEL_HUD_TAG", "REC // NIGHT 01").strip()

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "resource/fonts/MicrosoftYaHeiBold.ttc",
    "resource/fonts/TitanOne-Regular.ttf",
]
MONO_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
]


def get_font(size: int, mono: bool = False) -> ImageFont.FreeTypeFont:
    candidates = MONO_CANDIDATES if mono else FONT_CANDIDATES
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ==============================================================================
# 1. ORIGINAL STORY & SCENE DIRECTOR (GEMINI_KEY_1 / GROQ_KEY_1)
# ==============================================================================
STORY_PREMISES = [
    {
        "premise_id": "dog_hallway_3am",
        "title": "If Your Dog Ever Sits Facing Your Bedroom Door at 3:14 AM... DO NOT OPEN IT",
        "thumb_top_white": "DO NOT ",
        "thumb_top_red": "OPEN IT",
        "thumb_bubble_1": "Let me in...",
        "thumb_bubble_2": "Let me in...",
        "concept": "A late-night survival rules story where your dog suddenly wakes up, sits motionless facing your closed bedroom door, and something in the hallway starts mimicking your dad's voice asking you to unlock the door.",
    },
    {
        "premise_id": "three_knocks_window",
        "title": "If Someone Ever Knocks on Your Bedroom Door Three Times After 2 AM... STAY IN BED",
        "thumb_top_white": "STAY IN ",
        "thumb_top_red": "BED",
        "thumb_bubble_1": "Are you up?",
        "thumb_bubble_2": "Are you up?",
        "concept": "A tense psychological household horror story with 7 strict survival rules when a voice identical to your mother knocks three times after 2 AM and tests whether you are awake.",
    },
    {
        "premise_id": "kitchen_voice_call",
        "title": "If You Ever Hear Your Own Name Called From Downstairs at Night... LOCK YOUR DOOR",
        "thumb_top_white": "LOCK YOUR ",
        "thumb_top_red": "DOOR",
        "thumb_bubble_1": "Come here...",
        "thumb_bubble_2": "Come here...",
        "concept": "A chilling 7-rule household horror story where someone calls your name from the bottom of the stairs using a family member's voice, then walks up to your bedroom door to check if you're asleep.",
    },
]

SYSTEM_STORY_PROMPT = """You are the head writer and visual animation director for a top USA minimalist 2D dark-horror animation channel.
Create a 100% ORIGINAL, deeply unsettling first-person ("you") psychological "Household Survival Rules" horror story.
DO NOT copy "If Your Mom Ever Says Goodnight to You Twice". Write a fresh story based on the requested premise.

Return ONLY valid JSON (no markdown fences) with this exact structure:
{
  "title": "If ... [High CTR Viral Title]",
  "thumb_top_white": "LOCK YOUR ",
  "thumb_top_red": "DOOR",
  "thumb_bubble_1": "Short normal phrase",
  "thumb_bubble_2": "Short mimic phrase",
  "description": "YouTube SEO description...",
  "tags": ["scary stories", "horror animation", "rules horror"],
  "scenes": [
    {
      "id": 1,
      "type": "HALLWAY_3_DOORS",
      "hud": "NORMAL",
      "dur": 7.0,
      "sfx": "ambience",
      "narration": "Vivid, tense second-person narration (20-32 words)...",
      "params": {}
    }
  ]
}

CRITICAL VISUAL RULES:
- Generate between 28 and 34 scenes totaling 220 to 260 seconds.
- Every scene "type" MUST be one of these exact 14 visual templates:
  1. "HALLWAY_3_DOORS" -> params: {"mode": "empty" | "normal_parent" | "dark_entity_left" | "dark_entity_waves" | "yellow_eyed_figure", "red_bubble": "optional text"}
  2. "STAIRS_SCENE" -> params: {"bubble": "text", "is_entity": false}
  3. "BEDROOM_WIDE" -> params: {"child_state": "lying" | "head_up" | "under_blanket" | "standing_door" | "standing_door_sad", "red_bubbles": ["text"], "white_bubble": "text", "warm_window": false, "red_x_window": false, "show_bookshelf": false, "door_open_entity": false, "has_dog": false}
  4. "BED_CLOSEUP_LISTEN" -> params: {"sub_text": "-LISTEN CLOSELY.-"}
  5. "DUAL_COMPARISON" -> params: {"normal_text": "phrase", "entity_text": "phrase"}
  6. "RULE_CARD" -> params: {"rule": 3, "title": "CHECK UNDER THE DOOR"}
  7. "DOOR_GAP_CLOSEUP" -> params: {"sliding": false}
  8. "SPLIT_DOOR_CUTAWAY" -> params: {"mode": "eyes_under_gap" | "entity_standing" | "entity_listening", "red_bubble": "optional text"}
  9. "DOOR_LOCK_CLOSEUP" -> params: {"red_text": "LOCK IT NOW"}
  10. "PHONE_SCREEN" -> params: {"sender": "Mom", "msg": "Are you awake?", "time": "2:14 AM", "sub_green": "DO NOT REPLY"}
  11. "SPLIT_WALL_TWO_BEDS" -> params: {}
  12. "FLASHBACK_TABLE" -> params: {"bubble": "text", "with_sibling": false}
  13. "BEDROOM_EMPTY_NIGHTSTAND" -> params: {}
  14. "HALLWAY_2_DOORS" -> params: {"red_bubble": "optional text"}
- Optional on any scene starting a new rule (Rules 1 to 7): include `"rule_intro": {"num": 1, "title": "LOCK THE DOOR IMMEDIATELY"}` inside `"params"`.
- Progressively cover RULE 1 through RULE 7 with `"hud"` set to `"NORMAL"`, `"RULE 1"`, `"RULE 2"`, `"RULE 3"`, `"RULE 4"`, `"RULE 5"`, `"RULE 6"`, `"RULE 7"`, and `"AFTER"`.
- `"sfx"` must be one of: `"ambience"`, `"footsteps"`, `"knock"`, `"whisper"`, `"lock_click"`, `"heartbeat"`, `"phone_buzz"`, `"riser"`, `"sub_drop"`, `"clock_tick"`.
"""


def build_fallback_original_story(premise: Dict[str, str]) -> Dict[str, Any]:
    """High-retention original 32-scene story when LLM APIs are unreachable."""
    return {
        "title": "If Someone Knocks on Your Bedroom Door Three Times After 2 AM... DO NOT ANSWER",
        "thumb_top_white": "DO NOT ",
        "thumb_top_red": "ANSWER",
        "thumb_bubble_1": "Are you awake?",
        "thumb_bubble_2": "Are you awake?",
        "description": (
            "If you ever hear three slow knocks on your bedroom door after 2 AM, followed by a voice that sounds "
            "just like someone in your house... do not answer. Follow these 7 rules if you want to make it to morning.\n\n"
            "#horrorstories #animatedhorror #scarystories #ruleshorror #creepy"
        ),
        "tags": [
            "scary stories", "horror animation", "rules horror", "2d horror story",
            "creepy rules", "nightmare stories", "psychological horror", "dont answer the door"
        ],
        "scenes": [
            {"id": 1, "type": "HALLWAY_3_DOORS", "hud": "NORMAL", "dur": 7.0, "sfx": "ambience",
             "narration": "Every house makes strange settling noises after two in the morning. Most nights, the hallway outside your bedroom is completely empty and still.",
             "params": {"mode": "empty"}},
            {"id": 2, "type": "STAIRS_SCENE", "hud": "NORMAL", "dur": 7.5, "sfx": "ambience",
             "narration": "Hours earlier, you watched your mom head upstairs, turn off the landing light, and tell you she was going straight to sleep.",
             "params": {"bubble": "See you in the morning!", "is_entity": False}},
            {"id": 3, "type": "BEDROOM_WIDE", "hud": "NORMAL", "dur": 7.0, "sfx": "clock_tick",
             "narration": "By two-fifteen, your room is pitch black except for the strip of yellow hallway light glowing beneath your closed bedroom door.",
             "params": {"child_state": "lying", "has_dog": True}},
            {"id": 4, "type": "BED_CLOSEUP_LISTEN", "hud": "NORMAL", "dur": 7.5, "sfx": "knock",
             "narration": "Then, three slow, measured knocks echo against your wooden door. Right after the third knock, a voice calls out softly.",
             "params": {"sub_text": "-THREE SLOW KNOCKS.-"}},
            {"id": 5, "type": "DUAL_COMPARISON", "hud": "NORMAL", "dur": 8.0, "sfx": "whisper",
             "narration": "It uses her exact voice, down to the gentle sigh at the end. Expect the cadence is too flat, and the pause between words feels rehearsed.",
             "params": {"normal_text": "Honey, are you up?", "entity_text": "Honey... are you up?"}},
            {"id": 6, "type": "HALLWAY_3_DOORS", "hud": "NORMAL", "dur": 7.0, "sfx": "footsteps",
             "narration": "If she had actually walked from her room, you would have heard her door latch click open. The hallway was dead silent before that knock.",
             "params": {"mode": "normal_parent"}},
            {"id": 7, "type": "HALLWAY_3_DOORS", "hud": "RULE 1", "dur": 8.0, "sfx": "riser",
             "narration": "Rule number one. Never say a single word back through the door. Whatever is standing in the hallway cannot open a closed door unless you acknowledge it.",
             "params": {"mode": "dark_entity_left", "rule_intro": {"num": 1, "title": "NEVER ANSWER THROUGH THE DOOR"}}},
            {"id": 8, "type": "BEDROOM_WIDE", "hud": "RULE 1", "dur": 7.5, "sfx": "whisper",
             "narration": "It will repeat the question a second time, slightly louder, pressing its mouth right against the gap near the doorframe.",
             "params": {"child_state": "head_up", "red_bubbles": ["Honey, are you up?"], "has_dog": True}},
            {"id": 9, "type": "FLASHBACK_TABLE", "hud": "RULE 1", "dur": 7.5, "sfx": "ambience",
             "narration": "It builds its vocabulary by listening through the vents during dinner, stitching together phrases it heard your family say earlier that evening.",
             "params": {"bubble": "Did you lock the back door?", "with_sibling": False}},
            {"id": 10, "type": "HALLWAY_3_DOORS", "hud": "RULE 2", "dur": 8.0, "sfx": "heartbeat",
             "narration": "Rule number two. Watch your dog or check the silence in the room. Animals never bark at it. Instead, they freeze and stare at the bottom hinge.",
             "params": {"mode": "dark_entity_waves", "rule_intro": {"num": 2, "title": "STAY COMPLETELY SILENT"}}},
            {"id": 11, "type": "BEDROOM_WIDE", "hud": "RULE 2", "dur": 7.5, "sfx": "heartbeat",
             "narration": "Hold your breath when you shift on the mattress. Even the rustle of sheets tells it exactly which side of the room your bed is on.",
             "params": {"child_state": "head_up", "has_dog": True}},
            {"id": 12, "type": "DOOR_LOCK_CLOSEUP", "hud": "RULE 2", "dur": 7.0, "sfx": "lock_click",
             "narration": "If your thumb is already near the deadbolt, do not turn it while it is knocking. Wait until the knocking stops completely.",
             "params": {"red_text": "DO NOT TOUCH THE LOCK YET"}},
            {"id": 13, "type": "RULE_CARD", "hud": "RULE 3", "dur": 6.0, "sfx": "sub_drop",
             "narration": "Rule number three. Always watch the strip of light underneath your bedroom door.",
             "params": {"rule": 3, "title": "WATCH THE LIGHT UNDER THE DOOR"}},
            {"id": 14, "type": "DOOR_GAP_CLOSEUP", "hud": "RULE 3", "dur": 7.5, "sfx": "ambience",
             "narration": "Look closely at the two dark breaks in the amber light. Human feet shift their weight naturally every few seconds.",
             "params": {"sliding": False}},
            {"id": 15, "type": "DOOR_GAP_CLOSEUP", "hud": "RULE 3", "dur": 7.5, "sfx": "footsteps",
             "narration": "When this thing moves away from the door, the shadows do not lift off the floorboards. They glide sideways like paper.",
             "params": {"sliding": True}},
            {"id": 16, "type": "BEDROOM_WIDE", "hud": "RULE 4", "dur": 8.0, "sfx": "riser",
             "narration": "Rule number four. The moment the shadows slide out of view, drop below your blanket line and keep your eyes off the floor gap.",
             "params": {"child_state": "under_blanket", "rule_intro": {"num": 4, "title": "HIDE BEFORE IT LOOKS UNDER"}}},
            {"id": 17, "type": "SPLIT_DOOR_CUTAWAY", "hud": "RULE 4", "dur": 8.0, "sfx": "whisper",
             "narration": "Because it has not actually left. It drops flat onto the hallway carpet and presses two pale yellow eyes against the crack under the door.",
             "params": {"mode": "eyes_under_gap"}},
            {"id": 18, "type": "BEDROOM_WIDE", "hud": "RULE 4", "dur": 7.0, "sfx": "heartbeat",
             "narration": "If it sees your ankles on the floor or catches you staring back at the crack, the Brass doorknob will start rattling violently.",
             "params": {"child_state": "under_blanket"}},
            {"id": 19, "type": "BEDROOM_WIDE", "hud": "RULE 4", "dur": 7.5, "sfx": "whisper",
             "narration": "Outside, its tone turns urgente and panicked, begging you to open the door because something is downstairs.",
             "params": {"child_state": "under_blanket", "red_bubbles": ["Open up, hurry!", "Please let me in!"]}},
            {"id": 20, "type": "SPLIT_DOOR_CUTAWAY", "hud": "RULE 4", "dur": 7.5, "sfx": "ambience",
             "narration": "Its body remains bent at a crooked angle in the hallway while it throws a terrified human voice straight into the wood.",
             "params": {"mode": "entity_standing", "red_bubble": "Something is in the house!"}},
            {"id": 21, "type": "HALLWAY_3_DOORS", "hud": "RULE 5", "dur": 7.5, "sfx": "phone_buzz",
             "narration": "Rule number five. Never reply to any text message that arrives while the shadow is outside your door.",
             "params": {"mode": "empty", "rule_intro": {"num": 5, "title": "NEVER REPLY TO NIGHT TEXTS"}}},
            {"id": 22, "type": "PHONE_SCREEN", "hud": "RULE 5", "dur": 8.0, "sfx": "phone_buzz",
             "narration": "Your phone screen will light up on the nightstand with a message from inside the house asking if you heard that noise.",
             "params": {"sender": "Mom", "msg": "Did you just knock on my door?", "time": "2:19 AM", "sub_green": "LEAVE IT UNREAD"}},
            {"id": 23, "type": "BEDROOM_EMPTY_NIGHTSTAND", "hud": "RULE 5", "dur": 7.0, "sfx": "ambience",
             "narration": "Leave the phone face up on the table. If the blue light of the screen reflects off your face, it knows you are still awake.",
             "params": {}},
            {"id": 24, "type": "HALLWAY_2_DOORS", "hud": "RULE 6", "dur": 8.0, "sfx": "footsteps",
             "narration": "Rule number six. Even if you hear footsteps move down the hall toward your sibling's or parents' room, do not step out to warn them.",
             "params": {"red_bubble": "Are you awake in there?", "rule_intro": {"num": 6, "title": "DO NOT LEAVE YOUR ROOM"}}},
            {"id": 25, "type": "SPLIT_WALL_TWO_BEDS", "hud": "RULE 6", "dur": 7.5, "sfx": "ambience",
             "narration": "Anyone truly fast asleep behind a closed door is invisible to it. It only hunts the person who reacts.",
             "params": {}},
            {"id": 26, "type": "BEDROOM_WIDE", "hud": "RULE 6", "dur": 7.5, "sfx": "heartbeat",
             "narration": "Sometimes it mimics a quiet conversation in the hallway just to trick you into pressing your ear against the door panel.",
             "params": {"child_state": "standing_door"}},
            {"id": 27, "type": "SPLIT_DOOR_CUTAWAY", "hud": "RULE 6", "dur": 8.0, "sfx": "whisper",
             "narration": "Because one inch of wood is the only thing separating your ear from its grinning face waiting on the other side.",
             "params": {"mode": "entity_listening"}},
            {"id": 28, "type": "BEDROOM_WIDE", "hud": "RULE 7", "dur": 8.0, "sfx": "clock_tick",
             "narration": "Rule number seven. Do not trust the first golden light that appears outside your bedroom window.",
             "params": {"child_state": "standing_door_sad", "warm_window": True, "rule_intro": {"num": 7, "title": "VERIFY THE WALL CLOCK BEFORE DAWN"}}},
            {"id": 29, "type": "BEDROOM_WIDE", "hud": "RULE 7", "dur": 7.5, "sfx": "riser",
             "narration": "If the glass glows like sunrise while your wall clock still reads three-thirty, look away from the window immediately.",
             "params": {"child_state": "head_up", "warm_window": True, "red_x_window": True, "show_bookshelf": True}},
            {"id": 30, "type": "BEDROOM_WIDE", "hud": "AFTER", "dur": 7.5, "sfx": "ambience",
             "narration": "Only when the clock passes six-thirty and real morning traffic hums in the distance is it finally safe to unlock the door.",
             "params": {"child_state": "standing_door", "door_open_entity": True, "white_bubble": "Morning! Did you sleep well?"}},
            {"id": 31, "type": "HALLWAY_3_DOORS", "hud": "AFTER", "dur": 7.5, "sfx": "whisper",
             "narration": "Your mom stands in the bright kitchen making coffee, swearing she never left her bed once during the night.",
             "params": {"mode": "yellow_eyed_figure", "red_bubble": "Why didn't you open the door?"}},
            {"id": 32, "type": "DOOR_LOCK_CLOSEUP", "hud": "AFTER", "dur": 7.5, "sfx": "lock_click",
             "narration": "Which is why tonight, before the clock hits two, you make sure the deadbolt clicks into place before the first knock ever comes.",
             "params": {"red_text": ""}},
        ],
    }


def generate_original_story() -> Dict[str, Any]:
    """Generates a brand-new original story via GEMINI_KEY_1 or GROQ_KEY_1."""
    premise = random.choice(STORY_PREMISES)
    user_prompt = (
        f"Write a brand-new original story using this premise:\n"
        f"Title Idea: {premise['title']}\n"
        f"Concept: {premise['concept']}\n"
        f"Remember: output ONLY valid JSON matching the exact schema with 28-32 scenes."
    )

    # 1. Try GEMINI_KEY_1 / GEMINI_KEY_2
    for key_name in ["GEMINI_KEY_1", "GEMINI_KEY_2", "GEMINI_API_KEY"]:
        api_key = os.environ.get(key_name, "").strip()
        if not api_key:
            continue
        for model in ["gemini-2.5-flash", "gemini-2.0-flash"]:
            try:
                print(f"[STORY] Requesting new original script from {key_name} ({model})...")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "systemInstruction": {"parts": [{"text": SYSTEM_STORY_PROMPT}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.85,
                        "responseMimeType": "application/json",
                    },
                }
                r = requests.post(url, json=payload, timeout=90)
                if r.status_code == 200:
                    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    data = json.loads(txt)
                    if isinstance(data.get("scenes"), list) and len(data["scenes"]) >= 20:
                        print(f"[STORY] Generated original story: '{data.get('title')}' ({len(data['scenes'])} scenes)")
                        return data
            except Exception as e:
                print(f"[STORY] {key_name} ({model}) warning: {e}")

    # 2. Try GROQ_KEY_1 / GROQ_KEY_2
    for key_name in ["GROQ_KEY_1", "GROQ_KEY_2", "GROQ_API_KEY"]:
        api_key = os.environ.get(key_name, "").strip()
        if not api_key:
            continue
        try:
            print(f"[STORY] Requesting new original script from {key_name} (llama-3.3-70b-versatile)...")
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SYSTEM_STORY_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.8,
                "response_format": {"type": "json_object"},
            }
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            if r.status_code == 200:
                txt = r.json()["choices"][0]["message"]["content"].strip()
                data = json.loads(txt)
                if isinstance(data.get("scenes"), list) and len(data["scenes"]) >= 20:
                    print(f"[STORY] Generated original story via Groq: '{data.get('title')}' ({len(data['scenes'])} scenes)")
                    return data
        except Exception as e:
            print(f"[STORY] {key_name} warning: {e}")

    print("[STORY] Using built-in original story script ('Three Knocks After 2 AM').")
    return build_fallback_original_story(premise)


# ==============================================================================
# 2. TRUE SVG CUBIC-BEZIER VECTOR ENGINE (CAIROSVG)
# ==============================================================================
SVG_DEFS = """
<defs>
  <filter id="softGlow" x="-40%" y="-40%" width="180%" height="180%">
    <feGaussianBlur stdDeviation="8" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <filter id="heavyGlow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur stdDeviation="18" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <filter id="eyeGlow" x="-100%" y="-100%" width="300%" height="300%">
    <feGaussianBlur stdDeviation="5" result="blur"/>
    <feMerge>
      <feMergeNode in="blur"/>
      <feMergeNode in="SourceGraphic"/>
    </feMerge>
  </filter>
  <radialGradient id="sconceGlow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#FFE08A" stop-opacity="0.95"/>
    <stop offset="35%" stop-color="#FF9E3D" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="#FF8000" stop-opacity="0.0"/>
  </radialGradient>
  <radialGradient id="redAura" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#E61919" stop-opacity="0.48"/>
    <stop offset="60%" stop-color="#B01010" stop-opacity="0.18"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.0"/>
  </radialGradient>
  <linearGradient id="lampCone" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#FFD470" stop-opacity="0.42"/>
    <stop offset="100%" stop-color="#FF9920" stop-opacity="0.03"/>
  </linearGradient>
  <linearGradient id="doorSpill" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#FFAE38" stop-opacity="0.90"/>
    <stop offset="45%" stop-color="#D97818" stop-opacity="0.38"/>
    <stop offset="100%" stop-color="#000000" stop-opacity="0.0"/>
  </linearGradient>
  <linearGradient id="warmWindowGrad" x1="0%" y1="0%" x2="0%" y2="100%">
    <stop offset="0%" stop-color="#FFB84D" stop-opacity="0.95"/>
    <stop offset="100%" stop-color="#CC6614" stop-opacity="0.85"/>
  </linearGradient>
</defs>
"""


def svg_protagonist_standing(
    cx: float,
    floor_y: float,
    scale: float = 1.0,
    scared: bool = True,
    sad: bool = False,
    facing: int = 1,
    yellow_eyes: bool = False,
    breath: float = 0.0,
) -> str:
    """Smooth Cubic-Bezier 2D vector rig for the protagonist."""
    s = scale
    head_y = floor_y - 168 * s + breath
    neck_y = floor_y - 128 * s + breath
    hip_y = floor_y - 58 * s
    rx = 34 * s
    ry = 36 * s

    # Smooth rounded hoodie/shirt torso with cubic beziers
    torso_path = (
        f"M {cx - 28*s:.1f},{neck_y:.1f} "
        f"C {cx - 38*s:.1f},{neck_y + 18*s:.1f} {cx - 34*s:.1f},{hip_y - 10*s:.1f} {cx - 28*s:.1f},{hip_y:.1f} "
        f"L {cx + 28*s:.1f},{hip_y:.1f} "
        f"C {cx + 34*s:.1f},{hip_y - 10*s:.1f} {cx + 38*s:.1f},{neck_y + 18*s:.1f} {cx + 28*s:.1f},{neck_y:.1f} Z"
    )

    # Legs & curved arms
    legs_arms = f"""
    <path d="M {cx - 13*s:.1f},{hip_y:.1f} L {cx - 14*s:.1f},{floor_y:.1f}" stroke="#F5F5F7" stroke-width="{max(7, int(11*s))}" stroke-linecap="round"/>
    <path d="M {cx + 13*s:.1f},{hip_y:.1f} L {cx + 14*s:.1f},{floor_y:.1f}" stroke="#F5F5F7" stroke-width="{max(7, int(11*s))}" stroke-linecap="round"/>
    """
    if scared:
        # Hands held slightly up near chest in tension
        legs_arms += f"""
        <path d="M {cx - 27*s:.1f},{neck_y + 12*s:.1f} Q {cx - 42*s:.1f},{neck_y + 38*s:.1f} {cx - 18*s:.1f},{neck_y + 46*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9*s))}" stroke-linecap="round"/>
        <path d="M {cx + 27*s:.1f},{neck_y + 12*s:.1f} Q {cx + 42*s:.1f},{neck_y + 38*s:.1f} {cx + 18*s:.1f},{neck_y + 46*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9*s))}" stroke-linecap="round"/>
        """
    else:
        legs_arms += f"""
        <path d="M {cx - 27*s:.1f},{neck_y + 10*s:.1f} Q {cx - 36*s:.1f},{neck_y + 36*s:.1f} {cx - 32*s:.1f},{hip_y - 4*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9*s))}" stroke-linecap="round"/>
        <path d="M {cx + 27*s:.1f},{neck_y + 10*s:.1f} Q {cx + 36*s:.1f},{neck_y + 36*s:.1f} {cx + 32*s:.1f},{hip_y - 4*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9*s))}" stroke-linecap="round"/>
        """

    ex_off = 5 * s * facing
    if yellow_eyes:
        eyes_svg = f"""
        <ellipse cx="{cx - 11*s + ex_off:.1f}" cy="{head_y:.1f}" rx="{6*s:.1f}" ry="{8*s:.1f}" fill="#FFE600" filter="url(#eyeGlow)"/>
        <ellipse cx="{cx + 11*s + ex_off:.1f}" cy="{head_y:.1f}" rx="{6*s:.1f}" ry="{8*s:.1f}" fill="#FFE600" filter="url(#eyeGlow)"/>
        """
    else:
        eyes_svg = f"""
        <ellipse cx="{cx - 11*s + ex_off:.1f}" cy="{head_y - 1*s:.1f}" rx="{4.5*s:.1f}" ry="{6.8*s:.1f}" fill="#0B0B0E"/>
        <ellipse cx="{cx + 11*s + ex_off:.1f}" cy="{head_y - 1*s:.1f}" rx="{4.5*s:.1f}" ry="{6.8*s:.1f}" fill="#0B0B0E"/>
        <circle cx="{cx - 12.5*s + ex_off:.1f}" cy="{head_y - 3.5*s:.1f}" r="{1.5*s:.1f}" fill="#FFFFFF"/>
        <circle cx="{cx + 9.5*s + ex_off:.1f}" cy="{head_y - 3.5*s:.1f}" r="{1.5*s:.1f}" fill="#FFFFFF"/>
        """

    # Eyebrows & mouth
    brows_mouth = ""
    if sad or scared:
        brows_mouth += f"""
        <path d="M {cx - 18*s + ex_off:.1f},{head_y - 11*s:.1f} Q {cx - 11*s + ex_off:.1f},{head_y - 15*s:.1f} {cx - 5*s + ex_off:.1f},{head_y - 13*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="{max(2, int(2.6*s))}" stroke-linecap="round"/>
        <path d="M {cx + 5*s + ex_off:.1f},{head_y - 13*s:.1f} Q {cx + 11*s + ex_off:.1f},{head_y - 15*s:.1f} {cx + 18*s + ex_off:.1f},{head_y - 11*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="{max(2, int(2.6*s))}" stroke-linecap="round"/>
        """
    if scared:
        brows_mouth += f"""
        <ellipse cx="{cx + ex_off:.1f}" cy="{head_y + 13*s:.1f}" rx="{4.8*s:.1f}" ry="{6.2*s:.1f}" fill="#0B0B0E"/>
        <path d="M {cx - 23*s:.1f},{head_y - 8*s:.1f} C {cx - 27*s:.1f},{head_y + 1*s:.1f} {cx - 19*s:.1f},{head_y + 1*s:.1f} {cx - 23*s:.1f},{head_y - 8*s:.1f} Z" fill="#9ED8FF"/>
        """
    else:
        brows_mouth += f"""
        <path d="M {cx - 6*s + ex_off:.1f},{head_y + 13*s:.1f} Q {cx + ex_off:.1f},{head_y + 10*s:.1f} {cx + 6*s + ex_off:.1f},{head_y + 13*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="{max(2, int(2.5*s))}" stroke-linecap="round"/>
        """

    return f"""
    <g>
      {legs_arms}
      <path d="{torso_path}" fill="#F5F5F7"/>
      <rect x="{cx - 8*s:.1f}" y="{neck_y - 10*s:.1f}" width="{16*s:.1f}" height="{14*s:.1f}" rx="{5*s:.1f}" fill="#F5F5F7"/>
      <ellipse cx="{cx:.1f}" cy="{head_y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#F5F5F7"/>
      {eyes_svg}
      {brows_mouth}
    </g>
    """


def svg_head_in_bed(
    cx: float,
    cy: float,
    scale: float = 1.0,
    scared: bool = True,
    facing: int = 1,
) -> str:
    """Renders ONLY the protagonist's head resting on the pillow above the blanket."""
    s = scale
    rx, ry = 32 * s, 34 * s
    ex_off = 5 * s * facing
    sweat = ""
    if scared:
        sweat = f"""
        <path d="M {cx - 20*s:.1f},{cy - 10*s:.1f} C {cx - 24*s:.1f},{cy - 1*s:.1f} {cx - 16*s:.1f},{cy - 1*s:.1f} {cx - 20*s:.1f},{cy - 10*s:.1f} Z" fill="#9ED8FF"/>
        <ellipse cx="{cx + ex_off:.1f}" cy="{cy + 12*s:.1f}" rx="{4.2*s:.1f}" ry="{5.5*s:.1f}" fill="#0B0B0E"/>
        """
    else:
        sweat = f"""
        <path d="M {cx - 5*s + ex_off:.1f},{cy + 12*s:.1f} L {cx + 5*s + ex_off:.1f},{cy + 12*s:.1f}" stroke="#0B0B0E" stroke-width="2.5" stroke-linecap="round"/>
        """

    return f"""
    <g>
      <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="#F5F5F7"/>
      <ellipse cx="{cx - 10*s + ex_off:.1f}" cy="{cy - 2*s:.1f}" rx="{4.3*s:.1f}" ry="{6.5*s:.1f}" fill="#0B0B0E"/>
      <ellipse cx="{cx + 10*s + ex_off:.1f}" cy="{cy - 2*s:.1f}" rx="{4.3*s:.1f}" ry="{6.5*s:.1f}" fill="#0B0B0E"/>
      <circle cx="{cx - 11.5*s + ex_off:.1f}" cy="{cy - 4*s:.1f}" r="{1.4*s:.1f}" fill="#FFFFFF"/>
      <circle cx="{cx + 8.5*s + ex_off:.1f}" cy="{cy - 4*s:.1f}" r="{1.4*s:.1f}" fill="#FFFFFF"/>
      <path d="M {cx - 16*s + ex_off:.1f},{cy - 11*s:.1f} Q {cx - 10*s + ex_off:.1f},{cy - 15*s:.1f} {cx - 4*s + ex_off:.1f},{cy - 12*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="2.4" stroke-linecap="round"/>
      <path d="M {cx + 4*s + ex_off:.1f},{cy - 12*s:.1f} Q {cx + 10*s + ex_off:.1f},{cy - 15*s:.1f} {cx + 16*s + ex_off:.1f},{cy - 11*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="2.4" stroke-linecap="round"/>
      {sweat}
    </g>
    """


def svg_parent_or_entity(
    cx: float,
    floor_y: float,
    scale: float = 1.0,
    mode: str = "normal",
    waving: bool = False,
    pointing: bool = False,
    head_tilt_deg: float = 0.0,
) -> str:
    """
    Smooth Cubic-Bezier silhouette for the Mother / Entity figure.
    mode: 'normal', 'dark_head', 'creepy_smile'
    """
    s = scale
    head_y = floor_y - 292 * s
    shoulder_y = floor_y - 238 * s
    waist_y = floor_y - 165 * s
    hem_y = floor_y - 36 * s

    # Flowing dress/gown with smooth cubic bezier curves
    dress_path = (
        f"M {cx - 28*s:.1f},{shoulder_y:.1f} "
        f"Q {cx:.1f},{shoulder_y - 6*s:.1f} {cx + 28*s:.1f},{shoulder_y:.1f} "
        f"C {cx + 34*s:.1f},{shoulder_y + 28*s:.1f} {cx + 22*s:.1f},{waist_y - 12*s:.1f} {cx + 23*s:.1f},{waist_y:.1f} "
        f"C {cx + 38*s:.1f},{waist_y + 45*s:.1f} {cx + 50*s:.1f},{hem_y - 25*s:.1f} {cx + 52*s:.1f},{hem_y:.1f} "
        f"Q {cx:.1f},{hem_y + 8*s:.1f} {cx - 52*s:.1f},{hem_y:.1f} "
        f"C {cx - 50*s:.1f},{hem_y - 25*s:.1f} {cx - 38*s:.1f},{waist_y + 45*s:.1f} {cx - 23*s:.1f},{waist_y:.1f} "
        f"C {cx - 22*s:.1f},{waist_y - 12*s:.1f} {cx - 34*s:.1f},{shoulder_y + 28*s:.1f} {cx - 28*s:.1f},{shoulder_y:.1f} Z"
    )

    # Legs & neck
    base_parts = f"""
    <path d="M {cx - 13*s:.1f},{hem_y - 4*s:.1f} L {cx - 14*s:.1f},{floor_y:.1f}" stroke="#F5F5F7" stroke-width="{max(6, int(10*s))}" stroke-linecap="round"/>
    <path d="M {cx + 13*s:.1f},{hem_y - 4*s:.1f} L {cx + 14*s:.1f},{floor_y:.1f}" stroke="#F5F5F7" stroke-width="{max(6, int(10*s))}" stroke-linecap="round"/>
    <rect x="{cx - 7*s:.1f}" y="{shoulder_y - 22*s:.1f}" width="{14*s:.1f}" height="{26*s:.1f}" rx="{5*s:.1f}" fill="#F5F5F7"/>
    <path d="{dress_path}" fill="#F5F5F7"/>
    """

    # Arms
    if waving:
        arms = f"""
        <path d="M {cx - 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx - 48*s:.1f},{shoulder_y + 55*s:.1f} {cx - 38*s:.1f},{waist_y + 15*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        <path d="M {cx + 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx + 62*s:.1f},{shoulder_y - 12*s:.1f} {cx + 76*s:.1f},{head_y - 8*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        <circle cx="{cx + 77*s:.1f}" cy="{head_y - 10*s:.1f}" r="{7*s:.1f}" fill="#F5F5F7"/>
        """
    elif pointing:
        arms = f"""
        <path d="M {cx - 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx - 45*s:.1f},{shoulder_y + 52*s:.1f} {cx - 36*s:.1f},{waist_y + 18*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        <path d="M {cx + 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx + 66*s:.1f},{shoulder_y + 4*s:.1f} {cx + 105*s:.1f},{shoulder_y - 4*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        """
    else:
        arms = f"""
        <path d="M {cx - 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx - 46*s:.1f},{shoulder_y + 58*s:.1f} {cx - 36*s:.1f},{waist_y + 24*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        <path d="M {cx + 27*s:.1f},{shoulder_y + 8*s:.1f} Q {cx + 46*s:.1f},{shoulder_y + 58*s:.1f} {cx + 36*s:.1f},{waist_y + 24*s:.1f}" fill="none" stroke="#F5F5F7" stroke-width="{max(6, int(9.5*s))}" stroke-linecap="round"/>
        """

    # Head & face inside optional rotation group
    tilt = head_tilt_deg if head_tilt_deg != 0 else (-14.0 if mode == "creepy_smile" else 0.0)
    if mode == "normal":
        head_group = f"""
        <g transform="rotate({tilt:.1f} {cx:.1f} {head_y:.1f})">
          <circle cx="{cx:.1f}" cy="{head_y - 34*s:.1f}" r="{15*s:.1f}" fill="#D8D8DE"/>
          <ellipse cx="{cx:.1f}" cy="{head_y:.1f}" rx="{31*s:.1f}" ry="{34*s:.1f}" fill="#F5F5F7"/>
          <path d="M {cx - 31*s:.1f},{head_y - 6*s:.1f} Q {cx:.1f},{head_y - 36*s:.1f} {cx + 31*s:.1f},{head_y - 6*s:.1f}" fill="none" stroke="#E2E2E8" stroke-width="{4*s:.1f}"/>
          <circle cx="{cx - 10*s:.1f}" cy="{head_y - 3*s:.1f}" r="{3.6*s:.1f}" fill="#0B0B0E"/>
          <circle cx="{cx + 10*s:.1f}" cy="{head_y - 3*s:.1f}" r="{3.6*s:.1f}" fill="#0B0B0E"/>
          <path d="M {cx - 9*s:.1f},{head_y + 10*s:.1f} Q {cx:.1f},{head_y + 18*s:.1f} {cx + 9*s:.1f},{head_y + 10*s:.1f}" fill="none" stroke="#0B0B0E" stroke-width="{2.6*s:.1f}" stroke-linecap="round"/>
        </g>
        """
    elif mode == "dark_head":
        head_group = f"""
        <g transform="rotate({tilt:.1f} {cx:.1f} {head_y:.1f})">
          <circle cx="{cx:.1f}" cy="{head_y - 34*s:.1f}" r="{14*s:.1f}" fill="#141418" stroke="#3A3A44" stroke-width="1.5"/>
          <ellipse cx="{cx:.1f}" cy="{head_y:.1f}" rx="{31*s:.1f}" ry="{34*s:.1f}" fill="#0C0C10" stroke="#454552" stroke-width="2"/>
        </g>
        """
    else:  # creepy_smile
        teeth_lines = ""
        for tx in range(-14, 16, 6):
            teeth_lines += f'<line x1="{cx + tx*s:.1f}" y1="{head_y + 8*s:.1f}" x2="{cx + tx*s:.1f}" y2="{head_y + 21*s:.1f}" stroke="#111115" stroke-width="{1.6*s:.1f}"/>'
        head_group = f"""
        <g transform="rotate({tilt:.1f} {cx:.1f} {head_y:.1f})">
          <circle cx="{cx + 5*s:.1f}" cy="{head_y - 34*s:.1f}" r="{14*s:.1f}" fill="#141418" stroke="#4A4A55" stroke-width="1.5"/>
          <ellipse cx="{cx:.1f}" cy="{head_y:.1f}" rx="{32*s:.1f}" ry="{35*s:.1f}" fill="#0D0D12" stroke="#D8D8E0" stroke-width="2.2"/>
          <ellipse cx="{cx - 11*s:.1f}" cy="{head_y - 5*s:.1f}" rx="{6.5*s:.1f}" ry="{5.0*s:.1f}" fill="#FFE600" filter="url(#eyeGlow)"/>
          <ellipse cx="{cx + 11*s:.1f}" cy="{head_y - 5*s:.1f}" rx="{6.5*s:.1f}" ry="{5.0*s:.1f}" fill="#FFE600" filter="url(#eyeGlow)"/>
          <circle cx="{cx - 11*s:.1f}" cy="{head_y - 5*s:.1f}" r="{1.8*s:.1f}" fill="#000000"/>
          <circle cx="{cx + 11*s:.1f}" cy="{head_y - 5*s:.1f}" r="{1.8*s:.1f}" fill="#000000"/>
          <path d="M {cx - 19*s:.1f},{head_y + 7*s:.1f} Q {cx:.1f},{head_y + 28*s:.1f} {cx + 19*s:.1f},{head_y + 7*s:.1f} Z" fill="#F5F5F7" stroke="#111115" stroke-width="1.5"/>
          {teeth_lines}
        </g>
        """

    return f"<g>{base_parts}{arms}{head_group}</g>"


def svg_dog_silhouette(cx: float, floor_y: float, scale: float = 1.0) -> str:
    """Alert dog sitting on the bedroom floor staring toward the door."""
    s = scale
    return f"""
    <g>
      <!-- Body & Haunches -->
      <path d="M {cx - 26*s:.1f},{floor_y:.1f}
               C {cx - 30*s:.1f},{floor_y - 36*s:.1f} {cx - 14*s:.1f},{floor_y - 68*s:.1f} {cx + 6*s:.1f},{floor_y - 72*s:.1f}
               C {cx + 22*s:.1f},{floor_y - 74*s:.1f} {cx + 24*s:.1f},{floor_y - 38*s:.1f} {cx + 22*s:.1f},{floor_y:.1f} Z"
            fill="#E8E8EE"/>
      <!-- Head & Snout facing right toward the door -->
      <circle cx="{cx + 12*s:.1f}" cy="{floor_y - 84*s:.1f}" r="{18*s:.1f}" fill="#E8E8EE"/>
      <path d="M {cx + 24*s:.1f},{floor_y - 90*s:.1f} L {cx + 42*s:.1f},{floor_y - 84*s:.1f} L {cx + 24*s:.1f},{floor_y - 75*s:.1f} Z" fill="#E8E8EE"/>
      <!-- Perked Ears -->
      <path d="M {cx + 2*s:.1f},{floor_y - 98*s:.1f} L {cx + 8*s:.1f},{floor_y - 118*s:.1f} L {cx + 18*s:.1f},{floor_y - 98*s:.1f} Z" fill="#E8E8EE"/>
      <!-- Tail -->
      <path d="M {cx - 24*s:.1f},{floor_y - 12*s:.1f} Q {cx - 46*s:.1f},{floor_y - 26*s:.1f} {cx - 40*s:.1f},{floor_y - 44*s:.1f}" fill="none" stroke="#E8E8EE" stroke-width="{6*s:.1f}" stroke-linecap="round"/>
      <!-- Focused Eye -->
      <circle cx="{cx + 20*s:.1f}" cy="{floor_y - 87*s:.1f}" r="{2.8*s:.1f}" fill="#0B0B0E"/>
    </g>
    """


def svg_speech_bubble(
    cx: float,
    cy: float,
    text: str,
    is_red: bool = False,
    tail_dir: str = "down_left",
) -> str:
    """Clean vector speech bubble with optional crimson glow."""
    clean = xml_escape(text)
    bw = max(210, min(680, len(text) * 18 + 64))
    bh = 68
    x1, y1 = cx - bw / 2, cy - bh / 2
    x2, y2 = cx + bw / 2, cy + bh / 2

    if tail_dir == "down_left":
        tail = f"M {cx - 24:.1f},{y2 - 2:.1f} L {cx - 48:.1f},{y2 + 24:.1f} L {cx + 2:.1f},{y2 - 2:.1f} Z"
    elif tail_dir == "down_right":
        tail = f"M {cx - 2:.1f},{y2 - 2:.1f} L {cx + 48:.1f},{y2 + 24:.1f} L {cx + 24:.1f},{y2 - 2:.1f} Z"
    else:
        tail = f"M {cx - 16:.1f},{y2 - 2:.1f} L {cx:.1f},{y2 + 22:.1f} L {cx + 16:.1f},{y2 - 2:.1f} Z"

    if is_red:
        return f"""
        <g>
          <ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{bw*0.65:.1f}" ry="{bh*0.95:.1f}" fill="url(#redAura)"/>
          <rect x="{x1:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="16" fill="#C81919" stroke="#FF5252" stroke-width="2.5" filter="url(#softGlow)"/>
          <path d="{tail}" fill="#C81919"/>
          <text x="{cx:.1f}" y="{cy + 9:.1f}" fill="#FFFFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{clean}</text>
        </g>
        """
    else:
        return f"""
        <g>
          <rect x="{x1:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="16" fill="#F5F5F7" stroke="#D0D0D8" stroke-width="2"/>
          <path d="{tail}" fill="#F5F5F7"/>
          <text x="{cx:.1f}" y="{cy + 9:.1f}" fill="#0D0D12" font-family="DejaVu Sans, Arial, sans-serif" font-size="26" font-weight="bold" text-anchor="middle">{clean}</text>
        </g>
        """


def svg_sound_waves(cx: float, cy: float, count: int = 3, facing_right: bool = True, color: str = "#FFFFFF") -> str:
    out = ""
    for i in range(count):
        r = 26 + i * 20
        if facing_right:
            out += f'<path d="M {cx + r*0.5:.1f},{cy - r*0.7:.1f} Q {cx + r*1.15:.1f},{cy:.1f} {cx + r*0.5:.1f},{cy + r*0.7:.1f}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>'
        else:
            out += f'<path d="M {cx - r*0.5:.1f},{cy - r*0.7:.1f} Q {cx - r*1.15:.1f},{cy:.1f} {cx - r*0.5:.1f},{cy + r*0.7:.1f}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>'
    return out


def svg_sconce(cx: float, cy: float) -> str:
    return f"""
    <g>
      <circle cx="{cx:.1f}" cy="{cy:.1f}" r="85" fill="url(#sconceGlow)"/>
      <rect x="{cx - 10:.1f}" y="{cy - 14:.1f}" width="20" height="26" rx="4" fill="#FFE699" stroke="#AA7722" stroke-width="1.5"/>
      <rect x="{cx - 6:.1f}" y="{cy + 12:.1f}" width="12" height="5" fill="#775522"/>
    </g>
    """


def svg_bed(bed_x: float, floor_y: float, child_state: str = "head_up") -> str:
    """Clean vector bed with slatted headboard, pillow, protagonist head, and curved blanket mound."""
    slats = ""
    for sx in range(int(bed_x + 8), int(bed_x + 32), 7):
        slats += f'<line x1="{sx}" y1="{floor_y - 210}" x2="{sx}" y2="{floor_y - 80}" stroke="#3A281B" stroke-width="2"/>'

    head_svg = ""
    if child_state in ("lying", "head_up"):
        head_svg = svg_head_in_bed(
            bed_x + 115,
            floor_y - 142 if child_state == "head_up" else floor_y - 130,
            scale=0.95,
            scared=(child_state == "head_up"),
            facing=1,
        )

    blanket_top = floor_y - 148 if child_state != "under_blanket" else floor_y - 165
    blanket_path = (
        f"M {bed_x + 88:.1f},{floor_y - 88:.1f} "
        f"C {bed_x + 120:.1f},{blanket_top:.1f} {bed_x + 310:.1f},{blanket_top - 12:.1f} {bed_x + 412:.1f},{floor_y - 88:.1f} Z"
    )

    return f"""
    <g>
      <!-- Headboard & Frame -->
      <rect x="{bed_x:.1f}" y="{floor_y - 220:.1f}" width="36" height="220" rx="4" fill="#63432B" stroke="#8C6242" stroke-width="2"/>
      {slats}
      <rect x="{bed_x + 36:.1f}" y="{floor_y - 88:.1f}" width="390" height="56" fill="#4D331F" stroke="#755034" stroke-width="2"/>
      <rect x="{bed_x + 406:.1f}" y="{floor_y - 108:.1f}" width="24" height="108" rx="3" fill="#63432B" stroke="#8C6242" stroke-width="2"/>
      <!-- Pillow -->
      <rect x="{bed_x + 46:.1f}" y="{floor_y - 122:.1f}" width="92" height="34" rx="14" fill="#E6E6EE" stroke="#B5B5C2" stroke-width="1.5"/>
      <!-- Protagonist Head on Pillow -->
      {head_svg}
      <!-- Curved Duvet/Blanket Mound -->
      <path d="{blanket_path}" fill="#26334A" stroke="#4D648D" stroke-width="2.5"/>
    </g>
    """


def build_scene_svg(scene: Dict[str, Any], t_sec: float) -> str:
    """Builds the complete 1920x1080 SVG document for a scene at time t_sec."""
    stype = scene.get("type", "BEDROOM_WIDE")
    params = scene.get("params", {})
    breath = math.sin(t_sec * 3.0) * 2.5

    # Check if this frame is within the 1.7s Rule Card intro flash
    rule_intro = params.get("rule_intro")
    if rule_intro and t_sec < 1.7:
        stype = "RULE_CARD"
        params = {"rule": rule_intro.get("num", 1), "title": rule_intro.get("title", "")}

    body = ""

    # 1. Floor line & baseboard
    if stype not in ("RULE_CARD", "PHONE_SCREEN", "DOOR_GAP_CLOSEUP", "DOOR_LOCK_CLOSEUP"):
        body += f'<line x1="0" y1="{FLOOR_Y}" x2="{W}" y2="{FLOOR_Y}" stroke="#FFFFFF" stroke-width="3"/>'

    # 2. Scene Templates
    if stype == "HALLWAY_3_DOORS":
        body += f'<rect x="0" y="{FLOOR_Y - 16}" width="{W}" height="16" fill="#2B1B10" stroke="#5A3B22" stroke-width="1"/>'
        door_xs = [360, 875, 1390]
        sconce_xs = [220, 695, 1210, 1700]
        for sx in sconce_xs:
            body += svg_sconce(sx, 360)
        for idx, dx in enumerate(door_xs):
            body += f"""
            <rect x="{dx}" y="{FLOOR_Y - 370}" width="170" height="370" fill="#101216" stroke="#8C8C98" stroke-width="3"/>
            <rect x="{dx + 16}" y="{FLOOR_Y - 350}" width="138" height="150" fill="none" stroke="#4E4E58" stroke-width="2"/>
            <rect x="{dx + 16}" y="{FLOOR_Y - 180}" width="138" height="150" fill="none" stroke="#4E4E58" stroke-width="2"/>
            <circle cx="{dx + 146}" cy="{FLOOR_Y - 175}" r="6" fill="#D9A74A"/>
            <polygon points="{dx - 10},{FLOOR_Y + 2} {dx + 180},{FLOOR_Y + 2} {dx + 225},{FLOOR_Y + 60} {dx - 55},{FLOOR_Y + 60}" fill="url(#doorSpill)"/>
            """
        mode = params.get("mode", "empty")
        if mode in ("normal_parent", "white_mom"):
            body += svg_parent_or_entity(1120, FLOOR_Y, scale=0.88, mode="normal", waving=False)
        elif mode in ("dark_entity_left", "dark_head_mom_left"):
            body += svg_parent_or_entity(530, FLOOR_Y, scale=0.88, mode="dark_head")
        elif mode in ("dark_entity_waves", "dark_head_mom_left_waves"):
            body += svg_parent_or_entity(530, FLOOR_Y, scale=0.88, mode="dark_head", pointing=True)
            body += svg_sound_waves(590, FLOOR_Y - 260, count=3, facing_right=True)
        elif mode in ("yellow_eyed_figure", "yellow_eyed_child"):
            body += svg_protagonist_standing(960, FLOOR_Y, scale=0.78, scared=False, yellow_eyes=True, breath=breath)

        if params.get("red_bubble"):
            bx = 960 if "yellow" in mode else 640
            body += svg_speech_bubble(bx, 340, params["red_bubble"], is_red=True, tail_dir="down_left")

    elif stype == "HALLWAY_2_DOORS":
        body += f'<rect x="0" y="{FLOOR_Y - 16}" width="{W}" height="16" fill="#2B1B10" stroke="#5A3B22" stroke-width="1"/>'
        for sx in [280, 960, 1640]:
            body += svg_sconce(sx, 360)
        for dx in [460, 1290]:
            body += f"""
            <rect x="{dx}" y="{FLOOR_Y - 370}" width="175" height="370" fill="#101216" stroke="#8C8C98" stroke-width="3"/>
            <circle cx="{dx + 150}" cy="{FLOOR_Y - 175}" r="6" fill="#D9A74A"/>
            <polygon points="{dx - 10},{FLOOR_Y + 2} {dx + 185},{FLOOR_Y + 2} {dx + 225},{FLOOR_Y + 60} {dx - 55},{FLOOR_Y + 60}" fill="url(#doorSpill)"/>
            """
        body += svg_parent_or_entity(960, FLOOR_Y, scale=0.90, mode="dark_head")
        if params.get("red_bubble"):
            body += svg_speech_bubble(960, 340, params["red_bubble"], is_red=True)

    elif stype in ("STAIRS_SCENE", "STAIRS_GOODNIGHT"):
        body += '<text x="205" y="185" fill="#8C8C96" font-family="DejaVu Sans Mono, monospace" font-size="25" font-weight="bold">NORMAL</text>'
        # Thermostat [o=]
        body += """
        <rect x="460" y="455" width="74" height="44" rx="5" fill="#141418" stroke="#7A7A85" stroke-width="2"/>
        <circle cx="482" cy="477" r="9" fill="none" stroke="#9A9AA6" stroke-width="2"/>
        <line x1="500" y1="471" x2="522" y2="471" stroke="#9A9AA6" stroke-width="2"/>
        <line x1="500" y1="483" x2="522" y2="483" stroke="#9A9AA6" stroke-width="2"/>
        """
        # Stairs
        sx, sy = 960, FLOOR_Y
        pts = f"{sx},{sy} "
        for i in range(11):
            pts += f"{sx + i*72},{sy - (i+1)*52} {sx + (i+1)*72},{sy - (i+1)*52} "
        pts += f"{sx + 792},{sy}"
        body += f'<polygon points="{pts}" fill="#17181D" stroke="#8C8C96" stroke-width="3"/>'
        body += f'<line x1="{sx}" y1="{sy - 135}" x2="{sx + 740}" y2="{sy - 690}" stroke="#B0B0BA" stroke-width="5"/>'
        body += svg_parent_or_entity(820, FLOOR_Y, scale=0.95, mode="normal", waving=True)
        body += svg_speech_bubble(620, 420, params.get("bubble", "Night, honey!"), is_red=params.get("is_entity", False), tail_dir="down_right")

    elif stype == "BEDROOM_WIDE":
        if params.get("show_bookshelf"):
            body += f'<rect x="75" y="{FLOOR_Y - 400}" width="175" height="400" fill="#101216" stroke="#787884" stroke-width="3"/>'
            for sy in range(FLOOR_Y - 320, FLOOR_Y, 80):
                body += f'<line x1="75" y1="{sy}" x2="250" y2="{sy}" stroke="#787884" stroke-width="3"/>'

        # Nightstand & warm lamp
        nx = 290
        body += f"""
        <polygon points="{nx + 45},{FLOOR_Y - 210} {nx - 45},{FLOOR_Y} {nx + 135},{FLOOR_Y}" fill="url(#lampCone)"/>
        <rect x="{nx}" y="{FLOOR_Y - 125}" width="92" height="125" fill="#1D1610" stroke="#7A5A3C" stroke-width="2.5"/>
        <line x1="{nx + 10}" y1="{FLOOR_Y - 65}" x2="{nx + 82}" y2="{FLOOR_Y - 65}" stroke="#7A5A3C" stroke-width="2"/>
        <circle cx="{nx + 46}" cy="{FLOOR_Y - 92}" r="4" fill="#D9A74A"/>
        <line x1="{nx + 46}" y1="{FLOOR_Y - 125}" x2="{nx + 46}" y2="{FLOOR_Y - 165}" stroke="#B5B5C0" stroke-width="4"/>
        <polygon points="{nx + 20},{FLOOR_Y - 165} {nx + 72},{FLOOR_Y - 165} {nx + 60},{FLOOR_Y - 208} {nx + 32},{FLOOR_Y - 208}" fill="#FFE49E" stroke="#C8963E" stroke-width="2"/>
        """

        # Bed & protagonist state
        cstate = params.get("child_state", "head_up")
        body += svg_bed(430, FLOOR_Y, child_state=cstate)

        # Wall Clock
        body += """
        <circle cx="640" cy="300" r="36" fill="#101216" stroke="#9A9AA6" stroke-width="3"/>
        <line x1="640" y1="300" x2="640" y2="276" stroke="#E0E0E8" stroke-width="3" stroke-linecap="round"/>
        <line x1="640" y1="300" x2="658" y2="306" stroke="#E0E0E8" stroke-width="2.5" stroke-linecap="round"/>
        """

        # 4-Pane Window
        wx, wy, ww, wh = 930, 250, 230, 260
        wfill = "url(#warmWindowGrad)" if params.get("warm_window") else "#0D1524"
        body += f"""
        <rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="{wfill}" stroke="#8E8E9A" stroke-width="3"/>
        <line x1="{wx + ww/2}" y1="{wy}" x2="{wx + ww/2}" y2="{wy + wh}" stroke="#8E8E9A" stroke-width="3"/>
        <line x1="{wx}" y1="{wy + wh/2}" x2="{wx + ww}" y2="{wy + wh/2}" stroke="#8E8E9A" stroke-width="3"/>
        """
        if not params.get("warm_window"):
            body += f'<circle cx="{wx + 170}" cy="{wy + 58}" r="22" fill="#DCE8FF"/><circle cx="{wx + 180}" cy="{wy + 52}" r="20" fill="#0D1524"/>'
        if params.get("red_x_window"):
            body += f"""
            <line x1="{wx - 15}" y1="{wy - 15}" x2="{wx + ww + 15}" y2="{wy + wh + 15}" stroke="#E61919" stroke-width="10" filter="url(#softGlow)"/>
            <line x1="{wx + ww + 15}" y1="{wy - 15}" x2="{wx - 15}" y2="{wy + wh + 15}" stroke="#E61919" stroke-width="10" filter="url(#softGlow)"/>
            """

        # Bedroom Door on Right
        dx, dw, dh = 1470, 195, 420
        body += f"""
        <rect x="{dx}" y="{FLOOR_Y - dh}" width="{dw}" height="{dh}" fill="#12141A" stroke="#A0A0AC" stroke-width="3.5"/>
        <rect x="{dx + 22}" y="{FLOOR_Y - dh + 26}" width="{dw - 44}" height="165" fill="none" stroke="#52525E" stroke-width="2"/>
        <rect x="{dx + 22}" y="{FLOOR_Y - 195}" width="{dw - 44}" height="165" fill="none" stroke="#52525E" stroke-width="2"/>
        <circle cx="{dx + 28}" cy="{FLOOR_Y - 195}" r="7" fill="#E6B84D"/>
        <polygon points="{dx},{FLOOR_Y - 6} {dx + dw},{FLOOR_Y - 6} {dx + dw + 65},{FLOOR_Y + 68} {dx - 65},{FLOOR_Y + 68}" fill="url(#doorSpill)"/>
        <rect x="{dx + 48}" y="{FLOOR_Y - 5}" width="28" height="7" fill="#08080A"/>
        <rect x="{dx + 108}" y="{FLOOR_Y - 5}" width="28" height="7" fill="#08080A"/>
        """

        if params.get("door_open_entity") or params.get("door_open_mom"):
            body += f'<rect x="{dx + 6}" y="{FLOOR_Y - dh + 6}" width="{dw - 12}" height="{dh - 12}" fill="#070709"/>'
            body += svg_parent_or_entity(dx + 96, FLOOR_Y, scale=0.88, mode="normal", waving=True)

        if cstate in ("standing_door", "standing_door_sad"):
            body += svg_protagonist_standing(dx - 95, FLOOR_Y, scale=0.92, scared=(cstate == "standing_door"), sad=(cstate == "standing_door_sad"), facing=1, breath=breath)

        if params.get("has_dog"):
            body += svg_dog_silhouette(1180, FLOOR_Y, scale=0.88)

        for idx, rb in enumerate(params.get("red_bubbles", [])):
            body += svg_speech_bubble(dx - 85, 360 + idx * 105, rb, is_red=True, tail_dir="down_right")
            body += svg_sound_waves(dx - 15, FLOOR_Y - 230, count=3, facing_right=False)

        if params.get("white_bubble"):
            body += svg_speech_bubble(dx - 110, 360, params["white_bubble"], is_red=False, tail_dir="down_right")

    elif stype == "BEDROOM_EMPTY_NIGHTSTAND":
        nx = 560
        body += f"""
        <polygon points="{nx + 60},{FLOOR_Y - 260} {nx - 70},{FLOOR_Y} {nx + 190},{FLOOR_Y}" fill="url(#lampCone)"/>
        <rect x="{nx}" y="{FLOOR_Y - 165}" width="120" height="165" fill="#1D1610" stroke="#8C6440" stroke-width="3"/>
        <polygon points="{nx + 25},{FLOOR_Y - 210} {nx + 95},{FLOOR_Y - 210} {nx + 80},{FLOOR_Y - 265} {nx + 40},{FLOOR_Y - 265}" fill="#FFE49E" stroke="#C8963E" stroke-width="2"/>
        <rect x="{nx + 165}" y="{FLOOR_Y - 172}" width="36" height="10" rx="3" fill="#66B2FF" filter="url(#softGlow)"/>
        """
        body += svg_bed(900, FLOOR_Y, child_state="under_blanket")

    elif stype == "BED_CLOSEUP_LISTEN":
        bx = 420
        body += f'<rect x="{bx}" y="250" width="58" height="645" rx="6" fill="#63432B" stroke="#8C6242" stroke-width="3"/>'
        for sx in range(bx + 12, bx + 50, 10):
            body += f'<line x1="{sx}" y1="270" x2="{sx}" y2="740" stroke="#3A281B" stroke-width="3"/>'
        body += f"""
        <rect x="{bx + 58}" y="720" width="900" height="125" fill="#4D331F" stroke="#755034" stroke-width="3"/>
        <rect x="{bx + 82}" y="650" width="210" height="70" rx="26" fill="#E6E6EE" stroke="#B5B5C2" stroke-width="2"/>
        """
        body += svg_head_in_bed(bx + 230, 560, scale=1.95, scared=True, facing=1)
        body += f'<path d="M {bx + 190},720 C {bx + 290},540 {bx + 680},530 {bx + 920},720 Z" fill="#26334A" stroke="#4D648D" stroke-width="3.5"/>'
        body += svg_sound_waves(1360, 510, count=4, facing_right=False)
        sub = xml_escape(params.get("sub_text", "-JUST LISTEN.-"))
        body += f'<text x="{W/2}" y="855" fill="#B8B8C4" font-family="DejaVu Sans, Arial, sans-serif" font-size="27" font-weight="bold" text-anchor="middle">{sub}</text>'

    elif stype in ("DUAL_COMPARISON", "DUAL_MOM_COMPARISON"):
        body += f'<line x1="{W/2}" y1="120" x2="{W/2}" y2="{FLOOR_Y}" stroke="#454552" stroke-width="3"/>'
        body += svg_parent_or_entity(520, FLOOR_Y, scale=1.18, mode="normal", waving=True)
        body += svg_speech_bubble(520, 260, params.get("normal_text", "Goodnight"), is_red=False, tail_dir="down_left")
        body += svg_parent_or_entity(1400, FLOOR_Y, scale=1.18, mode="creepy_smile", waving=False)
        body += svg_speech_bubble(1400, 260, params.get("entity_text", "Goodnight"), is_red=True, tail_dir="down_left")

    elif stype == "RULE_CARD":
        rnum = int(params.get("rule", 1))
        rtitle = xml_escape(params.get("title", "FOLLOW THE RULE"))
        body += f"""
        <rect x="{W/2 - 115}" y="275" width="230" height="58" rx="8" fill="#0D0D12" stroke="#FFFFFF" stroke-width="3"/>
        <text x="{W/2}" y="314" fill="#FFFFFF" font-family="DejaVu Sans Mono, monospace" font-size="32" font-weight="bold" text-anchor="middle">RULE {rnum}</text>
        <text x="{W/2}" y="475" fill="#FFFFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="56" font-weight="bold" text-anchor="middle">{rtitle}</text>
        """
        start_x = W // 2 - (7 * 64 + 6 * 18) // 2
        for i in range(1, 8):
            bx = start_x + (i - 1) * 82
            by = 620
            if i <= rnum:
                body += f'<rect x="{bx}" y="{by}" width="64" height="64" rx="6" fill="#FFFFFF" stroke="#FFFFFF" stroke-width="2.5"/>'
                body += f'<text x="{bx + 32}" y="{by + 43}" fill="#000000" font-family="DejaVu Sans Mono, monospace" font-size="30" font-weight="bold" text-anchor="middle">{i}</text>'
            else:
                body += f'<rect x="{bx}" y="{by}" width="64" height="64" rx="6" fill="none" stroke="#5A5A66" stroke-width="2.5"/>'
                body += f'<text x="{bx + 32}" y="{by + 43}" fill="#6A6A76" font-family="DejaVu Sans Mono, monospace" font-size="30" font-weight="bold" text-anchor="middle">{i}</text>'

    elif stype == "DOOR_GAP_CLOSEUP":
        gap_y = 660
        body += f"""
        <rect x="260" y="130" width="1400" height="{gap_y - 130}" fill="#14161D" stroke="#9A9AA8" stroke-width="4"/>
        <rect x="330" y="180" width="580" height="400" fill="none" stroke="#4E505C" stroke-width="3"/>
        <rect x="1010" y="180" width="580" height="400" fill="none" stroke="#4E505C" stroke-width="3"/>
        <polygon points="260,{gap_y} 1660,{gap_y} 1860,910 60,910" fill="url(#doorSpill)"/>
        <rect x="260" y="{gap_y - 8}" width="1400" height="18" fill="#FFE28A" filter="url(#softGlow)"/>
        """
        shift = int((t_sec * 95) % 340) if params.get("sliding") else 0
        f1, f2 = 760 + shift, 1040 + shift
        body += f"""
        <ellipse cx="{f1}" cy="{gap_y + 10}" rx="68" ry="18" fill="#050507"/>
        <ellipse cx="{f2}" cy="{gap_y + 10}" rx="68" ry="18" fill="#050507"/>
        <polygon points="{f1 - 55},{gap_y + 14} {f1 + 55},{gap_y + 14} {f1 + 120},910 {f1 - 120},910" fill="#050507" opacity="0.88"/>
        <polygon points="{f2 - 55},{gap_y + 14} {f2 + 55},{gap_y + 14} {f2 + 120},910 {f2 - 120},910" fill="#050507" opacity="0.88"/>
        """
        if params.get("sliding"):
            for ax in [520, 620, 720]:
                body += f'<path d="M {ax},{gap_y + 65} L {ax + 55},{gap_y + 65} L {ax + 40},{gap_y + 52} M {ax + 55},{gap_y + 65} L {ax + 40},{gap_y + 78}" fill="none" stroke="#FFE28A" stroke-width="3.5" stroke-linecap="round"/>'

    elif stype == "SPLIT_DOOR_CUTAWAY":
        wx = W // 2
        body += f"""
        <rect x="{wx - 18}" y="110" width="36" height="{FLOOR_Y - 110}" fill="#22242C" stroke="#FFFFFF" stroke-width="3"/>
        <circle cx="{wx - 34}" cy="{FLOOR_Y - 210}" r="9" fill="#E6B84D"/>
        <circle cx="{wx + 34}" cy="{FLOOR_Y - 210}" r="9" fill="#E6B84D"/>
        """
        mode = params.get("mode", "entity_standing")
        if mode == "eyes_under_gap":
            body += f"""
            <path d="M {wx - 360},{FLOOR_Y} C {wx - 310},{FLOOR_Y - 120} {wx - 140},{FLOOR_Y - 95} {wx - 28},{FLOOR_Y - 15} Z" fill="#F5F5F7"/>
            <ellipse cx="{wx - 95}" cy="{FLOOR_Y - 42}" rx="38" ry="32" fill="#0C0C10" stroke="#D8D8E2" stroke-width="2"/>
            <circle cx="{wx - 72}" cy="{FLOOR_Y - 38}" r="7" fill="#FFE600" filter="url(#eyeGlow)"/>
            <circle cx="{wx - 50}" cy="{FLOOR_Y - 38}" r="7" fill="#FFE600" filter="url(#eyeGlow)"/>
            <line x1="{wx - 40}" y1="{FLOOR_Y - 35}" x2="{wx + 240}" y2="{FLOOR_Y - 10}" stroke="#FFE600" stroke-width="2.5" stroke-dasharray="10,8"/>
            """
            body += svg_bed(wx + 220, FLOOR_Y, child_state="under_blanket")
        elif mode == "entity_standing":
            body += svg_parent_or_entity(wx - 230, FLOOR_Y, scale=1.08, mode="creepy_smile")
            if params.get("red_bubble"):
                body += svg_speech_bubble(wx - 260, 290, params["red_bubble"], is_red=True, tail_dir="down_right")
            body += svg_bed(wx + 220, FLOOR_Y, child_state="under_blanket")
        else:  # entity_listening
            body += svg_parent_or_entity(wx - 135, FLOOR_Y, scale=1.08, mode="creepy_smile", head_tilt_deg=14.0)
            body += svg_protagonist_standing(wx + 125, FLOOR_Y, scale=0.98, scared=True, facing=-1, breath=breath)

    elif stype == "DOOR_LOCK_CLOSEUP":
        body += """
        <line x1="680" y1="90" x2="680" y2="900" stroke="#8E8E9A" stroke-width="4"/>
        <line x1="1240" y1="90" x2="1240" y2="900" stroke="#8E8E9A" stroke-width="4"/>
        <rect x="810" y="250" width="300" height="440" rx="22" fill="#181A22" stroke="#B0B0BC" stroke-width="4"/>
        <circle cx="960" cy="380" r="68" fill="#252834" stroke="#FFFFFF" stroke-width="4"/>
        <rect x="915" y="362" width="90" height="36" rx="10" fill="#E6B84D" stroke="#FFFFFF" stroke-width="3" transform="rotate(-18 960 380)"/>
        <circle cx="960" cy="565" r="56" fill="#2A2D3A" stroke="#C8C8D4" stroke-width="4"/>
        <!-- Anatomical 2D Vector Hand & Fingers -->
        <path d="M 1480,690 L 1125,455 L 1065,535 L 1410,775 Z" fill="#F5F5F7"/>
        <ellipse cx="1075" cy="462" rx="56" ry="48" fill="#F5F5F7"/>
        <rect x="975" y="388" width="84" height="22" rx="11" fill="#F5F5F7" stroke="#181A22" stroke-width="2"/>
        <rect x="968" y="414" width="90" height="22" rx="11" fill="#F5F5F7" stroke="#181A22" stroke-width="2"/>
        <rect x="978" y="440" width="82" height="22" rx="11" fill="#F5F5F7" stroke="#181A22" stroke-width="2"/>
        <rect x="994" y="466" width="68" height="20" rx="10" fill="#F5F5F7" stroke="#181A22" stroke-width="2"/>
        <path d="M 1050,415 Q 1020,365 1055,348 Q 1090,355 1095,415 Z" fill="#F5F5F7" stroke="#181A22" stroke-width="2"/>
        """
        if params.get("red_text"):
            rt = xml_escape(params["red_text"])
            body += f'<text x="960" y="205" fill="#FF2B2B" font-family="DejaVu Sans, Arial, sans-serif" font-size="52" font-weight="bold" text-anchor="middle" filter="url(#softGlow)">{rt}</text>'

    elif stype == "PHONE_SCREEN":
        px, py, pw, ph = 690, 120, 540, 740
        sender = xml_escape(params.get("sender", "Mom"))
        msg = xml_escape(params.get("msg", "Are you awake?"))
        tm = xml_escape(params.get("time", "2:14 AM"))
        body += f"""
        <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="48" fill="#0B0C10" stroke="#B8B8C6" stroke-width="5"/>
        <rect x="{px + 185}" y="{py + 22}" width="170" height="22" rx="11" fill="#1C1D24"/>
        <circle cx="{px + pw/2}" cy="{py + 125}" r="42" fill="#2A2D38" stroke="#787888" stroke-width="2"/>
        <text x="{px + pw/2}" y="{py + 138}" fill="#FFFFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="32" font-weight="bold" text-anchor="middle">{sender[:1]}</text>
        <text x="{px + pw/2}" y="{py + 205}" fill="#FFFFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="28" font-weight="bold" text-anchor="middle">{sender}</text>
        <rect x="{px + 42}" y="{py + 275}" width="390" height="92" rx="24" fill="#232630"/>
        <text x="{px + 72}" y="{py + 330}" fill="#FFFFFF" font-family="DejaVu Sans, Arial, sans-serif" font-size="27" font-weight="bold">{msg}</text>
        <text x="{px + 52}" y="{py + 402}" fill="#828594" font-family="DejaVu Sans, Arial, sans-serif" font-size="21">{tm} · Delivered</text>
        """
        if params.get("sub_green"):
            sg = xml_escape(params["sub_green"])
            body += f'<text x="{W/2}" y="905" fill="#3CE66E" font-family="DejaVu Sans Mono, monospace" font-size="27" font-weight="bold" text-anchor="middle">{sg}</text>'

    elif stype == "SPLIT_WALL_TWO_BEDS":
        wx = W // 2
        body += f'<rect x="{wx - 16}" y="110" width="32" height="{FLOOR_Y - 110}" fill="#22242C" stroke="#FFFFFF" stroke-width="3"/>'
        body += svg_bed(230, FLOOR_Y, child_state="lying")
        body += svg_bed(wx + 230, FLOOR_Y, child_state="head_up")

    elif stype == "FLASHBACK_TABLE":
        body += '<text x="1580" y="155" fill="#8C8C96" font-family="DejaVu Sans Mono, monospace" font-size="26" font-weight="bold">EARLIER</text>'
        body += f"""
        <rect x="650" y="{FLOOR_Y - 155}" width="620" height="22" rx="4" fill="#63432B" stroke="#9E704C" stroke-width="2"/>
        <rect x="700" y="{FLOOR_Y - 133}" width="22" height="133" fill="#63432B"/>
        <rect x="1200" y="{FLOOR_Y - 133}" width="22" height="133" fill="#63432B"/>
        """
        body += svg_parent_or_entity(530, FLOOR_Y, scale=0.95, mode="normal", waving=True)
        body += svg_protagonist_standing(1360, FLOOR_Y, scale=0.86, scared=False, facing=-1)
        body += svg_speech_bubble(680, 390, params.get("bubble", "You were talking in your sleep!"), is_red=False, tail_dir="down_left")

    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#000000"/>{SVG_DEFS}{body}</svg>'


def add_hud_and_captions(
    img: Image.Image,
    hud_state: str,
    caption_line: str,
    global_t: float,
) -> Image.Image:
    """Draws the clean top HUD (without any other creator's channel name) and bottom ALL-CAPS captions."""
    draw = ImageDraw.Draw(img)
    f_hud = get_font(26, mono=True)
    f_cap = get_font(42, mono=False)

    # Top-left HUD: REC // NIGHT 01 | <STATE>
    draw.text((62, 42), f"{HUD_PREFIX}   |   {hud_state}", fill=(205, 205, 215), font=f_hud)

    # Top-right blinking red dot + timecode
    mm = int(global_t // 60)
    ss = int(global_t % 60)
    ff = int((global_t - int(global_t)) * FPS)
    tc = f"00:{mm:02d}:{ss:02d}:{ff:02d}"
    if int(global_t * 2) % 2 == 0:
        draw.ellipse([1605, 48, 1623, 66], fill=(235, 30, 30))
    draw.text((1638, 42), tc, fill=(205, 205, 215), font=f_hud)

    # Bottom centered ALL-CAPS caption below the floor line
    if caption_line:
        up = caption_line.upper()
        bbox = draw.textbbox((0, 0), up, font=f_cap)
        tw = bbox[2] - bbox[0]
        tx = (W - tw) // 2
        ty = 948
        # Crisp black stroke + white text
        for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
            draw.text((tx + ox, ty + oy), up, fill=(0, 0, 0), font=f_cap)
        draw.text((tx, ty), up, fill=(255, 255, 255), font=f_cap)

    return img


def render_svg_to_pil(svg_str: str) -> Image.Image:
    """Renders SVG string to a crisp anti-aliased 1920x1080 PIL image via CairoSVG."""
    if HAS_CAIRO:
        png_bytes = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), output_width=W, output_height=H)
        return Image.open(BytesIO(png_bytes)).convert("RGB")
    return Image.new("RGB", (W, H), (0, 0, 0))


# ==============================================================================
# 3. STUDIO VOICE ENGINE (ELEVENLABS_KEY_1 -> GEMINI_KEY_1 NATIVE TTS -> FALLBACK)
# ==============================================================================
VOICE_PROVIDER_LOCK: Optional[str] = None  # Keeps the exact same voice across all scenes!


def check_elevenlabs_quota(total_chars_needed: int) -> Tuple[bool, str]:
    """Checks if ELEVENLABS_KEY_1 has enough remaining characters for the full video."""
    for kname in ["ELEVENLABS_KEY_1", "ELEVENLABS_KEY_2", "ELEVENLABS_API_KEY"]:
        key = os.environ.get(kname, "").strip()
        if not key:
            continue
        try:
            r = requests.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": key},
                timeout=15,
            )
            if r.status_code == 200:
                sub = r.json()
                used = int(sub.get("character_count", 0))
                limit = int(sub.get("character_limit", 0))
                rem = limit - used
                print(f"[VOICE] {kname} quota remaining: {rem} chars (needed: ~{total_chars_needed})")
                if rem >= total_chars_needed + 150:
                    return True, key
            else:
                # Some API keys don't have user_read permission but still work for TTS
                return True, key
        except Exception as e:
            print(f"[VOICE] {kname} check warning: {e}")
    return False, ""


def tts_elevenlabs(text: str, out_mp3: Path, api_key: str) -> bool:
    """Generates tense, deep horror narration using ElevenLabs API."""
    # Adam (pNInz6obpgDQGcFmaJgB) - deep, calm, intense American storyteller
    voice_id = "pNInz6obpgDQGcFmaJgB"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.50,
            "similarity_boost": 0.82,
            "style": 0.28,
            "use_speaker_boost": True,
        },
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=45)
        if r.status_code == 200 and len(r.content) > 1000:
            out_mp3.write_bytes(r.content)
            return True
        print(f"[VOICE] ElevenLabs HTTP {r.status_code}: {r.text[:160]}")
    except Exception as e:
        print(f"[VOICE] ElevenLabs exception: {e}")
    return False


def tts_gemini_native(text: str, out_mp3: Path) -> bool:
    """Uses GEMINI_KEY_1 (gemini-2.5-flash-preview-tts) for natural studio horror narration."""
    for kname in ["GEMINI_KEY_1", "GEMINI_KEY_2", "GEMINI_API_KEY"]:
        api_key = os.environ.get(kname, "").strip()
        if not api_key:
            continue
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
        prompt = (
            "Read the following horror narration in a calm, low, suspenseful late-night American male storyteller voice "
            f"with natural pauses:\n\n{text}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": "Charon"}
                    }
                },
            },
        }
        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                b64_data = (
                    r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                )
                pcm_bytes = base64.b64decode(b64_data)
                raw_wav = out_mp3.with_suffix(".gemini.wav")
                with wave.open(str(raw_wav), "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(pcm_bytes)
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(raw_wav), "-ar", "44100", "-ac", "2", str(out_mp3)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
                raw_wav.unlink(missing_ok=True)
                if out_mp3.exists() and out_mp3.stat().st_size > 1000:
                    return True
        except Exception as e:
            print(f"[VOICE] Gemini Native TTS ({kname}) warning: {e}")
    return False


async def _edge_tts_fallback(text: str, out_mp3: Path):
    comm = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="-10%", pitch="-8Hz")
    await comm.save(str(out_mp3))


def master_voice_audio(in_mp3: Path, out_wav: Path) -> float:
    """Applies dark-storyteller studio EQ (warm low-end, crisp presence, compression) and returns duration."""
    raw_tmp = out_wav.with_suffix(".pre.wav")
    af_chain = (
        "highpass=f=65,"
        "equalizer=f=135:width_type=o:width=1.2:g=3.8,"
        "equalizer=f=3800:width_type=o:width=1.5:g=2.2,"
        "acompressor=threshold=-18dB:ratio=3:attack=15:release=180:makeup=2.5dB,"
        "alimiter=limit=0.95"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(in_mp3),
            "-af", af_chain,
            "-ar", "44100", "-ac", "2", str(raw_tmp)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    # Add 0.30s dramatic pause at end of each scene line
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_tmp),
            "-af", "apad=pad_dur=0.30",
            "-ar", "44100", "-ac", "2", str(out_wav)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw_tmp.unlink(missing_ok=True)
    with wave.open(str(out_wav), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def synthesize_all_scenes_voice(scenes: List[Dict[str, Any]]) -> List[Tuple[Path, float, str]]:
    """Synthesizes consistent studio narration across all scenes."""
    total_chars = sum(len(s.get("narration", "")) for s in scenes)
    has_el, el_key = check_elevenlabs_quota(total_chars)

    provider = "elevenlabs" if has_el else "gemini_or_edge"
    used_provider_name = "ElevenLabs Studio" if has_el else "Gemini 2.5 Studio / Neural Mastered"
    print(f"[VOICE] Selected primary voice engine for full video consistency: {used_provider_name}")

    results: List[Tuple[Path, float, str]] = []
    for idx, sc in enumerate(scenes):
        text = sc.get("narration", "").strip()
        mp3_path = AUDIO_DIR / f"vo_{idx:03d}.mp3"
        wav_path = AUDIO_DIR / f"vo_{idx:03d}.wav"

        ok = False
        if provider == "elevenlabs" and el_key:
            ok = tts_elevenlabs(text, mp3_path, el_key)
            if not ok:
                print("[VOICE] ElevenLabs fallback triggered -> trying Gemini 2.5 Native TTS...")
                provider = "gemini_or_edge"

        if not ok:
            ok = tts_gemini_native(text, mp3_path)
            if ok:
                used_provider_name = "Gemini 2.5 Native Audio"
            else:
                asyncio.run(_edge_tts_fallback(text, mp3_path))
                used_provider_name = "Mastered Neural Storyteller"
                # Respect rate limits between Gemini TTS requests
            time.sleep(1.2)

        dur = master_voice_audio(mp3_path, wav_path)
        results.append((wav_path, max(dur, float(sc.get("dur", 6.5))), used_provider_name))
        print(f"  -> Scene {idx+1:02d}/{len(scenes):02d} voice ready ({dur:.2f}s) [{sc.get('type')}]")

    return results


# ==============================================================================
# 4. PROCEDURAL HORROR SFX & MIXING ENGINE
# ==============================================================================
def build_scene_sfx(sfx_name: str, duration: float, out_wav: Path):
    sr = 44100
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    # Subtle dark room tone
    audio = 0.022 * np.sin(2 * np.pi * 52.0 * t) + 0.012 * np.sin(2 * np.pi * 78.0 * t)

    if sfx_name == "knock":
        for kt in [0.45, 1.05, 1.65]:
            if kt + 0.14 < duration:
                s = int(kt * sr)
                l = int(0.12 * sr)
                env = np.exp(-np.linspace(0, 26, l))
                thump = 0.45 * np.sin(2 * np.pi * 105 * np.linspace(0, 0.12, l)) * env
                audio[s:s+l] += thump

    elif sfx_name == "footsteps":
        for ft in np.arange(0.4, duration - 0.3, 0.72):
            s = int(ft * sr)
            l = int(0.11 * sr)
            if s + l < n:
                env = np.exp(-np.linspace(0, 24, l))
                audio[s:s+l] += 0.25 * np.sin(2 * np.pi * 82 * np.linspace(0, 0.11, l)) * env

    elif sfx_name == "heartbeat":
        for ht in np.arange(0.3, duration - 0.4, 0.92):
            for off, amp in [(0.0, 0.32), (0.19, 0.22)]:
                s = int((ht + off) * sr)
                l = int(0.12 * sr)
                if s + l < n:
                    env = np.exp(-np.linspace(0, 20, l))
                    audio[s:s+l] += amp * np.sin(2 * np.pi * 48 * np.linspace(0, 0.12, l)) * env

    elif sfx_name == "lock_click":
        ct = min(1.0, duration * 0.45)
        s = int(ct * sr)
        l = int(0.08 * sr)
        if s + l < n:
            env = np.exp(-np.linspace(0, 42, l))
            audio[s:s+l] += 0.42 * np.sin(2 * np.pi * 1150 * np.linspace(0, 0.08, l)) * env

    elif sfx_name == "phone_buzz":
        for bt in [0.5, 1.3]:
            if bt + 0.35 < duration:
                s = int(bt * sr)
                l = int(0.30 * sr)
                audio[s:s+l] += 0.18 * np.sin(2 * np.pi * 145 * np.linspace(0, 0.30, l))

    elif sfx_name == "riser":
        freqs = np.linspace(65, 310, n)
        audio += 0.09 * np.sin(2 * np.pi * freqs * t / sr * np.arange(n)) * np.linspace(0.1, 1.0, n)

    elif sfx_name == "sub_drop":
        l = min(n, int(1.8 * sr))
        freqs = np.linspace(110, 32, l)
        env = np.exp(-np.linspace(0, 4.5, l))
        audio[:l] += 0.38 * np.sin(2 * np.pi * freqs * np.linspace(0, 1.8, l)) * env

    audio = np.clip(audio, -0.92, 0.92)
    pcm = (audio * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm]).ravel()
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(stereo.tobytes())


# ==============================================================================
# 5. THUMBNAIL GENERATOR (MATCHES SPLIT-DOOR STYLE FOR EACH NEW STORY)
# ==============================================================================
def generate_custom_thumbnail(story: Dict[str, Any], out_jpg: Path):
    w1 = xml_escape(story.get("thumb_top_white", "LOCK YOUR "))
    w2 = xml_escape(story.get("thumb_top_red", "DOOR"))
    b1 = xml_escape(story.get("thumb_bubble_1", "Are you awake?"))
    b2 = xml_escape(story.get("thumb_bubble_2", "Are you awake?"))

    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
      <rect width="{W}" height="{H}" fill="#000000"/>
      {SVG_DEFS}
      <!-- Glowing Floor & Center Door Slab -->
      <line x1="0" y1="925" x2="{W}" y2="925" stroke="#FFFFFF" stroke-width="6" filter="url(#softGlow)"/>
      <rect x="{W//2 - 22}" y="220" width="44" height="705" rx="6" fill="#FFFFFF" filter="url(#softGlow)"/>
      <circle cx="{W//2 - 42}" cy="585" r="14" fill="#FFFFFF" filter="url(#softGlow)"/>
      <circle cx="{W//2 + 42}" cy="585" r="14" fill="#FFFFFF" filter="url(#softGlow)"/>

      <!-- Left: Grinning Yellow-Eyed Entity + Normal/Red Speech Bubbles -->
      {svg_speech_bubble(340, 390, b1, is_red=False, tail_dir="down_right")}
      {svg_speech_bubble(340, 620, b2, is_red=True, tail_dir="down_right")}
      {svg_parent_or_entity(740, 925, scale=1.55, mode="creepy_smile", head_tilt_deg=-16.0)}

      <!-- Right: Terrified Curled Protagonist Hugging Knees Against Door -->
      <g>
        <!-- Curled Torso & Knees -->
        <path d="M 1030,925 C 1015,820 1045,735 1110,745 C 1175,755 1215,830 1205,925 Z" fill="#F5F5F7"/>
        <path d="M 1135,925 C 1130,835 1175,795 1225,810 C 1265,825 1265,885 1250,925 Z" fill="#E4E4EC" stroke="#141418" stroke-width="3"/>
        <path d="M 1085,785 Q 1185,805 1225,845" fill="none" stroke="#F5F5F7" stroke-width="20" stroke-linecap="round"/>
        <!-- Terrified Head -->
        {svg_head_in_bed(1115, 675, scale=1.85, scared=True, facing=-1)}
      </g>

      <!-- Top Bold Headline -->
      <text x="{W/2}" y="155" font-family="DejaVu Sans, Arial, sans-serif" font-size="122" font-weight="bold" text-anchor="middle">
        <tspan fill="#FFFFFF">{w1}</tspan><tspan fill="#FF1E1E" filter="url(#softGlow)">{w2}</tspan>
      </text>
    </svg>
    """
    img = render_svg_to_pil(svg)
    img.save(str(out_jpg), quality=95)
    print(f"[THUMBNAIL] Saved 16:9 thumbnail -> {out_jpg}")


# ==============================================================================
# 6. VIDEO RENDERER & CONTACT SHEET VERIFIER
# ==============================================================================
def split_caption_chunks(narration: str) -> List[str]:
    words = narration.strip().split()
    if not words:
        return [""]
    chunks = []
    cur = []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) >= 36 or len(cur) >= 7:
            chunks.append(" ".join(cur))
            cur = []
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def render_full_video():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if WORK_DIR.exists():
        shutil.rmtree(WORK_DIR)
    if AUDIO_DIR.exists():
        shutil.rmtree(AUDIO_DIR)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate brand-new original story
    story = generate_original_story()
    scenes = story["scenes"]

    # 2. Generate studio narration for all scenes
    voice_data = synthesize_all_scenes_voice(scenes)

    # 3. Render each scene clip with CairoSVG + smooth camera push + SFX mix
    clip_paths: List[Path] = []
    global_t = 0.0
    used_voice_engine = voice_data[0][2] if voice_data else "Mastered Studio"

    for idx, sc in enumerate(scenes):
        vo_wav, dur, _ = voice_data[idx]
        sfx_wav = AUDIO_DIR / f"sfx_{idx:03d}.wav"
        mix_wav = AUDIO_DIR / f"mix_{idx:03d}.wav"
        build_scene_sfx(sc.get("sfx", "ambience"), dur, sfx_wav)

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(vo_wav),
                "-i", str(sfx_wav),
                "-filter_complex", "[0:a]volume=1.0[vo];[1:a]volume=0.35[sfx];[vo][sfx]amix=inputs=2:duration=first:dropout_transition=1[a]",
                "-map", "[a]", "-ar", "44100", "-ac", "2", str(mix_wav)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        # Render keyframes at 4 FPS for smooth animation & caption sync
        step_fps = 4
        n_steps = max(1, int(math.ceil(dur * step_fps)))
        chunks = split_caption_chunks(sc.get("narration", ""))
        scene_frame_dir = WORK_DIR / f"sc_{idx:03d}"
        scene_frame_dir.mkdir(parents=True, exist_ok=True)

        for step in range(n_steps):
            local_t = step / float(step_fps)
            c_idx = min(len(chunks) - 1, int((local_t / max(dur, 0.01)) * len(chunks)))
            svg_doc = build_scene_svg(sc, local_t)
            pil_img = render_svg_to_pil(svg_doc)
            pil_img = add_hud_and_captions(
                pil_img,
                sc.get("hud", "NORMAL"),
                chunks[c_idx],
                global_t + local_t,
            )
            pil_img.save(str(scene_frame_dir / f"f_{step:04d}.jpg"), quality=92)

        clip_mp4 = WORK_DIR / f"clip_{idx:03d}.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-framerate", str(step_fps),
                "-i", str(scene_frame_dir / "f_%04d.jpg"),
                "-i", str(mix_wav),
                "-vf", f"fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                "-c:a", "aac", "-b:a", "192k",
                "-t", f"{dur:.3f}",
                "-shortest",
                str(clip_mp4)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        clip_paths.append(clip_mp4)
        global_t += dur
        shutil.rmtree(scene_frame_dir, ignore_errors=True)

    # 4. Concatenate all clips into 16:9 Long Video
    concat_txt = WORK_DIR / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{c.resolve()}'" for c in clip_paths), encoding="utf-8")

    long_mp4 = OUTPUT_DIR / "long_video_16x9.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy", str(long_mp4)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    print(f"[VIDEO] Saved 16:9 Long Video ({global_t:.1f}s) -> {long_mp4}")

    # 5. Extract 9:16 Viral Short (first 56 seconds centered on action)
    short_mp4 = OUTPUT_DIR / "viral_short_9x16.mp4"
    short_dur = min(56.0, global_t)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(long_mp4),
            "-t", f"{short_dur:.2f}",
            "-vf", "crop=608:1080:656:0,scale=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            str(short_mp4)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    print(f"[SHORT] Saved 9:16 Viral Short ({short_dur:.1f}s) -> {short_mp4}")

    # 6. Generate 16:9 Custom Thumbnail
    thumb_jpg = OUTPUT_DIR / "thumbnail_16x9.jpg"
    generate_custom_thumbnail(story, thumb_jpg)

    # 7. Generate Visual Contact Sheet for Instant Inspection
    contact_jpg = OUTPUT_DIR / "contact_sheet.jpg"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(long_mp4),
            "-vf", "fps=1/7,scale=320:180,drawtext=text='%{pts\\:hms}':x=8:y=8:fontsize=16:fontcolor=yellow:box=1:boxcolor=black@0.7,tile=5x8",
            "-frames:v", "1",
            str(contact_jpg)
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    # 8. Save Publishing Package & Audit Report
    pub_txt = OUTPUT_DIR / "publishing_package.txt"
    pub_txt.write_text(
        f"TITLE:\n{story.get('title')}\n\n"
        f"DESCRIPTION:\n{story.get('description')}\n\n"
        f"TAGS:\n{', '.join(story.get('tags', []))}\n",
        encoding="utf-8",
    )

    audit_json = OUTPUT_DIR / "audit_report.json"
    audit_json.write_text(
        json.dumps(
            {
                "status": "SUCCESS",
                "original_story_title": story.get("title"),
                "hud_brand_tag": HUD_PREFIX,
                "renderer": "CairoSVG Cubic-Bezier Vector Engine" if HAS_CAIRO else "PIL Fallback",
                "voice_engine": used_voice_engine,
                "scene_count": len(scenes),
                "total_duration_seconds": round(global_t, 2),
                "outputs": {
                    "long_video_16x9": str(long_mp4),
                    "viral_short_9x16": str(short_mp4),
                    "thumbnail_16x9": str(thumb_jpg),
                    "contact_sheet": str(contact_jpg),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("[DONE] All studio outputs generated in output/ directory.")


if __name__ == "__main__":
    render_full_video()
