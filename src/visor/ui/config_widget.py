from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal


class ConfigWidget(QWidget):
    """Widget for configuring navigation cooldowns"""
    
    # Signals
    configChanged = Signal(int, int, int)  # (positive, neutral, negative)
    historyLimitChanged = Signal(int)
    resetPositive = Signal()
    resetNegative = Signal()
    resetAll = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("⚙️ Repeat Configuration")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Control how many files must be viewed before a file can repeat based on its vote.\n"
            "0 = never repeats"
        )
        desc.setStyleSheet("color: gray; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # --- Positive ---
        positive_group = QGroupBox("Upvoted Files")
        positive_layout = QHBoxLayout(positive_group)
        
        positive_layout.addWidget(QLabel("Repeat after:"))
        
        self.positive_spin = QSpinBox()
        self.positive_spin.setRange(0, 200)
        self.positive_spin.setValue(5)
        self.positive_spin.setSuffix(" files")
        self.positive_spin.setSpecialValueText("Never")
        self.positive_spin.valueChanged.connect(self._on_config_changed)
        positive_layout.addWidget(self.positive_spin)
        
        layout.addWidget(positive_group)
        
        # --- Neutral ---
        neutral_group = QGroupBox("Neutral Files")
        neutral_layout = QHBoxLayout(neutral_group)
        
        neutral_layout.addWidget(QLabel("Repeat after:"))
        
        self.neutral_spin = QSpinBox()
        self.neutral_spin.setRange(0, 200)
        self.neutral_spin.setValue(20)
        self.neutral_spin.setSuffix(" files")
        self.neutral_spin.setSpecialValueText("Never")
        self.neutral_spin.valueChanged.connect(self._on_config_changed)
        neutral_layout.addWidget(self.neutral_spin)
        
        layout.addWidget(neutral_group)
        
        # --- Negative ---
        negative_group = QGroupBox("Downvoted Files")
        negative_layout = QHBoxLayout(negative_group)
        
        negative_layout.addWidget(QLabel("Repeat after:"))
        
        self.negative_spin = QSpinBox()
        self.negative_spin.setRange(0, 200)
        self.negative_spin.setValue(0)
        self.negative_spin.setSuffix(" files")
        self.negative_spin.setSpecialValueText("Never")
        self.negative_spin.valueChanged.connect(self._on_config_changed)
        negative_layout.addWidget(self.negative_spin)
        
        layout.addWidget(negative_group)
        
        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # --- History ---
        history_group = QGroupBox("History")
        history_layout = QHBoxLayout(history_group)

        history_layout.addWidget(QLabel("File limit:"))

        self.history_spin = QSpinBox()
        self.history_spin.setRange(100, 100000)
        self.history_spin.setValue(1000)
        self.history_spin.setSingleStep(100)
        self.history_spin.setToolTip("How many files to remember when navigating backwards")
        self.history_spin.valueChanged.connect(self._on_history_changed)
        history_layout.addWidget(self.history_spin)

        layout.addWidget(history_group)
        
        # Separator
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3)
        
        # Quick presets
        preset_label = QLabel("Quick presets:")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label)
        
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(5)
        
        # Preset: Balanced
        btn_balanced = QPushButton("Balanced")
        btn_balanced.setToolTip("Positive: 5, Neutral: 20, Negative: 0")
        btn_balanced.clicked.connect(lambda: self.set_config(5, 20, 0, 1000))
        preset_layout.addWidget(btn_balanced)
        
        # Preset: Favor positive
        btn_aggressive = QPushButton("Favor Positive")
        btn_aggressive.setToolTip("Positive: 3, Neutral: 30, Negative: 0")
        btn_aggressive.clicked.connect(lambda: self.set_config(3, 30, 0, 1000))
        preset_layout.addWidget(btn_aggressive)
        
        # Preset: Second chance
        btn_second = QPushButton("Second Chance")
        btn_second.setToolTip("Positive: 5, Neutral: 20, Negative: 50")
        btn_second.clicked.connect(lambda: self.set_config(5, 20, 50, 1000))
        preset_layout.addWidget(btn_second)
        
        # Preset: Almost random
        btn_random = QPushButton("Almost Random")
        btn_random.setToolTip("Positive: 10, Neutral: 10, Negative: 10")
        btn_random.clicked.connect(lambda: self.set_config(10, 10, 10, 1000))
        preset_layout.addWidget(btn_random)
        
        layout.addLayout(preset_layout)
        
        # Separator
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line4)
        
        # Vote management
        votes_label = QLabel("Vote Management")
        votes_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(votes_label)

        # Button: Reset positive
        reset_pos_btn = QPushButton("Reset Upvoted")
        reset_pos_btn.setToolTip("All positively voted files return to neutral")
        reset_pos_btn.clicked.connect(self._reset_positive)
        reset_pos_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(reset_pos_btn)

        # Button: Reset negative
        reset_neg_btn = QPushButton("Reset Downvoted")
        reset_neg_btn.setToolTip("All negatively voted files return to neutral")
        reset_neg_btn.clicked.connect(self._reset_negative)
        reset_neg_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        layout.addWidget(reset_neg_btn)

        # Button: Reset ALL
        reset_all_btn = QPushButton("Reset ALL Votes")
        reset_all_btn.setToolTip("ALL votes return to neutral")
        reset_all_btn.clicked.connect(self._reset_all)
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        layout.addWidget(reset_all_btn)
        
        # Spacer
        layout.addStretch()
    
    def _on_config_changed(self):
        """Emit signal when configuration changes"""
        self.configChanged.emit(
            self.positive_spin.value(),
            self.neutral_spin.value(),
            self.negative_spin.value()
        )
        self.historyLimitChanged.emit(self.history_spin.value())
    
    def _on_history_changed(self, value):
        """Emit signal when history limit changes"""
        self.historyLimitChanged.emit(value)
    
    def set_config(self, positive: int, neutral: int, negative: int, history: int = 1000):
        """Set configuration"""
        self.positive_spin.setValue(positive)
        self.neutral_spin.setValue(neutral)
        self.negative_spin.setValue(negative)
        self.history_spin.setValue(history)
        self._on_config_changed()
    
    def get_config(self) -> tuple:
        """Get current configuration"""
        return (
            self.positive_spin.value(),
            self.neutral_spin.value(),
            self.negative_spin.value(),
            self.history_spin.value()
        )
    
    def set_history_limit(self, limit: int):
        """Set history limit"""
        self.history_spin.setValue(limit)

    def get_history_limit(self) -> int:
        """Get history limit"""
        return self.history_spin.value()
    
    def _reset_positive(self):
        """Emit signal to reset positive"""
        self.resetPositive.emit()

    def _reset_negative(self):
        """Emit signal to reset negative"""
        self.resetNegative.emit()

    def _reset_all(self):
        """Emit signal to reset all"""
        self.resetAll.emit()