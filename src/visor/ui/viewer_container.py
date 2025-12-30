from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl


class ViewerContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Estado ---
        self._is_fullscreen = False
        self._duration = 0

        # --- Multimedia ---
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        self.video_widget = QVideoWidget(self)
        self.player.setVideoOutput(self.video_widget)

        # --- Controles ---
        self.play_button = QPushButton("▶")
        self.position_slider = QSlider(Qt.Horizontal)
        self.time_label = QLabel("00:00 / 00:00")

        self.play_button.clicked.connect(self.toggle_play)
        self.position_slider.sliderMoved.connect(self.seek)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_state_changed)

        # --- Layout controles ---
        controls = QHBoxLayout()
        controls.addWidget(self.play_button)
        controls.addWidget(self.position_slider, 1)
        controls.addWidget(self.time_label)

        self.controls_widget = QWidget()
        self.controls_widget.setLayout(controls)

        # --- Layout principal ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.video_widget, 1)
        layout.addWidget(self.controls_widget)

        # --- Eventos ---
        self.video_widget.mouseDoubleClickEvent = self._on_video_double_click
        self.setFocusPolicy(Qt.StrongFocus)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def show_file(self, path: str):
        url = QUrl.fromLocalFile(path)
        self.player.setSource(url)
        self.player.play()

    # ------------------------------------------------------------------
    # Reproducción
    # ------------------------------------------------------------------

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def seek(self, position):
        self.player.setPosition(position)

    # ------------------------------------------------------------------
    # Señales del reproductor
    # ------------------------------------------------------------------

    def _on_position_changed(self, position):
        self.position_slider.blockSignals(True)
        self.position_slider.setValue(position)
        self.position_slider.blockSignals(False)
        self._update_time_label(position, self._duration)

    def _on_duration_changed(self, duration):
        self._duration = duration
        self.position_slider.setRange(0, duration)
        self._update_time_label(self.player.position(), duration)

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")

    # ------------------------------------------------------------------
    # Fullscreen
    # ------------------------------------------------------------------

    def toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        self.video_widget.setFullScreen(self._is_fullscreen)

        if self._is_fullscreen:
            self.controls_widget.hide()
        else:
            self.controls_widget.show()

    def _on_video_double_click(self, event):
        self.toggle_fullscreen()
        event.accept()

    # ------------------------------------------------------------------
    # Teclado
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        key = event.key()

        if key == Qt.Key_Space:
            self.toggle_play()
            event.accept()
            return

        if key == Qt.Key_Right:
            self.player.setPosition(self.player.position() + 5000)
            event.accept()
            return

        if key == Qt.Key_Left:
            self.player.setPosition(self.player.position() - 5000)
            event.accept()
            return

        if key == Qt.Key_F:
            self.toggle_fullscreen()
            event.accept()
            return

        if key == Qt.Key_Escape and self._is_fullscreen:
            self.toggle_fullscreen()
            event.accept()
            return

        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _update_time_label(self, pos, dur):
        def fmt(ms):
            s = ms // 1000
            return f"{s // 60:02d}:{s % 60:02d}"

        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")
