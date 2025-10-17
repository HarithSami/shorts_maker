"""
Video analysis functionality for scene detection and speech boundary detection
"""
import os
import wave
import shutil
from PyQt6.QtCore import QThread, pyqtSignal
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
import webrtcvad
from spleeter.separator import Separator


class AnalysisThread(QThread):
    """Thread for analyzing video scenes and speech"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        # Initialize Spleeter for vocal isolation
        self.separator = Separator('spleeter:2stems')  # Separates vocals and accompaniment
        
    def run(self):
        try:
            result = {
                'scenes': [],
                'speech_boundaries': [],
                'error': None
            }
            
            # Detect scenes
            self.progress.emit("Detecting scene changes...")
            result['scenes'] = self.detect_scenes()
            
            # Detect speech boundaries
            self.progress.emit("Analyzing speech patterns...")
            result['speech_boundaries'] = self.detect_speech_boundaries()
            
            self.finished.emit(result)
            
        except Exception as e:
            result = {'scenes': [], 'speech_boundaries': [], 'error': str(e)}
            self.finished.emit(result)
    
    def detect_scenes(self):
        """Detect scene changes using PySceneDetect"""
        try:
            video = open_video(self.video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(ContentDetector(threshold=27.0))
            
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()
            
            # Convert to timestamps in seconds
            scenes = []
            for scene in scene_list:
                start_time = scene[0].get_seconds()
                end_time = scene[1].get_seconds()
                scenes.append((start_time, end_time))
            
            return scenes
        except Exception as e:
            print(f"Scene detection error: {e}")
            return []
    
    def detect_speech_boundaries(self):
        """Detect speech boundaries using webrtcvad on isolated vocals"""
        try:
            # Extract audio from video
            video = VideoFileClip(self.video_path)
            
            if video.audio is None:
                video.close()
                return []
            
            # Write full audio to temporary file for Spleeter
            temp_full_audio = "temp_full_audio.wav"
            video.audio.write_audiofile(temp_full_audio, fps=44100, nbytes=2, 
                                       codec='pcm_s16le', logger=None)
            video.close()
            
            self.progress.emit("Isolating vocals from audio...")
            
            # Use Spleeter to isolate vocals
            output_dir = "temp_spleeter_output"
            self.separator.separate_to_file(temp_full_audio, output_dir)
            
            # The isolated vocals will be in output_dir/temp_full_audio/vocals.wav
            vocals_path = os.path.join(output_dir, "temp_full_audio", "vocals.wav")
            
            # Resample vocals to 16kHz for webrtcvad
            temp_vocals_16k = "temp_vocals_16k.wav"
            vocals_clip = AudioFileClip(vocals_path)
            vocals_clip.write_audiofile(temp_vocals_16k, fps=16000, nbytes=2,
                                       codec='pcm_s16le', logger=None)
            vocals_clip.close()
            
            self.progress.emit("Detecting speech patterns in vocals...")
            
            # Process isolated vocals with webrtcvad
            vad = webrtcvad.Vad(2)  # Aggressiveness: 0-3 (2 is balanced)
            
            with wave.open(temp_vocals_16k, 'rb') as wf:
                sample_rate = wf.getframerate()
                frame_duration = 30  # ms
                frame_size = int(sample_rate * frame_duration / 1000)
                
                frames = []
                while True:
                    frame = wf.readframes(frame_size)
                    if len(frame) < frame_size * 2:  # 2 bytes per sample
                        break
                    frames.append(frame)
                
                # Detect speech/silence in isolated vocals
                speech_boundaries = []
                in_speech = False
                speech_start = 0
                silence_duration = 0
                min_silence = 0.3  # Minimum silence to mark sentence boundary
                
                for i, frame in enumerate(frames):
                    timestamp = i * frame_duration / 1000.0
                    
                    try:
                        is_speech = vad.is_speech(frame, sample_rate)
                    except:
                        continue
                    
                    if is_speech:
                        if not in_speech:
                            # Speech started
                            speech_start = timestamp
                            in_speech = True
                        silence_duration = 0
                    else:
                        # Silence detected
                        if in_speech:
                            silence_duration += frame_duration / 1000.0
                            
                            # If silence long enough, mark as sentence boundary
                            if silence_duration >= min_silence:
                                speech_boundaries.append(timestamp)
                                in_speech = False
                                silence_duration = 0
            
            # Clean up temporary files
            for temp_file in [temp_full_audio, temp_vocals_16k]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            
            return speech_boundaries
            
        except Exception as e:
            print(f"Speech detection error: {e}")
            import traceback
            traceback.print_exc()
            return []


class SmartBoundaryFinder:
    """Helper class for finding smart boundaries for cuts"""
    
    @staticmethod
    def find_smart_boundary(time_point, scenes, speech_boundaries, 
                          enable_smart_cuts, priority, max_adjustment, boundary_type='start'):
        """Find the nearest smart boundary for a cut point"""
        if not enable_smart_cuts:
            return time_point
        
        if not scenes and not speech_boundaries:
            return time_point
        
        # Get candidate boundaries within range
        scene_boundaries = []
        for start, end in scenes:
            if boundary_type == 'start':
                scene_boundaries.append(start)
            else:
                scene_boundaries.append(end)
        
        speech_bounds = speech_boundaries
        
        # Filter to those within max_adjustment
        nearby_scenes = [s for s in scene_boundaries 
                        if abs(s - time_point) <= max_adjustment]
        nearby_speech = [s for s in speech_bounds 
                        if abs(s - time_point) <= max_adjustment]
        
        # Apply priority logic
        if priority == "Scene Changes First":
            if nearby_scenes:
                return min(nearby_scenes, key=lambda x: abs(x - time_point))
            elif nearby_speech:
                return min(nearby_speech, key=lambda x: abs(x - time_point))
                
        elif priority == "Speech Boundaries First":
            if nearby_speech:
                return min(nearby_speech, key=lambda x: abs(x - time_point))
            elif nearby_scenes:
                return min(nearby_scenes, key=lambda x: abs(x - time_point))
                
        elif priority == "Nearest Boundary (either)":
            all_boundaries = nearby_scenes + nearby_speech
            if all_boundaries:
                return min(all_boundaries, key=lambda x: abs(x - time_point))
                
        elif priority == "Scene Start + Speech End":
            if boundary_type == 'start' and nearby_scenes:
                return min(nearby_scenes, key=lambda x: abs(x - time_point))
            elif boundary_type == 'end' and nearby_speech:
                return min(nearby_speech, key=lambda x: abs(x - time_point))
            else:
                all_boundaries = nearby_scenes + nearby_speech
                if all_boundaries:
                    return min(all_boundaries, key=lambda x: abs(x - time_point))
        
        return time_point