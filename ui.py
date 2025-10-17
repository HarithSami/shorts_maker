"""
UI components for the Smart YouTube Shorts Clip Generator
"""
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QListWidget, QFileDialog, QSpinBox, QLineEdit,
                             QMessageBox, QProgressBar, QGroupBox, QCheckBox,
                             QComboBox, QTabWidget, QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer, QUrl, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart YouTube Shorts Clip Generator")
        self.setGeometry(100, 100, 1200, 800)
        self.setAcceptDrops(True)
        
        # Apply modern styling
        self.setStyleSheet(self._get_app_stylesheet())
        
        # Initialize UI components
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header section (video loading and info)
        self._create_header_section(main_layout)
        
        # Main content with tabs and clips list
        self._create_main_content(main_layout)
        
        # Footer section (progress and export)
        self._create_footer_section(main_layout)
    
    def _create_header_section(self, main_layout):
        """Create the header section with video loading and info"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        
        # Top row with load button (smaller, aligned left)
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("📁 Load Video")
        self.load_btn.setObjectName("loadButton")
        button_layout.addWidget(self.load_btn)
        button_layout.addStretch()  # Push button to left
        header_layout.addLayout(button_layout)
        
        # Large drop area
        self.drop_area = QLabel("🎬 Drag & Drop Video File Here\n\nSupported formats: MP4, AVI, MOV, MKV, WMV")
        self.drop_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area.setObjectName("dropArea")
        self.drop_area.setMinimumHeight(120)
        header_layout.addWidget(self.drop_area)
        
        # Video info
        self.info_label = QLabel("No video loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setObjectName("infoLabel")
        header_layout.addWidget(self.info_label)
        
        # Analysis status
        self.analysis_label = QLabel("")
        self.analysis_label.setObjectName("analysisLabel")
        header_layout.addWidget(self.analysis_label)
        
        main_layout.addWidget(header_frame)
    
    def _create_main_content(self, main_layout):
        """Create the main content area with tabs and clips list"""
        # Create horizontal splitter for tabs and clips list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Create tab widget for different approaches
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        
        # Smart Cutting Tab
        self._create_smart_cutting_tab()
        
        # Random Clips Tab
        self._create_random_clips_tab()
        
        # Manual Selection Tab
        self._create_manual_clip_tab()
        
        # Add tabs to splitter
        splitter.addWidget(self.tab_widget)
        
        # Create clips list section
        clips_widget = self._create_clips_list_widget()
        splitter.addWidget(clips_widget)
        
        # Set splitter proportions (60% tabs, 40% clips list)
        splitter.setSizes([600, 400])
        
        main_layout.addWidget(splitter)
    
    def _create_smart_cutting_tab(self):
        """Create the smart cutting tab"""
        smart_widget = QWidget()
        smart_layout = QVBoxLayout(smart_widget)
        smart_layout.setSpacing(15)
        
        # Enable smart cuts checkbox
        self.enable_smart_cuts = QCheckBox("🧠 Enable Smart Cuts (align to scenes/speech)")
        self.enable_smart_cuts.setChecked(True)
        self.enable_smart_cuts.setObjectName("smartCutsCheckbox")
        smart_layout.addWidget(self.enable_smart_cuts)
        
        # Priority settings group
        priority_group = QGroupBox("Cutting Priority")
        priority_layout = QVBoxLayout(priority_group)
        
        priority_row = QHBoxLayout()
        priority_row.addWidget(QLabel("Priority:"))
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([
            "Scene Changes First",
            "Speech Boundaries First", 
            "Nearest Boundary (either)",
            "Scene Start + Speech End"
        ])
        self.priority_combo.setCurrentIndex(0)
        priority_row.addWidget(self.priority_combo)
        
        priority_row.addWidget(QLabel("Max Adjustment:"))
        self.max_adjustment_spin = QSpinBox()
        self.max_adjustment_spin.setMinimum(1)
        self.max_adjustment_spin.setMaximum(30)
        self.max_adjustment_spin.setValue(5)
        self.max_adjustment_spin.setSuffix(" sec")
        priority_row.addWidget(self.max_adjustment_spin)
        
        priority_row.addStretch()
        priority_layout.addLayout(priority_row)
        smart_layout.addWidget(priority_group)
        
        # Analyze button
        self.analyze_btn = QPushButton("🔍 Analyze Video (Detect Scenes & Speech)")
        self.analyze_btn.setObjectName("analyzeButton")
        smart_layout.addWidget(self.analyze_btn)
        
        smart_layout.addStretch()
        
        self.tab_widget.addTab(smart_widget, "🧠 Smart Cutting")
    
    def _create_random_clips_tab(self):
        """Create the random clips generation tab"""
        random_widget = QWidget()
        random_layout = QVBoxLayout(random_widget)
        random_layout.setSpacing(15)
        
        # Parameters group
        params_group = QGroupBox("Generation Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # First row: Number of clips and duration
        row1 = QHBoxLayout()
        
        num_layout = QVBoxLayout()
        num_layout.addWidget(QLabel("Number of Clips:"))
        self.num_clips_spin = QSpinBox()
        self.num_clips_spin.setMinimum(1)
        self.num_clips_spin.setMaximum(10000)
        self.num_clips_spin.setValue(5)
        num_layout.addWidget(self.num_clips_spin)
        row1.addLayout(num_layout)
        
        duration_layout = QVBoxLayout()
        duration_layout.addWidget(QLabel("Clip Duration (seconds):"))
        self.clip_duration_spin = QSpinBox()
        self.clip_duration_spin.setMinimum(5)
        self.clip_duration_spin.setMaximum(300)
        self.clip_duration_spin.setValue(30)
        duration_layout.addWidget(self.clip_duration_spin)
        row1.addLayout(duration_layout)
        
        params_layout.addLayout(row1)
        
        # Second row: Base name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Base Name:"))
        self.base_name_input = QLineEdit()
        self.base_name_input.setText("short")
        self.base_name_input.setPlaceholderText("short")
        name_layout.addWidget(self.base_name_input)
        params_layout.addLayout(name_layout)
        
        random_layout.addWidget(params_group)
        
        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.allow_overlap_checkbox = QCheckBox("🔄 Allow Overlapping Clips")
        self.allow_overlap_checkbox.setChecked(False)
        options_layout.addWidget(self.allow_overlap_checkbox)
        
        random_layout.addWidget(options_group)
        
        # Generate button
        self.generate_btn = QPushButton("🎲 Generate Random Clips")
        self.generate_btn.setObjectName("generateButton")
        random_layout.addWidget(self.generate_btn)
        
        random_layout.addStretch()
        
        self.tab_widget.addTab(random_widget, "🎲 Random Clips")
    
    def _create_manual_clip_tab(self):
        """Create the manual clip selection tab"""
        manual_widget = QWidget()
        manual_layout = QVBoxLayout(manual_widget)
        manual_layout.setSpacing(15)
        
        # Time selection group
        time_group = QGroupBox("Time Selection")
        time_layout = QVBoxLayout(time_group)
        
        # Time inputs row
        time_row = QHBoxLayout()
        
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Start (seconds):"))
        self.start_spin = QSpinBox()
        self.start_spin.setMaximum(999999)
        start_layout.addWidget(self.start_spin)
        time_row.addLayout(start_layout)
        
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("End (seconds):"))
        self.end_spin = QSpinBox()
        self.end_spin.setMaximum(999999)
        end_layout.addWidget(self.end_spin)
        time_row.addLayout(end_layout)
        
        time_layout.addLayout(time_row)
        manual_layout.addWidget(time_group)
        
        # Clip naming group
        naming_group = QGroupBox("Clip Name")
        naming_layout = QHBoxLayout(naming_group)
        
        self.clip_name = QLineEdit()
        self.clip_name.setPlaceholderText("manual_clip_1")
        naming_layout.addWidget(self.clip_name)
        
        manual_layout.addWidget(naming_group)
        
        # Add clip button
        self.add_clip_btn = QPushButton("➕ Add Manual Clip")
        self.add_clip_btn.setObjectName("addClipButton")
        manual_layout.addWidget(self.add_clip_btn)
        
        manual_layout.addStretch()
        
        self.tab_widget.addTab(manual_widget, "✂️ Manual Selection")
    
    def _create_clips_list_widget(self):
        """Create the clips list widget"""
        clips_widget = QWidget()
        clips_layout = QVBoxLayout(clips_widget)
        clips_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        clips_header_layout = QHBoxLayout()
        header_label = QLabel("📋 Clips to Export")
        header_label.setObjectName("clipsHeader")
        clips_header_layout.addWidget(header_label)
        
        self.clips_count_label = QLabel("(0 clips)")
        self.clips_count_label.setObjectName("clipsCount")
        clips_header_layout.addWidget(self.clips_count_label)
        clips_header_layout.addStretch()
        clips_layout.addLayout(clips_header_layout)
        
        # Clips list
        self.clips_list = QListWidget()
        self.clips_list.setObjectName("clipsList")
        clips_layout.addWidget(self.clips_list)
        
        # List controls
        list_controls = QHBoxLayout()
        self.remove_btn = QPushButton("🗑️ Remove Selected")
        self.remove_btn.setObjectName("removeButton")
        list_controls.addWidget(self.remove_btn)
        
        self.clear_btn = QPushButton("🧹 Clear All")
        self.clear_btn.setObjectName("clearButton")
        list_controls.addWidget(self.clear_btn)
        
        clips_layout.addLayout(list_controls)
        
        return clips_widget
    
    def _create_footer_section(self, main_layout):
        """Create the footer section with progress and export"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        footer_frame.setObjectName("footerFrame")
        footer_layout = QVBoxLayout(footer_frame)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setObjectName("progressBar")
        footer_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setObjectName("progressLabel")
        footer_layout.addWidget(self.progress_label)
        
        # Export button
        self.export_btn = QPushButton("🚀 Export All Clips")
        self.export_btn.setObjectName("exportButton")
        footer_layout.addWidget(self.export_btn)
        
        main_layout.addWidget(footer_frame)
    
    def _get_app_stylesheet(self):
        """Return the application stylesheet for dark mode UI"""
        return """
            /* Main Window - Dark Theme */
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            /* Header and Footer Frames */
            #headerFrame, #footerFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                margin: 2px;
            }
            
            /* Load Button - Smaller and Compact */
            #loadButton {
                background-color: #0d7377;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                max-width: 150px;
            }
            
            #loadButton:hover {
                background-color: #14a085;
            }
            
            #loadButton:pressed {
                background-color: #0a5d61;
            }
            
            /* Drop Area - Large and Prominent */
            #dropArea {
                background-color: #3a3a3a;
                border: 2px dashed #666666;
                border-radius: 12px;
                padding: 30px;
                color: #cccccc;
                font-size: 16px;
                font-weight: bold;
            }
            
            #dropArea:hover {
                border-color: #0d7377;
                background-color: #404040;
                color: #ffffff;
            }
            
            /* Info and Analysis Labels */
            #infoLabel {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 6px;
                padding: 12px;
                color: #e0e0e0;
            }
            
            #analysisLabel {
                color: #aaaaaa;
                font-style: italic;
                padding: 5px;
            }
            
            /* Tab Widget */
            #mainTabs {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
            
            #mainTabs::pane {
                border: 1px solid #404040;
                border-radius: 8px;
                background-color: #2d2d2d;
            }
            
            #mainTabs::tab-bar {
                alignment: center;
            }
            
            QTabBar::tab {
                background-color: #404040;
                border: 1px solid #555555;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                margin-right: 2px;
                font-weight: bold;
                color: #cccccc;
            }
            
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                border-bottom: 2px solid #0d7377;
                color: #ffffff;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #4a4a4a;
                color: #ffffff;
            }
            
            /* Checkboxes and Labels */
            #smartCutsCheckbox {
                font-weight: bold;
                color: #0d7377;
                padding: 8px;
            }
            
            QLabel {
                color: #e0e0e0;
            }
            
            /* Action Buttons */
            #analyzeButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            
            #analyzeButton:hover {
                background-color: #9c27b0;
            }
            
            #generateButton {
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            
            #generateButton:hover {
                background-color: #ff9800;
            }
            
            #addClipButton {
                background-color: #388e3c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-weight: bold;
            }
            
            #addClipButton:hover {
                background-color: #4caf50;
            }
            
            #exportButton {
                background-color: #2e7d32;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            
            #exportButton:hover {
                background-color: #4caf50;
            }
            
            #exportButton:pressed {
                background-color: #1b5e20;
            }
            
            /* Clips List Section */
            #clipsHeader {
                font-weight: bold;
                font-size: 14px;
                color: #0d7377;
            }
            
            #clipsCount {
                color: #aaaaaa;
                font-style: italic;
            }
            
            #clipsList {
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2d2d2d;
                alternate-background-color: #3a3a3a;
                color: #ffffff;
            }
            
            #clipsList::item {
                padding: 8px;
                border-bottom: 1px solid #404040;
            }
            
            #clipsList::item:selected {
                background-color: #0d7377;
            }
            
            #clipsList::item:hover {
                background-color: #404040;
            }
            
            /* Remove and Clear Buttons */
            #removeButton, #clearButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            
            #removeButton:hover, #clearButton:hover {
                background-color: #f44336;
            }
            
            /* Progress Bar */
            #progressBar {
                border: 1px solid #404040;
                border-radius: 6px;
                text-align: center;
                background-color: #2d2d2d;
                color: #ffffff;
            }
            
            #progressBar::chunk {
                background-color: #0d7377;
                border-radius: 5px;
            }
            
            #progressLabel {
                color: #aaaaaa;
                font-style: italic;
                text-align: center;
            }
            
            /* Group Boxes */
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                color: #e0e0e0;
                background-color: #2d2d2d;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #ffffff;
            }
            
            /* Input Fields */
            QSpinBox, QLineEdit, QComboBox {
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 6px;
                background-color: #404040;
                color: #ffffff;
            }
            
            QSpinBox:focus, QLineEdit:focus, QComboBox:focus {
                border-color: #0d7377;
                outline: none;
            }
            
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            
            QComboBox QAbstractItemView {
                background-color: #404040;
                border: 1px solid #555555;
                selection-background-color: #0d7377;
                color: #ffffff;
            }
            
            /* Checkboxes */
            QCheckBox {
                spacing: 8px;
                color: #e0e0e0;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555555;
                border-radius: 3px;
                background-color: #404040;
            }
            
            QCheckBox::indicator:checked {
                background-color: #0d7377;
                border-color: #0d7377;
            }
            
            QCheckBox::indicator:checked:hover {
                background-color: #14a085;
            }
            
            QCheckBox::indicator:hover {
                border-color: #0d7377;
            }
            
            /* Splitter */
            QSplitter::handle {
                background-color: #404040;
            }
            
            QSplitter::handle:horizontal {
                width: 3px;
            }
            
            QSplitter::handle:vertical {
                height: 3px;
            }
        """