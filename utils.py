"""
Utility functions for the video clip extractor
"""


def format_time(seconds):
    """Format seconds into MM:SS format"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def is_valid_video_file(file_path):
    """Check if the file is a valid video file"""
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
    return file_path.lower().endswith(valid_extensions)


def get_video_info(file_path):
    """Get basic video information"""
    from moviepy.video.io.VideoFileClip import VideoFileClip
    
    try:
        video = VideoFileClip(file_path)
        duration = int(video.duration)
        video.close()
        return duration
    except Exception as e:
        raise Exception(f"Failed to load video: {str(e)}")


def validate_clip_parameters(start, end, video_duration):
    """Validate clip parameters"""
    if start >= end:
        return False, "Start time must be less than end time!"
    
    if start < 0 or end > video_duration:
        return False, f"Times must be between 0 and {video_duration} seconds!"
    
    return True, ""