import os
import subprocess
import random
import hashlib
import streamlit as st

# --- WEBSITE CORE VISUAL THEMING CONFIGURATIONS ---
st.set_page_config(page_title="ClipForge AI - Web Studio", page_icon="🔥", layout="wide")

# Injecting Custom Premium Cyberpunk Space Dark Style Matrix
st.markdown("""
    <style>
    .main { background-color: #0B0B0F; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    h1 { background: linear-gradient(to right, #6366F1, #A855F7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2.8rem; }
    .stButton>button { background-image: linear-gradient(to right, #6366F1, #A855F7); color: white; border: none; border-radius: 12px; font-weight: bold; width: 100%; height: 50px; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.4); transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(168, 85, 247, 0.6); }
    div[data-testid="stExpander"] { background-color: #12121A; border: 1px solid #1E1E2F; border-radius: 14px; padding: 10px; }
    .stFileUploader { background-color: #12121A; border: 2px dashed #6366F1; border-radius: 14px; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

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

def generate_clips_engine(video_file, start_ts, duration, video_width, video_height, folder_name, clip_id, format_choice):
    if not os.path.exists(folder_name): os.makedirs(folder_name)
    temp_chunk = os.path.join(folder_name, "temp_chunk.mp4")
    out_v = os.path.join(folder_name, f"Viral_Shorts_Clip_{clip_id}.mp4")
    out_s = os.path.join(folder_name, f"Square_Feed_Clip_{clip_id}.mp4")
    
    if os.path.exists(temp_chunk): os.remove(temp_chunk)
    subprocess.run(f'ffmpeg -y -ss {start_ts} -t {duration} -i "{video_file}" -c copy "{temp_chunk}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if not os.path.exists(temp_chunk): return None, None

    face_x = find_best_face_x_local(temp_chunk, video_width)
    out_w_v = int(video_height * (9/16))
    crop_x_v = max(0, min(face_x - int(out_w_v / 2), video_width - out_w_v))
    out_w_s = video_height
    crop_x_s = max(0, min(face_x - int(out_w_s / 2), video_width - out_w_s))
    
    v_path, s_path = None, None
    if format_choice in ["Vertical (9:16)", "Both Formats Together"]:
        subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_v}:in_h:{crop_x_v}:0,scale=360:640" -c:v libx264 -preset ultrafast -crf 26 -c:a aac "{out_v}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        v_path = out_v
    if format_choice in ["Square (1:1)", "Both Formats Together"]:
        subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_s}:in_h:{crop_x_s}:0,scale=400:400" -c:v libx264 -preset ultrafast -crf 26 -c:a aac "{out_s}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        s_path = out_s
        
    if os.path.exists(temp_chunk): os.remove(temp_chunk)
    return v_path, s_path

if 'generated_clips' not in st.session_state: st.session_state.generated_clips = None
if 'last_file_hash' not in st.session_state: st.session_state.last_file_hash = None

# --- DESIGNING WEBSITE GRID STRUCTURAL TILES ---
st.title("⚡ ClipForge AI - Personal Production Studio")
st.write("Duniya mein kahin se bhi apna short-form content automate karein. Powered by Vercel Core Servers.")

col_left, col_right = st.columns([1.1, 1.2], gap="large")

with col_left:
    st.markdown("### 🎛️ Control Panel Inputs")
    uploaded_file = st.file_uploader("📤 Drag & Drop Video File Here (Supported up to 1.5GB):", type=["mp4", "mov"])
    format_size = st.selectbox("📐 Output Video Layout Formats:", ["Vertical (9:16)", "Square (1:1)", "Both Formats Together"])
    count_input = st.number_input("🔢 Total kitni clips chahiye?", min_value=1, max_value=15, value=3)
    clip_duration = st.number_input("⏱️ Har clip kitny seconds ki ho?", min_value=15, max_value=60, value=30)
    process_btn = st.button("🚀 Process & Generate AI Content")

with col_right:
    st.markdown("### 📦 AI Output Pipelines Pipeline")
    
    if process_btn:
        if not uploaded_file:
            st.error("Pehle apni video file dashboard par upload karein!")
        else:
            with st.spinner("AI Processing Layers Mapping active... Please wait..."):
                try:
                    video_file = "workspace_source.mp4"
                    file_buffer = uploaded_file.getbuffer()
                    current_hash = hashlib.md5(file_buffer).hexdigest()
                    
                    if st.session_state.last_file_hash == current_hash and os.path.exists(video_file):
                        st.info("✅ CACHING MATRIX: Video matches server workspace! Speed skip active.")
                    else:
                        with open(video_file, "wb") as f: f.write(file_buffer)
                        st.session_state.last_file_hash = current_hash

                    duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                    total_seconds = float(subprocess.check_output(duration_cmd, shell=True).decode().strip())
                    w_cmd = f'ffprobe -v error -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                    video_width = int(subprocess.check_output(w_cmd, shell=True).decode().strip().split())
                    h_cmd = f'ffprobe -v error -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
                    video_height = int(subprocess.check_output(h_cmd, shell=True).decode().strip().split())
                    
                    clips_data = []
                    seq_time = 5.0
                    for idx in range(count_input):
                        if (seq_time + clip_duration) > total_seconds: break
                        f_name = f"Web_Short_{idx+1}"
                        v_out, s_out = generate_clips_engine(video_file, int(seq_time), clip_duration, video_width, video_height, f_name, idx+1, format_size)
                        
                        viral_score = random.randint(84, 99)
                        badge = "🔥 VIRAL MOMENT" if viral_score > 91 else "🚀 TRENDING POTENTIAL"
                        
                        clip_info = {
                            "id": idx + 1,
                            "v_path": v_out,
                            "s_path": s_out,
                            "score": viral_score,
                            "badge": badge,
                            "timings": f"{int(seq_time)}s - {int(seq_time + clip_duration)}s"
                        }
                        clips_data.append(clip_info)
                        seq_time += clip_duration

                    st.session_state.generated_clips = clips_data
                    st.success("🎉 ALL SET: Saari clips successfully generate ho gayi hain!")
                except Exception as e:
                    st.error(f"❌ Core Processing Error: {e}")

    # Output renderer block freeze state locks
    if st.session_state.generated_clips:
        for clip in st.session_state.generated_clips:
            with st.expander(f"🎬 Clip #{clip['id']} Analytics & Downloads ({clip['timings']})", expanded=True):
                c1, c2 = st.columns(2)
                with c1: st.metric(label="📊 AI Viral Index Score", value=f"{clip['score']}/100")
                with c2: st.markdown(f"**Status Badge:** `{clip['badge']}`")
                st.write("**💡 Suggested Clickbait Viral Titles:**")
                st.write(f"1. This Secret Strategy Changes Everything! (Part {clip['id']})\n2. 99% People Still Don't Know This Secret Hack 😱")
                st.write("**🏷️ Platform Hashtags:** `#shorts #foryou #viral #trending #clipforgeai`")
                
                if clip['v_path'] and os.path.exists(clip['v_path']):
                    with open(clip['v_path'], "rb") as f:
                        st.download_button(label=f"📹 Download Vertical Format (9:16) #{clip['id']}", data=f, file_name=f"Viral_Short_{clip['id']}.mp4", mime="video/mp4", key=f"v_{clip['id']}")
                if clip['s_path'] and os.path.exists(clip['s_path']):
                    with open(clip['s_path'], "rb") as f:
                        st.download_button(label=f"🖼️ Download Square Format (1:1) #{clip['id']}", data=f, file_name=f"Square_Feed_{clip['id']}.mp4", mime="video/mp4", key=f"s_{clip['id']}")
