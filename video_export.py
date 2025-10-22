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
        """Export clips with proper resource management to avoid subprocess issues"""
        import gc
        
        for i, clip_info in enumerate(self.clips):
            start, end, name = clip_info
            self.progress.emit(i + 1, f"Exporting: {name} ({i+1}/{len(self.clips)})")
            
            output_path = os.path.join(self.output_folder, f"{name}.mp4")
            
            # Load video fresh for each clip to avoid resource conflicts
            video = None
            clip = None
            
            try:
                # Load video for this specific clip
                video = VideoFileClip(self.video_path)
                
                # Create subclip - use different method name based on version
                if MOVIEPY_V2 or hasattr(video, 'subclipped'):
                    # MoviePy v2.0+ uses subclipped()
                    clip = video.subclipped(start, end)
                else:
                    # MoviePy v1.x uses subclip()
                    clip = video.subclip(start, end)
                
                # Write video file with multiple fallback strategies
                success = False
                
                # Strategy 1: Try with all parameters
                if not success:
                    try:
                        clip.write_videofile(
                            output_path, 
                            codec='libx264', 
                            audio_codec='aac',
                            temp_audiofile=f'temp-audio-{i}.m4a',
                            remove_temp=True,
                            logger=None,
                            preset='medium',
                            threads=2,  # Reduced threads to avoid conflicts
                            verbose=False
                        )
                        success = True
                    except (AttributeError, TypeError, OSError):
                        pass
                
                # Strategy 2: Try without logger parameter
                if not success:
                    try:
                        clip.write_videofile(
                            output_path, 
                            codec='libx264', 
                            audio_codec='aac',
                            temp_audiofile=f'temp-audio-{i}.m4a',
                            remove_temp=True,
                            preset='medium',
                            threads=2,
                            verbose=False
                        )
                        success = True
                    except (AttributeError, TypeError, OSError):
                        pass
                
                # Strategy 3: Minimal parameters
                if not success:
                    try:
                        clip.write_videofile(
                            output_path, 
                            codec='libx264',
                            verbose=False
                        )
                        success = True
                    except Exception as e:
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
                
                if not success:
                    self.finished.emit(False, f"Failed to export {name} after trying all methods")
                    return
                    
            except Exception as e:
                self.finished.emit(False, f"Error processing {name}: {str(e)}")
                return
            finally:
                # Ensure proper cleanup for each clip
                if clip is not None:
                    try:
                        clip.close()
                        del clip
                    except:
                        pass
                
                if video is not None:
                    try:
                        video.close()
                        del video
                    except:
                        pass
                
                # Force garbage collection to free resources
                gc.collect()
                
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