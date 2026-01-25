from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QGroupBox, QFrame
)
from PySide6.QtCore import Qt, Signal


class ConfigWidget(QWidget):
    """Widget para configurar cooldowns de navegación"""
    
    # Señales
    configChanged = Signal(int, int, int)  # (positive, neutral, negative)

    historyLimitChanged = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Título
        title = QLabel("⚙️ Configuración de Repetición")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Descripción
        desc = QLabel(
            "Controla cada cuántos archivos se pueden repetir según su voto.\n"
            "0 = nunca se repite"
        )
        desc.setStyleSheet("color: gray; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # --- Positivos ---
        positive_group = QGroupBox("👍 Archivos Positivos")
        positive_layout = QHBoxLayout(positive_group)
        
        positive_layout.addWidget(QLabel("Repetir después de:"))
        
        self.positive_spin = QSpinBox()
        self.positive_spin.setRange(0, 200)
        self.positive_spin.setValue(5)
        self.positive_spin.setSuffix(" archivos")
        self.positive_spin.valueChanged.connect(self._on_config_changed)
        positive_layout.addWidget(self.positive_spin)
        
        layout.addWidget(positive_group)
        
        # --- Neutrales ---
        neutral_group = QGroupBox("⚪ Archivos Neutrales")
        neutral_layout = QHBoxLayout(neutral_group)
        
        neutral_layout.addWidget(QLabel("Repetir después de:"))
        
        self.neutral_spin = QSpinBox()
        self.neutral_spin.setRange(0, 200)
        self.neutral_spin.setValue(20)
        self.neutral_spin.setSuffix(" archivos")
        self.neutral_spin.valueChanged.connect(self._on_config_changed)
        neutral_layout.addWidget(self.neutral_spin)
        
        layout.addWidget(neutral_group)
        
        # --- Negativos ---
        negative_group = QGroupBox("👎 Archivos Negativos")
        negative_layout = QHBoxLayout(negative_group)
        
        negative_layout.addWidget(QLabel("Repetir después de:"))
        
        self.negative_spin = QSpinBox()
        self.negative_spin.setRange(0, 200)
        self.negative_spin.setValue(0)
        self.negative_spin.setSuffix(" archivos")
        self.negative_spin.setSpecialValueText("Nunca")
        self.negative_spin.valueChanged.connect(self._on_config_changed)
        negative_layout.addWidget(self.negative_spin)
        
        layout.addWidget(negative_group)
        
        # --- Historial ---
        history_group = QGroupBox("📜 Historial")
        history_layout = QHBoxLayout(history_group)

        history_layout.addWidget(QLabel("Límite de archivos:"))

        self.history_spin = QSpinBox()
        self.history_spin.setRange(100, 100000)
        self.history_spin.setValue(1000)
        self.history_spin.setSingleStep(100)
        self.history_spin.setToolTip("Cuántos archivos recordar al navegar hacia atrás")
        self.history_spin.valueChanged.connect(self._on_history_changed)
        history_layout.addWidget(self.history_spin)

        layout.addWidget(history_group)
        
        # Separador
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)
        
        # Botones de preset
        preset_label = QLabel("Configuraciones rápidas:")
        preset_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preset_label)
        
        preset_layout = QVBoxLayout()
        preset_layout.setSpacing(5)
        
        # Preset: Balanceado
        btn_balanced = QPushButton("⚖️ Balanceado")
        btn_balanced.setToolTip("Positivos: 5, Neutrales: 20, Negativos: 0")
        btn_balanced.clicked.connect(lambda: self.set_config(5, 20, 0, 1000))
        preset_layout.addWidget(btn_balanced)
        
        # Preset: Favorece positivos
        btn_aggressive = QPushButton("🔥 Favorece Positivos")
        btn_aggressive.setToolTip("Positivos: 3, Neutrales: 30, Negativos: 0")
        btn_aggressive.clicked.connect(lambda: self.set_config(3, 30, 0, 1000))
        preset_layout.addWidget(btn_aggressive)
        
        # Preset: Segunda oportunidad
        btn_second = QPushButton("🔄 Segunda Oportunidad")
        btn_second.setToolTip("Positivos: 5, Neutrales: 20, Negativos: 50")
        btn_second.clicked.connect(lambda: self.set_config(5, 20, 50, 1000))
        preset_layout.addWidget(btn_second)
        
        # Preset: Aleatorio
        btn_random = QPushButton("🎲 Casi Aleatorio")
        btn_random.setToolTip("Positivos: 10, Neutrales: 10, Negativos: 10")
        btn_random.clicked.connect(lambda: self.set_config(10, 10, 10, 1000))
        preset_layout.addWidget(btn_random)
        
        layout.addLayout(preset_layout)
        


        # Separador
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3)

        # Sección de gestión de votos
        votes_label = QLabel("📊 Gestión de Votos")
        votes_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(votes_label)

        # Botón: Resetear positivos
        reset_pos_btn = QPushButton("🗑️ Resetear Positivos")
        reset_pos_btn.setToolTip("Todos los archivos votados positivamente pasan a neutral")
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

        # Botón: Resetear negativos
        reset_neg_btn = QPushButton("🗑️ Resetear Negativos")
        reset_neg_btn.setToolTip("Todos los archivos votados negativamente pasan a neutral")
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

        # Botón: Resetear TODO
        reset_all_btn = QPushButton("⚠️ Resetear TODOS los Votos")
        reset_all_btn.setToolTip("TODOS los votos pasan a neutral")
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



        # Espaciador
        layout.addStretch()
        
        # Botón de aplicar
        apply_btn = QPushButton("✓ Aplicar Configuración")
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        apply_btn.clicked.connect(self._on_config_changed)
        layout.addWidget(apply_btn)
    
    def _on_config_changed(self):
        """Emitir señal cuando cambia la configuración"""
        self.configChanged.emit(
            self.positive_spin.value(),
            self.neutral_spin.value(),
            self.negative_spin.value()
        )

    def _on_history_changed(self, value):
        """Emitir señal cuando cambia el límite de historial"""
        self.historyLimitChanged.emit(value)
    
    def set_config(self, positive: int, neutral: int, negative: int, history: int = 1000):
        """Establecer configuración"""
        self.positive_spin.setValue(positive)
        self.neutral_spin.setValue(neutral)
        self.negative_spin.setValue(negative)
        self.history_spin.setValue(history)
        self._on_config_changed()

    def set_history_limit(self, limit: int):
        """Establecer límite de historial"""
        self.history_spin.setValue(limit)

    def get_history_limit(self) -> int:
        """Obtener límite de historial"""
        return self.history_spin.value()
    
    def get_config(self) -> tuple:
        """Obtener configuración actual"""
        return (
            self.positive_spin.value(),
            self.neutral_spin.value(),
            self.negative_spin.value(),
            self.history_spin.value()
        )
    # Señales para comunicar con MainWindow
    resetPositive = Signal()
    resetNegative = Signal()
    resetAll = Signal()

    def _reset_positive(self):
        """Emitir señal para resetear positivos"""
        self.resetPositive.emit()

    def _reset_negative(self):
        """Emitir señal para resetear negativos"""
        self.resetNegative.emit()

    def _reset_all(self):
        """Emitir señal para resetear todos"""
        self.resetAll.emit()