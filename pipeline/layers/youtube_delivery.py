import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_to_youtube_private(video_path: str, meta: dict, thumbnail_path: str = None):
    if not os.path.exists("yt_token.json") and os.environ.get("YT_TOKEN_JSON", "").strip():
        open("yt_token.json", "w").write(os.environ["YT_TOKEN_JSON"])
    if not os.path.exists("yt_token.json"):
        print(f"ℹ️ [Layer 6] YouTube Token not added yet -> Master Video ready locally: {video_path}")
        return None
    creds = google.oauth2.credentials.Credentials.from_authorized_user_file("yt_token.json")
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"], "categoryId": "27"},
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
    vid_id = res["id"]
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(videoId=vid_id, media_body=MediaFileUpload(thumbnail_path)).execute()
        except Exception:
            pass
    print(f"🎉 Uploaded to YouTube Studio (PRIVATE)! Video ID: {vid_id}")
    return vid_id
