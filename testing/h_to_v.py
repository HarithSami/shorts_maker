import cv2
import os
import numpy as np
from pathlib import Path

def create_blurred_background(frame, target_width, target_height):
    """Create a blurred background version of the frame"""
    # Resize frame to fill the target dimensions
    blurred = cv2.GaussianBlur(frame, (51, 51), 0)
    
    # Scale to fill the entire target area
    h, w = frame.shape[:2]
    scale = max(target_width / w, target_height / h)
    new_w, new_h = int(w * scale), int(h * scale)
    
    blurred_resized = cv2.resize(blurred, (new_w, new_h))
    
    # Center crop to target dimensions
    start_x = (new_w - target_width) // 2
    start_y = (new_h - target_height) // 2
    background = blurred_resized[start_y:start_y + target_height, start_x:start_x + target_width]
    
    return background

def convert_horizontal_to_vertical(input_path, output_path, use_blur=True):
    """
    Convert horizontal video to vertical 9:16 format
    
    Args:
        input_path: Path to input video
        output_path: Path for output video
        use_blur: If True, use blurred background. If False, use black background
    """
    
    # Open input video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {input_path}")
        return False
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Original dimensions: {original_width}x{original_height}")
    print(f"FPS: {fps}, Total frames: {total_frames}")
    
    # Calculate target dimensions (9:16 aspect ratio)
    # Use the original height as reference for the vertical dimension
    target_height = max(original_height, int(original_width * 16/9))
    target_width = int(target_height * 9/16)
    
    print(f"Target dimensions: {target_width}x{target_height}")
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (target_width, target_height))
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        if frame_count % 30 == 0:  # Progress update every 30 frames
            print(f"Processing frame {frame_count}/{total_frames}")
        
        if use_blur:
            # Create blurred background
            background = create_blurred_background(frame, target_width, target_height)
        else:
            # Create black background
            background = np.zeros((target_height, target_width, 3), dtype=np.uint8)
        
        # Scale original frame to fit within target dimensions while maintaining aspect ratio
        h, w = frame.shape[:2]
        scale = min(target_width / w, target_height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        scaled_frame = cv2.resize(frame, (new_w, new_h))
        
        # Center the scaled frame on the background
        start_x = (target_width - new_w) // 2
        start_y = (target_height - new_h) // 2
        
        background[start_y:start_y + new_h, start_x:start_x + new_w] = scaled_frame
        
        out.write(background)
    
    # Cleanup
    cap.release()
    out.release()
    
    print(f"Conversion complete! Output saved to: {output_path}")
    return True

def main():
    # Configuration
    USE_BLUR_BACKGROUND = True  # Toggle this to switch between blur and black background
    
    # Paths
    input_dir = Path("input")
    output_dir = Path("export")
    input_file = input_dir / "input.mp4"
    
    # Create directories if they don't exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file not found at {input_file}")
        print("Please place your video file at 'input/input.mp4'")
        return
    
    # Generate output filename
    background_type = "blur" if USE_BLUR_BACKGROUND else "black"
    output_file = output_dir / f"vertical_{background_type}_{input_file.stem}.mp4"
    
    print(f"Converting {input_file} to vertical format...")
    print(f"Background type: {'Blurred' if USE_BLUR_BACKGROUND else 'Black'}")
    
    # Convert video
    success = convert_horizontal_to_vertical(
        str(input_file), 
        str(output_file), 
        USE_BLUR_BACKGROUND
    )
    
    if success:
        print(f"\n✅ Success! Vertical video saved as: {output_file}")
    else:
        print("\n❌ Conversion failed!")

if __name__ == "__main__":
    main()