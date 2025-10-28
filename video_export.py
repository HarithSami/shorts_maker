"""
Video export functionality for creating clips using direct FFmpeg (faster than MoviePy)
"""
import os
import subprocess
import cv2
from PyQt6.QtCore import QThread, pyqtSignal


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
        """Export clips using direct FFmpeg (much faster than MoviePy)"""
        
        # Get video info first
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.finished.emit(False, f"Could not open video: {self.video_path}")
                return
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            
        except Exception as e:
            self.finished.emit(False, f"Failed to read video info: {str(e)}")
            return
        
        # Process each clip using direct FFmpeg (like auto-crop-ai.py)
        for i, clip_info in enumerate(self.clips):
            start, end, name = clip_info
            self.progress.emit(i + 1, f"Exporting: {name} ({i+1}/{len(self.clips)})")
            
            output_path = os.path.join(self.output_folder, f"{name}.mp4")
            
            try:
                # Use FFmpeg directly for maximum speed (like auto-crop-ai.py)
                command = [
                    'ffmpeg', '-y',  # Overwrite output files
                    '-i', self.video_path,  # Input file
                    '-ss', str(start),  # Start time
                    '-t', str(end - start),  # Duration
                    '-c:v', 'libx264',  # Video codec
                    '-preset', 'fast',  # Fast encoding preset
                    '-crf', '23',  # Quality setting
                    '-c:a', 'aac',  # Audio codec
                    '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
                    output_path
                ]
                
                # Run FFmpeg command
                result = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
            except subprocess.CalledProcessError as e:
                error_msg = f"FFmpeg failed for {name}:\n{e.stderr}"
                self.finished.emit(False, error_msg)
                return
            except FileNotFoundError:
                error_msg = (
                    "FFmpeg not found! Please install FFmpeg:\n\n"
                    "Windows: Download from https://ffmpeg.org/download.html\n"
                    "Or use: winget install ffmpeg\n\n"
                    "This method is much faster than MoviePy!"
                )
                self.finished.emit(False, error_msg)
                return
            except Exception as e:
                self.finished.emit(False, f"Error processing {name}: {str(e)}")
                return
                
        self.finished.emit(True, f"✅ All {len(self.clips)} clips exported successfully!\n\nLocation: {self.output_folder}")


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