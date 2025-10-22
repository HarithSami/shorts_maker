# pip install opencv-python moviepy imageio-ffmpeg numpy

import cv2
import numpy as np
import os
from pathlib import Path
from moviepy.editor import VideoFileClip

def create_blurred_background(frame, target_width, target_height):
    """Create blurred background filling target aspect."""
    blurred = cv2.GaussianBlur(frame, (51, 51), 0)
    h, w = frame.shape[:2]
    scale = max(target_width / w, target_height / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(blurred, (new_w, new_h))
    start_x = (new_w - target_width) // 2
    start_y = (new_h - target_height) // 2
    return resized[start_y:start_y + target_height, start_x:start_x + target_width]

def convert_horizontal_to_vertical(input_path, temp_output_path, use_blur=True):
    """Convert horizontal video to vertical 9:16 AVI (no audio)."""
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: cannot open {input_path}")
        return False

    fps = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Input {w}x{h} @ {fps:.2f}fps, {frames} frames")

    target_h = max(h, int(w * 16/9))
    target_w = int(target_h * 9/16)
    if target_w > 1080:
        target_w, target_h = 1080, 1920
    print(f"Output {target_w}x{target_h}")

    if os.path.exists(temp_output_path):
        os.remove(temp_output_path)

    codecs = [
        ('MJPG', cv2.VideoWriter_fourcc(*'MJPG')),
        ('XVID', cv2.VideoWriter_fourcc(*'XVID')),
        ('DIVX', cv2.VideoWriter_fourcc(*'DIVX')),
    ]
    out = None
    for name, fourcc in codecs:
        out = cv2.VideoWriter(temp_output_path, fourcc, fps, (target_w, target_h), True)
        if out.isOpened():
            print(f"Using codec {name}")
            break
        else:
            out.release()
            out = None
    if not out or not out.isOpened():
        print("Error: could not open any video writer.")
        cap.release()
        return False

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if use_blur:
            bg = create_blurred_background(frame, target_w, target_h)
        else:
            bg = np.zeros((target_h, target_w, 3), np.uint8)
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = cv2.resize(frame, (new_w, new_h))
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2
        bg[y:y + new_h, x:x + new_w] = scaled
        out.write(np.ascontiguousarray(bg, np.uint8))
        frame_idx += 1
        if frame_idx % 30 == 0:
            print(f"{frame_idx}/{frames} frames processed")

    cap.release()
    out.release()
    print(f"Video written to {temp_output_path}")
    return True

def attach_audio(original_video, silent_video, output_with_audio):
    """Attach original audio track using MoviePy (uses bundled ffmpeg)."""
    orig = VideoFileClip(original_video)
    silent = VideoFileClip(silent_video)
    if orig.audio is None:
        print("No audio track found in original.")
        silent.write_videofile(output_with_audio, codec='libx264', audio=False)
        return
    final = silent.set_audio(orig.audio)
    final.write_videofile(output_with_audio, codec='libx264', audio_codec='aac')

def main():
    # Configuration: Set to False for black background, True for blurred background
    USE_BLURRED_BACKGROUND = False
    
    input_dir = Path("input")
    output_dir = Path("export")
    input_file = input_dir / "input.mp4"
    temp_output = output_dir / "vertical_temp.avi"
    final_output = output_dir / "vertical_output_with_audio.mp4"

    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    if not input_file.exists():
        print(f"Missing input file: {input_file}")
        return

    background_type = "blurred" if USE_BLURRED_BACKGROUND else "black"
    print(f"Converting {input_file} to vertical format with {background_type} background...")
    success = convert_horizontal_to_vertical(str(input_file), str(temp_output), use_blur=USE_BLURRED_BACKGROUND)
    if not success:
        print("Conversion failed.")
        return

    print("Attaching audio...")
    attach_audio(str(input_file), str(temp_output), str(final_output))
    print(f"Final video saved to {final_output}")
    
    # Clean up temporary file
    if temp_output.exists():
        temp_output.unlink()
        print(f"Cleaned up temporary file: {temp_output}")

if __name__ == "__main__":
    main()
