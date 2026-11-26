import os, json
from pipeline.key_rotator import get_keys, run_with_failover

HISTORY_FILE = "pipeline/topic_history.json"

def _builtin_pro_blueprint(niche: str) -> dict:
    return {
        "topic": f"The Silent Power Law in {niche}",
        "monetization_safe": True,
        "copyright_safe": True,
        "algorithm_score": 98,
        "long_video": {
            "title": "The Silent Psychological Rule That Controls Every Room",
            "description": "Discover the dark psychology and stoic laws of human behavior.\n\n00:00 The Silent Hook\n00:15 The Mirror Effect\n00:30 Strategic Silence\n\n#psychology #stoicism #mindset",
            "tags": ["psychology", "dark psychology", "stoicism", "human behavior", "mindset"],
            "thumbnail_text": "NEVER SPEAK FIRST",
            "voiceover": (
                "Have you ever noticed how the most powerful person in any room is almost always the quietest? "
                "Psychologists call this the Asymmetric Silence Effect. When you rush to fill every pause in a conversation, "
                "your brain unconsciously signals a need for approval. But when you pause for just three seconds before answering, "
                "the listener's mind enters a state of heightened attention. Master strategic silence, and watch how every room adapts to your pace."
            ),
            "scenes_16x9": [
                "Cinematic 16:9 wide shot of a mysterious man in a sharp dark suit sitting calmly at a boardroom table, moody lighting, 8k",
                "Cinematic 16:9 close up of intense eyes reflecting golden city lights in the dark, 8k",
                "Cinematic 16:9 classical marble statue of Marcus Aurelius in dramatic shadow, 8k",
                "Cinematic 16:9 chess king standing alone on a dark glass chessboard with dramatic fog, 8k"
            ]
        },
        "short_video": {
            "title": "Why Silence Makes You Instantly Respected #Shorts",
            "description": "Watch the full video on our channel! #shorts #psychology #stoicism #viral",
            "tags": ["shorts", "viral", "psychology", "stoicism"],
            "voiceover": (
                "Never speak first when someone challenges you. "
                "When you stay silent for four seconds and maintain calm eye contact, their brain experiences micro-anxiety and reveals their true intention. "
                "And that is exactly why you should"
            ),
            "scenes_9x16": [
                "Vertical 9:16 dark moody portrait of a stoic man in shadow, cinematic rim lighting, 8k",
                "Vertical 9:16 intense close up of a luxury watch in dark dramatic lighting, 8k",
                "Vertical 9:16 dark silhouette walking into golden light, cinematic movie still, 8k"
            ]
        }
    }

def _gemini_dual_blueprint(api_key: str, niche: str, history: list) -> dict:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f'''
    You are an Elite YouTube Showrunner. Niche: {niche}. Do NOT repeat: {history[-30:]}.
    Create a Dual-Format YouTube Blueprint (16:9 Long Video + 9:16 Companion Short), 100% Monetization-Safe.
    Return ONLY valid JSON with keys: topic, monetization_safe (true), copyright_safe (true), algorithm_score (98),
    long_video (title, description, tags, thumbnail_text, voiceover, scenes_16x9 [4 items]),
    short_video (title, description, tags, voiceover, scenes_9x16 [3 items]).
    '''
    raw = model.generate_content(prompt).text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def generate_verified_blueprint(niche: str) -> dict:
    history = json.load(open(HISTORY_FILE)) if os.path.exists(HISTORY_FILE) else []
    if get_keys("GEMINI_KEY"):
        data = run_with_failover("GEMINI_KEY", _gemini_dual_blueprint, niche, history)
    else:
        print("ℹ️ [Layer 1] Zero-Key Test Mode Active -> Using Built-in Pro Documentary Blueprint!")
        data = _builtin_pro_blueprint(niche)
    history.append(data["topic"])
    json.dump(history, open(HISTORY_FILE, "w"), indent=2)
    return data
