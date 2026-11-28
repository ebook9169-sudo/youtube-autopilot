import os
import re
import sys
import json
import math
import wave
import shutil
import random
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("Lullorin2DEngine")


# ==============================================================================
# 1. API KEY ROTATOR (FOR VOICEOVER)
# ==============================================================================
class MultiKeyRotator:
    def __init__(self):
        self.Pools: Dict[str, List[str]] = {
            "GEMINI": self._collect("GEMINI_KEY"),
            "GROQ": self._collect("GROQ_KEY"),
            "HF": self._collect("HF_TOKEN"),
            "ELEVENLABS": self._collect("ELEVENLABS_KEY"),
        }
        self.idx = {k: 0 for k in self.Pools}

    @staticmethod
    def _collect(prefix: str) -> List[str]:
        keys: List[str] = []
        for i in range(1, 10):
            val = os.environ.get(f"{prefix}_{i}", "").strip()
            if val and val not in keys:
                keys.append(val)
        single = os.environ.get(prefix, "").strip()
        if single and single not in keys:
            keys.append(single)
        return keys

    def get_key(self, service: str) -> Optional[str]:
        pool = self.Pools.get(service, [])
        if not pool:
            return None
        key = pool[self.idx[service] % len(pool)]
        self.idx[service] += 1
        return key

    def log_status(self) -> Dict[str, int]:
        summary = {}
        logger.info("====================================================")
        logger.info("🔑 API KEY DIAGNOSTICS:")
        for svc, pool in self.Pools.items():
            summary[svc] = len(pool)
            logger.info(f"   - {svc}: {'✅ READY' if pool else '⚠️ FALLBACK'}")
        logger.info("====================================================")
        return summary


rotator = MultiKeyRotator()


# ==============================================================================
# 2. COMPLETE 38-SCENE MASTER STORYBOARD (MATCHING 0s - 800s CONTACT SHEET)
# ==============================================================================
LULLORIN_MASTER_STORYBOARD: Dict[str, Any] = {
    "title": "If Your Mom Ever Says Goodnight to You Twice... LOCK YOUR DOOR",
    "hook_text": "LOCK YOUR DOOR",
    "description": (
        "If your mom ever says goodnight to you twice, lock your door immediately. "
        "These are the survival rules you must follow when the voice outside your bedroom door "
        "sounds exactly like your mother, but isn't.\n\n"
        "#lullorin #ruleshorror #scarystories #horroranimation #creepypasta #lockyourdoor"
    ),
    "tags": [
        "if your mom ever says goodnight to you twice",
        "lock your door horror",
        "lullorin",
        "minimalist 2d horror animation",
        "rules horror story",
        "scary bedtime rules",
    ],
    "scenes": [
        {
            "id": 1,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01",
            "sfx": "ambience",
            "narration": (
                "If your mom ever says goodnight to you twice, lock your bedroom door immediately. "
                "Do not call out to her, and do not step into the hallway."
            ),
            "props": {"mode": "empty"},
        },
        {
            "id": 2,
            "template": "STAIRS_GOODNIGHT",
            "hud": "NIGHT 01",
            "sfx": "none",
            "narration": (
                "The first time she says it, everything is completely normal. "
                "Maybe she waves from the bottom of the stairs, yelling it up to you before heading to her own room."
            ),
            "props": {"bubble": "Night, honey!"},
        },
        {
            "id": 3,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01",
            "sfx": "none",
            "narration": (
                "You climb into bed, pull the blanket up to your chin, and listen as the house settles into silence. "
                "Then, a few minutes later, you hear it again."
            ),
            "props": {"child_state": "lying", "lamp_on": False},
        },
        {
            "id": 4,
            "template": "BED_CLOSEUP_LISTEN",
            "hud": "NIGHT 01",
            "sfx": "heartbeat",
            "narration": (
                "A second goodnight—softer this time, coming from right outside your closed bedroom door. "
                "Do not answer. Just listen."
            ),
            "props": {},
        },
        {
            "id": 5,
            "template": "DUAL_MOM_COMPARISON",
            "hud": "NIGHT 01",
            "sfx": "whisper",
            "narration": (
                "Your real mother already went to sleep. "
                "The thing standing in the dark hallway has borrowed her voice, and it is waiting for you to invite it inside."
            ),
            "props": {},
        },
        {
            "id": 6,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "thud",
            "narration": (
                "Rule Number One: Never answer the second goodnight. "
                "Keep your mouth shut, even if she calls your name."
            ),
            "props": {"rule_num": 1, "rule_title": "NEVER ANSWER THE SECOND GOODNIGHT"},
        },
        {
            "id": 7,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "footsteps",
            "narration": (
                "When it first enters the upstairs hallway, it does not know which bedroom door belongs to you yet. "
                "It walks slowly past each closed door in the dark."
            ),
            "props": {"mode": "white_mom"},
        },
        {
            "id": 8,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "whisper",
            "narration": (
                "It repeats that single word at every doorway in the hall, listening for the slightest rustle of sheets or a sleepy voice answering back."
            ),
            "props": {"mode": "red_bubble", "bubbles": ["Goodnight"]},
        },
        {
            "id": 9,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "whisper",
            "narration": (
                "If you reply—even in a quiet whisper—it will instantly know which room you are inside. "
                "And it will not leave your door for the rest of the night."
            ),
            "props": {"child_state": "sitting", "red_bubbles": ["Goodnight"], "waves": True},
        },
        {
            "id": 10,
            "template": "FLASHBACK_TABLE",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "none",
            "narration": (
                "It learns your voice by listening to you during the day, or when you talk in your sleep. "
                "Even if your real mom laughed about it at breakfast, tonight that habit can get you killed."
            ),
            "props": {"mode": "single", "bubble": "You were talking in your sleep!"},
        },
        {
            "id": 11,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "thud",
            "narration": (
                "Rule Number Two: Check your lock before the footsteps stop. "
                "If your door is unlocked, you only have seconds to turn the deadbolt."
            ),
            "props": {"rule_num": 2, "rule_title": "LOCK YOUR DOOR IN COMPLETE SILENCE"},
        },
        {
            "id": 12,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "footsteps",
            "narration": (
                "As long as its footsteps are still moving down the hall, you can quietly slip out of bed and reach for the lock. "
                "Move slowly so the floorboards do not creak."
            ),
            "props": {"mode": "dark_head_mom"},
        },
        {
            "id": 13,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "whisper",
            "narration": (
                "If it stops at your door, it will begin stringing phrases together—saying goodnight, sleep tight, I love you—in the exact same flat tone."
            ),
            "props": {
                "child_state": "lying",
                "red_bubbles": ["Goodnight", "Sleep tight", "I love you"],
                "waves": True,
            },
        },
        {
            "id": 14,
            "template": "DOOR_LOCK_CLOSEUP",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "lock_click",
            "narration": (
                "If you are turning the lock while it is standing right on the other side, freeze immediately. "
                "If it hears the metal click while speaking, it will force the handle down."
            ),
            "props": {"show_freeze": True},
        },
        {
            "id": 15,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "thud",
            "narration": (
                "Rule Number Three: Watch the gap under your door. "
                "The hallway light underneath your door is your only warning system."
            ),
            "props": {"rule_num": 3, "rule_title": "WATCH THE GAP UNDER YOUR DOOR"},
        },
        {
            "id": 16,
            "template": "DOOR_GAP_CLOSEUP",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "ambience",
            "narration": (
                "Look at the thin strip of yellow light on the floor beneath your door. "
                "If two dark shadows block the light, that means it is standing right outside waiting for you."
            ),
            "props": {"shadows": "center"},
        },
        {
            "id": 17,
            "template": "DOOR_GAP_CLOSEUP",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "footsteps",
            "narration": (
                "Only when you see those two shadows slide completely away from the gap is it safe to exhale. "
                "Never take your eyes off that strip of light."
            ),
            "props": {"shadows": "sliding"},
        },
        {
            "id": 18,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "none",
            "narration": (
                "Whatever you do, do not kneel down on the floor to peek underneath the door gap. "
                "Stay standing or stay in your bed."
            ),
            "props": {"child_state": "standing_door", "red_x_window": True},
        },
        {
            "id": 19,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "heartbeat",
            "narration": (
                "Because the moment you lower your face to the floor, you will realize it is already lying flat on the hallway carpet—staring back at you from the bottom crack."
            ),
            "props": {"mode": "eyes_under_gap"},
        },
        {
            "id": 20,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "thud",
            "narration": (
                "Rule Number Four: Ignore every excuse it uses to make you open the door. "
                "It will try to sound gentle and forgetful."
            ),
            "props": {"rule_num": 4, "rule_title": "IGNORE EVERY EXCUSE TO OPEN THE DOOR"},
        },
        {
            "id": 21,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "knock",
            "narration": (
                "Around two in the morning, it will tap softly on the wood and say, I forgot to kiss you goodnight. "
                "Keep your eyes on the bedsheets and do not say a word."
            ),
            "props": {
                "child_state": "sitting",
                "warm_window": True,
                "red_bubbles": ["I forgot to kiss you goodnight"],
                "waves": True,
            },
        },
        {
            "id": 22,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "ambience",
            "narration": (
                "When you do not answer, the hallway will go dead silent for several minutes. "
                "Do not be fooled into thinking it walked away."
            ),
            "props": {"child_state": "sitting", "warm_window": False},
        },
        {
            "id": 23,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "heartbeat",
            "narration": (
                "Only two inches of wood separate you from what is standing out there. "
                "Your real mother would never stand motionless in the dark for an hour waiting for the latch to turn."
            ),
            "props": {"mode": "entity_standing"},
        },
        {
            "id": 24,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 5",
            "sfx": "thud",
            "narration": (
                "Rule Number Five: Do not reply to any text message from your mom after midnight. "
                "Pretend you are fast asleep."
            ),
            "props": {"rule_num": 5, "rule_title": "NEVER REPLY TO TEXTS AFTER MIDNIGHT"},
        },
        {
            "id": 25,
            "template": "PHONE_SCREEN",
            "hud": "NIGHT 01 | RULE 5",
            "sfx": "phone_ping",
            "narration": (
                "Your phone screen will light up with a message from Mom asking, Are you awake? "
                "Do not tap the screen. If the message shows as read, it knows you are listening."
            ),
            "props": {"msg": "Are you awake?"},
        },
        {
            "id": 26,
            "template": "SPLIT_WALL_TWO_BEDS",
            "hud": "NIGHT 01 | A STORY",
            "sfx": "whisper",
            "narration": (
                "A few minutes later, you may hear your mother's voice echoing softly through the bedroom wall from the room next door."
            ),
            "props": {},
        },
        {
            "id": 27,
            "template": "FLASHBACK_TABLE",
            "hud": "NIGHT 01 | A STORY",
            "sfx": "none",
            "narration": (
                "It will replay familiar sounds from your house—like laughter at the dinner table—trying to trick your brain into believing the danger has passed."
            ),
            "props": {"mode": "two_kids", "bubble": "Ha ha ha!"},
        },
        {
            "id": 28,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "thud",
            "narration": (
                "Rule Number Six: Control your breathing when the knocking turns into crying. "
                "Around three thirty AM, it will drop the calm act."
            ),
            "props": {"rule_num": 6, "rule_title": "HIDE UNDER YOUR BLANKET AND STAY SILENT"},
        },
        {
            "id": 29,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "knock",
            "narration": (
                "You will hear frantic knocking mixed with distorted sobbing and repeated goodnights. "
                "Eventually, it will stop all at once."
            ),
            "props": {
                "child_state": "sitting",
                "red_bubbles": ["Goodnight!", "(knock knock)", "(crying)"],
                "waves": True,
            },
        },
        {
            "id": 30,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "heartbeat",
            "narration": (
                "That sudden silence is a trap. It has pressed its ear flat against the outside of your door, listening for your breathing."
            ),
            "props": {"mode": "entity_listening"},
        },
        {
            "id": 31,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "ambience",
            "narration": (
                "Pull your blanket completely over your head. "
                "If you need to cough or gasp for air, bury your face deep into your pillow so no sound escapes."
            ),
            "props": {"child_state": "under_blanket"},
        },
        {
            "id": 32,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "thud",
            "narration": (
                "Rule Number Seven: Even when morning comes, ask a memory question before unlocking the door."
            ),
            "props": {"rule_num": 7, "rule_title": "TEST HER MEMORY BEFORE YOU UNLOCK IT"},
        },
        {
            "id": 33,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "none",
            "narration": (
                "When the clock passes six AM, you will want to rip that door open and run downstairs. "
                "But before your hand touches the lock, stop and think."
            ),
            "props": {"child_state": "standing_door", "warm_window": True},
        },
        {
            "id": 34,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "ambience",
            "narration": (
                "Because sometimes, it is still standing right outside in the morning shadow—waiting for you to undo the lock yourself."
            ),
            "props": {"mode": "dark_head_mom"},
        },
        {
            "id": 35,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "none",
            "narration": (
                "Through the closed door, ask her something only your real mother could know—like what she cooked for dinner the night you broke your arm."
            ),
            "props": {
                "child_state": "standing_door",
                "warm_window": True,
                "white_bubble": "What did you make the night I broke my arm?",
            },
        },
        {
            "id": 36,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "heartbeat",
            "narration": (
                "If the voice on the other side doesn't laugh, doesn't argue, or simply repeats Goodnight one more time—step back from the door."
            ),
            "props": {"child_state": "standing_door_sad", "warm_window": True},
        },
        {
            "id": 37,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | AFTER",
            "sfx": "none",
            "narration": (
                "Only when your real mom opens her own bedroom door down the hall and answers you naturally is the night truly over."
            ),
            "props": {
                "child_state": "sitting",
                "door_open_mom": True,
                "white_bubble": "Goodnight, Mom.",
            },
        },
        {
            "id": 38,
            "template": "DOOR_LOCK_CLOSEUP",
            "hud": "NIGHT 01 | AFTER",
            "sfx": "lock_click",
            "narration": (
                "Because once that thing learns your voice too, it won't need your mother's anymore. "
                "So if your mom ever says goodnight twice... lock your door."
            ),
            "props": {"show_freeze": False},
        },
    ],
}


# ==============================================================================
# 3. FONT LOADER & GEOMETRIC PRIMITIVES FOR @LULLORIN 2D VECTOR STYLE
# ==============================================================================
def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "resource/fonts/MicrosoftYaHeiBold.ttc",
        "resource/fonts/TitanOne-Regular.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                pass
    return ImageFont.load_default()


COL_BLACK = (0, 0, 0, 255)
COL_WHITE = (248, 248, 248, 255)
COL_LIGHT_GREY = (185, 185, 185, 255)
COL_MID_GREY = (105, 105, 105, 255)
COL_DARK_GREY = (42, 42, 46, 255)
COL_AMBER = (210, 128, 38, 255)
COL_AMBER_DIM = (120, 72, 22, 160)
COL_RED = (228, 28, 36, 255)
COL_YELLOW_EYE = (255, 238, 75, 255)
COL_MOON_BLUE = (108, 122, 148, 255)
COL_IOS_BLUE = (28, 118, 232, 255)

FLOOR_Y = 900


def draw_hud_and_floor(
    draw: ImageDraw.ImageDraw,
    hud_label: str,
    global_frame: int,
    fps: int,
    caption: str,
) -> None:
    font_hud = _load_font(18)
    font_cap = _load_font(30)

    draw.text((48, 32), f"LULLORIN     {hud_label}", font=font_hud, fill=(195, 195, 195, 230))

    total_sec = global_frame // fps
    ff = global_frame % fps
    mm = (total_sec // 60) % 60
    ss = total_sec % 60
    tc_str = f"00:{mm:02d}:{ss:02d}:{ff:02d}"
    if (global_frame // 12) % 2 == 0:
        draw.ellipse([1725, 36, 1737, 48], fill=COL_RED)
    draw.text((1748, 32), tc_str, font=font_hud, fill=(195, 195, 195, 230))

    draw.rectangle([0, FLOOR_Y, 1920, 1080], fill=(0, 0, 0, 255))
    draw.line([(0, FLOOR_Y), (1920, FLOOR_Y)], fill=(215, 215, 215, 255), width=3)

    if caption:
        cap_up = caption.upper()
        tb = draw.textbbox((0, 0), cap_up, font=font_cap)
        tw = tb[2] - tb[0]
        tx = (1920 - tw) // 2
        ty = FLOOR_Y + 66
        draw.text((tx, ty), cap_up, font=font_cap, fill=COL_WHITE)


def draw_speech_bubble(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    is_red: bool = False,
    tail_dir: str = "down",
    scale: float = 1.0,
) -> None:
    font_b = _load_font(max(int(24 * scale), 14))
    tb = draw.textbbox((0, 0), text, font=font_b)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    pad_x = int(24 * scale)
    pad_y = int(14 * scale)
    x0 = x - tw // 2 - pad_x
    y0 = y - th // 2 - pad_y
    x1 = x + tw // 2 + pad_x
    y1 = y + th // 2 + pad_y

    bg = COL_RED if is_red else COL_WHITE
    fg = (0, 0, 0, 255)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=int(22 * scale), fill=bg)

    if tail_dir == "down":
        draw.polygon([(x - 10, y1), (x + 10, y1), (x - 4, y1 + 16)], fill=bg)
    elif tail_dir == "left":
        draw.polygon([(x0, y - 8), (x0, y + 8), (x0 - 18, y + 6)], fill=bg)
    elif tail_dir == "right":
        draw.polygon([(x1, y - 8), (x1, y + 8), (x1 + 18, y + 6)], fill=bg)

    draw.text((x - tw // 2, y - th // 2 - 2), text, font=font_b, fill=fg)


def draw_sound_waves(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    direction: str = "left",
    phase: float = 0.0,
    count: int = 3,
) -> None:
    for i in range(count):
        r = 28 + i * 22 + int(8 * math.sin(phase * 2 * math.pi - i * 0.9))
        alpha = max(60, min(240, int(220 - i * 45)))
        bbox = [cx - r, cy - r, cx + r, cy + r]
        if direction == "left":
            draw.arc(bbox, start=135, end=225, fill=(240, 240, 240, alpha), width=3)
        elif direction == "right":
            draw.arc(bbox, start=-45, end=45, fill=(240, 240, 240, alpha), width=3)
        elif direction == "both":
            draw.arc(bbox, start=135, end=225, fill=(240, 240, 240, alpha), width=3)
            draw.arc(bbox, start=-45, end=45, fill=(240, 240, 240, alpha), width=3)


def draw_child_character(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float = 1.0,
    expr: str = "fear",
    facing: str = "right",
    sweat: bool = True,
    yellow_eyes: bool = False,
    crouching: bool = False,
) -> None:
    head_r = int(38 * scale)
    hx = x
    hy = y - int((110 if not crouching else 75) * scale)

    if crouching:
        draw.rounded_rectangle(
            [hx - int(26 * scale), hy + head_r - 4, hx + int(26 * scale), y - int(18 * scale)],
            radius=int(18 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx - int(12 * scale), y - int(48 * scale), hx + int(34 * scale), y],
            radius=int(12 * scale),
            fill=COL_WHITE,
        )
    else:
        torso_top = hy + head_r - 4
        torso_bot = y - int(42 * scale)
        draw.rounded_rectangle(
            [hx - int(24 * scale), torso_top, hx + int(24 * scale), torso_bot],
            radius=int(14 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx - int(19 * scale), torso_bot - 6, hx - int(5 * scale), y],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx + int(5 * scale), torso_bot - 6, hx + int(19 * scale), y],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx - int(33 * scale), torso_top + 6, hx - int(21 * scale), torso_bot - 4],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx + int(21 * scale), torso_top + 6, hx + int(33 * scale), torso_bot - 4],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )

    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=COL_WHITE)
    draw.arc(
        [hx - int(14 * scale), hy - head_r - int(12 * scale), hx + int(14 * scale), hy - head_r + int(10 * scale)],
        start=190,
        end=350,
        fill=COL_WHITE,
        width=max(int(3 * scale), 2),
    )

    eye_offset = int(10 * scale) if facing == "right" else (-int(10 * scale) if facing == "left" else 0)
    ex1 = hx - int(12 * scale) + eye_offset
    ex2 = hx + int(12 * scale) + eye_offset
    ey = hy - int(4 * scale)
    er = max(int(5 * scale), 3)

    if yellow_eyes:
        draw.ellipse([ex1 - er - 3, ey - er - 3, ex1 + er + 3, ey + er + 3], fill=COL_YELLOW_EYE)
        draw.ellipse([ex2 - er - 3, ey - er - 3, ex2 + er + 3, ey + er + 3], fill=COL_YELLOW_EYE)
        draw.ellipse([ex1 - 2, ey - 2, ex1 + 2, ey + 2], fill=COL_BLACK)
        draw.ellipse([ex2 - 2, ey - 2, ex2 + 2, ey + 2], fill=COL_BLACK)
    else:
        draw.ellipse([ex1 - er, ey - er, ex1 + er, ey + er], fill=COL_BLACK)
        draw.ellipse([ex2 - er, ey - er, ex2 + er, ey + er], fill=COL_BLACK)

    draw.line(
        [(ex1 - er - 2, ey - er - 6), (ex1 + er, ey - er - 10)],
        fill=COL_BLACK,
        width=max(int(3 * scale), 2),
    )
    draw.line(
        [(ex2 - er, ey - er - 10), (ex2 + er + 2, ey - er - 6)],
        fill=COL_BLACK,
        width=max(int(3 * scale), 2),
    )
    my = hy + int(14 * scale)
    if expr == "fear":
        draw.arc(
            [hx - int(12 * scale) + eye_offset, my - int(4 * scale), hx + int(12 * scale) + eye_offset, my + int(12 * scale)],
            start=195,
            end=345,
            fill=COL_BLACK,
            width=max(int(3 * scale), 2),
        )
    else:
        draw.line(
            [(hx - int(9 * scale) + eye_offset, my + 2), (hx + int(9 * scale) + eye_offset, my + 2)],
            fill=COL_BLACK,
            width=max(int(3 * scale), 2),
        )

    if sweat:
        sx = hx + head_r + int(8 * scale)
        sy = hy - int(18 * scale)
        draw.ellipse([sx, sy, sx + int(7 * scale), sy + int(12 * scale)], fill=COL_WHITE)
        draw.ellipse([sx + int(8 * scale), sy + int(12 * scale), sx + int(14 * scale), sy + int(22 * scale)], fill=COL_WHITE)


def draw_mom_figure(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float = 1.0,
    mode: str = "normal",
    waving: bool = False,
    leaning_right: bool = False,
) -> None:
    head_r = int(42 * scale)
    hx = x + (int(22 * scale) if leaning_right else 0)
    hy = y - int(255 * scale)

    hair_col = (70, 70, 75, 255) if mode == "dark_head" else (210, 210, 215, 255)
    draw.rounded_rectangle(
        [hx - head_r - int(8 * scale), hy - head_r - int(4 * scale), hx + head_r + int(8 * scale), hy + head_r + int(18 * scale)],
        radius=int(24 * scale),
        fill=hair_col,
    )

    draw.rectangle(
        [hx - int(9 * scale), hy + head_r - 4, hx + int(9 * scale), hy + head_r + int(24 * scale)],
        fill=COL_DARK_GREY if mode == "dark_head" else COL_WHITE,
    )

    dress_top = hy + head_r + int(18 * scale)
    dress_bot = y - int(68 * scale)
    body_col = (175, 175, 180, 255) if mode == "dark_head" else COL_WHITE
    draw.polygon(
        [
            (x - int(28 * scale), dress_top),
            (x + int(28 * scale), dress_top),
            (x + int(56 * scale), dress_bot),
            (x - int(56 * scale), dress_bot),
        ],
        fill=body_col,
    )

    draw.rounded_rectangle([x - int(24 * scale), dress_bot - 4, x - int(8 * scale), y], radius=6, fill=body_col)
    draw.rounded_rectangle([x + int(8 * scale), dress_bot - 4, x + int(24 * scale), y], radius=6, fill=body_col)

    if waving:
        draw.line(
            [(x - int(28 * scale), dress_top + 8), (x - int(48 * scale), dress_bot - 20)],
            fill=body_col,
            width=max(int(12 * scale), 4),
        )
        draw.line(
            [(x + int(26 * scale), dress_top + 10), (x + int(56 * scale), hy - int(20 * scale))],
            fill=body_col,
            width=max(int(12 * scale), 4),
        )
    else:
        draw.line(
            [(x - int(28 * scale), dress_top + 8), (x - int(52 * scale), dress_bot - 10)],
            fill=body_col,
            width=max(int(12 * scale), 4),
        )
        draw.line(
            [(x + int(28 * scale), dress_top + 8), (x + int(52 * scale), dress_bot - 10)],
            fill=body_col,
            width=max(int(12 * scale), 4),
        )

    head_fill = (55, 55, 60, 255) if mode == "dark_head" else COL_WHITE
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=head_fill)

    if mode == "normal":
        ey = hy - int(4 * scale)
        draw.ellipse([hx - int(16 * scale), ey - 4, hx - int(8 * scale), ey + 4], fill=COL_BLACK)
        draw.ellipse([hx + int(8 * scale), ey - 4, hx + int(16 * scale), ey + 4], fill=COL_BLACK)
        draw.arc(
            [hx - int(14 * scale), hy + int(4 * scale), hx + int(14 * scale), hy + int(20 * scale)],
            start=15,
            end=165,
            fill=COL_BLACK,
            width=max(int(3 * scale), 2),
        )
    elif mode == "entity":
        ey = hy - int(8 * scale)
        er = int(9 * scale)
        for ex in (hx - int(15 * scale), hx + int(15 * scale)):
            draw.ellipse([ex - er - 3, ey - er - 3, ex + er + 3, ey + er + 3], fill=(220, 200, 60, 120))
            draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=COL_YELLOW_EYE)
            draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=COL_BLACK)

        mouth_box = [hx - int(28 * scale), hy - int(4 * scale), hx + int(28 * scale), hy + int(30 * scale)]
        draw.chord(mouth_box, start=5, end=175, fill=COL_BLACK)
        for tx in range(hx - int(20 * scale), hx + int(22 * scale), max(int(7 * scale), 4)):
            draw.line([(tx, hy + int(6 * scale)), (tx, hy + int(24 * scale))], fill=(210, 210, 200, 220), width=2)


# ==============================================================================
# 4. SCENE TEMPLATE RENDERERS (MATCHING ALL 41 FRAMES OF CONTACT SHEET)
# ==============================================================================
def render_template_frame(
    scene: Dict[str, Any],
    t_norm: float,
    local_frame: int,
    global_frame: int,
    fps: int,
    active_caption: str,
) -> Image.Image:
    img = Image.new("RGBA", (1920, 1080), COL_BLACK)
    draw = ImageDraw.Draw(img, "RGBA")
    tpl = scene["template"]
    props = scene.get("props", {})
    phase = local_frame / float(fps)
    breathe = int(3 * math.sin(phase * 2.5))

    if tpl == "HALLWAY_3_DOORS":
        door_xs = [280, 810, 1340]
        door_w, door_h = 300, 560
        door_top = FLOOR_Y - door_h

        for dx in door_xs:
            draw.rectangle([dx, door_top, dx + door_w, FLOOR_Y], outline=COL_MID_GREY, width=3)
            draw.rectangle([dx + 14, door_top + 14, dx + door_w - 14, FLOOR_Y], outline=(60, 60, 65, 255), width=1)
            draw.ellipse([dx + door_w - 42, door_top + 290, dx + door_w - 26, door_top + 306], fill=COL_MID_GREY)

        for sx in [695, 1225]:
            sy = door_top + 165
            for r in range(68, 10, -12):
                alpha = int(85 * (1.0 - r / 70.0))
                draw.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(215, 130, 35, alpha))
            draw.polygon([(sx - 12, sy - 6), (sx + 12, sy - 6), (sx, sy + 10)], fill=COL_AMBER)

        mode = props.get("mode", "empty")
        if mode == "white_mom":
            draw_mom_figure(draw, 1150, FLOOR_Y, scale=1.18, mode="normal")
        elif mode == "dark_head_mom":
            draw_mom_figure(draw, 840, FLOOR_Y, scale=1.22, mode="dark_head")
        elif mode == "red_bubble":
            draw_sound_waves(draw, 960, door_top + 270, direction="both", phase=phase, count=3)
            draw_speech_bubble(draw, 960, door_top + 195, "Goodnight", is_red=True, tail_dir="down")

    elif tpl == "STAIRS_GOODNIGHT":
        font_lbl = _load_font(22)
        draw.text((120, 165), "NORMAL", font=font_lbl, fill=COL_MID_GREY)

        sx, sy = 760, FLOOR_Y
        steps = 8
        step_w, step_h = 75, 52
        pts = [(sx, sy)]
        for i in range(steps):
            pts.append((sx + i * step_w, sy - (i + 1) * step_h))
            pts.append((sx + (i + 1) * step_w, sy - (i + 1) * step_h))
        draw.line(pts, fill=COL_WHITE, width=3)
        draw.line([(sx, sy - 140), (sx + steps * step_w, sy - steps * step_h - 140)], fill=COL_MID_GREY, width=3)
        for i in range(0, steps + 1, 2):
            px = sx + i * step_w
            py = sy - i * step_h
            draw.line([(px, py), (px, py - 140)], fill=COL_MID_GREY, width=2)

        top_x = sx + steps * step_w + 30
        top_y = sy - steps * step_h
        draw.rectangle([top_x, top_y - 340, top_x + 190, top_y], outline=COL_WHITE, width=3)

        draw_mom_figure(draw, 540, FLOOR_Y, scale=1.05, mode="normal", waving=True)
        draw_speech_bubble(draw, 880, 210, props.get("bubble", "Night, honey!"), is_red=False, tail_dir="down")

    elif tpl == "BEDROOM_WIDE":
        cx, cy, cr = 640, 245, 42
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=COL_MID_GREY, width=2)
        draw.line([(cx, cy), (cx, cy - 26)], fill=COL_MID_GREY, width=2)
        draw.line([(cx, cy), (cx + 20, cy + 6)], fill=COL_MID_GREY, width=2)

        wx, wy, ww, wh = 1030, 390, 210, 215
        if props.get("warm_window"):
            draw.rectangle([wx, wy, wx + ww, wy + wh], fill=(120, 88, 38, 95))
            draw.ellipse([wx + 80, wy + 36, wx + 136, wy + 92], fill=(220, 175, 85, 220))
        else:
            draw.rectangle([wx, wy, wx + ww, wy + wh], fill=(24, 30, 42, 120))
            draw.ellipse([wx + 80, wy + 36, wx + 136, wy + 92], fill=COL_MOON_BLUE)
        draw.rectangle([wx, wy, wx + ww, wy + wh], outline=COL_MID_GREY, width=3)
        draw.line([(wx + ww // 2, wy), (wx + ww // 2, wy + wh)], fill=COL_MID_GREY, width=2)
        draw.line([(wx, wy + wh // 2), (wx + ww, wy + wh // 2)], fill=COL_MID_GREY, width=2)

        if props.get("red_x_window"):
            draw.line([(wx + 120, wy - 70), (wx + 185, wy - 5)], fill=COL_RED, width=10)
            draw.line([(wx + 185, wy - 70), (wx + 120, wy - 5)], fill=COL_RED, width=10)

        nx = 135
        draw.rectangle([nx, FLOOR_Y - 170, nx + 130, FLOOR_Y], outline=COL_MID_GREY, width=3)
        draw.rectangle([nx + 16, FLOOR_Y - 145, nx + 114, FLOOR_Y - 95], outline=COL_MID_GREY, width=2)
        draw.rectangle([nx + 56, FLOOR_Y - 235, nx + 74, FLOOR_Y - 170], fill=COL_WHITE)
        draw.polygon([(nx + 36, FLOOR_Y - 235), (nx + 94, FLOOR_Y - 235), (nx + 80, FLOOR_Y - 290), (nx + 50, FLOOR_Y - 290)], fill=COL_WHITE)

        dx, dw, dh = 1480, 275, 620
        dy = FLOOR_Y - dh
        draw.polygon(
            [(dx, FLOOR_Y), (dx + dw, FLOOR_Y), (dx + dw + 70, FLOOR_Y + 26), (dx - 110, FLOOR_Y + 26)],
            fill=(185, 110, 28, 175),
        )
        if props.get("door_open_mom"):
            draw.rectangle([dx, dy, dx + dw, FLOOR_Y], fill=(18, 18, 22, 255), outline=COL_WHITE, width=4)
            draw_mom_figure(draw, dx + dw // 2, FLOOR_Y, scale=1.08, mode="normal")
        else:
            draw.rectangle([dx, dy, dx + dw, FLOOR_Y], fill=(8, 8, 10, 255), outline=COL_WHITE, width=4)
            draw.ellipse([dx + 28, dy + 330, dx + 46, dy + 348], fill=COL_WHITE)

        bx, bw = 310, 560
        draw.rectangle([bx, FLOOR_Y - 300, bx + 22, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx + bw, FLOOR_Y - 190, bx + bw + 20, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx, FLOOR_Y - 110, bx + bw, FLOOR_Y - 40], fill=COL_WHITE)

        c_state = props.get("child_state", "lying")
        if c_state == "lying":
            draw.ellipse([bx + 42, FLOOR_Y - 195, bx + 124, FLOOR_Y - 115], fill=COL_WHITE)
            draw.ellipse([bx + 88, FLOOR_Y - 172, bx + 98, FLOOR_Y - 162], fill=COL_BLACK)
            draw.chord([bx + 100, FLOOR_Y - 210 + breathe, bx + bw - 10, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
        elif c_state == "sitting":
            draw.chord([bx + 110, FLOOR_Y - 195, bx + bw - 10, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
            draw_child_character(draw, bx + 110, FLOOR_Y - 80, scale=1.08, expr="fear", facing="right", sweat=True)
        elif c_state == "under_blanket":
            draw.chord([bx + 50, FLOOR_Y - 245 + breathe, bx + bw - 20, FLOOR_Y - 40], start=180, end=360, fill=COL_WHITE)
        elif c_state in ("standing_door", "standing_door_sad"):
            draw.chord([bx + 70, FLOOR_Y - 175, bx + bw - 15, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
            draw_child_character(
                draw,
                dx - 95,
                FLOOR_Y,
                scale=1.05,
                expr="fear" if c_state == "standing_door" else "sad",
                facing="left",
                sweat=(c_state == "standing_door"),
            )

        if props.get("waves"):
            draw_sound_waves(draw, dx - 10, dy + 240, direction="left", phase=phase, count=3)

        red_bubbles = props.get("red_bubbles", [])
        for idx_b, b_txt in enumerate(red_bubbles):
            by = dy + 135 + idx_b * 78
            draw_speech_bubble(draw, dx - 30, by, b_txt, is_red=True, tail_dir="right")

        if props.get("white_bubble"):
            wb = props["white_bubble"]
            draw_speech_bubble(draw, 920, 420, wb, is_red=False, tail_dir="down")

    elif tpl == "BED_CLOSEUP_LISTEN":
        draw.rectangle([90, FLOOR_Y - 280, 320, FLOOR_Y], outline=COL_MID_GREY, width=4)
        draw.rectangle([185, FLOOR_Y - 400, 225, FLOOR_Y - 280], fill=COL_WHITE)
        draw.polygon([(130, FLOOR_Y - 400), (280, FLOOR_Y - 400), (250, FLOOR_Y - 510), (160, FLOOR_Y - 510)], fill=COL_WHITE)

        draw.rectangle([430, FLOOR_Y - 520, 470, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([430, FLOOR_Y - 180, 1650, FLOOR_Y - 50], fill=COL_WHITE)
        draw.chord([640, FLOOR_Y - 380 + breathe, 1620, FLOOR_Y - 50], start=180, end=360, fill=COL_LIGHT_GREY)

        draw_child_character(draw, 690, FLOOR_Y - 140, scale=1.85, expr="fear", facing="right", sweat=True)
        draw_sound_waves(draw, 1180, FLOOR_Y - 410, direction="left", phase=phase, count=3)

    elif tpl == "DUAL_MOM_COMPARISON":
        draw_mom_figure(draw, 330, FLOOR_Y, scale=1.55, mode="normal")
        draw_speech_bubble(draw, 540, 210, "Goodnight", is_red=False, tail_dir="left", scale=1.2)
        draw_sound_waves(draw, 540, 520, direction="right", phase=phase, count=2)

        draw_mom_figure(draw, 1180, FLOOR_Y, scale=1.55, mode="entity")
        draw_speech_bubble(draw, 1450, 195, "Goodnight", is_red=True, tail_dir="left", scale=1.25)

    elif tpl == "RULE_CARD":
        r_num = int(props.get("rule_num", 1))
        r_title = props.get("rule_title", "LOCK YOUR DOOR")
        font_badge = _load_font(34)
        font_title = _load_font(56)
        font_box = _load_font(24)

        badge_str = f"RULE {r_num}"
        tb = draw.textbbox((0, 0), badge_str, font=font_badge)
        bw, bh = tb[2] - tb[0] + 64, tb[3] - tb[1] + 32
        bx0, by0 = (1920 - bw) // 2, 310
        draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=14, outline=COL_WHITE, width=3)
        draw.text((bx0 + 32, by0 + 14), badge_str, font=font_badge, fill=COL_WHITE)

        tb2 = draw.textbbox((0, 0), r_title, font=font_title)
        tw2 = tb2[2] - tb2[0]
        draw.text(((1920 - tw2) // 2, 455), r_title, font=font_title, fill=COL_WHITE)

        start_x = 1920 // 2 - (7 * 54) // 2
        box_y = 600
        for i in range(1, 8):
            x0 = start_x + (i - 1) * 54
            is_cur = i == r_num
            fill_c = COL_WHITE if is_cur else (0, 0, 0, 255)
            out_c = COL_WHITE if i <= r_num else COL_MID_GREY
            txt_c = COL_BLACK if is_cur else out_c
            draw.rounded_rectangle([x0, box_y, x0 + 42, box_y + 42], radius=6, fill=fill_c, outline=out_c, width=2)
            draw.text((x0 + 13, box_y + 7), str(i), font=font_box, fill=txt_c)

    elif tpl == "DOOR_GAP_CLOSEUP":
        dx0, dx1 = 360, 1560
        gap_y = FLOOR_Y - 38

        draw.polygon(
            [(dx0, gap_y), (dx1, gap_y), (dx1 + 220, FLOOR_Y + 18), (dx0 - 220, FLOOR_Y + 18)],
            fill=COL_AMBER,
        )

        s_mode = props.get("shadows", "center")
        offset = int(t_norm * 520) if s_mode == "sliding" else 0
        for fx in (840 + offset, 1040 + offset):
            if dx0 - 40 <= fx <= dx1 + 40:
                draw.ellipse([fx - 55, gap_y - 6, fx + 55, gap_y + 24], fill=COL_BLACK)
                draw.polygon(
                    [(fx - 50, gap_y + 10), (fx + 50, gap_y + 10), (fx + 85, FLOOR_Y + 18), (fx - 85, FLOOR_Y + 18)],
                    fill=(12, 8, 4, 235),
                )

        draw.rectangle([dx0, 110, dx1, gap_y], fill=(10, 10, 12, 255), outline=COL_WHITE, width=5)
        draw.rectangle([dx0 + 36, 140, dx1 - 36, gap_y - 34], outline=COL_MID_GREY, width=2)

    elif tpl == "SPLIT_DOOR_CUTAWAY":
        wall_x = 960
        draw.ellipse([420, 320, 480, 380], fill=COL_AMBER_DIM)
        draw.rectangle([1440, 390, 1640, 590], outline=COL_MID_GREY, width=3)
        draw.ellipse([1515, 425, 1565, 475], fill=COL_MOON_BLUE)

        draw.rectangle([wall_x - 16, 170, wall_x + 16, FLOOR_Y - 18], fill=COL_WHITE)
        draw.ellipse([wall_x - 42, 560, wall_x - 20, 582], fill=COL_WHITE)
        draw.ellipse([wall_x + 20, 560, wall_x + 42, 582], fill=COL_WHITE)

        mode = props.get("mode", "entity_standing")
        if mode == "eyes_under_gap":
            draw_child_character(draw, wall_x + 170, FLOOR_Y, scale=1.25, expr="fear", facing="left", sweat=True)
            draw.ellipse([wall_x - 85, FLOOR_Y - 26, wall_x - 67, FLOOR_Y - 8], fill=COL_YELLOW_EYE)
            draw.ellipse([wall_x - 55, FLOOR_Y - 26, wall_x - 37, FLOOR_Y - 8], fill=COL_YELLOW_EYE)
        elif mode == "entity_standing":
            draw_mom_figure(draw, wall_x - 185, FLOOR_Y, scale=1.35, mode="dark_head")
            draw_child_character(draw, wall_x + 175, FLOOR_Y, scale=1.2, expr="fear", facing="left", sweat=True)
        elif mode == "entity_listening":
            draw_mom_figure(draw, wall_x - 165, FLOOR_Y, scale=1.35, mode="dark_head", leaning_right=True)
            draw_child_character(draw, wall_x + 195, FLOOR_Y, scale=1.15, expr="fear", facing="left", crouching=True)
            draw_sound_waves(draw, wall_x + 30, FLOOR_Y - 150, direction="right", phase=phase, count=2)

    elif tpl == "DOOR_LOCK_CLOSEUP":
        plate_x, plate_y = 850, 260
        draw.line([(1140, 100), (1140, FLOOR_Y)], fill=COL_WHITE, width=4)
        draw.rounded_rectangle([plate_x, plate_y, plate_x + 170, plate_y + 520], radius=32, outline=COL_WHITE, width=5)

        cx, cy = plate_x + 85, plate_y + 125
        draw.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], outline=COL_WHITE, width=4)
        angle = -0.6 + 1.2 * t_norm
        dx = int(46 * math.cos(angle))
        dy = int(46 * math.sin(angle))
        draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=COL_WHITE, width=16)

        draw.rounded_rectangle([plate_x + 40, plate_y + 340, plate_x + 210, plate_y + 390], radius=16, fill=COL_LIGHT_GREY)
        draw.polygon([(460, FLOOR_Y), (650, FLOOR_Y), (cx + 10, cy + 55), (cx - 60, cy + 10)], fill=COL_WHITE)

        if props.get("show_freeze"):
            font_frz = _load_font(34)
            draw.text((1380, 520), "FREEZE", font=font_frz, fill=COL_RED)

    elif tpl == "PHONE_SCREEN":
        px0, py0, px1, py1 = 740, 140, 1180, 860
        draw.rounded_rectangle([px0, py0, px1, py1], radius=48, fill=(18, 20, 26, 255), outline=COL_MID_GREY, width=6)
        draw.rounded_rectangle([900, py0 + 20, 1020, py0 + 34], radius=7, fill=COL_BLACK)

        font_p = _load_font(26)
        font_s = _load_font(18)
        draw.text((925, py0 + 68), "Mom", font=font_p, fill=COL_WHITE)
        draw.line([(px0 + 20, py0 + 115), (px1 - 20, py0 + 115)], fill=COL_DARK_GREY, width=2)

        bx0, by0, bx1, by1 = px0 + 45, py0 + 185, px1 - 65, py0 + 265
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=24, fill=COL_IOS_BLUE)
        draw.text((bx0 + 28, by0 + 24), props.get("msg", "Are you awake?"), font=font_p, fill=COL_WHITE)
        draw.text((bx0 + 10, by1 + 14), "12:07 AM · Delivered", font=font_s, fill=COL_MID_GREY)

    elif tpl == "SPLIT_WALL_TWO_BEDS":
        draw.rectangle([952, 160, 968, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([280, FLOOR_Y - 240, 300, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([280, FLOOR_Y - 100, 740, FLOOR_Y - 40], fill=COL_WHITE)
        draw.chord([340, FLOOR_Y - 180, 720, FLOOR_Y - 40], start=180, end=360, fill=COL_LIGHT_GREY)
        draw.rectangle([1620, FLOOR_Y - 240, 1640, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([1180, FLOOR_Y - 100, 1640, FLOOR_Y - 40], fill=COL_WHITE)
        draw_child_character(draw, 1480, FLOOR_Y - 80, scale=1.05, expr="fear", facing="left", sweat=True)
        draw_sound_waves(draw, 960, FLOOR_Y - 220, direction="right", phase=phase, count=3)

    elif tpl == "FLASHBACK_TABLE":
        tx0, tx1, ty = 520, 1140, FLOOR_Y - 210
        draw.rectangle([tx0, ty, tx1, FLOOR_Y], outline=COL_WHITE, width=4)
        draw_child_character(draw, 690, ty, scale=1.05, expr="normal", facing="right", sweat=False)
        if props.get("mode") == "two_kids":
            draw_child_character(draw, 970, ty, scale=1.05, expr="normal", facing="left", sweat=False)
            draw_speech_bubble(draw, 540, 290, props.get("bubble", "Ha ha ha!"), is_red=False, tail_dir="down")
            draw_mom_figure(draw, 1520, FLOOR_Y, scale=1.18, mode="normal")
        else:
            draw_mom_figure(draw, 1420, FLOOR_Y, scale=1.18, mode="normal")
            draw_speech_bubble(draw, 1020, 220, props.get("bubble", "You were talking in your sleep!"), is_red=False, tail_dir="right")

    draw_hud_and_floor(draw, scene.get("hud", "NIGHT 01"), global_frame, fps, active_caption)
    return img.convert("RGB")


# ==============================================================================
# 5. EXACT "LOCK YOUR DOOR" REFERENCE THUMBNAIL GENERATOR
# ==============================================================================
def build_exact_lock_your_door_thumbnail(out_jpg: Path) -> None:
    W, H = 1280, 720
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    glow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer, "RGBA")
    draw = ImageDraw.Draw(base, "RGBA")

    floor_y = 678

    door_x = 768
    door_w = 40
    door_top = 185
    gdraw.line([(0, floor_y), (W, floor_y)], fill=(255, 255, 255, 180), width=10)
    gdraw.rectangle([door_x - 6, door_top - 6, door_x + door_w + 6, floor_y], fill=(255, 255, 255, 140))
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=10))
    base = Image.alpha_composite(base, glow_layer)
    draw = ImageDraw.Draw(base, "RGBA")

    draw.line([(0, floor_y), (W, floor_y)], fill=COL_WHITE, width=5)
    draw.rectangle([door_x, door_top, door_x + door_w, floor_y], fill=COL_WHITE)
    draw.ellipse([door_x - 22, 430, door_x - 4, 452], fill=COL_WHITE)
    draw.ellipse([door_x + door_w + 4, 430, door_x + door_w + 22, 452], fill=COL_WHITE)

    cx = door_x + door_w + 54
    hr = 38
    hx, hy = cx, floor_y - 148
    draw.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=COL_WHITE)
    draw.ellipse([hx + 6, hy - 14, hx + 20, hy], fill=COL_BLACK)
    draw.ellipse([hx + 11, hy - 9, hx + 15, hy - 5], fill=COL_WHITE)
    draw.chord([hx - 4, hy + 8, hx + 24, hy + 28], start=180, end=360, fill=COL_BLACK)
    draw.ellipse([hx - 6, hy - 22, hx, hy - 10], fill=COL_BLACK)
    draw.ellipse([hx + hr + 8, hy - 26, hx + hr + 18, hy - 14], fill=COL_WHITE)
    draw.ellipse([hx + hr + 16, hy - 10, hx + hr + 26, hy + 2], fill=COL_WHITE)
    draw.rounded_rectangle([cx - 42, floor_y - 110, cx + 10, floor_y - 8], radius=24, fill=COL_WHITE)
    draw.polygon([(cx - 10, floor_y - 95), (cx + 48, floor_y - 80), (cx + 68, floor_y - 8), (cx + 22, floor_y - 8)], fill=COL_WHITE)
    draw.line([(cx - 18, floor_y - 82), (cx + 42, floor_y - 52)], fill=COL_BLACK, width=4)

    mx = 605
    draw.polygon([(mx - 32, 345), (mx + 32, 345), (mx + 64, 585), (mx - 64, 585)], fill=COL_WHITE)
    draw.rounded_rectangle([mx - 34, 575, mx - 12, floor_y], radius=8, fill=COL_WHITE)
    draw.rounded_rectangle([mx + 12, 575, mx + 34, floor_y], radius=8, fill=COL_WHITE)
    draw.line([(mx - 30, 355), (mx - 70, 515)], fill=COL_WHITE, width=18)
    draw.line([(mx + 30, 355), (mx + 70, 515)], fill=COL_WHITE, width=18)
    for fx in (-78, -70, -62):
        draw.line([(mx + fx, 515), (mx + fx - 4, 542)], fill=COL_WHITE, width=4)
    for fx in (62, 70, 78):
        draw.line([(mx + fx, 515), (mx + fx + 4, 542)], fill=COL_WHITE, width=4)

    ehx, ehy = mx + 32, 282
    draw.polygon([(ehx - 52, ehy - 30), (ehx + 58, ehy - 10), (ehx + 48, ehy + 65), (ehx - 62, ehy + 42)], fill=(230, 230, 235, 255))
    draw.ellipse([ehx - 46, ehy - 46, ehx + 46, ehy + 46], fill=COL_WHITE)
    for ex, ey in [(ehx - 12, ehy - 10), (ehx + 18, ehy - 2)]:
        draw.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill=(245, 230, 80, 140))
        draw.ellipse([ex - 7, ey - 7, ex + 7, ey + 7], fill=COL_YELLOW_EYE)
        draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=COL_BLACK)
    draw.chord([ehx - 32, ehy - 8, ehx + 34, ehy + 38], start=10, end=185, fill=COL_BLACK)
    for tx in range(ehx - 22, ehx + 26, 7):
        draw.line([(tx, ehy + 12), (tx, ehy + 30)], fill=COL_WHITE, width=2)

    font_b1 = _load_font(34)
    font_b2 = _load_font(34)
    draw.rounded_rectangle([355, 195, 565, 268], radius=32, fill=COL_WHITE)
    draw.polygon([(535, 265), (558, 262), (582, 288)], fill=COL_WHITE)
    draw.text((376, 212), "Goodnight", font=font_b1, fill=COL_BLACK)

    draw.rounded_rectangle([335, 288, 558, 368], radius=32, fill=COL_RED)
    draw.polygon([(555, 318), (555, 338), (585, 322)], fill=COL_RED)
    draw.text((356, 308), "Goodnight", font=font_b2, fill=COL_BLACK)

    font_title = _load_font(112)
    t_white = "LOCK YOUR "
    t_red = "DOOR"
    w1 = draw.textbbox((0, 0), t_white, font=font_title)[2]
    w2 = draw.textbbox((0, 0), t_red, font=font_title)[2]
    start_x = (W - (w1 + w2)) // 2
    draw.text((start_x, 38), t_white, font=font_title, fill=COL_WHITE)
    draw.text((start_x + w1, 38), t_red, font=font_title, fill=COL_RED)

    base.convert("RGB").save(out_jpg, "JPEG", quality=96)
    logger.info(f"🖼️ Exact Reference Thumbnail ('LOCK YOUR DOOR') saved to {out_jpg}")


# ==============================================================================
# 6. VOICEOVER + SCENE-RELEVANT SOUND EFFECTS (DOOR KNOCK, LOCK, HEARTBEAT)
# ==============================================================================
def generate_sfx_wav(sfx_type: str, duration: float, out_wav: Path) -> None:
    sr = 44100
    n_samples = int(sr * duration)
    buf = np.zeros(n_samples, dtype=np.float32)

    if sfx_type == "knock":
        for t_k in [0.6, 1.0, 1.4]:
            idx = int(t_k * sr)
            length = int(0.09 * sr)
            if idx + length < n_samples:
                t_arr = np.linspace(0, 0.09, length)
                env = np.exp(-t_arr * 45.0)
                buf[idx : idx + length] += 0.35 * env * np.sin(2 * np.pi * 115.0 * t_arr)
    elif sfx_type == "lock_click":
        idx = int(0.45 * sr)
        length = int(0.06 * sr)
        if idx + length < n_samples:
            t_arr = np.linspace(0, 0.06, length)
            env = np.exp(-t_arr * 70.0)
            buf[idx : idx + length] += 0.30 * env * (
                np.sin(2 * np.pi * 920.0 * t_arr) + 0.5 * np.sin(2 * np.pi * 1850.0 * t_arr)
            )
    elif sfx_type == "phone_ping":
        idx = int(0.35 * sr)
        length = int(0.18 * sr)
        if idx + length < n_samples:
            t_arr = np.linspace(0, 0.18, length)
            env = np.exp(-t_arr * 18.0)
            buf[idx : idx + length] += 0.20 * env * np.sin(2 * np.pi * 1046.5 * t_arr)
    elif sfx_type == "thud":
        length = min(int(0.45 * sr), n_samples)
        t_arr = np.linspace(0, 0.45, length)
        env = np.exp(-t_arr * 9.0)
        buf[:length] += 0.32 * env * np.sin(2 * np.pi * 58.0 * t_arr)
    elif sfx_type == "heartbeat":
        t_cur = 0.4
        while t_cur + 0.35 < duration:
            for offset, amp in [(0.0, 0.22), (0.18, 0.15)]:
                idx = int((t_cur + offset) * sr)
                length = int(0.10 * sr)
                if idx + length < n_samples:
                    t_arr = np.linspace(0, 0.10, length)
                    env = np.exp(-t_arr * 32.0)
                    buf[idx : idx + length] += amp * env * np.sin(2 * np.pi * 52.0 * t_arr)
            t_cur += 1.15

    pcm = np.clip(buf * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


async def _edge_tts_save(text: str, out_mp3: Path) -> bool:
    import edge_tts

    for voice in ["en-US-ChristopherNeural", "en-US-AndrewNeural", "en-US-GuyNeural"]:
        try:
            comm = edge_tts.Communicate(text, voice, rate="-5%", pitch="-2Hz")
            await comm.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 1000:
                return True
        except Exception as e:
            logger.warning(f"edge-tts ({voice}) failed: {e}")
    return False


def get_media_duration(path: Path) -> float:
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
    )
    try:
        return max(float(res.stdout.strip()), 1.0)
    except Exception:
        return 5.0


def synthesize_scene_audio(text: str, sfx_type: str, out_wav: Path) -> float:
    raw_mp3 = out_wav.with_suffix(".raw.mp3")
    vo_wav = out_wav.with_suffix(".vo.wav")
    sfx_wav = out_wav.with_suffix(".sfx.wav")
    generated = False

    el_key = rotator.get_key("ELEVENLABS")
    if el_key:
        try:
            url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
            headers = {"xi-api-key": el_key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.62, "similarity_boost": 0.80},
            }
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            if r.status_code == 200 and len(r.content) > 2000:
                raw_mp3.write_bytes(r.content)
                generated = True
        except Exception:
            pass

    if not generated:
        asyncio.run(_edge_tts_save(text, raw_mp3))

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_mp3),
            "-af", "highpass=f=80,treble=g=2.0:f=3600,acompressor=threshold=-18dB:ratio=2.5:makeup=2dB,apad=pad_dur=0.45",
            "-ar", "44100", "-ac", "2", str(vo_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    dur = get_media_duration(vo_wav)
    generate_sfx_wav(sfx_type, dur, sfx_wav)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(vo_wav), "-i", str(sfx_wav),
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0[aout]",
            "-map", "[aout]", "-ar", "44100", "-ac", "2", str(out_wav),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    raw_mp3.unlink(missing_ok=True)
    vo_wav.unlink(missing_ok=True)
    sfx_wav.unlink(missing_ok=True)
    return dur


# ==============================================================================
# 7. SCENE ANIMATION & VIDEO STITCHER
# ==============================================================================
def split_caption_phrases(text: str, max_chars: int = 42) -> List[str]:
    sentences = re.split(r"(?<=[.!?—:;])\s+", text.strip())
    chunks: List[str] = []
    for s in sentences:
        words = s.split()
        cur: List[str] = []
        for w in words:
            cand = " ".join(cur + [w])
            if len(cand) <= max_chars or not cur:
                cur.append(w)
                if w.endswith((",", ";", ":")) and len(cand) >= 18:
                    chunks.append(" ".join(cur))
                    cur = []
            else:
                chunks.append(" ".join(cur))
                cur = [w]
        if cur:
            chunks.append(" ".join(cur))
    return [c.strip() for c in chunks if c.strip()]


def render_animated_2d_scene_clip(
    scene: Dict[str, Any],
    audio_path: Path,
    start_global_frame: int,
    out_mp4: Path,
    fps: int = 24,
) -> int:
    dur = get_media_duration(audio_path)
    total_frames = max(int(math.ceil(dur * fps)), fps * 2)

    phrases = split_caption_phrases(scene["narration"], max_chars=42)
    if not phrases:
        phrases = [scene["narration"]]
    weights = [max(len(p), 1) for p in phrases]
    tot_w = float(sum(weights))
    bounds: List[Tuple[float, float, str]] = []
    acc = 0.0
    for p, w in zip(phrases, weights):
        sf = acc / tot_w
        acc += w
        ef = acc / tot_w
        bounds.append((sf, ef, p))

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", "1920x1080", "-pix_fmt", "rgb24", "-r", str(fps),
        "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(out_mp4),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    try:
        for f in range(total_frames):
            t_norm = f / float(max(total_frames - 1, 1))
            active_cap = bounds[-1][2]
            for sf, ef, p in bounds:
                if sf <= t_norm <= ef:
                    active_cap = p
                    break

            frame_img = render_template_frame(
                scene=scene,
                t_norm=t_norm,
                local_frame=f,
                global_frame=start_global_frame + f,
                fps=fps,
                active_caption=active_cap,
            )
            proc.stdin.write(frame_img.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait()

    return start_global_frame + total_frames


def stitch_clips_with_bgm(clips: List[Path], out_mp4: Path) -> float:
    concat_txt = out_mp4.parent / f"concat_{out_mp4.stem}.txt"
    concat_txt.write_text("\n".join(f"file '{c.resolve()}'" for c in clips), encoding="utf-8")
    merged = out_mp4.parent / f"merged_{out_mp4.stem}.mp4"

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c", "copy", str(merged)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    dur = get_media_duration(merged)
    songs = list(Path("resource/songs").glob("*.mp3"))
    if songs:
        bgm = random.choice(songs)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(merged), "-stream_loop", "-1", "-i", str(bgm),
                "-filter_complex",
                f"[1:a]lowpass=f=620,volume=0.06,afade=t=in:st=0:d=2,afade=t=out:st={max(dur - 3, 1):.1f}:d=3[bgm];"
                f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
                "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out_mp4),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        merged.unlink(missing_ok=True)
    else:
        shutil.move(str(merged), str(out_mp4))

    concat_txt.unlink(missing_ok=True)
    return get_media_duration(out_mp4)


def render_vertical_short_from_long(long_mp4: Path, short_mp4: Path) -> float:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(long_mp4), "-t", "58",
            "-vf", "crop=1080:1080:420:0,pad=1080:1920:0:420:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            str(short_mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return get_media_duration(short_mp4)


def main() -> None:
    key_summary = rotator.log_status()
    out_dir = Path("output")
    work_dir = out_dir / "work"
    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    story = LULLORIN_MASTER_STORYBOARD
    scenes = story["scenes"]
    clips: List[Path] = []
    global_frame = 0

    logger.info(f"🎬 Rendering 38-Scene @Lullorin 2D Minimalist Horror Video: '{story['title']}'")

    for idx, scene in enumerate(scenes):
        wav_p = work_dir / f"scene_{idx:02d}.wav"
        mp4_p = work_dir / f"scene_{idx:02d}.mp4"

        synthesize_scene_audio(scene["narration"], scene.get("sfx", "none"), wav_p)
        global_frame = render_animated_2d_scene_clip(
            scene=scene,
            audio_path=wav_p,
            start_global_frame=global_frame,
            out_mp4=mp4_p,
            fps=24,
        )
        clips.append(mp4_p)
        logger.info(f"✅ Rendered 2D Minimalist Scene {idx + 1:02d}/{len(scenes)} ({scene['template']})")

    long_mp4 = out_dir / "long_video_16x9.mp4"
    short_mp4 = out_dir / "viral_short_9x16.mp4"
    thumb_jpg = out_dir / "thumbnail_16x9.jpg"

    long_dur = stitch_clips_with_bgm(clips, long_mp4)
    short_dur = render_vertical_short_from_long(long_mp4, short_mp4)
    build_exact_lock_your_door_thumbnail(thumb_jpg)

    (out_dir / "publishing_package.txt").write_text(
        f"TITLE:\n{story['title']}\n\n"
        f"THUMBNAIL HOOK:\n{story['hook_text']}\n\n"
        f"DESCRIPTION:\n{story['description']}\n\n"
        f"TAGS:\n{', '.join(story['tags'])}\n",
        encoding="utf-8",
    )

    audit = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reference_channel": "@Lullorin",
        "reference_video": "If Your Mom Ever Says Goodnight to You Twice... LOCK YOUR DOOR (wU_PUYMs5Bo)",
        "visual_style": "Minimalist 2D Black-Background Vector Animation (Zero 3D / Zero External AI Photos)",
        "scene_count": len(scenes),
        "long_video_duration_seconds": round(long_dur, 2),
        "short_video_duration_seconds": round(short_dur, 2),
        "api_keys_detected": key_summary,
    }
    (out_dir / "audit_report.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    shutil.rmtree(work_dir, ignore_errors=True)
    logger.info(f"🎉 FINISHED! Long Video: {long_dur:.1f}s | Thumbnail: {thumb_jpg}")


if __name__ == "__main__":
    main()
