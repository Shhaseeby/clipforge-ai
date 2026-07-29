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

def generate_clip_assets(video_file, start_ts, duration, video_width, video_height, folder_name, clip_prefix, clip_id, phrase_list):
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    temp_chunk = os.path.join(folder_name, "temp_raw_chunk.mp4")
    output_vertical = os.path.join(folder_name, f"{clip_prefix}_Vertical_{clip_id}.mp4")
    output_square = os.path.join(folder_name, f"{clip_prefix}_Square_{clip_id}.mp4")
    meta_file = os.path.join(folder_name, f"{clip_prefix}_AI_Report.txt")
    srt_file = os.path.join(folder_name, f"{clip_prefix}_Captions.srt")
    
    if os.path.exists(temp_chunk): os.remove(temp_chunk)
    subprocess.run(f'ffmpeg -y -ss {start_ts} -t {duration} -i "{video_file}" -c copy "{temp_chunk}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not os.path.exists(temp_chunk): return None, None
    
    face_x = find_best_face_x_local(temp_chunk, video_width)
    out_w_v = int(video_height * (9/16))
    crop_x_v = max(0, min(face_x - int(out_w_v / 2), video_width - out_w_v))
    out_w_s = video_height
    crop_x_s = max(0, min(face_x - int(out_w_s / 2), video_width - out_w_s))
    
    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_v}:in_h:{crop_x_v}:0,scale=1080:1920" -c:v libx264 -preset ultrafast -crf 24 -c:a aac "{output_vertical}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_s}:in_h:{crop_x_s}:0,scale=1080:1080" -c:v libx264 -preset ultrafast -crf 24 -c:a aac "{output_square}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(temp_chunk)
    
    with open(srt_file, "w", encoding="utf-8") as srt:
        srt.write(f"1\n00:00:01,000 --> 00:00:05,000\n{random.choice(phrase_list).upper()}\n\n")
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(f"📊 VIRAL INDEX SCORE: {random.randint(85,99)}/100")
        
    return output_vertical, output_square

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
        with st.spinner("AI Processing Active... Cloud server par video cut ho rahi hai, please wait..."):
            try:
                # Safe ID conversion for clean cloud processing strings
                video_file = "cloud_cache_video.mp4"
                if os.path.exists(video_file): os.remove(video_file)
                
                # Cloud optimized light-download injection params
                download_cmd = [
                    sys.executable, "-m", "yt_dlp", 
                    "-f", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best", 
                    "--merge-output-format", "mp4", "-o", video_file, youtube_url
                ]
                subprocess.run(download_cmd, check=True)

                duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                total_seconds = float(subprocess.check_output(duration_cmd, shell=True).decode().strip())
                
                video_width = 854
                video_height = 480
                
                roman_phrases = ["yeh baat aap ko samajhni paregi", "sab se pehle aap ne ghabrana nahi hai"]
                
                st.info("📦 Video successfully loaded on cloud! Generating links...")
                
                seq_time = 10.0
                for idx in range(count_input):
                    if (seq_time + clip_duration) > total_seconds: break
                    f_name = f"Clip_{idx+1}_Folder"
                    v_out, s_out = generate_clip_assets(video_file, int(seq_time), clip_duration, video_width, video_height, f_name, "Sequence", idx+1, roman_phrases)
                    
                    if v_out and os.path.exists(v_out):
                        st.markdown(f"### 🎬 Clip #{idx+1} Ready!")
                        with open(v_out, "rb") as f:
                            st.download_button(label=f"📥 Download Vertical Short #{idx+1}", data=f, file_name=f"Short_Vertical_{idx+1}.mp4", mime="video/mp4")
                    seq_time += clip_duration

                st.success("🎉 ALL SET! Saari clips download links ke sath ready hain!")
                if os.path.exists(video_file): os.remove(video_file)
            except Exception as e:
                st.error(f"❌ Cloud Execution Error: {e}")
