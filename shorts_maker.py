import sys
import os
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QListWidget, QFileDialog, QSpinBox, QLineEdit,
                             QMessageBox, QProgressBar, QGroupBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from moviepy import VideoFileClip

class ExportThread(QThread):
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

class VideoClipExtractor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.video_duration = 0
        self.clips = []
        self.export_thread = None
        
        self.setWindowTitle("YouTube Shorts Random Clip Generator")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Load video area with drag & drop
        load_layout = QVBoxLayout()
        load_btn = QPushButton("Load Video (or drag & drop video file here)")
        load_btn.clicked.connect(self.load_video)
        load_btn.setStyleSheet("padding: 20px; font-size: 14px;")
        load_layout.addWidget(load_btn)
        main_layout.addLayout(load_layout)
        
        # Video info
        self.info_label = QLabel("No video loaded - Drag & drop a video file or click Load Video")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        main_layout.addWidget(self.info_label)
        
        # Random clips generation section
        random_group = QGroupBox("Random Clips Generator")
        random_layout = QVBoxLayout()
        
        params_layout = QHBoxLayout()
        
        # Number of clips
        num_layout = QVBoxLayout()
        num_layout.addWidget(QLabel("Number of Clips:"))
        self.num_clips_spin = QSpinBox()
        self.num_clips_spin.setMinimum(1)
        self.num_clips_spin.setMaximum(10000)  # Increased from 100
        self.num_clips_spin.setValue(5)
        num_layout.addWidget(self.num_clips_spin)
        params_layout.addLayout(num_layout)
        
        # Clip duration
        duration_layout = QVBoxLayout()
        duration_layout.addWidget(QLabel("Clip Duration (seconds):"))
        self.clip_duration_spin = QSpinBox()
        self.clip_duration_spin.setMinimum(5)
        self.clip_duration_spin.setMaximum(300)
        self.clip_duration_spin.setValue(30)
        duration_layout.addWidget(self.clip_duration_spin)
        params_layout.addLayout(duration_layout)
        
        # Base name
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Base Name:"))
        self.base_name_input = QLineEdit()
        self.base_name_input.setText("short")
        self.base_name_input.setPlaceholderText("short")
        name_layout.addWidget(self.base_name_input)
        params_layout.addLayout(name_layout)
        
        random_layout.addLayout(params_layout)
        
        # Allow overlapping checkbox
        self.allow_overlap_checkbox = QCheckBox("Allow Overlapping Clips")
        self.allow_overlap_checkbox.setChecked(False)
        self.allow_overlap_checkbox.setStyleSheet("font-weight: bold; padding: 5px;")
        random_layout.addWidget(self.allow_overlap_checkbox)
        
        # Generate button
        generate_btn = QPushButton("Generate Random Clips")
        generate_btn.clicked.connect(self.generate_random_clips)
        generate_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px;")
        random_layout.addWidget(generate_btn)
        
        random_group.setLayout(random_layout)
        main_layout.addWidget(random_group)
        
        # Manual clip section
        manual_group = QGroupBox("Manual Clip Selection (Optional)")
        manual_layout = QVBoxLayout()
        
        clip_layout = QHBoxLayout()
        
        # Start time
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start (seconds):"))
        self.start_spin = QSpinBox()
        self.start_spin.setMaximum(999999)
        start_layout.addWidget(self.start_spin)
        clip_layout.addLayout(start_layout)
        
        # End time
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End (seconds):"))
        self.end_spin = QSpinBox()
        self.end_spin.setMaximum(999999)
        end_layout.addWidget(self.end_spin)
        clip_layout.addLayout(end_layout)
        
        # Clip name
        name_layout = QVBoxLayout()
        name_layout.addWidget(QLabel("Clip Name:"))
        self.clip_name = QLineEdit()
        self.clip_name.setPlaceholderText("manual_clip_1")
        name_layout.addWidget(self.clip_name)
        clip_layout.addLayout(name_layout)
        
        manual_layout.addLayout(clip_layout)
        
        # Add clip button
        add_clip_btn = QPushButton("Add Manual Clip")
        add_clip_btn.clicked.connect(self.add_clip)
        manual_layout.addWidget(add_clip_btn)
        
        manual_group.setLayout(manual_layout)
        main_layout.addWidget(manual_group)
        
        # Clips list
        clips_header_layout = QHBoxLayout()
        clips_header_layout.addWidget(QLabel("Clips to Export:"))
        self.clips_count_label = QLabel("(0 clips)")
        self.clips_count_label.setStyleSheet("color: #666; font-style: italic;")
        clips_header_layout.addWidget(self.clips_count_label)
        clips_header_layout.addStretch()
        main_layout.addLayout(clips_header_layout)
        
        self.clips_list = QListWidget()
        main_layout.addWidget(self.clips_list)
        
        # List controls
        list_controls = QHBoxLayout()
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_clip)
        list_controls.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_clips)
        list_controls.addWidget(clear_btn)
        
        main_layout.addLayout(list_controls)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        main_layout.addWidget(self.progress_label)
        
        # Export button
        export_btn = QPushButton("Export All Clips")
        export_btn.clicked.connect(self.export_clips)
        export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 12px; font-size: 14px;")
        main_layout.addWidget(export_btn)
    
    def update_clips_count(self):
        """Update the clips count label"""
        count = len(self.clips)
        self.clips_count_label.setText(f"({count} clip{'s' if count != 1 else ''})")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            video_file = files[0]
            # Check if it's a video file
            valid_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm')
            if video_file.lower().endswith(valid_extensions):
                self.load_video_file(video_file)
            else:
                QMessageBox.warning(self, "Invalid File", "Please drop a valid video file!")
        
    def load_video(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", 
            "Video Files (*.mp4 *.avi *.mov *.mkv *.flv);;All Files (*)"
        )
        
        if file_path:
            self.load_video_file(file_path)
    
    def load_video_file(self, file_path):
        self.video_path = file_path
        
        # Get video duration using moviepy
        try:
            video = VideoFileClip(file_path)
            self.video_duration = int(video.duration)
            video.close()
            
            self.start_spin.setMaximum(self.video_duration)
            self.end_spin.setMaximum(self.video_duration)
            self.end_spin.setValue(min(60, self.video_duration))
            
            self.info_label.setText(f"✓ Video loaded: {os.path.basename(file_path)} - Duration: {self.format_time(self.video_duration)}")
            self.info_label.setStyleSheet("padding: 10px; background-color: #d4edda; border-radius: 5px; color: #155724;")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")
    
    def generate_random_clips(self):
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        num_clips = self.num_clips_spin.value()
        clip_duration = self.clip_duration_spin.value()
        base_name = self.base_name_input.text().strip() or "short"
        allow_overlap = self.allow_overlap_checkbox.isChecked()
        
        if clip_duration >= self.video_duration:
            QMessageBox.warning(self, "Invalid Duration", 
                              f"Clip duration must be less than video duration ({self.video_duration}s)")
            return
        
        # Generate random clips
        if allow_overlap:
            generated_clips = self.generate_overlapping_clips(num_clips, clip_duration)
        else:
            generated_clips = self.generate_non_overlapping_clips(num_clips, clip_duration)
        
        if len(generated_clips) < num_clips and not allow_overlap:
            QMessageBox.warning(self, "Limited Clips", 
                              f"Could only generate {len(generated_clips)} non-overlapping clips. "
                              f"Try shorter duration, fewer clips, or enable 'Allow Overlapping Clips'.")
        
        # Clear existing clips
        self.clips.clear()
        self.clips_list.clear()
        
        # Add generated clips
        for i, (start, end, _) in enumerate(generated_clips, 1):
            name = f"{base_name}_{i:04d}"  # Changed to 4-digit padding for more clips
            self.clips.append((start, end, name))
            self.clips_list.addItem(
                f"{name} ({self.format_time(start)} - {self.format_time(end)}, {end-start}s)"
            )
        
        self.update_clips_count()
        QMessageBox.information(self, "Success", 
                               f"Generated {len(generated_clips)} random clips!")
    
    def generate_overlapping_clips(self, num_clips, duration):
        """Generate random clips that can overlap"""
        clips = []
        max_start = self.video_duration - duration
        
        if max_start <= 0:
            return clips
        
        for i in range(num_clips):
            start = random.randint(0, max_start)
            end = start + duration
            clips.append((start, end, ""))
        
        # Sort by start time
        clips.sort(key=lambda x: x[0])
        
        return clips
    
    def generate_non_overlapping_clips(self, num_clips, duration):
        """Generate random non-overlapping clips"""
        clips = []
        max_attempts = num_clips * 20  # Increased attempts
        attempts = 0
        
        while len(clips) < num_clips and attempts < max_attempts:
            attempts += 1
            
            # Random start position
            max_start = self.video_duration - duration
            if max_start <= 0:
                break
                
            start = random.randint(0, max_start)
            end = start + duration
            
            # Check if overlaps with existing clips
            overlaps = False
            for existing_start, existing_end, _ in clips:
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break
            
            if not overlaps:
                clips.append((start, end, ""))
        
        # Sort by start time
        clips.sort(key=lambda x: x[0])
        
        return clips
    
    def set_start_time(self):
        current_time = self.player.position() // 1000
        self.start_spin.setValue(current_time)
    
    def set_end_time(self):
        current_time = self.player.position() // 1000
        self.end_spin.setValue(current_time)
    
    def add_clip(self):
        start = self.start_spin.value()
        end = self.end_spin.value()
        name = self.clip_name.text().strip()
        
        if not name:
            name = f"manual_clip_{len(self.clips) + 1}"
        
        if start >= end:
            QMessageBox.warning(self, "Invalid Range", "Start time must be less than end time!")
            return
        
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        self.clips.append((start, end, name))
        duration = end - start
        self.clips_list.addItem(f"{name} ({self.format_time(start)} - {self.format_time(end)}, {duration}s)")
        
        self.clip_name.setText("")
        self.update_clips_count()
    
    def remove_clip(self):
        current_row = self.clips_list.currentRow()
        if current_row >= 0:
            self.clips_list.takeItem(current_row)
            del self.clips[current_row]
            self.update_clips_count()
    
    def clear_all_clips(self):
        self.clips.clear()
        self.clips_list.clear()
        self.update_clips_count()
    
    def export_clips(self):
        if not self.clips:
            QMessageBox.warning(self, "No Clips", "Please generate or add at least one clip to export!")
            return
        
        output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_folder:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.clips))
        self.progress_bar.setValue(0)
        
        self.export_thread = ExportThread(self.video_path, self.clips, output_folder)
        self.export_thread.progress.connect(self.update_export_progress)
        self.export_thread.finished.connect(self.export_finished)
        self.export_thread.start()
    
    def update_export_progress(self, count, message):
        self.progress_bar.setValue(count)
        self.progress_label.setText(message)
    
    def export_finished(self, success, message):
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
    
    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoClipExtractor()
    window.show()
    sys.exit(app.exec())