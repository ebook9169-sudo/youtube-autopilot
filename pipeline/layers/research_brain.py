import os
import json
import random
import requests
from pipeline.key_rotator import rotator

STORY_SEEDS = [
    " waking up at 3:14 AM because you hear your own voice softly calling your name from inside the bathroom",
    "hearing four slow, polite knocks on your bedroom window even though your bedroom is on the third floor",
    "noticing your dog sitting completely frozen in the hallway staring at an empty ceiling corner and refusing to blink",
    "getting into an apartment elevator late at night and realizing the elevator mirror shows everyone except the person standing next to you",
    "waking up in the middle of the night and noticing all of your shoes have been neatly lined up facing your bed",
    "receiving an AirDrop photo on your phone at 2:47 AM taken from the crack of your own bedroom closet door",
    "hearing footsteps walking up your basement stairs every night at 3:00 AM, stopping right behind the locked door",
    "driving home alone on an empty road at night when your car dashboard alerts you that a passenger seatbelt in the backseat was just unbuckled",
    "finding a sticky note on your kitchen fridge in your own handwriting that says DO NOT TURN AROUND, even though you live alone",
    "looking through your front door peephole at night and seeing the hallway light on, even though someone is pressing their eye against the other side"
]

LULLORIN_PROMPT_TEMPLATE = """You are the head scriptwriter and art director for the viral USA YouTube channels @Lullorin, @Nightsill-u2n, and @NightoraVideos.
Write a 100% BRAND NEW, deeply unsettling second-person ("You...") psychological survival rules story based on this premise:
Premise: {seed}

CRITICAL RULES FOR SCRIPT & VISUALS:
1. NEVER copy old stories. Write a fresh, chilling, immersive narrative.
2. Start IMMEDIATELY in the eerie night situation (no boring intro). Build intense psychological dread, introduce 7 specific survival rules, and end with a bone-chilling final twist that changes everything.
3. Break the story into EXACTLY 14 scenes so visuals cut rapidly every few seconds like @Lullorin and @NightoraVideos.
4. Every `visual_prompt` MUST describe a clean, full-screen 2D dark minimalist pictogram illustration in the exact style of @Lullorin / @NightoraVideos:
   - Main character: smooth pure-white 2D minimalist pictogram silhouette figure (round white head, expressive terrified eyes, no facial mouth/nose clutter)
   - Environment: moody dark illustrated 2D room/hallway/car/house at night with deep atmospheric shadows and subtle red or cold blue rim lighting
   - Anomaly/Entity: tall pitch-black or dark-crimson shadow figure with glowing white pinhole eyes hiding in the background/doorway/window/mirror
   - Camera angles: vary between "Extreme close-up", "Wide cinematic shot", "Over-the-shoulder POV", "Low angle shot".

Return ONLY valid JSON with this exact structure:
{{
  "title": "DO NOT [Action] At 3:00 AM (7 Rules To Survive)",
  "thumbnail_text": "DON'T LOOK BACK",
  "thumbnail_prompt": "2D dark minimalist creepy pictogram illustration in the style of Lullorin and NightoraVideos, close-up of a pure white smooth pictogram character frozen in terror in a dark bedroom, while a tall pitch-black shadow figure with glowing white pinhole eyes leans out from a cracked red-lit doorway right behind them, high contrast, cinematic dark atmosphere, no text",
  "seo_description": "Full suspenseful description with hashtags #lullorin #nightora #survivalrules #creepy #donot #whatif",
  "tags": ["do not", "7 rules to survive", "lullorin style", "nightora", "creepy pictogram", "scary survival rules", "what if"],
  "publishing_package": {{
    "title_ideas": ["10 viral titles in @Lullorin and @NightoraVideos style..."],
    "thumbnail_prompts": ["5 detailed @Lullorin style thumbnail prompts..."]
  }},
  "scenes": [
    {{
      "scene_id": 1,
      "narration": "1 to 2 tense sentences of spoken narration for this scene...",
      "visual_prompt": "Wide cinematic 2D dark minimalist pictogram illustration, a pure white smooth stick-figure pictogram character lying awake in bed in a dark moody bedroom lit only by moonlight, looking toward a slightly open hallway door, eerie atmosphere, style of Lullorin and Nightora, no text",
      "motion": "zoom_in_slow"
    }}
  ]
}}"""

def _clean_and_parse_json(raw_text: str) -> dict:
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1:
        return json.loads(cleaned[start:end+1])
    raise ValueError("Invalid JSON response")

def generate_pro_storyboard(video_format="16:9") -> dict:
    custom_topic = os.environ.get("NICHE_OVERRIDE", "").strip()
    chosen_seed = custom_topic if custom_topic else random.choice(STORY_SEEDS)
    prompt = LULLORIN_PROMPT_TEMPLATE.format(seed=chosen_seed)
    print(f"[Brain] Generating 100% NEW @Lullorin / @NightoraVideos story for premise: {chosen_seed}")

    # 1. Try Gemini Free API across multiple model versions with strict JSON mode
    gemini_key = rotator.get_key("GEMINI_KEY")
    if gemini_key:
        for model_name in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.85,
                        "responseMimeType": "application/json"
                    }
                }
                resp = requests.post(url, json=payload, timeout=45)
                if resp.status_code == 200:
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = _clean_and_parse_json(raw)
                    if len(data.get("scenes", [])) >= 8:
                        print(f"[Brain] ✅ Generated Brand New Story via Gemini ({model_name}): {data.get('title')}")
                        return data
            except Exception as e:
                print(f"[Brain] Gemini ({model_name}) attempt note: {e}")

    # 2. Try Groq Free API (Llama-3.3-70B) with strict JSON Object mode
    groq_key = rotator.get_key("GROQ_KEY")
    if groq_key:
        try:
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You output only valid JSON objects."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.85,
                    "response_format": {"type": "json_object"}
                },
                timeout=40
            )
            if resp.status_code == 200:
                raw = resp.json()["choices"][0]["message"]["content"]
                data = _clean_and_parse_json(raw)
                if len(data.get("scenes", [])) >= 8:
                    print(f"[Brain] ✅ Generated Brand New Story via Groq Llama-3.3-70B: {data.get('title')}")
                    return data
        except Exception as e:
            print(f"[Brain] Groq API attempt note: {e}")

    # 3. Try Keyless Pollinations OpenAI Engine
    try:
        resp = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [{"role": "user", "content": prompt}],
                "model": "openai",
                "seed": random.randint(1000, 999999),
                "jsonMode": True
            },
            timeout=35
        )
        if resp.status_code == 200:
            data = _clean_and_parse_json(resp.text)
            if len(data.get("scenes", [])) >= 8:
                print(f"[Brain] ✅ Generated Brand New Story via Pollinations AI: {data.get('title')}")
                return data
    except Exception as e:
        print(f"[Brain] Pollinations LLM note: {e}")

    raise RuntimeError("All LLM APIs failed to generate a new story. Check GEMINI_KEY_1 or GROQ_KEY_1.")
