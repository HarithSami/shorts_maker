"""
Redesigned clean UI for Smart YouTube Shorts Clip Generator
"""
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSpinBox, QDoubleSpinBox,
                             QListWidget, QLineEdit, QProgressBar, QGroupBox,
                             QCheckBox, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class MainWindow(QMainWindow):
    """Main application window with clean, simplified design"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart YouTube Shorts Clip Generator")
        self.setGeometry(100, 100, 900, 700)
        self.setAcceptDrops(True)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("YouTube Shorts Clip Generator")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        
        # Video Loading Section
        video_section = self._create_video_section()
        main_layout.addWidget(video_section)
        
        # Info label
        self.info_label = QLabel("Drop a video file here or click 'Load Video'")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.info_label)
        
        # Clip Creator Section
        clip_creator_section = self._create_clip_creator_section()
        main_layout.addWidget(clip_creator_section)
        
        # Manual Clip Section
        manual_section = self._create_manual_clip_section()
        main_layout.addWidget(manual_section)
        
        # Clips List Section
        clips_section = self._create_clips_list_section()
        main_layout.addWidget(clips_section)
        
        # Export Section
        export_section = self._create_export_section()
        main_layout.addWidget(export_section)
        
        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.progress_label)
    
    def _create_video_section(self):
        """Create video loading section"""
        group = QGroupBox("1. Load Video")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📁 Load Video")
        self.load_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        layout.addWidget(self.load_btn)
        
        self.analyze_btn = QPushButton("🔍 Analyze Video (for smart detection)")
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(self.analyze_btn)
        
        self.analysis_label = QLabel("")
        self.analysis_label.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        layout.addWidget(self.analysis_label, stretch=1)
        
        group.setLayout(layout)
        return group
    
    def _create_clip_creator_section(self):
        """Create automatic clip generation section"""
        group = QGroupBox("2. Clip Creator")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Top row: Number of clips, duration, and name
        top_row = QHBoxLayout()
        
        top_row.addWidget(QLabel("Clips:"))
        self.num_clips_spin = QSpinBox()
        self.num_clips_spin.setRange(1, 100)
        self.num_clips_spin.setValue(5)
        self.num_clips_spin.setMinimumWidth(70)
        top_row.addWidget(self.num_clips_spin)
        
        top_row.addSpacing(15)
        
        top_row.addWidget(QLabel("Duration:"))
        self.clip_duration_spin = QDoubleSpinBox()
        self.clip_duration_spin.setRange(5, 300)
        self.clip_duration_spin.setValue(60)
        self.clip_duration_spin.setSuffix(" sec")
        self.clip_duration_spin.setMinimumWidth(90)
        top_row.addWidget(self.clip_duration_spin)
        
        top_row.addSpacing(15)
        
        top_row.addWidget(QLabel("Base Name:"))
        self.base_name_input = QLineEdit()
        self.base_name_input.setPlaceholderText("short")
        self.base_name_input.setMaximumWidth(120)
        top_row.addWidget(self.base_name_input)
        
        top_row.addStretch()
        layout.addLayout(top_row)
        
        # Bottom row: Method and options
        bottom_row = QHBoxLayout()
        
        bottom_row.addWidget(QLabel("Method:"))
        self.generation_method = QComboBox()
        self.generation_method.addItems([
            "Random",
            "Random + Scene Detection",
            "Random + Audio Detection"
        ])
        self.generation_method.setMinimumWidth(200)
        bottom_row.addWidget(self.generation_method)
        
        bottom_row.addSpacing(15)
        
        bottom_row.addWidget(QLabel("Max Adjust:"))
        self.max_adjustment_spin = QDoubleSpinBox()
        self.max_adjustment_spin.setRange(0, 10)
        self.max_adjustment_spin.setValue(2.0)
        self.max_adjustment_spin.setSuffix(" sec")
        self.max_adjustment_spin.setMinimumWidth(90)
        self.max_adjustment_spin.setEnabled(False)  # Disabled by default
        bottom_row.addWidget(self.max_adjustment_spin)
        
        bottom_row.addSpacing(15)
        
        self.allow_overlap_checkbox = QCheckBox("Allow Overlapping")
        self.allow_overlap_checkbox.setChecked(False)
        bottom_row.addWidget(self.allow_overlap_checkbox)
        
        bottom_row.addStretch()
        layout.addLayout(bottom_row)
        
        # Generate button
        self.generate_btn = QPushButton("✨ Generate Clips")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 30px;
                font-size: 15px;
                font-weight: bold;
                background-color: #6f42c1;
                color: white;
                border: none;
                border-radius: 5px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
        """)
        layout.addWidget(self.generate_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_manual_clip_section(self):
        """Create manual clip addition section"""
        group = QGroupBox("3. Add Manual Clip (Optional)")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Start:"))
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 10000)
        self.start_spin.setSuffix(" sec")
        self.start_spin.setMinimumWidth(90)
        layout.addWidget(self.start_spin)
        
        layout.addSpacing(10)
        
        layout.addWidget(QLabel("End:"))
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0, 10000)
        self.end_spin.setValue(60)
        self.end_spin.setSuffix(" sec")
        self.end_spin.setMinimumWidth(90)
        layout.addWidget(self.end_spin)
        
        layout.addSpacing(10)
        
        layout.addWidget(QLabel("Name:"))
        self.clip_name = QLineEdit()
        self.clip_name.setPlaceholderText("Optional")
        self.clip_name.setMaximumWidth(150)
        layout.addWidget(self.clip_name)
        
        self.add_clip_btn = QPushButton("➕ Add Clip")
        self.add_clip_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        layout.addWidget(self.add_clip_btn)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_clips_list_section(self):
        """Create clips list management section"""
        group = QGroupBox("4. Clips List")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QVBoxLayout()
        
        # Clips count label
        self.clips_count_label = QLabel("(0 clips)")
        self.clips_count_label.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        layout.addWidget(self.clips_count_label)
        
        # Clips list
        self.clips_list = QListWidget()
        self.clips_list.setMinimumHeight(120)
        layout.addWidget(self.clips_list)
        
        # Management buttons
        buttons_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("🗑️ Remove Selected")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        buttons_layout.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear All")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        buttons_layout.addWidget(self.clear_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_export_section(self):
        """Create export section"""
        group = QGroupBox("5. Export")
        group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 13px; }")
        layout = QHBoxLayout()
        
        self.export_btn = QPushButton("💾 Export All Clips")
        self.export_btn.setStyleSheet("""
            QPushButton {
                padding: 15px 40px;
                font-size: 16px;
                font-weight: bold;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(self.export_btn)
        layout.addStretch()
        
        group.setLayout(layout)
        return group