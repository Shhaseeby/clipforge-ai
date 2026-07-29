import os
import subprocess
import sys
import random
import streamlit as st

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

def find_best_face_x_local(local_video_path, video_width):
    if not OPENCV_AVAILABLE: return int(video_width / 2)
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        cap = cv2.VideoCapture(local_video_path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                x, y, w, h = faces
                return x + int(w / 2)
    except: pass
    return int(video_width / 2)

def generate_clip_assets_cloud(video_stream_url, start_ts, duration, video_width, video_height, folder_name, clip_prefix, clip_id, phrase_list):
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    temp_chunk = os.path.join(folder_name, "temp_raw_chunk.mp4")
    output_vertical = os.path.join(folder_name, f"{clip_prefix}_Vertical_{clip_id}.mp4")
    
    if os.path.exists(temp_chunk): os.remove(temp_chunk)
    if os.path.exists(output_vertical): os.remove(output_vertical)
    
    # Direct Cloud Link Extraction logic to prevent download crashes
    ffmpeg_chunk_cmd = f'ffmpeg -y -ss {start_ts} -t {duration} -i "{video_stream_url}" -c copy "{temp_chunk}"'
    subprocess.run(ffmpeg_chunk_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not os.path.exists(temp_chunk) or os.path.getsize(temp_chunk) < 5000: return None

    face_x = find_best_face_x_local(temp_chunk, video_width)
    out_w_v = int(video_height * (9/16))
    crop_x_v = max(0, min(face_x - int(out_w_v / 2), video_width - out_w_v))
    
    # Ultimate light speed encoding settings
    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_v}:in_h:{crop_x_v}:0,scale=640:1136" -c:v libx264 -preset ultrafast -crf 26 -c:a aac "{output_vertical}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(temp_chunk)
    
    return output_vertical

st.set_page_config(page_title="ClipForge AI Dashboard", page_icon="🔥", layout="centered")

st.title("🔥 ClipForge AI - Video Panel")
st.write("Turn long YouTube videos into viral short-form contents instantly.")

youtube_url = st.text_input("🔗 Apni YouTube Video Ka Link Paste Karein:", placeholder="https://youtube.com...")
count_input = st.number_input("Har category ki kitni clips chahiye?", min_value=1, max_value=5, value=2)
clip_duration = st.number_input("Har clip kitny seconds ki ho?", min_value=15, max_value=60, value=30)

if st.button("🚀 Generate Viral Shorts Now"):
    if not youtube_url:
        st.error("Pehle YouTube video ka link lagayein!")
    else:
        with st.spinner("AI Engine is bypassing cloud limits... Please wait..."):
            try:
                # Clean URL tracking garbage parameters like ?si=
                clean_url = youtube_url.split("?")[0]
                
                # Dynamic Stream Link Pull Strategy without full disk writing
                info_cmd = [sys.executable, "-m", "yt_dlp", "-g", "-f", "best[height<=480]/best", clean_url]
                video_stream_url = subprocess.check_output(info_cmd, text=True).strip().split('\n')[0]
                
                duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_stream_url}"'
                total_seconds = float(subprocess.check_output(duration_cmd, shell=True).decode().strip())
                
                video_width = 854
                video_height = 480
                
                st.info("📦 Stream Bridge Connected Successfully! Cutting clips...")
                
                # Run Sequence Engine loops sequentially
                seq_time = 15.0
                for idx in range(count_input):
                    if (seq_time + clip_duration) > total_seconds: break
                    f_name = f"Sequence_Clip_{idx+1}"
                    v_out = generate_clip_assets_cloud(video_stream_url, int(seq_time), clip_duration, video_width, video_height, f_name, "Sequence", idx+1, ["Ghabrana nahi hai"])
                    
                    if v_out and os.path.exists(v_out):
                        st.markdown(f"### 🎬 Sequence Clip #{idx+1} Ready!")
                        with open(v_out, "rb") as f:
                            st.download_button(label=f"📥 Download Vertical Short #{idx+1}", data=f, file_name=f"Short_Vertical_{idx+1}.mp4", mime="video/mp4")
                    seq_time += clip_duration

                st.success("🎉 ALL SET! Saari clips download buttons ke sath live hain!")
            except Exception as e:
                st.error(f"❌ Cloud Execution Bridge Error: {e}\nTip: Agar baar baar block aaye, to choti lengths ki videos try karein.")
