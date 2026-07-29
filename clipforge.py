import os
import subprocess
import random
import sys
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

def generate_clip_assets_cloud_safe(video_file, start_ts, duration, video_width, video_height, folder_name, clip_id, phrase_list):
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    temp_chunk = os.path.join(folder_name, "temp_raw_chunk.mp4")
    output_vertical = os.path.join(folder_name, f"Sequence_Vertical_{clip_id}.mp4")
    
    if os.path.exists(temp_chunk): os.remove(temp_chunk)
    if os.path.exists(output_vertical): os.remove(output_vertical)
    
    ffmpeg_chunk_cmd = f'ffmpeg -y -ss {start_ts} -t {duration} -i "{video_file}" -c copy "{temp_chunk}"'
    subprocess.run(ffmpeg_chunk_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not os.path.exists(temp_chunk): return None
    
    face_x = find_best_face_x_local(temp_chunk, video_width)
    out_w_v = int(video_height * (9/16))
    crop_x_v = max(0, min(face_x - int(out_w_v / 2), video_width - out_w_v))
    
    # Fast rendering presets mapping for stable outputs
    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_v}:in_h:{crop_x_v}:0,scale=360:640" -c:v libx264 -preset ultrafast -crf 28 -c:a aac "{output_vertical}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(temp_chunk)
    
    return output_vertical

st.set_page_config(page_title="ClipForge AI 24/7 Live", page_icon="🔥", layout="centered")

st.title("🔥 ClipForge AI - Professional Dashboard")
st.write("Upload any video to instantly split it into vertical shorts. 100% Free & Online!")

# 🔥 FIX: Disabling link entry to completely dodge YouTube restrictions
uploaded_file = st.file_uploader("📤 Apni MP4 Video File Upload Karein:", type=["mp4", "mov"])
count_input = st.number_input("Maximum kitni clips chahiye?", min_value=1, max_value=3, value=2)
clip_duration = st.number_input("Har clip kitny seconds ki ho?", min_value=15, max_value=45, value=30)

if st.button("🚀 Process & Generate Cloud Downloads"):
    if not uploaded_file:
        st.error("Pehle apni video file upload karein!")
    else:
        with st.spinner("AI Engine is cutting uploaded file inside cloud runtime slots..."):
            try:
                # Save uploaded file structure onto container virtual space safely
                video_file = "uploaded_source.mp4"
                with open(video_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                total_seconds = float(subprocess.check_output(duration_cmd, shell=True).decode().strip())
                
                # Fetch original spatial configurations via dynamic query parameters
                w_cmd = f'ffprobe -v error -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                video_width = int(subprocess.check_output(w_cmd, shell=True).decode().strip().split()[0])
                h_cmd = f'ffprobe -v error -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                video_height = int(subprocess.check_output(h_cmd, shell=True).decode().strip().split()[0])
                
                st.info("⚡ File loaded safely! Auto-framing sequences triggered...")
                roman_phrases = ["sab se pehle aap ne ghabrana nahi hai"]
                
                seq_time = 5.0
                for idx in range(count_input):
                    if (seq_time + clip_duration) > total_seconds: break
                    f_name = f"Cloud_Short_{idx+1}"
                    v_out = generate_clip_assets_cloud_safe(video_file, int(seq_time), clip_duration, video_width, video_height, f_name, idx+1, roman_phrases)
                    
                    if v_out and os.path.exists(v_out):
                        st.markdown(f"### 🎬 Clip #{idx+1} Ready!")
                        with open(v_out, "rb") as file_bytes:
                            st.download_button(label=f"📥 Download Vertical Short #{idx+1}", data=file_bytes, file_name=f"ClipForge_Short_{idx+1}.mp4", mime="video/mp4")
                    seq_time += clip_duration

                st.success("🎉 TASK COMPLETION: All clips generated successfully!")
                if os.path.exists(video_file): os.remove(video_file)
            except Exception as e:
                st.error(f"❌ Execution Interface Bridge Error: {e}")
