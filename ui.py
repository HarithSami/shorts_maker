"""
Modern Dark UI for Smart YouTube Shorts Clip Generator
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                             QListWidget, QLineEdit, QProgressBar, QFrame,
                             QCheckBox, QComboBox, QFileDialog, QAbstractSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor


class DropZone(QFrame):
    """Custom drop zone widget for file uploads"""
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #555;
                border-radius: 10px;
                background-color: #2a2a2a;
                color: #ccc;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_label = QLabel("📁")
        self.icon_label.setFont(QFont("Arial", 32))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("border: none; outline: none;")
        layout.addWidget(self.icon_label)
        
        self.text_label = QLabel("Drop video file here or click to browse")
        self.text_label.setFont(QFont("Arial", 12))
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("color: #ccc; margin: 10px; border: none; outline: none;")
        layout.addWidget(self.text_label)
        
        self.setLayout(layout)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #007acc;
                    border-radius: 10px;
                    background-color: #333;
                    color: #007acc;
                }
            """)
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #555;
                border-radius: 10px;
                background-color: #2a2a2a;
                color: #ccc;
            }
            QFrame:hover {
                border-color: #007acc;
                background-color: #333;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_dropped.emit(files[0])
        self.dragLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Video File", 
                "", 
                "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm)"
            )
            if file_path:
                self.file_dropped.emit(file_path)


class MainWindow(QMainWindow):
    """Main application window with modern dark design"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Shorts Clip Generator")
        self.setGeometry(100, 100, 800, 650)
        self.current_video_path = None
        
        # Apply dark theme
        self._apply_dark_theme()
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Title
        title = QLabel("YouTube Shorts Generator")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #fff; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.file_dropped.connect(self.handle_file_drop)
        main_layout.addWidget(self.drop_zone)
        
        # Video info
        self.video_info_label = QLabel("")
        self.video_info_label.setStyleSheet("color: #aaa; font-size: 12px; margin: 5px 0;")
        self.video_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.video_info_label)
        
        # Analysis options
        analysis_frame = self._create_analysis_frame()
        main_layout.addWidget(analysis_frame)
        
        # Clip settings
        settings_frame = self._create_settings_frame()
        main_layout.addWidget(settings_frame)
        
        # Generate button
        self.generate_btn = QPushButton("✨ Generate Clips")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet(self._get_button_style("#6f42c1", large=True))
        main_layout.addWidget(self.generate_btn)
        
        # Clips list
        clips_frame = self._create_clips_frame()
        main_layout.addWidget(clips_frame)
        
        # Export button
        self.export_btn = QPushButton("💾 Export All Clips")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet(self._get_button_style("#dc3545", large=True))
        main_layout.addWidget(self.export_btn)
        
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                background-color: #2a2a2a;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #ccc; font-size: 12px;")
        main_layout.addWidget(self.progress_label)
    
    def _apply_dark_theme(self):
        """Apply dark theme to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QSpinBox, QDoubleSpinBox, QLineEdit, QComboBox {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #fff;
                font-size: 12px;
                selection-background-color: #007acc;
                selection-color: #fff;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                border-color: #007acc;
                outline: none;
            }
            QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                selection-background-color: #007acc;
                selection-color: #fff;
                color: #fff;
            }
            QSpinBox QLineEdit:focus, QDoubleSpinBox QLineEdit:focus {
                background-color: transparent;
                selection-background-color: #007acc;
                selection-color: #fff;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #555;
                border-bottom: 1px solid #555;
                border-top-right-radius: 5px;
                background-color: #3a3a3a;
            }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {
                background-color: #007acc;
            }
            QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed {
                background-color: #005a9e;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #ccc;
                width: 0px;
                height: 0px;
            }
            QSpinBox::up-arrow:hover, QDoubleSpinBox::up-arrow:hover {
                border-bottom-color: #fff;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 20px;
                border-left: 1px solid #555;
                border-top: 1px solid #555;
                border-bottom-right-radius: 5px;
                background-color: #3a3a3a;
            }
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #007acc;
            }
            QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {
                background-color: #005a9e;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #ccc;
                width: 0px;
                height: 0px;
            }
            QSpinBox::down-arrow:hover, QDoubleSpinBox::down-arrow:hover {
                border-top-color: #fff;
            }
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 5px;
                color: #fff;
                selection-background-color: #007acc;
            }
            QCheckBox {
                color: #fff;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #555;
                border-radius: 3px;
                background-color: #2a2a2a;
            }
            QCheckBox::indicator:checked {
                background-color: #007acc;
                border-color: #007acc;
            }
        """)
    
    def _get_button_style(self, color, large=False):
        """Get button style with specified color"""
        size = "padding: 12px 30px; font-size: 14px;" if large else "padding: 8px 20px; font-size: 12px;"
        return f"""
            QPushButton {{
                {size}
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._darken_color(color)};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """
    
    def _darken_color(self, color):
        """Darken a hex color for hover effect"""
        color_map = {
            "#28a745": "#218838",
            "#6f42c1": "#5a32a3", 
            "#dc3545": "#c82333",
            "#007bff": "#0056b3",
            "#17a2b8": "#138496"
        }
        return color_map.get(color, color)
    
    def handle_file_drop(self, file_path):
        """Handle file drop/selection"""
        self.current_video_path = file_path
        filename = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
        self.video_info_label.setText(f"📹 {filename}")
        self.analyze_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
        
        # Update drop zone appearance
        self.drop_zone.text_label.setText(f"✅ {filename}")
        self.drop_zone.setStyleSheet("""
            QFrame {
                border: 2px solid #28a745;
                border-radius: 10px;
                background-color: #2a2a2a;
                color: #28a745;
            }
        """)
    
    def _create_analysis_frame(self):
        """Create analysis options frame"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        analysis_label = QLabel("Video Analysis")
        analysis_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header_layout.addWidget(analysis_label)
        header_layout.addStretch()
        
        # Analyze button
        self.analyze_btn = QPushButton("🔍 Analyze Video")
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setStyleSheet(self._get_button_style("#28a745"))
        self.analyze_btn.setMaximumWidth(150)
        header_layout.addWidget(self.analyze_btn)
        
        layout.addLayout(header_layout)
        
        # Checkboxes for analysis options
        options_layout = QHBoxLayout()
        
        self.scene_detection_checkbox = QCheckBox("Scene Detection")
        self.scene_detection_checkbox.setChecked(True)
        options_layout.addWidget(self.scene_detection_checkbox)
        
        options_layout.addSpacing(20)
        
        self.audio_detection_checkbox = QCheckBox("Audio Detection")
        self.audio_detection_checkbox.setChecked(True)
        options_layout.addWidget(self.audio_detection_checkbox)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        return frame
    
    def _create_settings_frame(self):
        """Create settings frame"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        
        # First row
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Clips:"))
        self.num_clips_spin = QSpinBox()
        self.num_clips_spin.setRange(1, 20)
        self.num_clips_spin.setValue(5)
        self.num_clips_spin.setMaximumWidth(60)
        # Configure for proper manual editing
        self.num_clips_spin.setKeyboardTracking(True)
        self.num_clips_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.num_clips_spin.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        # Ensure the line edit is editable
        line_edit = self.num_clips_spin.lineEdit()
        if line_edit:
            line_edit.setReadOnly(False)
            line_edit.selectAll()  # This helps with initial selection
        row1.addWidget(self.num_clips_spin)
        
        row1.addSpacing(20)
        row1.addWidget(QLabel("Duration:"))
        self.clip_duration_spin = QDoubleSpinBox()
        self.clip_duration_spin.setRange(1.0, 180.0)
        self.clip_duration_spin.setValue(60.0)
        self.clip_duration_spin.setMaximumWidth(80)
        self.clip_duration_spin.setDecimals(1)
        self.clip_duration_spin.setSingleStep(0.5)
        # Configure for proper manual editing
        self.clip_duration_spin.setKeyboardTracking(True)
        self.clip_duration_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.clip_duration_spin.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        # Ensure the line edit is editable
        line_edit = self.clip_duration_spin.lineEdit()
        if line_edit:
            line_edit.setReadOnly(False)
            line_edit.selectAll()  # This helps with initial selection
        row1.addWidget(self.clip_duration_spin)
        row1.addWidget(QLabel("sec"))
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # Second row
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Method:"))
        self.generation_method = QComboBox()
        self.generation_method.addItems([
            "Random",
            "Smart Detection"
        ])
        self.generation_method.setMinimumWidth(200)
        self.generation_method.setMaximumWidth(250)
        row2.addWidget(self.generation_method)
        
        row2.addSpacing(20)
        self.allow_overlap_checkbox = QCheckBox("Allow Overlapping")
        row2.addWidget(self.allow_overlap_checkbox)
        
        row2.addStretch()
        layout.addLayout(row2)
        
        return frame
    
    def _create_clips_frame(self):
        """Create clips list frame"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Header
        header = QHBoxLayout()
        clips_label = QLabel("Generated Clips")
        clips_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        header.addWidget(clips_label)
        
        self.clips_count_label = QLabel("(0 clips)")
        self.clips_count_label.setStyleSheet("color: #aaa; font-size: 11px;")
        header.addWidget(self.clips_count_label)
        header.addStretch()
        
        # Clear button
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.setStyleSheet(self._get_button_style("#6c757d"))
        self.clear_btn.setMinimumWidth(120)
        self.clear_btn.setMaximumWidth(150)
        header.addWidget(self.clear_btn)
        
        layout.addLayout(header)
        
        # Clips list
        self.clips_list = QListWidget()
        self.clips_list.setMaximumHeight(120)
        layout.addWidget(self.clips_list)
        
        return frame
    
    # Add compatibility properties for main.py
    @property
    def load_btn(self):
        """Compatibility property - file loading is handled by drop zone"""
        return self.drop_zone
    
    @property 
    def add_clip_btn(self):
        """Compatibility property - manual clip adding removed for minimal UI"""
        return None
    
    @property
    def remove_btn(self):
        """Compatibility property - individual clip removal handled by clear button"""
        return self.clear_btn
    
    @property
    def base_name_input(self):
        """Compatibility property - base name is fixed in minimal UI"""
        class DummyInput:
            def text(self): return "short"
        return DummyInput()
    
    @property
    def start_spin(self):
        """Compatibility property - manual clip adding removed"""
        class DummySpin:
            def setMaximum(self, val): pass
            def value(self): return 0
        return DummySpin()
    
    @property
    def end_spin(self):
        """Compatibility property - manual clip adding removed"""
        class DummySpin:
            def setMaximum(self, val): pass
            def setValue(self, val): pass
            def value(self): return 60
        return DummySpin()
    
    @property
    def clip_name(self):
        """Compatibility property - manual clip adding removed"""
        class DummyInput:
            def text(self): return ""
            def setText(self, text): pass
        return DummyInput()
    
    @property
    def max_adjustment_spin(self):
        """Compatibility property - max adjustment removed for minimal UI"""
        class DummySpin:
            def value(self): return 2.0
            def setEnabled(self, enabled): pass
        return DummySpin()
    
    # Real properties for the new checkboxes are created in _create_analysis_frame
