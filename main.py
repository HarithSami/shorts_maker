"""
Main application logic for the Smart YouTube Shorts Clip Generator
"""
import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from moviepy.video.io.VideoFileClip import VideoFileClip

from ui import MainWindow
from video_analysis import AnalysisThread, SmartBoundaryFinder
from video_export import ExportThread, ClipGenerator
from utils import format_time, is_valid_video_file, get_video_info, validate_clip_parameters


class VideoClipExtractor(MainWindow):
    """Main application class that combines UI with business logic"""
    
    def __init__(self):
        # Application state
        self.video_path = None
        self.video_duration = 0
        self.clips = []
        self.export_thread = None
        self.analysis_thread = None
        
        # Smart cutting data
        self.scenes = []
        self.speech_boundaries = []
        
        # Initialize parent (this creates all UI elements)
        super().__init__()
        
        # Connect UI signals to handlers (after UI is created)
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect UI signals to their respective handlers"""
        self.drop_zone.file_dropped.connect(self.load_video_file)
        self.generate_btn.clicked.connect(self.generate_clips)
        self.clear_btn.clicked.connect(self.clear_all_clips)
        self.export_btn.clicked.connect(self.export_clips)
        self.analyze_btn.clicked.connect(self.analyze_video)
        self.add_manual_clip_btn.clicked.connect(self.add_manual_clip)
        
        # Connect generation method change to enable/disable smart options
        self.generation_method.currentTextChanged.connect(self.on_method_changed)
    

    
    def load_video_file(self, file_path):
        """Load a video file and update UI"""
        if not is_valid_video_file(file_path):
            QMessageBox.warning(self, "Invalid File", "Please select a valid video file!")
            return
            
        self.video_path = file_path
        
        # Reset analysis data
        self.scenes = []
        self.speech_boundaries = []
        
        try:
            self.video_duration = get_video_info(file_path)
            
            # Update video info display
            filename = os.path.basename(file_path)
            duration_str = format_time(self.video_duration)
            self.video_info_label.setText(f"📹 {filename} • {duration_str}")
            
            # Enable buttons
            self.analyze_btn.setEnabled(True)
            self.generate_btn.setEnabled(True)
            
            # Enable manual clip controls
            self.manual_start_input.setEnabled(True)
            self.add_manual_clip_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load video: {str(e)}")
    
    def get_current_mode(self):
        """Get the current mode based on generation method selection"""
        method = self.generation_method.currentText()
        if "Smart" in method:
            return "Smart"
        else:
            return "Random"
    
    def on_method_changed(self, method):
        """Handle generation method change - enable/disable smart options"""
        is_smart_method = "Smart" in method
        
        # If switched to smart method and no analysis done yet
        if is_smart_method and self.video_path and not self.scenes and not self.speech_boundaries:
            reply = QMessageBox.question(
                self, "Analysis Required",
                "Smart detection methods require video analysis.\n\nAnalyze video now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.analyze_video()
            else:
                # Switch back to Random method
                self.generation_method.setCurrentText("Random")
    
    def analyze_video(self):
        """Start video analysis for scenes and speech"""
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        # Check if at least one analysis type is selected
        if not self.scene_detection_checkbox.isChecked() and not self.audio_detection_checkbox.isChecked():
            QMessageBox.warning(self, "No Analysis Selected", "Please select at least one analysis type (Scene or Audio Detection)!")
            return
        
        self.progress_label.setText("⏳ Analyzing video... This may take a minute.")
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)  # Indeterminate
        
        # Pass analysis options to the thread
        analyze_scenes = self.scene_detection_checkbox.isChecked()
        analyze_audio = self.audio_detection_checkbox.isChecked()
        
        self.analysis_thread = AnalysisThread(self.video_path, analyze_scenes, analyze_audio)
        self.analysis_thread.progress.connect(self.update_analysis_progress)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.start()
    
    def update_analysis_progress(self, message):
        """Update analysis progress display"""
        self.progress_label.setText(f"⏳ {message}")
    
    def analysis_finished(self, result):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)
        
        if result['error']:
            self.progress_label.setText(f"❌ Analysis failed: {result['error']}")
            QMessageBox.warning(self, "Analysis Error", f"Could not analyze video:\n{result['error']}")
            return
        
        self.scenes = result['scenes']
        self.speech_boundaries = result['speech_boundaries']
        
        info = f"✓ Analysis complete: {len(self.scenes)} scenes, {len(self.speech_boundaries)} speech boundaries detected"
        self.progress_label.setText(info)
        self.progress_label.setStyleSheet("color: #28a745; font-weight: bold;")
    
    def find_smart_boundary(self, time_point, boundary_type='start'):
        """Find the nearest smart boundary for a cut point"""
        mode = self.get_current_mode()
        method = self.generation_method.currentText()
        
        # Only apply smart boundaries if using smart method
        if mode != "Smart":
            return time_point
        
        # Determine priority based on enabled analysis types
        if self.scene_detection_checkbox.isChecked() and self.audio_detection_checkbox.isChecked():
            priority = "Scenes"  # Default to scenes if both are enabled
        elif self.scene_detection_checkbox.isChecked():
            priority = "Scenes"
        elif self.audio_detection_checkbox.isChecked():
            priority = "Speech"
        else:
            priority = "Scenes"  # Fallback
        
        return SmartBoundaryFinder.find_smart_boundary(
            time_point, self.scenes, self.speech_boundaries,
            True,  # Enable smart cuts
            priority,
            self.max_adjustment_spin.value(),
            boundary_type
        )
    
    def generate_clips(self):
        """Generate clips based on user parameters and selected mode"""
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        mode = self.get_current_mode()
        num_clips = self.num_clips_spin.value()
        clip_duration = self.clip_duration_spin.value()
        base_name = "short"  # Fixed base name for simplified UI
        allow_overlap = self.allow_overlap_checkbox.isChecked()
        
        if clip_duration >= self.video_duration:
            QMessageBox.warning(self, "Invalid Duration", 
                              f"Clip duration must be less than video duration ({self.video_duration}s)")
            return
        
        # Check if Smart mode is active but no analysis done
        if mode == "Smart" and not self.scenes and not self.speech_boundaries:
            QMessageBox.warning(self, "Analysis Required", 
                              "Smart Cutting mode requires video analysis.\nPlease analyze the video first.")
            return
        
        # Generate random clips
        if allow_overlap:
            generated_clips = ClipGenerator.generate_overlapping_clips(
                self.video_duration, num_clips, clip_duration)
        else:
            generated_clips = ClipGenerator.generate_non_overlapping_clips(
                self.video_duration, num_clips, clip_duration)
        
        if len(generated_clips) < num_clips and not allow_overlap:
            QMessageBox.warning(self, "Limited Clips", 
                              f"Could only generate {len(generated_clips)} non-overlapping clips. "
                              f"Try shorter duration, fewer clips, or enable 'Allow Overlapping Clips'.")
        
        # Apply smart boundaries if in Smart mode and analysis data is available
        if mode == "Smart" and (self.scenes or self.speech_boundaries):
            adjusted_clips = []
            for start, end, _ in generated_clips:
                smart_start = self.find_smart_boundary(start, 'start')
                smart_end = self.find_smart_boundary(end, 'end')
                
                # Ensure valid clip
                if smart_end > smart_start:
                    adjusted_clips.append((smart_start, smart_end, ""))
            
            generated_clips = adjusted_clips
        
        # Clear existing clips and add generated ones
        self.clips.clear()
        self.clips_list.clear()
        
        for i, (start, end, _) in enumerate(generated_clips, 1):
            name = f"{base_name}_{i:04d}"
            self.clips.append((start, end, name))
            duration = end - start
            self.clips_list.addItem(
                f"{name} ({format_time(start)} - {format_time(end)}, {duration:.1f}s)"
            )
        
        self.update_clips_count()
        
        mode_msg = f" using {mode} mode" if mode == "Smart" else ""
        self.progress_label.setText(f"✅ Generated {len(generated_clips)} clips{mode_msg}!")
        
        # Enable export button if clips were generated
        if self.clips:
            self.export_btn.setEnabled(True)
    
    def add_manual_clip(self):
        """Add a manual clip based on user input"""
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        # Get start time from input
        time_text = self.manual_start_input.text().strip()
        if not time_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter a start time in MM:SS format!")
            return
        
        try:
            # Parse MM:SS format
            if ":" in time_text:
                parts = time_text.split(":")
                if len(parts) != 2:
                    raise ValueError("Invalid format")
                minutes, seconds = int(parts[0]), int(parts[1])
                start_time = minutes * 60 + seconds
            else:
                # Try to parse as seconds only
                start_time = float(time_text)
        except (ValueError, IndexError):
            QMessageBox.warning(self, "Invalid Input", "Please enter time in MM:SS format (e.g., 01:30)!")
            return
        
        # Get clip duration from settings
        clip_duration = self.clip_duration_spin.value()
        end_time = start_time + clip_duration
        
        # Validate clip bounds
        if start_time < 0:
            QMessageBox.warning(self, "Invalid Time", "Start time cannot be negative!")
            return
        
        if start_time >= self.video_duration:
            QMessageBox.warning(self, "Invalid Time", 
                              f"Start time cannot be at or beyond video duration ({format_time(self.video_duration)})!")
            return
        
        # Auto-adjust end time if it extends beyond video duration
        if end_time > self.video_duration:
            end_time = self.video_duration
        
        # Apply smart boundaries if in Smart mode
        mode = self.get_current_mode()
        if mode == "Smart" and (self.scenes or self.speech_boundaries):
            smart_start = self.find_smart_boundary(start_time, 'start')
            smart_end = self.find_smart_boundary(end_time, 'end')
            
            # Ensure valid clip after smart adjustment
            if smart_end > smart_start and smart_end <= self.video_duration:
                start_time, end_time = smart_start, smart_end
        
        # Generate clip name
        clip_count = len(self.clips) + 1
        clip_name = f"manual_{clip_count:04d}"
        
        # Add clip to list
        self.clips.append((start_time, end_time, clip_name))
        duration = end_time - start_time
        self.clips_list.addItem(
            f"{clip_name} ({format_time(start_time)} - {format_time(end_time)}, {duration:.1f}s)"
        )
        
        self.update_clips_count()
        
        # Enable export button
        self.export_btn.setEnabled(True)
        
        # Clear input and show success
        self.manual_start_input.clear()
        self.manual_start_input.setText("00:00")
        self.progress_label.setText(f"✅ Added manual clip: {clip_name}")
    
    def clear_all_clips(self):
        """Clear all clips from the list"""
        self.clips.clear()
        self.clips_list.clear()
        self.update_clips_count()
    
    def update_clips_count(self):
        """Update the clips count label"""
        count = len(self.clips)
        self.clips_count_label.setText(f"({count} clip{'s' if count != 1 else ''})")
    
    def export_clips(self):
        """Export all clips to video files"""
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
        """Update export progress display"""
        self.progress_bar.setValue(count)
        self.progress_label.setText(message)
    
    def export_finished(self, success, message):
        """Handle export completion"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    window = VideoClipExtractor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()