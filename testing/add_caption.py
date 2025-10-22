from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

# Ensure export directory exists
os.makedirs("export", exist_ok=True)

# Load video from input directory
video = VideoFileClip("input/input.mp4")

# Create text image using PIL with rounded box and emoji support
def create_text_image(text, video_size, font_size=70):
    # Create a transparent image
    img = Image.new('RGBA', video_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to load fonts - prioritize color emoji fonts
    font = None
    emoji_font = None
    
    # Regular text font paths
    text_font_paths = [
        "C:/Windows/Fonts/arial.ttf",     # Arial
        "C:/Windows/Fonts/calibri.ttf",   # Calibri
        "C:/Windows/Fonts/segoeui.ttf",   # Segoe UI
    ]
    
    # Color emoji font paths
    emoji_font_paths = [
        "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
        "C:/Windows/Fonts/NotoColorEmoji.ttf",  # Noto Color Emoji (if installed)
    ]
    
    # Load regular font
    for font_path in text_font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue
    
    # Load emoji font
    for font_path in emoji_font_paths:
        try:
            emoji_font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue
    
    # Fallback to default if no font found
    if font is None:
        font = ImageFont.load_default()
    if emoji_font is None:
        emoji_font = font
    
    # Split text into text and emoji parts for better rendering
    import re
    
    # Get text dimensions using the main font
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Add padding for the rounded box
    padding = 25
    box_width = text_width + (padding * 2)
    box_height = text_height + (padding * 2)
    
    # Calculate position to center the box
    box_x = (video_size[0] - box_width) // 2
    box_y = (video_size[1] - box_height) // 2
    
    # Draw rounded rectangle background - WHITE container
    corner_radius = 20
    box_color = (255, 255, 255, 220)  # Semi-transparent white
    
    # Create rounded rectangle
    draw.rounded_rectangle(
        [box_x, box_y, box_x + box_width, box_y + box_height],
        radius=corner_radius,
        fill=box_color
    )
    
    # Calculate text position within the box
    text_x = box_x + padding
    text_y = box_y + padding
    
    # Draw text with slight outline for better readability - BLACK text
    outline_width = 1
    for adj in range(-outline_width, outline_width + 1):
        for adj2 in range(-outline_width, outline_width + 1):
            if adj != 0 or adj2 != 0:
                draw.text((text_x + adj, text_y + adj2), text, font=font, fill='white')
    
    # Draw main text in black
    draw.text((text_x, text_y), text, font=font, fill='black')
    
    return np.array(img)

# Create text overlay
text_array = create_text_image("watch till the end 😂", (video.w, video.h))
txt_clip = ImageClip(text_array, transparent=True, duration=video.duration)

# Overlay text on video
final_video = CompositeVideoClip([video, txt_clip])

# Write the result to export directory
final_video.write_videofile("export/output_with_caption.mp4", codec='libx264')

# Clean up
video.close()
final_video.close()

print("Video with caption exported successfully to export/output_with_caption.mp4")