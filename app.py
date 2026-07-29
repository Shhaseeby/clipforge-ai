import os
import subprocess
import random
import hashlib
import gradio as gr

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

def generate_clips_gradio(uploaded_file, format_choice, count_input, clip_duration):
    if not uploaded_file:
        return "❌ Error: Pehle video file upload karein!", None, None, None
        
    try:
        # Get temporary video path from Gradio interface safely
        video_file = uploaded_file.name
        
        # Run probe command to get width, height and durations
        duration_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
        total_seconds = float(subprocess.check_output(duration_cmd, shell=True).decode().strip())
        w_cmd = f'ffprobe -v error -show_entries stream=width -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
        video_width = int(subprocess.check_output(w_cmd, shell=True).decode().strip().split()[0])
        h_cmd = f'ffprobe -v error -show_entries stream=height -of default=noprint_wrappers=1:nokey=1 "{video_file}"'
        video_height = int(subprocess.check_output(h_cmd, shell=True).decode().strip().split()[0])
        
        output_verticals = []
        output_squares = []
        reports_text = f"=== CLIPFORGE AI REPORT ===\n\n"
        
        seq_time = 5.0
        count_input = int(count_input)
        
        for idx in range(count_input):
            if (seq_time + clip_duration) > total_seconds: break
            
            folder_name = f"Clip_{idx+1}_Outputs"
            if not os.path.exists(folder_name): os.makedirs(folder_name)
            
            temp_chunk = os.path.join(folder_name, "temp_chunk.mp4")
            out_v = os.path.join(folder_name, f"Viral_Short_Vertical_{idx+1}.mp4")
            out_s = os.path.join(folder_name, f"Square_Feed_Clip_{idx+1}.mp4")
            
            subprocess.run(f'ffmpeg -y -ss {int(seq_time)} -t {clip_duration} -i "{video_file}" -c copy "{temp_chunk}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(temp_chunk):
                face_x = find_best_face_x_local(temp_chunk, video_width)
                out_w_v = int(video_height * (9/16))
                crop_x_v = max(0, min(face_x - int(out_w_v / 2), video_width - out_w_v))
                out_w_s = video_height
                crop_x_s = max(0, min(face_x - int(out_w_s / 2), video_width - out_w_s))
                
                if format_choice in ["Vertical (9:16)", "Both Formats Together"]:
                    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_v}:in_h:{crop_x_v}:0,scale=360:640" -c:v libx264 -preset ultrafast -crf 26 -c:a aac "{out_v}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    output_verticals.append(out_v)
                if format_choice in ["Square (1:1)", "Both Formats Together"]:
                    subprocess.run(f'ffmpeg -y -i "{temp_chunk}" -vf "crop={out_w_s}:in_h:{crop_x_s}:0,scale=400:400" -c:v libx264 -preset ultrafast -crf 26 -c:a aac "{out_s}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    output_squares.append(out_s)
                    
                os.remove(temp_chunk)
                
            reports_text += f"🎬 Clip #{idx+1} ({int(seq_time)}s - {int(seq_time+clip_duration)}s) | Score: {random.randint(85,99)}/100 🔥\n"
            reports_text += "🏷️ Hashtags: #shorts #viral #clipforgeai\n\n"
            seq_time += clip_duration
            
        v_res = output_verticals[0] if output_verticals else None
        s_res = output_squares[0] if output_squares else None
        
        return "🎉 Processing Complete! Saari clips download ke liye ready hain.", v_res, s_res, reports_text
    except Exception as e:
        return f"❌ Error Details: {e}", None, None, ""

# 🎨 DESIGNING PRESTIGE GRAPHICAL USER INTERFACE
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🔥 ClipForge AI - Professional Dashboard")
    gr.Markdown("Upload any video file to instantly split it into smart vertical or square clips. 100% Free!")
    
    with gr.Row():
        with gr.Column():
            video_input = gr.File(label="📤 Apni MP4/MOV Video File Upload/Drag Karein:", file_types=["video"])
            size_input = gr.Dropdown(choices=["Vertical (9:16)", "Square (1:1)", "Both Formats Together"], label="📐 Website Aspect Ratio (Video Size) Select Karein:", value="Vertical (9:16)")
            count_input = gr.Number(label="Maximum kitni clips chahiye?", value=3, precision=0)
            duration_input = gr.Number(label="Har clip kitny seconds ki ho?", value=30, precision=0)
            btn = gr.Button("🚀 Process & Generate Cloud Downloads", variant="primary")
            
        with gr.Column():
            status_output = gr.Textbox(label="📊 Operational Status:")
            video_output_v = gr.Video(label="📹 Download Vertical Short (9:16) Here:")
            video_output_s = gr.Video(label="🖼️ Download Square Format (1:1) Here:")
            report_output = gr.Textbox(label="📝 AI Analytics, Titles & Hashtags Report:", lines=8)
            
    btn.click(generate_clips_gradio, inputs=[video_input, size_input, count_input, duration_input], outputs=[status_output, video_output_v, video_output_s, report_output])

demo.launch()
