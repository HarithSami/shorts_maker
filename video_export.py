"""
Video export functionality for creating clips
"""
import os
from PyQt6.QtCore import QThread, pyqtSignal
from moviepy.video.io.VideoFileClip import VideoFileClip


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
        try:
            for i, clip_info in enumerate(self.clips):
                start, end, name = clip_info
                self.progress.emit(i + 1, f"Exporting: {name}")
                
                output_path = os.path.join(self.output_folder, f"{name}.mp4")
                
                # Use moviepy for extraction
                video = VideoFileClip(self.video_path)
                clip = video.subclip(start, end)
                clip.write_videofile(output_path, codec='libx264', audio_codec='aac', 
                                    temp_audiofile='temp-audio.m4a', 
                                    remove_temp=True, logger=None)
                clip.close()
                video.close()
                
            self.finished.emit(True, "All clips exported successfully!")
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")


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
            start = random.randint(0, max_start)
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
                
            start = random.randint(0, max_start)
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