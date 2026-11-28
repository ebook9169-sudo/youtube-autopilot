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
logger = logging.getLogger("LullorinExactEngine")


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
# 2. 41-FRAME EXACT STORYBOARD (MATCHING EVERY FRAME OF 0s - 800s CONTACT SHEET)
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
        # 0s: 3-Door Hallway with 4 subtle warm sconces
        {
            "id": 1,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01",
            "sfx": "ambience",
            "narration": "If your mom ever says goodnight to you twice, lock your bedroom door immediately.",
            "props": {"mode": "empty"},
        },
        # 20s: Stairs with NORMAL label, thermostat [o=], Mom with bun waving "Night, honey!"
        {
            "id": 2,
            "template": "STAIRS_GOODNIGHT",
            "hud": "NIGHT 01",
            "sfx": "none",
            "narration": "The first time is normal—maybe she waves from the bottom of the stairs, yelling it up to you while heading to bed.",
            "props": {"bubble": "Night, honey!"},
        },
        # 40s: Bedroom wide, child lying in bed, moon window, clock, under-door light
        {
            "id": 3,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01",
            "sfx": "none",
            "narration": "You lie in bed in the dark room, and a few minutes later, you hear it again.",
            "props": {"child_state": "lying"},
        },
        # 60s: Bed close-up with slatted headboard, startled child, sound waves, "-JUST LISTEN.-"
        {
            "id": 4,
            "template": "BED_CLOSEUP_LISTEN",
            "hud": "NIGHT 01",
            "sfx": "heartbeat",
            "narration": "A second goodnight coming from right outside your closed door. Do not make a sound. Just listen.",
            "props": {},
        },
        # 80s: Dual Mom comparison (Left normal white bubble vs Right tilted dark-face yellow-eyed entity red bubble)
        {
            "id": 5,
            "template": "DUAL_MOM_COMPARISON",
            "hud": "NIGHT 01",
            "sfx": "whisper",
            "narration": "Your real mother is already asleep. Something else in the house is mimicking her voice to trick you.",
            "props": {},
        },
        # 100s: Rule 1 intro flash (first 2.2s) -> Hallway white Mom standing between doors 2 & 3
        {
            "id": 6,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "thud",
            "rule_intro": {"num": 1, "title": "NEVER ANSWER THE SECOND GOODNIGHT"},
            "narration": "Rule Number One: Never answer the second goodnight. When it enters the hallway, it doesn't know which room you're in yet.",
            "props": {"mode": "white_mom"},
        },
        # 120s: Hallway with red "Goodnight" bubble and sound waves on center door
        {
            "id": 7,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "whisper",
            "narration": "It tests each closed door down the hall, whispering goodnight and waiting for someone to answer.",
            "props": {"mode": "red_bubble"},
        },
        # 140s: Bedroom wide, red "Goodnight" bubble on door with waves, child head on pillow
        {
            "id": 8,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "whisper",
            "narration": "If you answer—even in a whisper—it will know exactly which bedroom is yours.",
            "props": {"child_state": "head_up", "red_bubbles": ["Goodnight"], "waves": True},
        },
        # 160s: Flashback table, Mom standing right saying "You were talking in your sleep!"
        {
            "id": 9,
            "template": "FLASHBACK_TABLE",
            "hud": "NIGHT 01 | RULE 1",
            "sfx": "none",
            "narration": "It learns your habits by listening at night. Even if your mom jokes that you were talking in your sleep, maybe she even laughs about it.",
            "props": {"mode": "single", "bubble": "You were talking in your sleep!"},
        },
        # 180s: Rule 2 intro flash -> Hallway Mom with dark shadowed head standing in front of door 1/2
        {
            "id": 10,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "footsteps",
            "rule_intro": {"num": 2, "title": "LOCK YOUR DOOR BEFORE IT STOPS"},
            "narration": "Rule Number Two: Lock your door while it is still walking. If you get up and turn it while it's moving down the hall, you have a chance.",
            "props": {"mode": "dark_head_mom_left"},
        },
        # 200s: Bedroom wide with 3 stacked red bubbles ("Goodnight", "Sleep tight", "I love you") + red glow
        {
            "id": 11,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "whisper",
            "narration": "Once it stops outside your room, it will repeat goodnight, sleep tight, I love you over and over.",
            "props": {
                "child_state": "lying",
                "red_bubbles": ["Goodnight", "Sleep tight", "I love you"],
                "waves": True,
            },
        },
        # 220s: Door lock close-up with anatomical hand & fingers turning deadbolt + red "FREEZE"
        {
            "id": 12,
            "template": "DOOR_LOCK_CLOSEUP",
            "hud": "NIGHT 01 | RULE 2",
            "sfx": "lock_click",
            "narration": "If you are turning the lock when it speaks right outside, freeze immediately and do not let the latch click.",
            "props": {"show_freeze": True},
        },
        # 240s: Dedicated Rule 3 Card ("WATCH THE GAP UNDER YOUR DOOR")
        {
            "id": 13,
            "template": "RULE_CARD",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "thud",
            "narration": "Rule Number Three: Watch the gap under your door.",
            "props": {"rule_num": 3, "rule_title": "WATCH THE GAP UNDER YOUR DOOR"},
        },
        # 260s: Under-door gap close-up with two dark foot shadows centered
        {
            "id": 14,
            "template": "DOOR_GAP_CLOSEUP",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "ambience",
            "narration": "If two dark shadows block the yellow light under the door, that means it's standing right outside.",
            "props": {"shadows": "center"},
        },
        # 280s: Under-door gap close-up with foot shadows sliding away
        {
            "id": 15,
            "template": "DOOR_GAP_CLOSEUP",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "footsteps",
            "narration": "Only if the shadows slide away from the bottom crack has it moved down the hallway.",
            "props": {"shadows": "sliding"},
        },
        # 300s: Bedroom wide, child standing by door, red X above window/head ("DO NOT KNEEL DOWN TO LOOK.")
        {
            "id": 16,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "none",
            "narration": "Do not kneel down to look underneath the door gap.",
            "props": {"child_state": "standing_door", "red_x_window": True},
        },
        # 320s: Split-door cutaway, child on right, glowing yellow eyes peeking under floor gap on left
        {
            "id": 17,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 3",
            "sfx": "heartbeat",
            "narration": "Because it crawls flat on the floor to see how tall you are and exactly where you are standing.",
            "props": {"mode": "eyes_under_gap"},
        },
        # 340s: Bedroom wide, warm amber moon window, child head up in bed ("SHE KNOCKS WHILE SHE'S")
        {
            "id": 18,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "knock",
            "rule_intro": {"num": 4, "title": "NEVER OPEN THE DOOR FOR ANY EXCUSE"},
            "narration": "Rule Number Four: Ignore every excuse. Sometimes she knocks while she's speaking in a soft, apologetic tone.",
            "props": {"child_state": "head_up", "warm_window": True},
        },
        # 360s: Bedroom wide, long red bubble "I forgot to kiss you goodnight" on door
        {
            "id": 19,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "whisper",
            "narration": "It will whisper through the wood that I forgot to kiss you goodnight.",
            "props": {
                "child_state": "head_up",
                "warm_window": True,
                "red_bubbles": ["I forgot to kiss you goodnight"],
                "waves": True,
            },
        },
        # 380s: Bedroom wide, cool blue moon window, silent room ("AND WHEN YOU DON'T ANSWER,")
        {
            "id": 20,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "ambience",
            "narration": "And when you don't answer, the hallway outside will go completely quiet.",
            "props": {"child_state": "head_up", "warm_window": False},
        },
        # 400s: Split-door cutaway, tall dark-headed Mom-Entity standing motionless on left, child on right
        {
            "id": 21,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 4",
            "sfx": "heartbeat",
            "narration": "Only something that isn't your mother can stand motionless outside a locked door for hours in the dark.",
            "props": {"mode": "entity_standing"},
        },
        # 420s: Hallway 3 doors, dark-headed Mom standing at door 1 with sound waves at bottom-left
        {
            "id": 22,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 5",
            "sfx": "whisper",
            "rule_intro": {"num": 5, "title": "DO NOT CHECK YOUR PHONE AFTER MIDNIGHT"},
            "narration": "Rule Number Five: Do not touch your phone. You might hear footsteps and her voice answering from down the hall.",
            "props": {"mode": "dark_head_mom_left_waves"},
        },
        # 440s: Phone screen ("Mom: Are you awake? 12:07 AM · Delivered" + green "ASLEEP IS SAFE")
        {
            "id": 23,
            "template": "PHONE_SCREEN",
            "hud": "NIGHT 01 | RULE 5",
            "sfx": "phone_ping",
            "narration": "It texts to catch the ones who aren't listening. Leave the screen dark—asleep is safe.",
            "props": {"msg": "Are you awake?"},
        },
        # 460s: Empty bed with nightstand on right ("YOUR MOM IS NOT RIGHT OUTSIDE.")
        {
            "id": 24,
            "template": "BEDROOM_EMPTY_NIGHTSTAND",
            "hud": "NIGHT 01 | RULE 5",
            "sfx": "ambience",
            "narration": "It wants you to think the hallway is clear and your mom is not right outside.",
            "props": {},
        },
        # 480s: Hallway 2 doors view with single warm sconce in center ("A FEW MINUTES LATER,")
        {
            "id": 25,
            "template": "HALLWAY_2_DOORS",
            "hud": "NIGHT 01 | A STORY",
            "sfx": "ambience",
            "narration": "A few minutes later, it will try a different trick from the room next door.",
            "props": {},
        },
        # 500s: Split-wall two beds ("VOICE THROUGH THE WALL,")
        {
            "id": 26,
            "template": "SPLIT_WALL_TWO_BEDS",
            "hud": "NIGHT 01 | A STORY",
            "sfx": "whisper",
            "narration": "You will hear a muffled voice through the wall, sounding like she is tucking someone else into bed.",
            "props": {},
        },
        # 520s: Flashback dinner table with little sister (red hair bow) + "Ha ha ha!" + Mom gesturing on right
        {
            "id": 27,
            "template": "FLASHBACK_TABLE",
            "hud": "NIGHT 01 | A STORY",
            "sfx": "none",
            "narration": "It mimics warm family memories—like laughing at the table—to make you forget why you locked the door.",
            "props": {"mode": "two_kids", "bubble": "Ha ha ha!"},
        },
        # 540s: Bedroom wide with 3 stacked red bubbles ("Goodnight!", "(knock knock)", "(crying)")
        {
            "id": 28,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "knock",
            "rule_intro": {"num": 6, "title": "STAY COMPLETELY SILENT WHEN IT CRIES"},
            "narration": "Rule Number Six: Do not move when the knocking turns desperate—yelling goodnight, knocking, and crying. Eventually, it'll stop.",
            "props": {
                "child_state": "head_up",
                "red_bubbles": ["Goodnight!", "(knock knock)", "(crying)"],
                "waves": True,
            },
        },
        # 560s: Split-door cutaway, Mom-Entity leaning forward pressing ear to door; child crouching on right
        {
            "id": 29,
            "template": "SPLIT_DOOR_CUTAWAY",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "heartbeat",
            "narration": "When the crying stops all at once, it has pressed its ear against the wood. It's listening to you.",
            "props": {"mode": "entity_listening"},
        },
        # 580s: Bedroom wide, child completely covered under white blanket mound ("IF YOU NEED TO COUGH,")
        {
            "id": 30,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "ambience",
            "narration": "If you need to cough or catch your breath, stay buried beneath the covers.",
            "props": {"child_state": "under_blanket"},
        },
        # 600s: Bedroom panned left showing bookshelf grid on far left ("AND IF, SOMEWHERE IN THE MIDDLE")
        {
            "id": 31,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "ambience",
            "narration": "And if, somewhere in the middle of the night, you hear the doorknob rattle slowly...",
            "props": {"child_state": "lying", "show_bookshelf": True},
        },
        # 620s: Bedroom wide, child pulling blanket completely over head ("PULL YOUR BLANKET OVER YOUR HEAD.")
        {
            "id": 32,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 6",
            "sfx": "ambience",
            "narration": "Pull your blanket over your head and keep your eyes shut tight.",
            "props": {"child_state": "under_blanket"},
        },
        # 640s: Bedroom wide, warm morning window, child standing by door ("YOU'LL WANT TO RIP THAT DOOR")
        {
            "id": 33,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "none",
            "rule_intro": {"num": 7, "title": "ASK A MEMORY QUESTION IN THE MORNING"},
            "narration": "Rule Number Seven: Wait for morning. When sunlight hits the window, you'll want to rip that door open—but before you unlock it, pause.",
            "props": {"child_state": "standing_door", "warm_window": True},
        },
        # 680s: Hallway 3 doors, dark-headed Mom-Entity still standing in front of door 1 ("BECAUSE IT'S STILL TRYING.")
        {
            "id": 34,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "ambience",
            "narration": "Because even at dawn, it is often still standing there—because it's still trying.",
            "props": {"mode": "dark_head_mom_left"},
        },
        # 700s: Bedroom wide, child at door with white bubble "What did you make the night I broke my arm?"
        {
            "id": 35,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "none",
            "narration": "Ask her something only your real mom knows—like what did you make the night I broke my arm?",
            "props": {
                "child_state": "standing_door",
                "warm_window": True,
                "white_bubble": "What did you make the night I broke my arm?",
            },
        },
        # 720s: Bedroom wide, child standing by door with sad/worried expression ("DOESN'T LAUGH, DOESN'T ARGUE,")
        {
            "id": 36,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | RULE 7",
            "sfx": "heartbeat",
            "narration": "If the voice on the other side doesn't laugh, doesn't argue, and just says goodnight again, do not touch the lock.",
            "props": {"child_state": "standing_door_sad", "warm_window": True},
        },
        # 740s: Bedroom wide, door open on right with real Mom standing inside doorway + "Goodnight, Mom."
        {
            "id": 37,
            "template": "BEDROOM_WIDE",
            "hud": "NIGHT 01 | AFTER",
            "sfx": "none",
            "narration": "Only when your real mom opens the door in the daylight, and for just a second smiles normally, are you safe.",
            "props": {
                "child_state": "head_up",
                "door_open_mom": True,
                "white_bubble": "Goodnight, Mom.",
            },
        },
        # 760s & 780s: Hallway 3 doors with small Child standing in hallway having glowing YELLOW EYES!
        {
            "id": 38,
            "template": "HALLWAY_3_DOORS",
            "hud": "NIGHT 01 | AFTER",
            "sfx": "heartbeat",
            "narration": "Because if you ever answered it in the dark, the next night it will use your voice to stand in the hallway.",
            "props": {"mode": "yellow_eyed_child"},
        },
        # 800s: Final Door Lock Close-up with hand turning deadbolt ("TWICE, SO IF YOUR MOM EVER SAYS")
        {
            "id": 39,
            "template": "DOOR_LOCK_CLOSEUP",
            "hud": "NIGHT 01 | AFTER",
            "sfx": "lock_click",
            "narration": "Twice. So if your mom ever says goodnight to you twice... lock your door.",
            "props": {"show_freeze": False},
        },
    ],
}


# ==============================================================================
# 3. FONT LOADER & AUTHENTIC @LULLORIN 2D CHARACTER / ENVIRONMENT DRAWING
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
COL_LIGHT_GREY = (195, 195, 198, 255)
COL_MID_GREY = (115, 115, 120, 255)
COL_DARK_GREY = (48, 48, 52, 255)
COL_AMBER = (212, 132, 42, 255)
COL_BASEBOARD = (68, 44, 18, 255)
COL_RED = (232, 28, 36, 255)
COL_YELLOW_EYE = (255, 240, 70, 255)
COL_MOON_BLUE = (112, 126, 152, 255)
COL_IOS_BLUE = (28, 118, 232, 255)
COL_SAFE_GREEN = (42, 175, 82, 255)

FLOOR_Y = 895


def _draw_soft_glow(
    base_img: Image.Image,
    cx: int,
    cy: int,
    radius: int,
    color_rgb: Tuple[int, int, int],
    max_alpha: int = 65,
) -> None:
    """Draws a smooth radial glow without creating solid orange circles."""
    size = radius * 2
    patch = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:size, 0:size]
    dist = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / float(max(radius, 1))
    alpha = np.clip((1.0 - dist) ** 2.2 * max_alpha, 0, 255).astype(np.uint8)
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[:, :, 0] = color_rgb[0]
    arr[:, :, 1] = color_rgb[1]
    arr[:, :, 2] = color_rgb[2]
    arr[:, :, 3] = alpha
    patch = Image.fromarray(arr, mode="RGBA")
    base_img.alpha_composite(patch, dest=(cx - radius, cy - radius))


def draw_sconce(base_img: Image.Image, draw: ImageDraw.ImageDraw, sx: int, sy: int) -> None:
    """Draws the small warm wall sconce exactly like @Lullorin 0s, 100s, 120s."""
    _draw_soft_glow(base_img, sx, sy, radius=58, color_rgb=(210, 125, 32), max_alpha=68)
    draw.polygon([(sx - 9, sy - 4), (sx + 9, sy - 4), (sx + 4, sy + 7), (sx - 4, sy + 7)], fill=(235, 160, 65, 255))
    draw.ellipse([sx - 3, sy - 8, sx + 3, sy - 2], fill=(255, 225, 140, 255))


def draw_hud_and_floor(
    draw: ImageDraw.ImageDraw,
    hud_label: str,
    global_frame: int,
    fps: int,
    caption: str,
    sub_green_text: str = "",
) -> None:
    font_hud = _load_font(19)
    font_cap = _load_font(42)
    font_green = _load_font(26)

    # Top-left HUD
    draw.text((48, 30), f"LULLORIN     {hud_label}", font=font_hud, fill=(205, 205, 205, 235))

    # Top-right HUD with blinking red dot
    total_sec = global_frame // fps
    ff = global_frame % fps
    mm = (total_sec // 60) % 60
    ss = total_sec % 60
    tc_str = f"00:{mm:02d}:{ss:02d}:{ff:02d}"
    if (global_frame // 12) % 2 == 0:
        draw.ellipse([1722, 34, 1734, 46], fill=COL_RED)
    draw.text((1745, 30), tc_str, font=font_hud, fill=(205, 205, 205, 235))

    # Solid black bottom bar + crisp white floor line
    draw.rectangle([0, FLOOR_Y, 1920, 1080], fill=(0, 0, 0, 255))
    draw.line([(0, FLOOR_Y), (1920, FLOOR_Y)], fill=(225, 225, 225, 255), width=3)

    if sub_green_text:
        tb_g = draw.textbbox((0, 0), sub_green_text, font=font_green)
        gw = tb_g[2] - tb_g[0]
        draw.text(((1920 - gw) // 2, FLOOR_Y + 14), sub_green_text, font=font_green, fill=COL_SAFE_GREEN)

    # Large bold ALL-CAPS bottom caption matching @Lullorin
    if caption:
        cap_up = caption.upper()
        tb = draw.textbbox((0, 0), cap_up, font=font_cap)
        tw = tb[2] - tb[0]
        tx = (1920 - tw) // 2
        ty = FLOOR_Y + (64 if not sub_green_text else 56)
        draw.text((tx, ty), cap_up, font=font_cap, fill=COL_WHITE)


def draw_speech_bubble(
    base_img: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    is_red: bool = False,
    tail_dir: str = "down",
    scale: float = 1.0,
) -> None:
    font_b = _load_font(max(int(30 * scale), 18))
    tb = draw.textbbox((0, 0), text, font=font_b)
    tw = tb[2] - tb[0]
    th = tb[3] - tb[1]
    pad_x = int(28 * scale)
    pad_y = int(16 * scale)
    x0 = x - tw // 2 - pad_x
    y0 = y - th // 2 - pad_y
    x1 = x + tw // 2 + pad_x
    y1 = y + th // 2 + pad_y

    if is_red:
        # Subtle red ambient glow behind entity speech bubbles (as seen in 120s, 140s, 200s, 540s)
        _draw_soft_glow(base_img, x, y, radius=max((x1 - x0) // 2 + 35, 70), color_rgb=(220, 20, 30), max_alpha=60)

    bg = COL_RED if is_red else COL_WHITE
    fg = (0, 0, 0, 255)
    draw.rounded_rectangle([x0, y0, x1, y1], radius=int(24 * scale), fill=bg)

    if tail_dir == "down":
        draw.polygon([(x - 12, y1 - 2), (x + 12, y1 - 2), (x - 6, y1 + 18)], fill=bg)
    elif tail_dir == "left":
        draw.polygon([(x0 + 2, y - 10), (x0 + 2, y + 10), (x0 - 20, y + 8)], fill=bg)
    elif tail_dir == "right":
        draw.polygon([(x1 - 2, y - 10), (x1 - 2, y + 10), (x1 + 20, y + 8)], fill=bg)

    draw.text((x - tw // 2, y - th // 2 - 2), text, font=font_b, fill=fg)


def draw_sound_waves(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    direction: str = "left",
    phase: float = 0.0,
    count: int = 3,
    radius_step: int = 26,
) -> None:
    for i in range(count):
        r = 32 + i * radius_step + int(7 * math.sin(phase * 2 * math.pi - i * 0.9))
        alpha = max(75, min(245, int(230 - i * 45)))
        bbox = [cx - r, cy - r, cx + r, cy + r]
        if direction == "left":
            draw.arc(bbox, start=132, end=228, fill=(240, 240, 240, alpha), width=3)
        elif direction == "right":
            draw.arc(bbox, start=-48, end=48, fill=(240, 240, 240, alpha), width=3)
        elif direction == "both":
            draw.arc(bbox, start=132, end=228, fill=(240, 240, 240, alpha), width=3)
            draw.arc(bbox, start=-48, end=48, fill=(240, 240, 240, alpha), width=3)


def draw_child_head_only(
    draw: ImageDraw.ImageDraw,
    hx: int,
    hy: int,
    scale: float = 1.0,
    expr: str = "fear",
    facing: str = "right",
    sweat: bool = True,
    yellow_eyes: bool = False,
    red_bow: bool = False,
) -> None:
    """Draws the expressive @Lullorin round white child head."""
    head_r = int(40 * scale)
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=COL_WHITE)

    # Hair tuft or sister's red bow (520s)
    if red_bow:
        bx, by = hx + int(14 * scale), hy - head_r + int(4 * scale)
        draw.polygon([(bx, by), (bx - 16, by - 10), (bx - 14, by + 8)], fill=COL_RED)
        draw.polygon([(bx, by), (bx + 16, by - 10), (bx + 14, by + 8)], fill=COL_RED)
        draw.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=COL_WHITE)
    else:
        draw.arc(
            [hx - int(15 * scale), hy - head_r - int(11 * scale), hx + int(15 * scale), hy - head_r + int(9 * scale)],
            start=195,
            end=345,
            fill=COL_WHITE,
            width=max(int(3 * scale), 2),
        )

    eye_offset = int(10 * scale) if facing == "right" else (-int(10 * scale) if facing == "left" else 0)
    ex1 = hx - int(12 * scale) + eye_offset
    ex2 = hx + int(12 * scale) + eye_offset
    ey = hy - int(4 * scale)
    er = max(int(5 * scale), 3)

    if yellow_eyes:
        for ex in (ex1, ex2):
            draw.ellipse([ex - er - 4, ey - er - 4, ex + er + 4, ey + er + 4], fill=COL_YELLOW_EYE)
            draw.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=COL_BLACK)
    else:
        draw.ellipse([ex1 - er, ey - er, ex1 + er, ey + er], fill=COL_BLACK)
        draw.ellipse([ex2 - er, ey - er, ex2 + er, ey + er], fill=COL_BLACK)

    # Expressive curved eyebrows
    draw.line(
        [(ex1 - er - 3, ey - er - 5), (ex1 + er, ey - er - 10)],
        fill=COL_BLACK,
        width=max(int(3 * scale), 2),
    )
    draw.line(
        [(ex2 - er, ey - er - 10), (ex2 + er + 3, ey - er - 5)],
        fill=COL_BLACK,
        width=max(int(3 * scale), 2),
    )

    my = hy + int(14 * scale)
    if expr == "gasp":
        draw.ellipse(
            [hx - int(11 * scale) + eye_offset, my - int(4 * scale), hx + int(11 * scale) + eye_offset, my + int(11 * scale)],
            fill=COL_BLACK,
        )
    elif expr == "fear":
        draw.arc(
            [hx - int(12 * scale) + eye_offset, my - int(3 * scale), hx + int(12 * scale) + eye_offset, my + int(12 * scale)],
            start=195,
            end=345,
            fill=COL_BLACK,
            width=max(int(3 * scale), 2),
        )
    else:
        draw.arc(
            [hx - int(10 * scale) + eye_offset, my - int(6 * scale), hx + int(10 * scale) + eye_offset, my + int(8 * scale)],
            start=15,
            end=165,
            fill=COL_BLACK,
            width=max(int(3 * scale), 2),
        )

    if sweat:
        sx = hx + (head_r + int(7 * scale) if facing != "right" else -head_r - int(14 * scale))
        sy = hy - int(20 * scale)
        draw.ellipse([sx, sy, sx + int(7 * scale), sy + int(13 * scale)], fill=COL_WHITE)
        draw.ellipse([sx + int(8 * scale), sy + int(11 * scale), sx + int(14 * scale), sy + int(22 * scale)], fill=COL_WHITE)


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
    red_bow: bool = False,
) -> None:
    head_r = int(40 * scale)
    hx = x
    hy = y - int((115 if not crouching else 78) * scale)

    if crouching:
        draw.rounded_rectangle(
            [hx - int(26 * scale), hy + head_r - 4, hx + int(26 * scale), y - int(16 * scale)],
            radius=int(18 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx - int(14 * scale), y - int(46 * scale), hx + int(34 * scale), y],
            radius=int(12 * scale),
            fill=COL_WHITE,
        )
    else:
        torso_top = hy + head_r - 4
        torso_bot = y - int(44 * scale)
        draw.rounded_rectangle(
            [hx - int(25 * scale), torso_top, hx + int(25 * scale), torso_bot],
            radius=int(15 * scale),
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
            [hx - int(34 * scale), torso_top + 6, hx - int(22 * scale), torso_bot - 4],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )
        draw.rounded_rectangle(
            [hx + int(22 * scale), torso_top + 6, hx + int(34 * scale), torso_bot - 4],
            radius=int(6 * scale),
            fill=COL_WHITE,
        )

    draw_child_head_only(
        draw,
        hx,
        hy,
        scale=scale,
        expr=expr,
        facing=facing,
        sweat=sweat,
        yellow_eyes=yellow_eyes,
        red_bow=red_bow,
    )


def draw_mom_figure(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float = 1.0,
    mode: str = "normal",
    waving: bool = False,
    leaning_right: bool = False,
    pointing_right: bool = False,
) -> None:
    """
    Draws the authentic @Lullorin Mother / Entity silhouette:
    - Clean rounded hair bun (no rectangle block behind head!)
    - Sloped shoulders, fitted waist, flared A-line skirt
    - Jointed arms with hands
    """
    head_r = int(40 * scale)
    lean_px = int(38 * scale) if leaning_right else 0
    hx = x + lean_px
    hy = y - int((248 if not leaning_right else 232) * scale)

    is_dark = mode == "dark_head"
    body_col = (182, 182, 188, 255) if is_dark else COL_WHITE
    head_col = (52, 52, 58, 255) if is_dark else COL_WHITE
    bun_col = (68, 68, 74, 255) if is_dark else (225, 225, 230, 255)

    # Clean rounded hair bun at top-back of head (like 20s, 160s, 520s)
    bun_x = hx - int(26 * scale) if not leaning_right else hx - int(30 * scale)
    bun_y = hy - int(26 * scale)
    bun_r = int(18 * scale)
    draw.ellipse([bun_x - bun_r, bun_y - bun_r, bun_x + bun_r, bun_y + bun_r], fill=bun_col)

    # Neck
    neck_top = hy + head_r - 6
    shoulder_y = neck_top + int(22 * scale)
    draw.polygon(
        [
            (hx - int(8 * scale), neck_top),
            (hx + int(8 * scale), neck_top),
            (x + lean_px // 2 + int(10 * scale), shoulder_y),
            (x + lean_px // 2 - int(10 * scale), shoulder_y),
        ],
        fill=head_col if is_dark else body_col,
    )

    # Fitted torso + flared A-line dress
    waist_y = shoulder_y + int(48 * scale)
    dress_bot = y - int(72 * scale)
    sx_center = x + lean_px // 2
    draw.polygon(
        [
            (sx_center - int(28 * scale), shoulder_y),
            (sx_center + int(28 * scale), shoulder_y),
            (x + int(22 * scale), waist_y),
            (x + int(54 * scale), dress_bot),
            (x - int(54 * scale), dress_bot),
            (x - int(22 * scale), waist_y),
        ],
        fill=body_col,
    )

    # Legs
    draw.rounded_rectangle([x - int(22 * scale), dress_bot - 4, x - int(7 * scale), y], radius=6, fill=body_col)
    draw.rounded_rectangle([x + int(7 * scale), dress_bot - 4, x + int(22 * scale), y], radius=6, fill=body_col)

    # Arms
    arm_w = max(int(11 * scale), 4)
    if waving:
        # Left arm down, right arm bent upward waving (20s)
        draw.line([(sx_center - int(26 * scale), shoulder_y + 4), (x - int(44 * scale), dress_bot - 22)], fill=body_col, width=arm_w)
        elbow_x, elbow_y = sx_center + int(44 * scale), shoulder_y + int(14 * scale)
        hand_x, hand_y = sx_center + int(48 * scale), hy - int(24 * scale)
        draw.line([(sx_center + int(26 * scale), shoulder_y + 4), (elbow_x, elbow_y)], fill=body_col, width=arm_w)
        draw.line([(elbow_x, elbow_y), (hand_x, hand_y)], fill=body_col, width=arm_w)
        draw.ellipse([hand_x - 8, hand_y - 8, hand_x + 8, hand_y + 8], fill=body_col)
    elif leaning_right:
        # Leaning against door listening (560s)
        draw.line([(sx_center - int(24 * scale), shoulder_y + 6), (x - int(42 * scale), dress_bot - 18)], fill=body_col, width=arm_w)
        draw.line([(sx_center + int(24 * scale), shoulder_y + 6), (x + int(68 * scale), shoulder_y + int(48 * scale))], fill=body_col, width=arm_w)
    elif pointing_right:
        draw.line([(sx_center - int(26 * scale), shoulder_y + 4), (x - int(44 * scale), dress_bot - 22)], fill=body_col, width=arm_w)
        draw.line([(sx_center + int(26 * scale), shoulder_y + 4), (x + int(78 * scale), shoulder_y + int(22 * scale))], fill=body_col, width=arm_w)
    else:
        draw.line([(sx_center - int(26 * scale), shoulder_y + 4), (x - int(48 * scale), dress_bot - 14)], fill=body_col, width=arm_w)
        draw.line([(sx_center + int(26 * scale), shoulder_y + 4), (x + int(48 * scale), dress_bot - 14)], fill=body_col, width=arm_w)

    # Head
    if mode == "entity":
        # Tilted creepy head with dark interior face, glowing yellow eyes, and wide toothed grin (80s)
        draw.ellipse([hx - head_r - 4, hy - head_r - 4, hx + head_r + 4, hy + head_r + 4], fill=COL_WHITE)
        draw.ellipse([hx - head_r + 5, hy - head_r + 5, hx + head_r - 5, hy + head_r - 5], fill=(24, 18, 16, 255))
        ey1, ey2 = hy - int(10 * scale), hy - int(4 * scale)
        ex1, ex2 = hx - int(14 * scale), hx + int(14 * scale)
        er = int(8 * scale)
        for ex, ey in [(ex1, ey1), (ex2, ey2)]:
            draw.ellipse([ex - er - 3, ey - er - 3, ex + er + 3, ey + er + 3], fill=(230, 210, 55, 130))
            draw.ellipse([ex - er, ey - er, ex + er, ey + er], fill=COL_YELLOW_EYE)
            draw.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=COL_BLACK)
        # Wide toothed grin
        draw.chord([hx - int(26 * scale), hy - int(2 * scale), hx + int(26 * scale), hy + int(28 * scale)], start=8, end=178, fill=COL_BLACK)
        for tx in range(hx - int(18 * scale), hx + int(20 * scale), max(int(6 * scale), 4)):
            draw.line([(tx, hy + int(8 * scale)), (tx, hy + int(22 * scale))], fill=(215, 215, 200, 230), width=2)
    else:
        draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=head_col)
        if mode == "normal":
            ey = hy - int(4 * scale)
            draw.ellipse([hx - int(15 * scale), ey - 4, hx - int(7 * scale), ey + 4], fill=COL_BLACK)
            draw.ellipse([hx + int(7 * scale), ey - 4, hx + int(15 * scale), ey + 4], fill=COL_BLACK)
            draw.arc(
                [hx - int(13 * scale), hy + int(4 * scale), hx + int(13 * scale), hy + int(18 * scale)],
                start=15,
                end=165,
                fill=COL_BLACK,
                width=max(int(3 * scale), 2),
            )


def render_rule_card_overlay(draw: ImageDraw.ImageDraw, r_num: int, r_title: str) -> None:
    font_badge = _load_font(34)
    font_title = _load_font(54)
    font_box = _load_font(24)

    badge_str = f"RULE {r_num}"
    tb = draw.textbbox((0, 0), badge_str, font=font_badge)
    bw, bh = tb[2] - tb[0] + 64, tb[3] - tb[1] + 32
    bx0, by0 = (1920 - bw) // 2, 305
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh], radius=14, outline=COL_WHITE, width=3)
    draw.text((bx0 + 32, by0 + 14), badge_str, font=font_badge, fill=COL_WHITE)

    tb2 = draw.textbbox((0, 0), r_title, font=font_title)
    tw2 = tb2[2] - tb2[0]
    draw.text(((1920 - tw2) // 2, 450), r_title, font=font_title, fill=COL_WHITE)

    start_x = 1920 // 2 - (7 * 54) // 2
    box_y = 595
    for i in range(1, 8):
        x0 = start_x + (i - 1) * 54
        is_cur = i == r_num
        fill_c = COL_WHITE if is_cur else (0, 0, 0, 255)
        out_c = COL_WHITE if i <= r_num else COL_MID_GREY
        txt_c = COL_BLACK if is_cur else out_c
        draw.rounded_rectangle([x0, box_y, x0 + 42, box_y + 42], radius=6, fill=fill_c, outline=out_c, width=2)
        draw.text((x0 + 13, box_y + 7), str(i), font=font_box, fill=txt_c)


# ==============================================================================
# 4. SCENE TEMPLATE RENDERERS (MATCHING ALL 41 FRAMES OF @LULLORIN SHEET)
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
    sub_green = ""

    # Brief 1.8s Rule Card flash at the start of a rule scene so it never hogs multiple contact-sheet slots
    rule_intro = scene.get("rule_intro")
    if rule_intro and phase < 1.8:
        render_rule_card_overlay(draw, int(rule_intro["num"]), rule_intro["title"])
        draw_hud_and_floor(draw, scene.get("hud", "NIGHT 01"), global_frame, fps, active_caption)
        return img.convert("RGB")

    # ------------------------------------------------------------------
    # TEMPLATE 1: HALLWAY_3_DOORS (0s, 100s, 120s, 180s, 420s, 680s, 760s, 780s)
    # ------------------------------------------------------------------
    if tpl == "HALLWAY_3_DOORS":
        # Subtle brown baseboard along the hallway wall
        draw.rectangle([0, FLOOR_Y - 14, 1920, FLOOR_Y], fill=COL_BASEBOARD)

        door_xs = [310, 810, 1310]
        door_w, door_h = 290, 565
        door_top = FLOOR_Y - door_h

        # 4 subtle wall sconces (left, mid-left, mid-right, right) — NO giant orange circles!
        for sx in [175, 705, 1205, 1735]:
            draw_sconce(img, draw, sx, door_top + 160)

        for dx in door_xs:
            draw.rectangle([dx, door_top, dx + door_w, FLOOR_Y], fill=(6, 6, 8, 255), outline=COL_MID_GREY, width=3)
            draw.rectangle([dx + 12, door_top + 12, dx + door_w - 12, FLOOR_Y], outline=(55, 55, 60, 255), width=1)
            draw.ellipse([dx + door_w - 40, door_top + 295, dx + door_w - 24, door_top + 311], fill=COL_MID_GREY)

        mode = props.get("mode", "empty")
        if mode == "white_mom":
            draw_mom_figure(draw, 1150, FLOOR_Y, scale=1.22, mode="normal")
        elif mode == "dark_head_mom_left":
            draw_mom_figure(draw, 640, FLOOR_Y, scale=1.25, mode="dark_head")
        elif mode == "dark_head_mom_left_waves":
            draw_mom_figure(draw, 640, FLOOR_Y, scale=1.25, mode="dark_head")
            draw_sound_waves(draw, 210, FLOOR_Y - 85, direction="right", phase=phase, count=3)
        elif mode == "red_bubble":
            draw_sound_waves(draw, 955, door_top + 275, direction="both", phase=phase, count=3)
            draw_speech_bubble(img, draw, 955, door_top + 190, "Goodnight", is_red=True, tail_dir="down")
        elif mode == "yellow_eyed_child":
            # 760s & 780s: Small child standing in front of left/center hallway door with glowing yellow eyes!
            draw_child_character(
                draw,
                655,
                FLOOR_Y,
                scale=1.12,
                expr="normal",
                facing="center",
                sweat=False,
                yellow_eyes=True,
            )

    # ------------------------------------------------------------------
    # TEMPLATE 2: HALLWAY_2_DOORS (480s)
    # ------------------------------------------------------------------
    elif tpl == "HALLWAY_2_DOORS":
        draw.rectangle([0, FLOOR_Y - 14, 1920, FLOOR_Y], fill=COL_BASEBOARD)
        door_w, door_h = 310, 575
        door_top = FLOOR_Y - door_h
        draw_sconce(img, draw, 960, door_top + 165)
        for dx in [430, 1180]:
            draw.rectangle([dx, door_top, dx + door_w, FLOOR_Y], fill=(6, 6, 8, 255), outline=COL_MID_GREY, width=3)
            draw.ellipse([dx + door_w - 42, door_top + 300, dx + door_w - 26, door_top + 316], fill=COL_MID_GREY)

    # ------------------------------------------------------------------
    # TEMPLATE 3: STAIRS_GOODNIGHT (20s)
    # ------------------------------------------------------------------
    elif tpl == "STAIRS_GOODNIGHT":
        font_lbl = _load_font(22)
        draw.text((130, 160), "NORMAL", font=font_lbl, fill=COL_MID_GREY)

        # Wall thermostat / control box [ o = ] from 20s
        tx, ty = 825, 290
        draw.rounded_rectangle([tx, ty, tx + 78, ty + 48], radius=6, outline=COL_MID_GREY, width=2)
        draw.ellipse([tx + 14, ty + 15, tx + 32, ty + 33], outline=COL_MID_GREY, width=2)
        draw.line([(tx + 44, ty + 18), (tx + 64, ty + 18)], fill=COL_MID_GREY, width=2)
        draw.line([(tx + 44, ty + 28), (tx + 64, ty + 28)], fill=COL_MID_GREY, width=2)

        # Stepped staircase + diagonal underside beam + handrail
        sx, sy = 770, FLOOR_Y
        steps = 8
        step_w, step_h = 72, 52
        pts = [(sx, sy)]
        for i in range(steps):
            pts.append((sx + i * step_w, sy - (i + 1) * step_h))
            pts.append((sx + (i + 1) * step_w, sy - (i + 1) * step_h))
        draw.line(pts, fill=COL_WHITE, width=3)
        draw.line([(sx + step_w, sy), (sx + steps * step_w, sy - (steps - 1) * step_h)], fill=COL_MID_GREY, width=2)
        draw.line([(sx, sy - 145), (sx + steps * step_w, sy - steps * step_h - 145)], fill=COL_MID_GREY, width=3)
        for i in range(0, steps + 1, 2):
            px = sx + i * step_w
            py = sy - i * step_h
            draw.line([(px, py), (px, py - 145)], fill=COL_MID_GREY, width=2)

        # Upstairs open door at top right
        top_x = sx + steps * step_w + 25
        top_y = sy - steps * step_h
        draw.rectangle([top_x, top_y - 350, top_x + 195, top_y], outline=COL_WHITE, width=3)
        draw.ellipse([top_x + 165, top_y - 170, top_x + 177, top_y - 158], fill=COL_WHITE)

        # Mom with hair bun waving at bottom of stairs
        draw_mom_figure(draw, 545, FLOOR_Y, scale=1.08, mode="normal", waving=True)
        draw_speech_bubble(img, draw, 910, 185, props.get("bubble", "Night, honey!"), is_red=False, tail_dir="down")

    # ------------------------------------------------------------------
    # TEMPLATE 4: BEDROOM_WIDE (40s, 140s, 200s, 300s, 340s, 360s, 380s, 540s, 580s, 600s, 620s, 640s, 700s, 720s, 740s)
    # ------------------------------------------------------------------
    elif tpl == "BEDROOM_WIDE":
        shift_x = 120 if props.get("show_bookshelf") else 0

        # Optional far-left bookshelf grid (600s)
        if props.get("show_bookshelf"):
            draw.rectangle([20, 260, 210, FLOOR_Y], outline=COL_MID_GREY, width=3)
            draw.line([(115, 260), (115, FLOOR_Y)], fill=COL_MID_GREY, width=2)
            for sy_shelf in range(380, FLOOR_Y, 130):
                draw.line([(20, sy_shelf), (210, sy_shelf)], fill=COL_MID_GREY, width=2)

        # 1. Wall Clock
        cx, cy, cr = 640 + shift_x, 240, 42
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], outline=COL_MID_GREY, width=2)
        draw.line([(cx, cy), (cx, cy - 26)], fill=COL_MID_GREY, width=2)
        draw.line([(cx, cy), (cx + 20, cy + 6)], fill=COL_MID_GREY, width=2)

        # 2. Four-pane Window with Moon
        wx, wy, ww, wh = 1020 + shift_x, 385, 215, 215
        if props.get("warm_window"):
            _draw_soft_glow(img, wx + ww // 2, wy + wh // 2, radius=155, color_rgb=(205, 145, 55), max_alpha=75)
            draw.rectangle([wx, wy, wx + ww, wy + wh], fill=(95, 70, 32, 110))
            draw.ellipse([wx + 80, wy + 36, wx + 136, wy + 92], fill=(225, 180, 90, 230))
        else:
            draw.rectangle([wx, wy, wx + ww, wy + wh], fill=(22, 28, 40, 125))
            draw.ellipse([wx + 80, wy + 36, wx + 136, wy + 92], fill=COL_MOON_BLUE)
        draw.rectangle([wx, wy, wx + ww, wy + wh], outline=COL_MID_GREY, width=3)
        draw.line([(wx + ww // 2, wy), (wx + ww // 2, wy + wh)], fill=COL_MID_GREY, width=2)
        draw.line([(wx, wy + wh // 2), (wx + ww, wy + wh // 2)], fill=COL_MID_GREY, width=2)

        if props.get("red_x_window"):
            draw.line([(wx + 125, wy - 72), (wx + 190, wy - 8)], fill=COL_RED, width=10)
            draw.line([(wx + 190, wy - 72), (wx + 125, wy - 8)], fill=COL_RED, width=10)

        # 3. Nightstand & Lamp
        nx = 135 + shift_x
        draw.rectangle([nx, FLOOR_Y - 170, nx + 130, FLOOR_Y], outline=COL_MID_GREY, width=3)
        draw.rectangle([nx + 16, FLOOR_Y - 145, nx + 114, FLOOR_Y - 95], outline=COL_MID_GREY, width=2)
        draw.ellipse([nx + 61, FLOOR_Y - 124, nx + 69, FLOOR_Y - 116], fill=COL_MID_GREY)
        draw.rectangle([nx + 56, FLOOR_Y - 235, nx + 74, FLOOR_Y - 170], fill=COL_WHITE)
        draw.polygon([(nx + 34, FLOOR_Y - 235), (nx + 96, FLOOR_Y - 235), (nx + 80, FLOOR_Y - 290), (nx + 50, FLOOR_Y - 290)], fill=COL_WHITE)

        # 4. Bedroom Door (right) + Warm Under-Door Light Spill
        dx, dw, dh = 1480 + shift_x, 275, 625
        dy = FLOOR_Y - dh
        if dx < 1920:
            draw.polygon(
                [(dx, FLOOR_Y), (dx + dw, FLOOR_Y), (dx + dw + 65, FLOOR_Y + 26), (dx - 115, FLOOR_Y + 26)],
                fill=(185, 110, 28, 175),
            )
            if props.get("door_open_mom"):
                # 740s: Open doorway with real Mom standing inside frame
                draw.rectangle([dx, dy, dx + dw, FLOOR_Y], fill=(14, 14, 18, 255), outline=COL_WHITE, width=4)
                draw.polygon([(dx, dy), (dx - 65, dy + 35), (dx - 65, FLOOR_Y + 15), (dx, FLOOR_Y)], fill=COL_WHITE)
                draw_mom_figure(draw, dx + dw // 2, FLOOR_Y, scale=1.10, mode="normal")
            else:
                draw.rectangle([dx, dy, dx + dw, FLOOR_Y], fill=(8, 8, 10, 255), outline=COL_WHITE, width=4)
                draw.ellipse([dx + 28, dy + 330, dx + 46, dy + 348], fill=COL_WHITE)

        # 5. Bed & Child Posture (Never standing on top of the mattress!)
        bx, bw = 310 + shift_x, 560
        draw.rectangle([bx, FLOOR_Y - 305, bx + 22, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx + bw, FLOOR_Y - 195, bx + bw + 20, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx, FLOOR_Y - 110, bx + bw, FLOOR_Y - 40], fill=COL_WHITE)

        c_state = props.get("child_state", "lying")
        if c_state == "lying":
            # 40s / 200s: Child lying low on pillow looking up/right, blanket mound over body
            draw.rounded_rectangle([bx + 26, FLOOR_Y - 145, bx + 125, FLOOR_Y - 110], radius=12, fill=COL_MID_GREY)
            draw_child_head_only(draw, bx + 85, FLOOR_Y - 152, scale=0.95, expr="fear", facing="right", sweat=False)
            draw.chord([bx + 105, FLOOR_Y - 210 + breathe, bx + bw - 8, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
        elif c_state == "head_up":
            # 140s / 340s / 360s / 380s / 540s / 740s: Child propped up on pillow under covers (head & shoulders only!)
            draw.rounded_rectangle([bx + 26, FLOOR_Y - 148, bx + 130, FLOOR_Y - 110], radius=12, fill=COL_MID_GREY)
            draw.chord([bx + 95, FLOOR_Y - 215 + breathe, bx + bw - 8, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
            draw_child_head_only(draw, bx + 98, FLOOR_Y - 178, scale=1.06, expr="fear", facing="right", sweat=True)
        elif c_state == "under_blanket":
            # 580s / 620s: Completely hidden under white blanket mound
            draw.chord([bx + 42, FLOOR_Y - 245 + breathe, bx + bw - 15, FLOOR_Y - 42], start=180, end=360, fill=COL_WHITE)
        elif c_state in ("standing_door", "standing_door_sad"):
            # 300s / 640s / 700s / 720s: Empty bed + child standing on the floor near the right door
            draw.chord([bx + 65, FLOOR_Y - 175, bx + bw - 15, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
            draw_child_character(
                draw,
                dx - 92,
                FLOOR_Y,
                scale=1.08,
                expr="fear" if c_state == "standing_door" else "sad",
                facing="left",
                sweat=(c_state == "standing_door"),
            )

        if props.get("waves"):
            draw_sound_waves(draw, dx - 12, dy + 245, direction="left", phase=phase, count=3)

        red_bubbles = props.get("red_bubbles", [])
        for idx_b, b_txt in enumerate(red_bubbles):
            by = dy + 135 + idx_b * 82
            draw_speech_bubble(img, draw, dx - 25, by, b_txt, is_red=True, tail_dir="right")

        if props.get("white_bubble"):
            draw_speech_bubble(img, draw, 930, 410, props["white_bubble"], is_red=False, tail_dir="down")

    # ------------------------------------------------------------------
    # TEMPLATE 5: BEDROOM_EMPTY_NIGHTSTAND (460s)
    # ------------------------------------------------------------------
    elif tpl == "BEDROOM_EMPTY_NIGHTSTAND":
        bx, bw = 480, 620
        draw.rectangle([bx, FLOOR_Y - 310, bx + 24, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx + bw, FLOOR_Y - 200, bx + bw + 22, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx, FLOOR_Y - 115, bx + bw, FLOOR_Y - 42], fill=COL_WHITE)
        draw.chord([bx + 60, FLOOR_Y - 195, bx + bw - 12, FLOOR_Y - 45], start=180, end=360, fill=COL_LIGHT_GREY)
        # Nightstand & phone on right (460s)
        nx = 1320
        draw.rectangle([nx, FLOOR_Y - 165, nx + 140, FLOOR_Y], outline=COL_MID_GREY, width=3)
        draw.rectangle([nx + 52, FLOOR_Y - 205, nx + 88, FLOOR_Y - 165], outline=COL_WHITE, width=2)

    # ------------------------------------------------------------------
    # TEMPLATE 6: BED_CLOSEUP_LISTEN (60s)
    # ------------------------------------------------------------------
    elif tpl == "BED_CLOSEUP_LISTEN":
        # Nightstand & Lamp on left
        draw.rectangle([75, FLOOR_Y - 285, 315, FLOOR_Y], outline=COL_MID_GREY, width=4)
        draw.rectangle([100, FLOOR_Y - 250, 290, FLOOR_Y - 165], outline=COL_MID_GREY, width=2)
        draw.ellipse([188, FLOOR_Y - 214, 202, FLOOR_Y - 200], fill=COL_MID_GREY)
        draw.rectangle([180, FLOOR_Y - 405, 210, FLOOR_Y - 285], fill=COL_WHITE)
        draw.polygon([(120, FLOOR_Y - 405), (270, FLOOR_Y - 405), (242, FLOOR_Y - 515), (148, FLOOR_Y - 515)], fill=COL_WHITE)

        # Slatted headboard & footboard (exact match to 60s)
        bx, bw = 420, 1220
        draw.rectangle([bx, FLOOR_Y - 535, bx + 36, FLOOR_Y], fill=COL_WHITE)
        for sx_bar in range(bx + 42, bx + 180, 28):
            draw.line([(sx_bar, FLOOR_Y - 460), (sx_bar, FLOOR_Y - 180)], fill=COL_MID_GREY, width=4)
        draw.rectangle([bx + bw, FLOOR_Y - 355, bx + bw + 34, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([bx, FLOOR_Y - 180, bx + bw, FLOOR_Y - 48], fill=COL_WHITE)

        # Blanket mound + large startled child sitting up under covers
        draw.chord([630, FLOOR_Y - 395 + breathe, bx + bw - 18, FLOOR_Y - 48], start=180, end=360, fill=COL_LIGHT_GREY)
        draw_child_head_only(draw, 695, FLOOR_Y - 365, scale=1.95, expr="gasp", facing="right", sweat=True)
        draw_sound_waves(draw, 1140, FLOOR_Y - 395, direction="left", phase=phase, count=3, radius_step=36)
        active_caption = "-JUST LISTEN.-"

    # ------------------------------------------------------------------
    # TEMPLATE 7: DUAL_MOM_COMPARISON (80s)
    # ------------------------------------------------------------------
    elif tpl == "DUAL_MOM_COMPARISON":
        # Left: Normal Mom + white "Goodnight" bubble + sound waves
        draw_mom_figure(draw, 330, FLOOR_Y, scale=1.55, mode="normal")
        draw_speech_bubble(img, draw, 530, 175, "Goodnight", is_red=False, tail_dir="down", scale=1.22)
        draw_sound_waves(draw, 540, 520, direction="right", phase=phase, count=2)

        # Right: Grinning yellow-eyed Entity Mom + red "Goodnight" bubble with glow
        draw_mom_figure(draw, 1185, FLOOR_Y, scale=1.55, mode="entity")
        draw_speech_bubble(img, draw, 1465, 165, "Goodnight", is_red=True, tail_dir="left", scale=1.25)

    # ------------------------------------------------------------------
    # TEMPLATE 8: RULE_CARD (240s)
    # ------------------------------------------------------------------
    elif tpl == "RULE_CARD":
        render_rule_card_overlay(
            draw,
            int(props.get("rule_num", 3)),
            props.get("rule_title", "WATCH THE GAP UNDER YOUR DOOR"),
        )

    # ------------------------------------------------------------------
    # TEMPLATE 9: DOOR_GAP_CLOSEUP (260s, 280s)
    # ------------------------------------------------------------------
    elif tpl == "DOOR_GAP_CLOSEUP":
        dx0, dx1 = 360, 1560
        gap_y = FLOOR_Y - 38

        draw.polygon(
            [(dx0, gap_y), (dx1, gap_y), (dx1 + 220, FLOOR_Y + 18), (dx0 - 220, FLOOR_Y + 18)],
            fill=COL_AMBER,
        )

        s_mode = props.get("shadows", "center")
        offset = int(t_norm * 540) if s_mode == "sliding" else 0
        for fx in (840 + offset, 1040 + offset):
            if dx0 - 40 <= fx <= dx1 + 40:
                draw.ellipse([fx - 55, gap_y - 6, fx + 55, gap_y + 24], fill=COL_BLACK)
                draw.polygon(
                    [(fx - 50, gap_y + 10), (fx + 50, gap_y + 10), (fx + 88, FLOOR_Y + 18), (fx - 88, FLOOR_Y + 18)],
                    fill=(10, 6, 2, 235),
                )

        draw.rectangle([dx0, 95, dx1, gap_y], fill=(8, 8, 10, 255), outline=COL_WHITE, width=5)
        draw.rectangle([dx0 + 38, 125, dx1 - 38, gap_y - 34], outline=COL_MID_GREY, width=2)

    # ------------------------------------------------------------------
    # TEMPLATE 10: SPLIT_DOOR_CUTAWAY (320s, 400s, 560s)
    # ------------------------------------------------------------------
    elif tpl == "SPLIT_DOOR_CUTAWAY":
        wall_x = 960
        draw_sconce(img, draw, 440, 350)
        draw.rectangle([1440, 390, 1645, 595], outline=COL_MID_GREY, width=3)
        draw.line([(1542, 390), (1542, 595)], fill=COL_MID_GREY, width=2)
        draw.line([(1440, 492), (1645, 492)], fill=COL_MID_GREY, width=2)
        draw.ellipse([1518, 425, 1568, 475], fill=COL_MOON_BLUE)

        draw.rectangle([wall_x - 16, 150, wall_x + 16, FLOOR_Y - 18], fill=COL_WHITE)
        draw.ellipse([wall_x - 42, 560, wall_x - 20, 582], fill=COL_WHITE)
        draw.ellipse([wall_x + 20, 560, wall_x + 42, 582], fill=COL_WHITE)

        mode = props.get("mode", "entity_standing")
        if mode == "eyes_under_gap":
            draw_child_character(draw, wall_x + 175, FLOOR_Y, scale=1.22, expr="fear", facing="left", sweat=True)
            draw.ellipse([wall_x - 86, FLOOR_Y - 26, wall_x - 68, FLOOR_Y - 8], fill=COL_YELLOW_EYE)
            draw.ellipse([wall_x - 56, FLOOR_Y - 26, wall_x - 38, FLOOR_Y - 8], fill=COL_YELLOW_EYE)
        elif mode == "entity_standing":
            draw_mom_figure(draw, wall_x - 185, FLOOR_Y, scale=1.35, mode="dark_head")
            draw_child_character(draw, wall_x + 175, FLOOR_Y, scale=1.20, expr="fear", facing="left", sweat=True)
        elif mode == "entity_listening":
            draw_mom_figure(draw, wall_x - 155, FLOOR_Y, scale=1.35, mode="dark_head", leaning_right=True)
            draw_child_character(draw, wall_x + 195, FLOOR_Y, scale=1.15, expr="fear", facing="left", crouching=True)
            draw_sound_waves(draw, wall_x + 34, FLOOR_Y - 145, direction="right", phase=phase, count=2)

    # ------------------------------------------------------------------
    # TEMPLATE 11: DOOR_LOCK_CLOSEUP (220s, 800s)
    # ------------------------------------------------------------------
    elif tpl == "DOOR_LOCK_CLOSEUP":
        plate_x, plate_y = 850, 250
        draw.line([(1145, 90), (1145, FLOOR_Y)], fill=COL_WHITE, width=4)
        draw.rounded_rectangle([plate_x, plate_y, plate_x + 175, plate_y + 530], radius=34, outline=COL_WHITE, width=4)

        cx, cy = plate_x + 88, plate_y + 125
        draw.ellipse([cx - 58, cy - 58, cx + 58, cy + 58], outline=COL_WHITE, width=4)
        angle = -0.55 + 1.1 * t_norm
        dx = int(46 * math.cos(angle))
        dy = int(46 * math.sin(angle))
        draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=COL_WHITE, width=16)

        # Door handle lever below
        draw.rounded_rectangle([plate_x - 35, plate_y + 345, plate_x + 135, plate_y + 395], radius=18, fill=COL_LIGHT_GREY)

        # Anatomical 2D white hand with forearm, palm, 4 fingers, and thumb gripping the deadbolt (220s / 800s)
        # Forearm reaching from bottom-left
        draw.polygon([(430, FLOOR_Y), (610, FLOOR_Y), (cx - 10, cy + 75), (cx - 85, cy + 25)], fill=COL_WHITE)
        # Palm & curved fingers gripping the lock
        draw.ellipse([cx - 82, cy - 22, cx + 12, cy + 68], fill=COL_WHITE)
        for f_idx in range(4):
            fx0 = cx - 68 + f_idx * 17
            fy0 = cy - 42 + f_idx * 4
            draw.rounded_rectangle([fx0, fy0, fx0 + 14, fy0 + 42], radius=6, fill=COL_WHITE, outline=COL_MID_GREY, width=1)
        # Thumb pressing against the side of the deadbolt
        draw.rounded_rectangle([cx - 8, cy + 2, cx + 34, cy + 26], radius=10, fill=COL_WHITE, outline=COL_MID_GREY, width=1)

        if props.get("show_freeze"):
            font_frz = _load_font(34)
            draw.text((1380, 520), "FREEZE", font=font_frz, fill=COL_RED)

    # ------------------------------------------------------------------
    # TEMPLATE 12: PHONE_SCREEN (440s)
    # ------------------------------------------------------------------
    elif tpl == "PHONE_SCREEN":
        px0, py0, px1, py1 = 740, 130, 1180, 855
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
        sub_green = "ASLEEP IS SAFE"

    # ------------------------------------------------------------------
    # TEMPLATE 13: SPLIT_WALL_TWO_BEDS (500s)
    # ------------------------------------------------------------------
    elif tpl == "SPLIT_WALL_TWO_BEDS":
        draw.rectangle([952, 140, 968, FLOOR_Y], fill=COL_WHITE)
        # Left bed with sleeping child
        draw.rectangle([280, FLOOR_Y - 245, 302, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([280, FLOOR_Y - 105, 745, FLOOR_Y - 40], fill=COL_WHITE)
        draw_child_head_only(draw, 355, FLOOR_Y - 148, scale=0.92, expr="normal", facing="right", sweat=False)
        draw.chord([385, FLOOR_Y - 185, 730, FLOOR_Y - 42], start=180, end=360, fill=COL_LIGHT_GREY)

        # Right bed with our protagonist sitting up listening to the wall
        draw.rectangle([1620, FLOOR_Y - 245, 1642, FLOOR_Y], fill=COL_WHITE)
        draw.rectangle([1175, FLOOR_Y - 105, 1642, FLOOR_Y - 40], fill=COL_WHITE)
        draw.chord([1195, FLOOR_Y - 185, 1545, FLOOR_Y - 42], start=180, end=360, fill=COL_LIGHT_GREY)
        draw_child_head_only(draw, 1525, FLOOR_Y - 175, scale=1.05, expr="fear", facing="left", sweat=True)
        draw_sound_waves(draw, 968, FLOOR_Y - 220, direction="right", phase=phase, count=3)

    # ------------------------------------------------------------------
    # TEMPLATE 14: FLASHBACK_TABLE (160s, 520s)
    # ------------------------------------------------------------------
    elif tpl == "FLASHBACK_TABLE":
        tx0, tx1, ty = 520, 1140, FLOOR_Y - 210
        draw.rectangle([tx0, ty, tx1, FLOOR_Y], outline=COL_WHITE, width=4)
        draw_child_character(draw, 675, ty, scale=1.05, expr="normal", facing="right", sweat=False)
        if props.get("mode") == "two_kids":
            # 520s: Sister with red hair bow sitting on right side of table + "Ha ha ha!" + Mom pointing on right
            draw_child_character(draw, 985, ty, scale=1.05, expr="normal", facing="left", sweat=False, red_bow=True)
            draw_speech_bubble(img, draw, 490, 260, props.get("bubble", "Ha ha ha!"), is_red=False, tail_dir="down")
            draw_mom_figure(draw, 1530, FLOOR_Y, scale=1.18, mode="normal", pointing_right=True)
        else:
            # 160s: Mom standing on right + "You were talking in your sleep!"
            draw_mom_figure(draw, 1430, FLOOR_Y, scale=1.18, mode="normal")
            draw_speech_bubble(img, draw, 1020, 205, props.get("bubble", "You were talking in your sleep!"), is_red=False, tail_dir="right")

    draw_hud_and_floor(draw, scene.get("hud", "NIGHT 01"), global_frame, fps, active_caption, sub_green_text=sub_green)
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
            "-af", "highpass=f=80,treble=g=2.0:f=3600,acompressor=threshold=-18dB:ratio=2.5:makeup=2dB,apad=pad_dur=0.35",
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
def split_caption_phrases(text: str, max_chars: int = 38) -> List[str]:
    sentences = re.split(r"(?<=[.!?—:;])\s+", text.strip())
    chunks: List[str] = []
    for s in sentences:
        words = s.split()
        cur: List[str] = []
        for w in words:
            cand = " ".join(cur + [w])
            if len(cand) <= max_chars or not cur:
                cur.append(w)
                if w.endswith((",", ";", ":")) and len(cand) >= 16:
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

    phrases = split_caption_phrases(scene["narration"], max_chars=38)
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

    logger.info(f"🎬 Rendering 39-Scene Exact @Lullorin 2D Horror Video: '{story['title']}'")

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
        logger.info(f"✅ Rendered Exact 2D Scene {idx + 1:02d}/{len(scenes)} ({scene['template']})")

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
        "visual_style": "Exact @Lullorin 2D Minimalist Black-Background Animation (All 41 Contact Sheet Frames Matched)",
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
