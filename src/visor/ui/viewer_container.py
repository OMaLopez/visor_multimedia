from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel,QPushButton, QSlider, QHBoxLayout
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
import os



class ViewerContainer(QWidget):

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov"}
    MAX_IMAGE_SIZE_MB = 200

    def __init__(self, parent=None):
        super().__init__(parent)

        # -------- Layout principal --------
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # -------- Imagen / Placeholder --------
        self.label = QLabel("Selecciona un archivo multimedia")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: white;")
        self.layout.addWidget(self.label)

        # -------- Vídeo --------
        self.video_widget = QVideoWidget()
        self.video_widget.hide()
        self.layout.addWidget(self.video_widget)

        self.player = QMediaPlayer(self)

        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.5)

        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)

        # -------- Controles --------
        self.controls = QWidget()
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(5, 5, 5, 5)
        self.controls.setLayout(controls_layout)

        self.play_button = QPushButton("▶")
        self.position_slider = QSlider(Qt.Horizontal)
        self.volume_slider = QSlider(Qt.Horizontal)

        self.position_slider.setRange(0, 0)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.position_slider)
        controls_layout.addWidget(self.volume_slider)

        self.controls.hide()
        self.layout.addWidget(self.controls)

        self.setFocusPolicy(Qt.StrongFocus)

        # -------- Conexiones --------
        self.play_button.clicked.connect(self._toggle_play)

        self.player.positionChanged.connect(self.position_slider.setValue)
        self.player.durationChanged.connect(self.position_slider.setRange)
        self.position_slider.sliderMoved.connect(self.player.setPosition)

        self.volume_slider.valueChanged.connect(
            lambda v: self.audio_output.setVolume(v / 100)
        )

    # =========================================================
    # API pública
    # =========================================================

    def show_file(self, path: str):
        if not os.path.isfile(path):
            return

        _, ext = os.path.splitext(path)
        ext = ext.lower()

        if ext in self.IMAGE_EXTENSIONS:
            self._show_image(path)
        elif ext in self.VIDEO_EXTENSIONS:
            self._show_video(path)
        else:
            self._show_placeholder("Formato no soportado")
        self.setFocus()

    # =========================================================
    # Imagen
    # =========================================================

    def _show_image(self, path: str):
        self._stop_video()
        self.controls.hide()

        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            self._show_placeholder("Imagen demasiado grande")
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._show_placeholder("No se pudo cargar la imagen")
            return

        self.video_widget.hide()
        self.label.show()
        self.label.setPixmap(
            pixmap.scaled(
                self.label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    # =========================================================
    # Vídeo
    # =========================================================

    def _show_video(self, path: str):
        self.label.hide()
        self.video_widget.show()
        self.controls.show()

        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.play_button.setText("⏸")

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_button.setText("▶")
        else:
            self.player.play()
            self.play_button.setText("⏸")

    def _stop_video(self):
        if self.player.playbackState() != QMediaPlayer.StoppedState:
            self.player.stop()

    def keyPressEvent(self, event):
        key = event.key()

        # Play / Pause
        if key == Qt.Key_Space:
            self._toggle_play()
            event.accept()
            return

        # Adelantar
        if key == Qt.Key_Right:
            self.player.setPosition(self.player.position() + 5000)
            event.accept()
            return

        # Retroceder
        if key == Qt.Key_Left:
            self.player.setPosition(self.player.position() - 5000)
            event.accept()
            return

        # Subir volumen
        if key == Qt.Key_Up:
            volume = min(self.audio_output.volume() + 0.05, 1.0)
            self.audio_output.setVolume(volume)
            self.volume_slider.setValue(int(volume * 100))
            event.accept()
            return

        # Bajar volumen
        if key == Qt.Key_Down:
            volume = max(self.audio_output.volume() - 0.05, 0.0)
            self.audio_output.setVolume(volume)
            self.volume_slider.setValue(int(volume * 100))
            event.accept()
            return

        # Detener
        if key == Qt.Key_Escape:
            self._stop_video()
            self._show_placeholder("Reproducción detenida")
            event.accept()
            return

        super().keyPressEvent(event)

    # =========================================================
    # Placeholder
    # =========================================================

    def _show_placeholder(self, text: str):
        self._stop_video()
        self.video_widget.hide()
        self.controls.hide()
        self.label.show()
        self.label.setPixmap(QPixmap())
        self.label.setText(text)

    # =========================================================
    # Resize
    # =========================================================

    def resizeEvent(self, event):
        pixmap = self.label.pixmap()
        if pixmap:
            self.label.setPixmap(
                pixmap.scaled(
                    self.label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        super().resizeEvent(event)
