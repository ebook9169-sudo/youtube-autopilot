import os
import json
import random
import requests
from pipeline.key_rotator import rotator

VINSA_MASTER_PROMPT = """You are the 'Vinsa by Digital Dollars' Viral USA Faceless YouTube Storyboard Engine.
Create a complete production blueprint in the viral USA Niche: "Do Not" / "What If" (1 Wrong Everyday Action -> 7 Survival Rules -> Chilling Psychological Final Twist) in Visual Style #5: CREEPY PICTOGRAM.

Return ONLY valid JSON matching this exact structure:
{
  "selected_idea": "Idea title",
  "title": "DO NOT [Action] At 3:00 AM (7 Rules To Survive)",
  "thumbnail_text": "DO NOT ANSWER IT",
  "seo_description": "Full SEO description with hashtags #creepy #rules #whatif #survivalrules",
  "tags": ["do not", "7 rules to survive", "creepy pictogram", "what if", "analog horror", "scary rules"],
  "publishing_package": {
    "title_ideas": ["10 high-CTR viral titles..."],
    "thumbnail_prompts": ["10 creepy pictogram thumbnail prompts..."]
  },
  "block_a_assets": {
    "style_lock": "Style #5 Creepy Pictogram, minimalist 2D stark white chalk stick-figure pictogram on dark gritty charcoal analog horror background, blood-red hazard accents, high contrast, no text",
    "main_character": "White minimalist stick-figure pictogram person with wide startled hollow eyes",
    "anomaly_entity": "Tall distorted dark-red pictogram figure with glowing white pinhole eyes and elongated limbs",
    "location": "Dark minimalist suburban house interior with white wireframe walls and dim red doorway",
    "key_prop": "Glowing smartphone screen showing a group chat interface with 5 circular icons"
  },
  "voiceover_parts": [
    "Part 1 (Hook): ...",
    "Part 2 (Escalation): ...",
    "Part 3 (Rules 1 to 4): ...",
    "Part 4 (Rules 5 to 7): ...",
    "Part 5 (The Final Twist): ..."
  ],
  "scenes": [
    {
      "scene_id": 1,
      "part_index": 0,
      "rule_badge": "THE MISTAKE",
      "narration": "Spoken narration for this scene...",
      "subtitle_caption": "SHORT PUNCHY CAPTION",
      "block_b_visual_prompt": "Scene 1 visual description referencing main_character, key_prop, and location",
      "block_c_motion": "zoom_in_slow",
      "sfx_cue": "phone_buzz",
      "scene_archetype": "phone_chat_5th"
    }
  ]
}
Provide exactly 10 scenes covering the Hook, Escalation, all 7 Survival Rules, and the Final Twist."""

def _parse_json_safely(raw_text: str):
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        return json.loads(cleaned[start:end+1])
    raise ValueError("No valid JSON object found")

def generate_pro_storyboard(video_format="16:9") -> dict:
    custom_topic = os.environ.get("NICHE_OVERRIDE", "").strip()
    prompt = VINSA_MASTER_PROMPT
    if custom_topic:
        prompt += f"\nBase the story on this specific trigger: {custom_topic}"

    # 1. Try Free Gemini API (GEMINI_KEY_1 / GEMINI_KEY_2)
    gemini_key = rotator.get_key("GEMINI_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=35)
            if resp.status_code == 200:
                raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                data = _parse_json_safely(raw)
                if len(data.get("scenes", [])) >= 6:
                    print("[Brain] Generated fresh Vinsa Storyboard via Gemini Free API!")
                    return data
        except Exception as e:
            print(f"[Brain] Gemini API fallback triggered: {e}")

    # 2. Try Free Groq API (MoneyPrinterTurbo's fast free LLM: GROQ_KEY_1 / GROQ_KEY_2)
    groq_key = rotator.get_key("GROQ_KEY")
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=30
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                data = _parse_json_safely(raw)
                if len(data.get("scenes", [])) >= 6:
                    print("[Brain] Generated fresh Vinsa Storyboard via Groq Free API!")
                    return data
        except Exception as e:
            print(f"[Brain] Groq API fallback triggered: {e}")

    # 3. Try MoneyPrinterTurbo's 100% Keyless Pollinations Text API
    try:
        resp = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "openai",
                "jsonMode": True
            },
            timeout=25
        )
        if resp.status_code == 200 and "scenes" in resp.text:
            data = _parse_json_safely(resp.text)
            if len(data.get("scenes", [])) >= 6:
                print("[Brain] Generated fresh Vinsa Storyboard via Keyless Pollinations AI!")
                return data
    except Exception as e:
        print(f"[Brain] Keyless LLM fallback triggered: {e}")

    # 4. Guaranteed Master Storyboard (Exact Reference Video Story: 5th Blank Member in Family Group Chat)
    print("[Brain] Using Master Reference Storyboard (5th Member in Family Chat - 7 Rules + Twist)")
    return {
        "selected_idea": "5th Blank Member in Family Group Chat (Outlier Score: 98/100)",
        "title": "DO NOT Delete The 5th Member In Your Family Group Chat (7 Survival Rules)",
        "thumbnail_text": "WHO ADDED NUMBER 5?",
        "seo_description": "You are scrolling through your family group chat late at night. Mom, Dad, Lily, You... and a 5th blank gray icon that says Added by Nobody. Follow these 7 Survival Rules immediately.\n\n#donot #survivalrules #creepy #whatif #analoghorror #scarystories",
        "tags": ["do not", "7 rules to survive", "what if", "creepy pictogram", "family group chat horror", "analog horror rules"],
        "publishing_package": {
            "title_ideas": [
                "DO NOT Delete The 5th Member In Your Family Group Chat (7 Rules)",
                "If A Blank Profile Joins Your Family Chat At 3AM, Follow These 7 Rules",
                "7 Rules To Survive When Your Phone Counts 5 People In A House Of 4",
                "DO NOT Check Who Added The 5th Member To Your Group Chat",
                "What If An Unnamed Account Starts Typing In Your Family Chat?",
                "NEVER Screenshot The 5th Member In Your Family Group Chat",
                "7 Survival Rules When Someone In Your House Isn't Who They Say They Are",
                "DO NOT Look Up When The 5th Group Chat Member Starts Typing",
                "Your Phone Isn't Broken: 7 Rules For The Extra Person In Your Chat",
                "If Your Family Chat Shows 5 Members Instead Of 4, Do This Immediately"
            ],
            "thumbnail_prompts": [
                "Creepy pictogram style: 4 white stick figures and 1 glowing blood-red figure inside a smartphone chat screen, bold text WHO ADDED #5?",
                "Creepy pictogram style: Stick figure in bed looking at glowing red phone icon showing '5 Members', dark red eyes in bedroom doorway"
            ]
        },
        "block_a_assets": {
            "style_lock": "minimalist 2D creepy pictogram illustration, stark white stick-figure silhouette on dark gritty charcoal analog horror background, blood-red hazard accents, VHS grain, no watermark",
            "main_character": "white minimalist stick-figure person with wide panicked hollow eyes",
            "anomaly_entity": "distorted crimson-red shadow pictogram figure with glowing white pinhole eyes",
            "location": "dark minimalist two-story house wireframe with dimly lit hallway and creaking staircase",
            "key_prop": "glowing smartphone screen displaying 4 white user icons and a 5th nameless blood-red icon"
        },
        "voiceover_parts": [
            "You are scrolling through your family group chat late at night. Mom. Dad. Your sister Lily. And you. Four people. Except at the top of the screen, it says five members. Right below your name is a blank gray circle with no photo and no name. Just the words: Added by blank.",
            "You close the app and count on your fingers. One. Two. Three. Four. Five. You restart your phone, but the fifth profile is still there. It is not a glitch. It has been silently reading every message, learning when your mom falls asleep, and which stair creaks in the hallway. If you want to survive the night, follow these seven rules.",
            "Rule Number One: Do not try to remove the fifth member. The moment your thumb presses remove, every locked door in your house will unlatch at once. Rule Number Two: Mute your phone immediately. If the fifth profile sends an audio file, do not press play. It is a recording of your own voice asking for help from inside your closet. Rule Number Three: Text the group chat saying Goodnight, I am going to sleep now, and place your phone face down. It needs to believe you are unaware.",
            "Rule Number Four: If you hear footsteps stop outside your bedroom door, do not check the hallway peephole. Watch the group chat typing indicator instead. Rule Number Five: If the blank profile says typing, hold your breath and count to seven. It is testing which room echoes. Rule Number Six: Do not call your parents on the phone. Whoever answers will use your mother's exact voice to tell you to open the door. Rule Number Seven: Stay under your blanket until 6:00 AM, and never look at the ceiling corner.",
            "If you survive until sunrise, the group chat will go back to four members. Everything will feel normal again. Except for one final truth. Your phone was never broken. Phones do not miscount. Someone inside your house manually typed in a fifth slot. And whoever it is has been sitting at your dinner table for a very long time."
        ],
        "scenes": [
            {
                "scene_id": 1,
                "part_index": 0,
                "rule_badge": "THE MISTAKE",
                "narration": "You are scrolling through your family group chat late at night. Mom, Dad, Lily, and you. Four people. Except at the top of the screen, it says five members. A blank gray circle with no name.",
                "subtitle_caption": "5 MEMBERS IN A FAMILY OF 4...",
                "block_b_visual_prompt": "close up of glowing smartphone screen held by white pictogram hands, showing 4 white family profile icons and a 5th glowing blood-red nameless icon",
                "block_c_motion": "zoom_in_slow",
                "sfx_cue": "phone_buzz",
                "scene_archetype": "phone_chat_5th"
            },
            {
                "scene_id": 2,
                "part_index": 1,
                "rule_badge": "1.. 2.. 3.. 4.. 5",
                "narration": "You close the app and count on your fingers. One, two, three, four, five. You restart your phone, but the fifth member is still there. It is learning when your family sleeps.",
                "subtitle_caption": "IT IS NOT A PHONE GLITCH",
                "block_b_visual_prompt": "four white stick figure family members in separate rooms of a dark house cross-section while a fifth red shadow figure stands on the stairs",
                "block_c_motion": "zoom_out_slow",
                "sfx_cue": "static_glitch",
                "scene_archetype": "counting_five"
            },
            {
                "scene_id": 3,
                "part_index": 2,
                "rule_badge": "RULE #1",
                "narration": "Rule Number One: Do not try to delete or remove the fifth member. The moment your thumb presses remove, every locked door in your house will unlatch at once.",
                "subtitle_caption": "RULE #1: DO NOT REMOVE IT",
                "block_b_visual_prompt": "white pictogram hand hovering over a red REMOVE button on phone screen with a giant red X hazard cross and unlocking door icon",
                "block_c_motion": "zoom_in_slow",
                "sfx_cue": "deep_boom",
                "scene_archetype": "do_not_delete"
            },
            {
                "scene_id": 4,
                "part_index": 2,
                "rule_badge": "RULE #2 & #3",
                "narration": "Rule Number Two: Mute your phone immediately. Never play its audio message. Rule Number Three: Text the chat saying you are going to sleep, and place your phone face down.",
                "subtitle_caption": "RULE #2 & #3: MUTE & PLACE FACE DOWN",
                "block_b_visual_prompt": "white stick figure in bed placing glowing smartphone face down on nightstand while a red soundwave emanates from bedroom closet door",
                "block_c_motion": "zoom_out_slow",
                "sfx_cue": "phone_buzz",
                "scene_archetype": "phone_face_down"
            },
            {
                "scene_id": 5,
                "part_index": 3,
                "rule_badge": "RULE #4 & #5",
                "narration": "Rule Number Four: If footsteps stop outside your door, do not look outside. Rule Number Five: When the blank profile says typing, hold your breath and count to seven.",
                "subtitle_caption": "RULE #4 & #5: HOLD YOUR BREATH",
                "block_b_visual_prompt": "dark bedroom door cracked open with two glowing red eyes peeking through the gap while a white stick figure covers its mouth in bed",
                "block_c_motion": "zoom_in_slow",
                "sfx_cue": "deep_boom",
                "scene_archetype": "doorway_eyes"
            },
            {
                "scene_id": 6,
                "part_index": 3,
                "rule_badge": "RULE #6 & #7",
                "narration": "Rule Number Six: Do not answer calls from your parents' numbers. It is mimicking their voice. Rule Number Seven: Stay under your blanket until 6:00 AM and never look at the ceiling.",
                "subtitle_caption": "RULE #6 & #7: DO NOT LOOK UP",
                "block_b_visual_prompt": "white stick figure hiding under blanket in bed while a distorted red pictogram figure clings upside down to the dark bedroom ceiling corner",
                "block_c_motion": "zoom_out_slow",
                "sfx_cue": "static_glitch",
                "scene_archetype": "family_house"
            },
            {
                "scene_id": 7,
                "part_index": 4,
                "rule_badge": "THE FINAL TWIST",
                "narration": "Here is the final truth. Your phone was never broken. Phones do not miscount. Someone inside your own house manually added a fifth name. And they have been reading along the whole time.",
                "subtitle_caption": "PHONES DO NOT MISCOUNT...",
                "block_b_visual_prompt": "4 white family stick figures sitting around a dinner table, one family member casting a monstrous blood-red shadow holding a phone behind their back",
                "block_c_motion": "zoom_in_slow",
                "sfx_cue": "heartbeat",
                "scene_archetype": "final_twist_table"
            }
        ]
    }
