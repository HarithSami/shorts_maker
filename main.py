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
        super().__init__()
        
        # Application state
        self.video_path = None
        self.video_duration = 0
        self.clips = []
        self.export_thread = None
        self.analysis_thread = None
        
        # Smart cutting data
        self.scenes = []
        self.speech_boundaries = []
        
        # Connect UI signals to handlers
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect UI signals to their respective handlers"""
        self.load_btn.clicked.connect(self.load_video)
        self.generate_btn.clicked.connect(self.generate_clips)
        self.add_clip_btn.clicked.connect(self.add_clip)
        self.remove_btn.clicked.connect(self.remove_clip)
        self.clear_btn.clicked.connect(self.clear_all_clips)
        self.export_btn.clicked.connect(self.export_clips)
        
        # Connect mode change to trigger analysis if needed
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
    
    def dragEnterEvent(self, event):
        """Handle drag enter events for file dropping"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Handle file drop events"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            video_file = files[0]
            if is_valid_video_file(video_file):
                self.load_video_file(video_file)
            else:
                QMessageBox.warning(self, "Invalid File", "Please drop a valid video file!")
    
    def load_video(self):
        """Load video file through file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Video File", "", 
            "Video Files (*.mp4 *.avi *.mov *.mkv *.flv);;All Files (*)"
        )
        
        if file_path:
            self.load_video_file(file_path)
    
    def load_video_file(self, file_path):
        """Load a video file and update UI"""
        self.video_path = file_path
        
        # Reset analysis data
        self.scenes = []
        self.speech_boundaries = []
        self.analysis_label.setText("")
        
        try:
            self.video_duration = get_video_info(file_path)
            
            self.start_spin.setMaximum(self.video_duration)
            self.end_spin.setMaximum(self.video_duration)
            self.end_spin.setValue(min(60, self.video_duration))
            
            self.info_label.setText(f"✓ Video loaded: {os.path.basename(file_path)} - Duration: {format_time(self.video_duration)}")
            self.info_label.setStyleSheet("padding: 10px; background-color: #d4edda; border-radius: 5px; color: #155724;")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
    
    def on_mode_changed(self, mode):
        """Handle mode change - trigger analysis if needed"""
        if not self.video_path:
            return
            
        # Check if we need analysis data but don't have it
        needs_scenes = "Scene" in mode and not self.scenes
        needs_speech = "Audio" in mode and not self.speech_boundaries
        
        if needs_scenes or needs_speech:
            reply = QMessageBox.question(
                self, "Analysis Required",
                f"{mode} mode requires video analysis.\n\nAnalyze video now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.analyze_video()
            else:
                # Reset to Random mode
                self.mode_combo.setCurrentIndex(0)
    
    def analyze_video(self):
        """Start video analysis for scenes and speech"""
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        self.analysis_label.setText("⏳ Analyzing video... This may take a minute.")
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)  # Indeterminate
        
        self.analysis_thread = AnalysisThread(self.video_path)
        self.analysis_thread.progress.connect(self.update_analysis_progress)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.start()
    
    def update_analysis_progress(self, message):
        """Update analysis progress display"""
        self.analysis_label.setText(f"⏳ {message}")
    
    def analysis_finished(self, result):
        """Handle analysis completion"""
        self.progress_bar.setVisible(False)
        
        if result['error']:
            self.analysis_label.setText(f"❌ Analysis failed: {result['error']}")
            QMessageBox.warning(self, "Analysis Error", f"Could not analyze video:\n{result['error']}")
            return
        
        self.scenes = result['scenes']
        self.speech_boundaries = result['speech_boundaries']
        
        info = f"✓ Analysis complete: {len(self.scenes)} scenes, {len(self.speech_boundaries)} speech boundaries detected"
        self.analysis_label.setText(info)
        self.analysis_label.setStyleSheet("padding: 5px; color: #155724; font-weight: bold;")
    
    def find_smart_boundary(self, time_point, boundary_type='start'):
        """Find the nearest smart boundary for a cut point"""
        mode = self.mode_combo.currentText()
        
        # Determine priority based on mode
        if "Scene" in mode:
            priority = "Scene Changes First"
        elif "Audio" in mode:
            priority = "Speech Boundaries First"
        else:
            return time_point  # No adjustment for Random mode
        
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
        
        mode = self.mode_combo.currentText()
        num_clips = self.num_clips_spin.value()
        clip_duration = self.clip_duration_spin.value()
        base_name = self.base_name_input.text().strip() or "short"
        allow_overlap = self.allow_overlap_checkbox.isChecked()
        
        if clip_duration >= self.video_duration:
            QMessageBox.warning(self, "Invalid Duration", 
                              f"Clip duration must be less than video duration ({self.video_duration}s)")
            return
        
        # Check if analysis is needed but not done
        if "Scene" in mode and not self.scenes:
            QMessageBox.warning(self, "Analysis Required", 
                              "Scene detection mode requires video analysis.\nPlease analyze the video first.")
            return
        
        if "Audio" in mode and not self.speech_boundaries:
            QMessageBox.warning(self, "Analysis Required", 
                              "Audio detection mode requires video analysis.\nPlease analyze the video first.")
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
        
        # Apply smart boundaries if not in Random mode
        if mode != "Random" and (self.scenes or self.speech_boundaries):
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
        
        mode_msg = f" using {mode} mode" if mode != "Random" else ""
        QMessageBox.information(self, "Success", 
                               f"Generated {len(generated_clips)} clips{mode_msg}!")
    
    def add_clip(self):
        """Add a manual clip to the list"""
        start = self.start_spin.value()
        end = self.end_spin.value()
        name = self.clip_name.text().strip()
        
        if not name:
            name = f"manual_clip_{len(self.clips) + 1}"
        
        # Validate parameters
        valid, error_msg = validate_clip_parameters(start, end, self.video_duration)
        if not valid:
            QMessageBox.warning(self, "Invalid Range", error_msg)
            return
        
        if not self.video_path:
            QMessageBox.warning(self, "No Video", "Please load a video first!")
            return
        
        self.clips.append((start, end, name))
        duration = end - start
        self.clips_list.addItem(f"{name} ({format_time(start)} - {format_time(end)}, {duration:.1f}s)")
        
        self.clip_name.setText("")
        self.update_clips_count()
    
    def remove_clip(self):
        """Remove selected clip from the list"""
        current_row = self.clips_list.currentRow()
        if current_row >= 0:
            self.clips_list.takeItem(current_row)
            del self.clips[current_row]
            self.update_clips_count()
    
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