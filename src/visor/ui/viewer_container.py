from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QPixmap, QKeyEvent


class ViewerContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Permitir foco para atajos
        self.setFocusPolicy(Qt.StrongFocus)

        # -------------------------------------------------
        # Layout principal
        # -------------------------------------------------
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # -------------------------------------------------
        # Imagen / Placeholder
        # -------------------------------------------------
        self.image_label = QLabel("Selecciona un archivo")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: black; color: white;"
        )
        self.layout.addWidget(self.image_label)

        # -------------------------------------------------
        # Vídeo
        # -------------------------------------------------
        self.video_widget = QVideoWidget()
        self.video_widget.hide()
        self.layout.addWidget(self.video_widget)

        # -------------------------------------------------
        # Multimedia
        # -------------------------------------------------
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # -------------------------------------------------
        # Controles
        # -------------------------------------------------
        self.controls = QWidget()
        controls_layout = QHBoxLayout(self.controls)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        self.play_button = QPushButton("▶")
        self.position_slider = QSlider(Qt.Horizontal)
        self.volume_slider = QSlider(Qt.Horizontal)

        self.position_slider.setEnabled(False)
        self.position_slider.setRange(0, 0)

        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.audio_output.setVolume(0.5)

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.volume_slider)

        self.controls.hide()
        self.layout.addWidget(self.controls)

        # -------------------------------------------------
        # Conexiones multimedia IMPORTANTES
        # -------------------------------------------------
        self.play_button.clicked.connect(self._toggle_play)

        self.player.mediaStatusChanged.connect(
            self._on_media_status_changed
        )
        self.player.playbackStateChanged.connect(
            self._on_playback_state_changed
        )
        self.player.positionChanged.connect(
            self._on_position_changed
        )

        self.position_slider.sliderMoved.connect(
            self.player.setPosition
        )

        self.volume_slider.valueChanged.connect(
            lambda v: self.audio_output.setVolume(v / 100)
        )

        # -------------------------------------------------
        # OSD
        # -------------------------------------------------
        self.osd_label = QLabel(self)
        self.osd_label.setAlignment(Qt.AlignCenter)
        self.osd_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 160);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 16px;
            }
        """)
        self.osd_label.hide()

        self.osd_timer = QTimer(self)
        self.osd_timer.setSingleShot(True)
        self.osd_timer.timeout.connect(self.osd_label.hide)

    # =================================================
    # API PÚBLICA
    # =================================================

    def show_file(self, path: str):
        if not path:
            self._show_placeholder("Sin archivo")
            return

        suffix = Path(path).suffix.lower()

        if suffix in {".mp4", ".mkv", ".avi", ".mov", ".webm"}:
            self._show_video(path)
            return

        if suffix in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            self._show_image(path)
            return

        self._show_placeholder("Formato no soportado")

    # =================================================
    # Implementación interna
    # =================================================

    def _show_video(self, path: str):
        self.image_label.hide()
        self.video_widget.show()
        self.controls.show()

        self.position_slider.setEnabled(False)
        self.position_slider.setRange(0, 0)

        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

        self._show_osd("▶ Reproduciendo")
        self.setFocus()

    def _show_image(self, path: str):
        self.player.stop()
        self.video_widget.hide()
        self.controls.hide()

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._show_placeholder("No se pudo cargar la imagen")
            return

        self.image_label.setPixmap(
            pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        self.image_label.show()
        self.setFocus()

    def _show_placeholder(self, text="Selecciona un archivo"):
        self.player.stop()
        self.video_widget.hide()
        self.controls.hide()

        self.position_slider.setEnabled(False)
        self.position_slider.setRange(0, 0)

        self.image_label.setText(text)
        self.image_label.setPixmap(QPixmap())
        self.image_label.show()

    # =================================================
    # Señales del reproductor (CRÍTICAS)
    # =================================================

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.LoadedMedia:
            duration = self.player.duration()
            if duration > 0:
                self.position_slider.setEnabled(True)
                self.position_slider.setRange(0, duration)

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")

    def _on_position_changed(self, position):
        if self.player.duration() > 0:
            self.position_slider.setValue(position)

    # =================================================
    # Controles
    # =================================================

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self._show_osd("⏸ Pausado")
        else:
            self.player.play()
            self._show_osd("▶ Reproduciendo")

    def _seek(self, delta_ms: int):
        duration = self.player.duration()
        if duration <= 0:
            return

        new_pos = self.player.position() + delta_ms
        new_pos = max(0, min(new_pos, duration))
        self.player.setPosition(new_pos)

    # =================================================
    # Teclado
    # =================================================

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if key == Qt.Key_Space:
            self._toggle_play()
            event.accept()
            return

        if key == Qt.Key_Right:
            self._seek(5000)
            event.accept()
            return

        if key == Qt.Key_Left:
            self._seek(-5000)
            event.accept()
            return

        if key == Qt.Key_Up:
            volume = min(self.audio_output.volume() + 0.05, 1.0)
            self.audio_output.setVolume(volume)
            self.volume_slider.setValue(int(volume * 100))
            self._show_osd(f"🔊 Volumen {int(volume * 100)}%")
            event.accept()
            return

        if key == Qt.Key_Down:
            volume = max(self.audio_output.volume() - 0.05, 0.0)
            self.audio_output.setVolume(volume)
            self.volume_slider.setValue(int(volume * 100))
            self._show_osd(f"🔊 Volumen {int(volume * 100)}%")
            event.accept()
            return

        if key == Qt.Key_Escape:
            self._show_placeholder("Reproducción detenida")
            self._show_osd("⏹ Detenido")
            event.accept()
            return

        super().keyPressEvent(event)

    # =================================================
    # OSD
    # =================================================

    def _show_osd(self, text, duration=1200):
        self.osd_label.setText(text)
        self.osd_label.adjustSize()
        self._position_osd()
        self.osd_label.show()
        self.osd_timer.start(duration)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_osd()

    def _position_osd(self):
        if not self.osd_label.isVisible():
            return

        w = self.osd_label.sizeHint().width()
        h = self.osd_label.sizeHint().height()

        x = (self.width() - w) // 2
        y = self.height() - h - 40

        self.osd_label.setGeometry(x, y, w, h)
