#!/usr/bin/env python3
"""
Simple test to verify QSpinBox manual editing functionality
"""
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpinBox, QDoubleSpinBox, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SpinBoxTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SpinBox Manual Editing Test")
        self.setGeometry(100, 100, 400, 300)
        
        layout = QVBoxLayout()
        
        # Test regular spinbox
        layout.addWidget(QLabel("Regular QSpinBox (should allow manual editing):"))
        self.regular_spin = QSpinBox()
        self.regular_spin.setRange(1, 100)
        self.regular_spin.setValue(5)
        layout.addWidget(self.regular_spin)
        
        # Test configured spinbox (like in our app)
        layout.addWidget(QLabel("Configured QSpinBox (our app style):"))
        self.configured_spin = QSpinBox()
        self.configured_spin.setRange(1, 20)
        self.configured_spin.setValue(5)
        self.configured_spin.setKeyboardTracking(True)
        self.configured_spin.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        layout.addWidget(self.configured_spin)
        
        # Test double spinbox
        layout.addWidget(QLabel("QDoubleSpinBox (should allow manual editing):"))
        self.double_spin = QDoubleSpinBox()
        self.double_spin.setRange(15.0, 180.0)
        self.double_spin.setValue(60.0)
        self.double_spin.setDecimals(1)
        self.double_spin.setSingleStep(0.5)
        self.double_spin.setKeyboardTracking(True)
        self.double_spin.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        layout.addWidget(self.double_spin)
        
        # Instructions
        instructions = QLabel("""
Instructions:
1. Click on each spinbox
2. Try typing numbers directly
3. Try selecting all text (Ctrl+A) and typing new values
4. Check if the cursor appears and text can be edited

If manual editing doesn't work, there may be a system-specific issue.
        """)
        instructions.setFont(QFont("Arial", 10))
        layout.addWidget(instructions)
        
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    window = SpinBoxTest()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()