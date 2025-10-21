"""
Video export functionality for creating clips
"""
import os
from PyQt6.QtCore import QThread, pyqtSignal

# Try importing from different locations based on moviepy version
try:
    from moviepy import VideoFileClip  # MoviePy v2.0+
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import VideoFileClip  # MoviePy v1.x
        MOVIEPY_V2 = False
    except ImportError:
        from moviepy.video.io.VideoFileClip import VideoFileClip  # Fallback
        MOVIEPY_V2 = False


class ExportThread(QThread):
    """Thread for exporting video clips"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, video_path, clips, output_folder):
        super().__init__()
        self.video_path = video_path
        self.clips = clips
        self.output_folder = output_folder
        
    def run(self):
        video = None
        try:
            # Load video once outside the loop for efficiency
            video = VideoFileClip(self.video_path)
            
            for i, clip_info in enumerate(self.clips):
                start, end, name = clip_info
                self.progress.emit(i + 1, f"Exporting: {name} ({i+1}/{len(self.clips)})")
                
                output_path = os.path.join(self.output_folder, f"{name}.mp4")
                
                # Create subclip - use different method name based on version
                try:
                    if MOVIEPY_V2 or hasattr(video, 'subclipped'):
                        # MoviePy v2.0+ uses subclipped()
                        clip = video.subclipped(start, end)
                    else:
                        # MoviePy v1.x uses subclip()
                        clip = video.subclip(start, end)
                    
                    # Write video file with error suppression
                    clip.write_videofile(
                        output_path, 
                        codec='libx264', 
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        logger=None,
                        preset='medium',
                        threads=4
                    )
                    
                    # Close the clip to free resources
                    clip.close()
                    
                except AttributeError as e:
                    # Provide helpful error message
                    error_msg = (
                        f"MoviePy compatibility issue detected.\n\n"
                        f"Your MoviePy version may be incompatible.\n"
                        f"Please try one of the following:\n\n"
                        f"1. Update to latest: pip install --upgrade moviepy\n"
                        f"2. Or install v1.0.3: pip uninstall moviepy && pip install moviepy==1.0.3\n\n"
                        f"Error: {str(e)}"
                    )
                    self.finished.emit(False, error_msg)
                    return
                except Exception as e:
                    self.finished.emit(False, f"Error exporting {name}: {str(e)}")
                    return
                
            self.finished.emit(True, f"✅ All {len(self.clips)} clips exported successfully!\n\nLocation: {self.output_folder}")
            
        except Exception as e:
            self.finished.emit(False, f"Error loading video: {str(e)}")
        finally:
            # Always close the video file
            if video is not None:
                try:
                    video.close()
                except:
                    pass


class ClipGenerator:
    """Helper class for generating random clips"""
    
    @staticmethod
    def generate_overlapping_clips(video_duration, num_clips, duration):
        """Generate random clips that can overlap"""
        import random
        
        clips = []
        max_start = video_duration - duration
        
        if max_start <= 0:
            return clips
        
        for i in range(num_clips):
            start = random.uniform(0, max_start)
            end = start + duration
            clips.append((start, end, ""))
        
        clips.sort(key=lambda x: x[0])
        return clips
    
    @staticmethod
    def generate_non_overlapping_clips(video_duration, num_clips, duration):
        """Generate random non-overlapping clips"""
        import random
        
        clips = []
        max_attempts = num_clips * 20
        attempts = 0
        
        while len(clips) < num_clips and attempts < max_attempts:
            attempts += 1
            
            max_start = video_duration - duration
            if max_start <= 0:
                break
                
            start = random.uniform(0, max_start)
            end = start + duration
            
            overlaps = False
            for existing_start, existing_end, _ in clips:
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break
            
            if not overlaps:
                clips.append((start, end, ""))
        
        clips.sort(key=lambda x: x[0])
        return clips