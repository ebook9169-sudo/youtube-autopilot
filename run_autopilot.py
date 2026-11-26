import os, json
from pipeline.layers.quota_manager import decide_production_plan
from pipeline.layers.research_brain import generate_verified_blueprint
from pipeline.layers.voice_engine import generate_voice_and_subs
from pipeline.layers.visual_assets import generate_visuals, generate_pro_thumbnail
from pipeline.layers.ffmpeg_animator import render_master_video
from pipeline.layers.quality_gate import inspect_and_certify
from pipeline.layers.youtube_delivery import upload_to_youtube_private

NICHE = os.environ.get("CHANNEL_NICHE", "Dark Psychology & Stoicism")

def run_factory():
    print("="*65)
    print("🚀 STARTING DUAL-FORMAT YOUTUBE AUTOPILOT FACTORY")
    print("="*65)
    plan = decide_production_plan()
    bp = generate_verified_blueprint(NICHE)
    report = {"topic": bp["topic"], "plan": plan, "outputs": {}}

    if plan["produce_long_16x9"]:
        print("\n🎬 [PRIORITY #1] Building 16:9 Pro Long-Form Video (1920x1080)...")
        lv = bp["long_video"]
        l_audio, l_ass = generate_voice_and_subs(lv["voiceover"], "long_16x9", "16:9", plan["long_voice_tier"]=="ELEVENLABS_PRO")
        l_imgs = generate_visuals(lv["scenes_16x9"], "16:9", "long_16x9")
        thumb = generate_pro_thumbnail(l_imgs[0], lv["thumbnail_text"])
        long_mp4 = render_master_video(l_imgs, l_audio, l_ass, "16:9", "output/long_video_16x9.mp4")
        report["outputs"]["long_video"] = inspect_and_certify(long_mp4, "1920x1080", bp)
        upload_to_youtube_private(long_mp4, lv, thumb)

    if plan["produce_short_9x16"]:
        print("\n⚡ [PRIORITY #2] Building 9:16 Companion Viral Short (1080x1920)...")
        sv = bp["short_video"]
        s_audio, s_ass = generate_voice_and_subs(sv["voiceover"], "short_9x16", "9:16", plan["short_voice_tier"]=="ELEVENLABS_PRO")
        s_imgs = generate_visuals(sv["scenes_9x16"], "9:16", "short_9x16")
        short_mp4 = render_master_video(s_imgs, s_audio, s_ass, "9:16", "output/short_video_9x16.mp4")
        report["outputs"]["short_video"] = inspect_and_certify(short_mp4, "1080x1920", bp)
        upload_to_youtube_private(short_mp4, sv)

    json.dump(report, open("output/audit_report.json", "w"), indent=2)
    print("\n🎉 ALL DONE! Audit Report saved to: output/audit_report.json")

if __name__ == "__main__":
    run_factory()
