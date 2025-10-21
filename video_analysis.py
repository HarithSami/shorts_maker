"""
Video analysis functionality for scene detection and speech boundary detection
"""
import os
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from moviepy.video.io.VideoFileClip import VideoFileClip
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
import librosa
from scipy import signal


class AnalysisThread(QThread):
    """Thread for analyzing video scenes and speech"""
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict)
    
    def __init__(self, video_path, analyze_scenes=True, analyze_audio=True):
        super().__init__()
        self.video_path = video_path
        self.analyze_scenes = analyze_scenes
        self.analyze_audio = analyze_audio
        
    def run(self):
        try:
            result = {
                'scenes': [],
                'speech_boundaries': [],
                'error': None
            }
            
            # Detect scenes if enabled
            if self.analyze_scenes:
                self.progress.emit("Detecting scene changes...")
                result['scenes'] = self.detect_scenes()
            
            # Detect speech boundaries if enabled
            if self.analyze_audio:
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
        """Detect speech boundaries using energy-based analysis with librosa"""
        try:
            # Extract audio from video
            video = VideoFileClip(self.video_path)
            
            if video.audio is None:
                video.close()
                return []
            
            # Write audio to temporary file
            temp_audio = "temp_audio.wav"
            video.audio.write_audiofile(temp_audio, fps=22050, nbytes=2, 
                                       codec='pcm_s16le', logger=None)
            video.close()
            
            self.progress.emit("Analyzing audio energy patterns...")
            
            # Load audio with librosa
            y, sr = librosa.load(temp_audio, sr=22050, mono=True)
            
            # Apply high-pass filter to reduce low-frequency noise
            sos = signal.butter(10, 300, 'hp', fs=sr, output='sos')
            y_filtered = signal.sosfilt(sos, y)
            
            # Calculate energy in frames
            frame_length = int(0.025 * sr)  # 25ms frames
            hop_length = int(0.010 * sr)    # 10ms hop
            
            # Calculate RMS energy
            rms = librosa.feature.rms(y=y_filtered, frame_length=frame_length, 
                                     hop_length=hop_length)[0]
            
            # Calculate spectral centroid (helps identify speech)
            spectral_centroid = librosa.feature.spectral_centroid(
                y=y_filtered, sr=sr, n_fft=frame_length, hop_length=hop_length)[0]
            
            # Normalize features
            rms_norm = (rms - np.mean(rms)) / (np.std(rms) + 1e-10)
            centroid_norm = (spectral_centroid - np.mean(spectral_centroid)) / (np.std(spectral_centroid) + 1e-10)
            
            # Combine features for better speech detection
            # Speech typically has moderate energy and spectral centroid
            combined_energy = 0.7 * rms_norm + 0.3 * centroid_norm
            
            # Adaptive thresholding
            threshold = np.percentile(combined_energy, 40)  # Lower 40% is likely silence
            
            # Detect speech/silence transitions
            is_speech = combined_energy > threshold
            
            # Find boundaries where speech ends (silence begins)
            speech_boundaries = []
            in_speech = False
            silence_frames = 0
            min_silence_frames = int(0.3 * sr / hop_length)  # 300ms of silence
            min_speech_frames = int(0.25 * sr / hop_length)  # 250ms minimum speech
            speech_start_frame = 0
            
            for i, speech_frame in enumerate(is_speech):
                time = librosa.frames_to_time(i, sr=sr, hop_length=hop_length)
                
                if speech_frame:
                    if not in_speech:
                        # Speech started
                        speech_start_frame = i
                        in_speech = True
                    silence_frames = 0
                else:
                    # Silence detected
                    if in_speech:
                        silence_frames += 1
                        
                        # If silence long enough and speech was long enough
                        if silence_frames >= min_silence_frames:
                            speech_duration = i - speech_start_frame
                            if speech_duration >= min_speech_frames:
                                # Mark this as a speech boundary
                                boundary_time = librosa.frames_to_time(
                                    i - silence_frames // 2, sr=sr, hop_length=hop_length)
                                speech_boundaries.append(boundary_time)
                            
                            in_speech = False
                            silence_frames = 0
            
            # Clean up temporary file
            if os.path.exists(temp_audio):
                os.remove(temp_audio)
            
            # Remove boundaries that are too close together (< 1 second)
            filtered_boundaries = []
            last_boundary = -999
            for boundary in speech_boundaries:
                if boundary - last_boundary > 1.0:
                    filtered_boundaries.append(boundary)
                    last_boundary = boundary
            
            return filtered_boundaries
            
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