
import streamlit as st
import os, glob, urllib.parse
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.oauth2.credentials, json

st.divider()
st.header("📤 Direct YouTube Auto-Upload (Private / Draft Mode)")

videos = sorted(glob.glob("./storage/tasks/**/final-*.mp4", recursive=True), key=os.path.getmtime, reverse=True)
if not videos:
    st.info("🎬 Pehle upar 'Generate Video' dabayein. Video bante hi yahan Auto-Upload ke liye aa jayegi!")
else:
    selected_video = st.selectbox("Select Generated Video:", videos)
    col1, col2 = st.columns(2)
    with col1:
        yt_title = st.text_input("Video Title:", "Mind-Blowing Facts You Didn't Know! #Shorts")
        yt_desc = st.text_area("Video Description:", "Subscribe for daily viral shorts!\n\n#shorts #viral #facts")
        yt_privacy = st.selectbox("Upload Mode:", ["private", "unlisted", "public"], index=0)
    with col2:
        secret_file = st.file_uploader("Upload Google 'client_secret.json' (One-Time):", type=["json"])
        if secret_file:
            with open("client_secret.json", "wb") as f:
                f.write(secret_file.getbuffer())
            st.success("✅ client_secret.json Saved!")

        if os.path.exists("client_secret.json") and not os.path.exists("yt_token.json"):
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json", ["https://www.googleapis.com/auth/youtube.upload"],
                redirect_uri="http://localhost:8080/"
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            st.markdown(f"👉 **[1. Click Here to Login with YouTube Channel]({auth_url})**")
            redirect_resp = st.text_input("2. Login ke baad browser ke upar ka poora 'localhost' URL yahan paste karein:")
            if redirect_resp and "code=" in redirect_resp:
                code_val = urllib.parse.parse_qs(urllib.parse.urlparse(redirect_resp).query)["code"][0]
                flow.fetch_token(code=code_val)
                with open("yt_token.json", "w") as f:
                    f.write(flow.credentials.to_json())
                st.success("🎉 YouTube Channel Connected Successfully!")

    if st.button("🚀 Auto-Upload to YouTube (Draft/Private)", type="primary"):
        if not os.path.exists("yt_token.json"):
            st.error("⚠️ Pehle right side se apna YouTube Channel connect karein!")
        else:
            with st.spinner("Uploading video directly to your YouTube Channel..."):
                creds = google.oauth2.credentials.Credentials.from_authorized_user_file("yt_token.json")
                youtube = build("youtube", "v3", credentials=creds)
                body = {
                    "snippet": {"title": yt_title, "description": yt_desc, "categoryId": "22"},
                    "status": {"privacyStatus": yt_privacy, "selfDeclaredMadeForKids": False}
                }
                media = MediaFileUpload(selected_video, chunksize=-1, resumable=True)
                res = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
                vid_id = res["id"]
                st.balloons()
                st.success(f"✅ Video Uploaded as '{yt_privacy.upper()}'! Ab aap YouTube Studio se ise Publish kar sakte hain:")
                st.markdown(f"🔗 **[Open in YouTube Studio](https://studio.youtube.com/video/{vid_id}/edit)**")
