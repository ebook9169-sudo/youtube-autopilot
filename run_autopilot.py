import os, json
from pipeline.layers.quota_manager import decide_production_plan
from pipeline.layers.research_brain import generate_verified_blueprint
from pipeline.layers.voice_engine import generate_section_by_section_voice
from pipeline.layers.visual_assets import generate_pictogram_scenes, generate_pro_thumbnail
from pipeline.layers.ffmpeg_animator import render_pictogram_master_video
from pipeline.layers.quality_gate import inspect_and_certify
from pipeline.layers.youtube_delivery import upload_to_youtube_private

NICHE = os.environ.get("CHANNEL_NICHE", "Do Not / 7 Survival Rules (Creepy Pictogram)")

def run_factory():
    os.makedirs("output", exist_ok=True)
    os.makedirs("pipeline", exist_ok=True)
    print("="*70)
    print("🚀 STARTING 'DO NOT / 7 SURVIVAL RULES' CREEPY PICTOGRAM FACTORY")
    print("="*70)

    plan = decide_production_plan()
    bp = generate_verified_blueprint(NICHE)
    report = {"topic": bp["topic"], "style": bp.get("style"), "publishing_package": bp.get("publishing_package"), "outputs": {}}

    # PRIORITY #1: 16:9 LONG VIDEO (Full 7 Survival Rules + Final Twist)
    print("\n🎬 [PRIORITY #1] Building 16:9 'Creepy Pictogram' Long Video (Section-by-Section Sync)...")
    lv = bp["long_video"]
    l_audios = generate_section_by_section_voice(lv["scenes"], prefix="long_16x9")
    l_imgs = generate_pictogram_scenes(lv["scenes"], aspect="16:9", prefix="long_16x9")
    thumb = generate_pro_thumbnail(l_imgs[0], lv["thumbnail_text"])
    long_mp4 = render_pictogram_master_video(l_imgs, l_audios, aspect="16:9", out_mp4="output/long_video_16x9.mp4")
    report["outputs"]["long_video"] = inspect_and_certify(long_mp4, "1920x1080", bp)
    upload_to_youtube_private(long_mp4, lv, thumb)

    # PRIORITY #2: 9:16 VIRAL SHORT
    print("\n⚡ [PRIORITY #2] Building 9:16 'Creepy Pictogram' Viral Short...")
    sv = bp["short_video"]
    s_audios = generate_section_by_section_voice(sv["scenes"], prefix="short_9x16")
    s_imgs = generate_pictogram_scenes(sv["scenes"], aspect="9:16", prefix="short_9x16")
    short_mp4 = render_pictogram_master_video(s_imgs, s_audios, aspect="9:16", out_mp4="output/short_video_9x16.mp4")
    report["outputs"]["short_video"] = inspect_and_certify(short_mp4, "1080x1920", bp)
    upload_to_youtube_private(short_mp4, sv)

    json.dump(report, open("output/audit_report.json", "w"), indent=2)
    print("\n🎉 CREEPY PICTOGRAM PACKAGE READY! Check output/audit_report.json")

if __name__ == "__main__":
    run_factory()
