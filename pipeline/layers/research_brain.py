import os, json
from pipeline.key_rotator import get_keys, run_with_failover

HISTORY_FILE = "pipeline/topic_history.json"

def _builtin_creepy_pictogram_blueprint() -> dict:
    """Exact 'Do Not / 7 Survival Rules' Creepy Pictogram Blueprint (USA Audience High-RPM)."""
    scenes_long = [
        {
            "section": "THE ANOMALY",
            "rule_badge": "ANOMALY DETECTED",
            "visual_type": "chat_ui",
            "caption_title": "5 MEMBERS IN FAMILY CHAT",
            "pictogram_mode": "family_plus_red_entity",
            "voice": "You scroll through your family group chat at 2:14 AM. Mom. Dad. Lily. You. And a fifth gray circle. No photo. No name. Below it in tiny letters, it just says: Added by... and then a blank space.",
            "prompt": "Creepy minimalist pictogram style, dark gritty charcoal background, white stick figure family of 4 and a 5th glowing crimson red faceless figure standing behind them, analog horror warning sign, 8k"
        },
        {
            "section": "THE 5-SECOND TEST",
            "rule_badge": "VERIFICATION PROTOCOL",
            "visual_type": "countdown",
            "caption_title": "COUNT: 1 - 2 - 3 - 4 - 5",
            "pictogram_mode": "phone_glitch",
            "voice": "Do not tap the profile. Here is what you do right now. Close the app. Count to five. One. Two. Three. Four. Five. Open it again. If the fifth circle is still there, it is not a glitch. Glitches do not learn your family's routine.",
            "prompt": "Creepy pictogram warning sign, white pictogram hand holding a smartphone with a glowing red skull icon on screen, dark VHS static background, analog horror style"
        },
        {
            "section": "SURVIVAL RULE #1",
            "rule_badge": "SURVIVAL RULE 01 / 07",
            "visual_type": "rule_1",
            "caption_title": "RULE #1: DO NOT LEAVE THE GROUP",
            "pictogram_mode": "crossed_exit",
            "voice": "It knows when Mom goes to sleep. It knows which stair creaks in your hallway. To survive the night, follow these rules carefully. Rule Number One: Do not leave the group chat. Leaving tells it that you noticed it.",
            "prompt": "Creepy pictogram hazard sign, white pictogram figure trying to run through an exit door with a giant red X over it, tall dark shadow figure watching, gritty analog horror"
        },
        {
            "section": "SURVIVAL RULE #2 & #3",
            "rule_badge": "SURVIVAL RULE 02 & 03",
            "visual_type": "rule_2",
            "caption_title": "RULE #2: IGNORE THE TYPING BUBBLE",
            "pictogram_mode": "typing_eyes",
            "voice": "Rule Number Two: If you see three gray dots typing from the blank profile, lock your screen and place the phone face down. Rule Number Three: If your bedroom door is slightly open, do not look through the gap.",
            "prompt": "Creepy pictogram style, white pictogram person lying in bed with phone face down, two glowing red eyes peeking through a slightly open bedroom door, dark VHS horror"
        },
        {
            "section": "SURVIVAL RULE #4 & #5",
            "rule_badge": "SURVIVAL RULE 04 & 05",
            "visual_type": "rule_4",
            "caption_title": "RULE #4: VERIFY VOICE CALLS",
            "pictogram_mode": "mimic_call",
            "voice": "Rule Number Four: If Mom or Dad texts you asking you to come downstairs, check their spelling. It copies their words, but it never uses punctuation. Rule Number Five: Keep your hallway light off until 6:00 AM.",
            "prompt": "Creepy pictogram warning card, white pictogram figure at top of stairs, red distorted double figure at bottom of stairs waving, analog emergency broadcast aesthetic"
        },
        {
            "section": "THE FINAL TWIST",
            "rule_badge": "CRITICAL WARNING // TWIST",
            "visual_type": "final_twist",
            "caption_title": "WHO IS THE 5TH MEMBER?",
            "pictogram_mode": "twist_reveal",
            "voice": "And finally, Rule Number Seven: Your phone is not broken. Phones do not miscount people in a house. Someone in your house gave it a fifth spot. And whoever it is... they have been reading along behind your shoulder this whole time.",
            "prompt": "Creepy pictogram final twist, white pictogram figure looking at glowing phone screen while a giant red pictogram shadow looms directly over their shoulder reading the screen, analog horror"
        }
    ]

    scenes_short = [
        scenes_long[0],
        scenes_long[1],
        scenes_long[2],
        scenes_long[5]
    ]

    return {
        "topic": "If You See a 5th Blank Profile in Your Family Chat, Follow These 7 Rules",
        "style": "Style #5: Creepy Pictogram (USA Viral Niche)",
        "monetization_safe": True,
        "copyright_safe": True,
        "algorithm_score": 99,
        "publishing_package": {
            "title_ideas": [
                "If Your Family Group Chat Has a 5th Blank Member, DO NOT Text Back",
                "7 Survival Rules If an Unknown Profile Joins Your Family Chat at 3 AM",
                "DO NOT Delete the 5th Member in Your Family Group Chat (7 Rules)"
            ]
        },
        "long_video": {
            "title": "If Your Family Chat Has a 5th Blank Member, DO NOT Text Back (7 Rules)",
            "description": "What if you see a 5th unnamed profile in your family group chat? Follow these survival rules carefully.\n\n00:00 The 5th Member Anomaly\n00:18 The 5-Second Verification Test\n00:35 Survival Rules #1 to #5\n01:10 The Final Twist\n\n#donot #whatif #survivalrules #creepy #analoghorror",
            "tags": ["do not", "what if", "7 survival rules", "creepy pictogram", "analog horror", "scary rules", "storytime"],
            "thumbnail_text": "DO NOT TEXT BACK",
            "scenes": scenes_long
        },
        "short_video": {
            "title": "If You See a 5th Blank Profile in Your Family Chat... #Shorts",
            "description": "Never leave the group chat. Watch the full 7 Survival Rules on our channel! #shorts #donot #whatif #creepy #rules",
            "tags": ["shorts", "donot", "whatif", "survivalrules", "creepy"],
            "scenes": scenes_short
        }
    }

def _gemini_vinsa_blueprint(api_key: str, history: list) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f'''
    You are the "Vinsa Master Skill" Showrunner for the viral USA "DO NOT / WHAT IF / 7 SURVIVAL RULES" niche in Style #5: CREEPY PICTOGRAM.
    Past topics (DO NOT REPEAT): {history[-30:]}.
    Create a brand-new, chilling, 100% Advertiser-Friendly (no gore/profanity, pure psychological uncanny suspense) story where an everyday object/app/place has a creepy anomaly, followed by Survival Rules and a mind-blowing Final Twist.
    Return ONLY valid JSON matching the exact schema of _builtin_creepy_pictogram_blueprint() with 6 scenes in long_video.scenes and 4 scenes in short_video.scenes.
    Each scene must have: "section", "rule_badge", "visual_type", "caption_title", "pictogram_mode", "voice" (25-35 words spoken second-person 'You'), and "prompt" (Creepy minimalist white & red pictogram on dark gritty analog horror background).
    '''
    raw = model.generate_content(prompt).text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_verified_blueprint(niche: str = "Do Not / 7 Survival Rules") -> dict:
    os.makedirs("pipeline", exist_ok=True)
    history = json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []
    if get_keys("GEMINI_KEY"):
        try:
            data = run_with_failover("GEMINI_KEY", _gemini_vinsa_blueprint, history)
        except Exception as e:
            print(f"ℹ️ Gemini fallback to Vinsa Master Blueprint ({e})")
            data = _builtin_creepy_pictogram_blueprint()
    else:
        print("ℹ️ [Vinsa Master Skill] Using Built-in Viral '5th Member in Family Chat' Creepy Pictogram Blueprint!")
        data = _builtin_creepy_pictogram_blueprint()

    history.append(data["topic"])
    json.dump(history, open(HISTORY_FILE, "w"), indent=2)
    return data
