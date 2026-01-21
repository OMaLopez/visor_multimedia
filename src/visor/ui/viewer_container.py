from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QSlider,
    QVBoxLayout, QHBoxLayout, QStackedLayout, QMessageBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QUrl, QTimer, QSize, Signal
from PySide6.QtGui import QPixmap, QKeyEvent, QImageReader


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}


class ViewerContainer(QWidget):
    # Señales
    voteChanged = Signal(str, int)  # (file_path, vote: 1/-1/0)
    requestNext = Signal()  # Solicitar siguiente archivo aleatorio
    requestPrevious = Signal()  # Solicitar archivo anterior
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self._duration = 0
        self._current_pixmap = None
        self._seeking = False
        self._video_widget = None
        self._current_file = None  # Archivo actualmente mostrado

        # ---------------- Player ----------------
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)

        # Connect player signals (persistent)
        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(self._on_duration)
        self.player.playbackStateChanged.connect(self._on_state)

        # ---------------- Stack ----------------
        self.stack = QStackedLayout(self)

        # ---------------- Image page ----------------
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: black;")

        image_page = QWidget()
        image_layout = QVBoxLayout(image_page)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.addWidget(self.image_label)
        
        # Voting controls overlay for images
        self._create_voting_controls()
        image_layout.addWidget(self.voting_controls)

        # ---------------- Video page ----------------
        self.video_page = QWidget()
        self.video_layout = QVBoxLayout(self.video_page)
        self.video_layout.setContentsMargins(0, 0, 0, 0)

        # Create persistent controls
        self._create_controls()

        # ---------------- Stack setup ----------------
        self.stack.addWidget(image_page)   # index 0
        self.stack.addWidget(self.video_page)  # index 1
        self.stack.setCurrentIndex(0)

        self.setFocusPolicy(Qt.StrongFocus)

    # =================================================
    # Voting controls
    # =================================================
    
    def _create_voting_controls(self):
        """Create voting status indicator"""
        self.voting_controls = QWidget()
        voting_layout = QHBoxLayout(self.voting_controls)
        voting_layout.setContentsMargins(5, 3, 5, 3)
        
        self.vote_status_label = QLabel("⚪")
        self.vote_status_label.setAlignment(Qt.AlignCenter)
        self.vote_status_label.setStyleSheet("""
            QLabel {
                background-color: rgba(43, 43, 43, 180);
                color: white;
                padding: 5px 15px;
                font-size: 16px;
                border-radius: 3px;
            }
        """)
        
        voting_layout.addStretch()
        voting_layout.addWidget(self.vote_status_label)
        voting_layout.addStretch()
        
        self.voting_controls.setStyleSheet("background-color: transparent;")
    
    def _vote(self, vote_type: int):
        """Handle voting with one-directional progression"""
        if not self._current_file:
            return
        
        current = self.get_current_vote()
        
        # Si es upvote (flecha arriba) - Solo avanza hacia positivo
        if vote_type == 1:
            if current == -1:  # Negativo → Neutral
                new_vote = 0
            elif current == 0:  # Neutral → Positivo
                new_vote = 1
            else:  # Ya es positivo, no hacer nada
                return
            
            self.voteChanged.emit(self._current_file, new_vote)
            self._update_vote_display(new_vote)
        
        # Si es downvote (flecha abajo) - Solo avanza hacia negativo
        elif vote_type == -1:
            if current == 1:  # Positivo → Neutral
                new_vote = 0
            elif current == 0:  # Neutral → Negativo
                new_vote = -1
            else:  # Ya es negativo, no hacer nada
                return
            
            self.voteChanged.emit(self._current_file, new_vote)
            self._update_vote_display(new_vote)
    
    def get_current_vote(self):
        """Get current vote from display"""
        text = self.vote_status_label.text()
        if "👍" in text:
            return 1
        elif "👎" in text:
            return -1
        else:
            return 0
    
    def _update_vote_display(self, current_vote: int):
        """Update vote status display"""
        if current_vote == 1:
            self.vote_status_label.setText("👍")
            self.vote_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(76, 175, 80, 180);
                    color: white;
                    padding: 5px 15px;
                    font-size: 16px;
                    border-radius: 3px;
                }
            """)
        elif current_vote == -1:
            self.vote_status_label.setText("👎")
            self.vote_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(244, 67, 54, 180);
                    color: white;
                    padding: 5px 15px;
                    font-size: 16px;
                    border-radius: 3px;
                }
            """)
        else:
            self.vote_status_label.setText("⚪")
            self.vote_status_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(43, 43, 43, 180);
                    color: white;
                    padding: 5px 15px;
                    font-size: 16px;
                    border-radius: 3px;
                }
            """)

    def set_current_vote(self, vote: int):
        """Set current vote from external source"""
        self._update_vote_display(vote)

    # =================================================
    # Video widgets - Create/Destroy
    # =================================================

    def _create_controls(self):
        """Create persistent video controls"""
        self.play_button = QPushButton("▶")
        self.play_button.setFixedWidth(40)
        
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setTracking(True)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMaximumWidth(100)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)

        # Volume setup: 0-100 range, default 10
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(10)
        self.audio.setVolume(0.1)  # Set initial volume (10%)

        # Connect signals
        self.play_button.clicked.connect(self.toggle_play)
        self.position_slider.sliderMoved.connect(self.player.setPosition)
        self.position_slider.sliderPressed.connect(lambda: setattr(self, '_seeking', True))
        self.position_slider.sliderReleased.connect(lambda: setattr(self, '_seeking', False))
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        # Controls layout
        controls = QHBoxLayout()
        controls.setContentsMargins(5, 5, 5, 5)
        controls.addWidget(self.play_button)
        controls.addWidget(self.position_slider, 1)
        controls.addWidget(self.time_label)
        controls.addWidget(QLabel("🔊"))
        controls.addWidget(self.volume_slider)

        self.controls_widget = QWidget()
        self.controls_widget.setLayout(controls)
        self.controls_widget.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: white;
                border: none;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QLabel {
                color: white;
            }
        """)

        # Add controls to video page
        self.video_layout.addWidget(self.controls_widget)

    def _create_video_widget(self):
        """Create video widget when needed"""
        if self._video_widget is not None:
            return  # Already exists
            
        self._video_widget = QVideoWidget()
        self._video_widget.setStyleSheet("background-color: black;")
        
        # Insert at top of layout (before controls)
        self.video_layout.insertWidget(0, self._video_widget, 1)
        
        # Connect to player
        self.player.setVideoOutput(self._video_widget)

    def _destroy_video_widget(self):
        """Destroy video widget to prevent overlay issues"""
        if self._video_widget is None:
            return  # Already destroyed
        
        # Disconnect from player
        self.player.setVideoOutput(None)
        
        # Remove from layout
        self.video_layout.removeWidget(self._video_widget)
        
        # Delete widget
        self._video_widget.deleteLater()
        self._video_widget = None

    # =================================================
    # Public API
    # =================================================

    def show_file(self, path: str):
        """Display image or video file"""
        self._current_file = path
        ext = Path(path).suffix.lower()

        if ext in IMAGE_EXTENSIONS:
            self._show_image(path)
        elif ext in VIDEO_EXTENSIONS:
            self._show_video(path)

    # =================================================
    # Image handling
    # =================================================

    def _show_image(self, path: str):
        """Display an image file with smart loading"""
        # Stop player and destroy video widget
        self.player.stop()
        self._destroy_video_widget()
        
        # Usar QImageReader para control avanzado
        reader = QImageReader(path)
        
        if not reader.canRead():
            QMessageBox.warning(self, "Error", f"No se puede leer la imagen:\n{path}")
            return
        
        # Obtener tamaño original
        original_size = reader.size()
        
        # Límite razonable: 8K (7680x4320)
        max_dimension = 7680
        
        # Si la imagen es muy grande, escalarla al cargar
        if original_size.width() > max_dimension or original_size.height() > max_dimension:
            # Calcular nuevo tamaño manteniendo aspecto
            if original_size.width() > original_size.height():
                scale_factor = max_dimension / original_size.width()
            else:
                scale_factor = max_dimension / original_size.height()
            
            new_width = int(original_size.width() * scale_factor)
            new_height = int(original_size.height() * scale_factor)
            
            reader.setScaledSize(QSize(new_width, new_height))
            print(f"Imagen redimensionada de {original_size.width()}x{original_size.height()} a {new_width}x{new_height}")
        
        # Leer imagen
        image = reader.read()
        
        if image.isNull():
            error = reader.errorString()
            QMessageBox.warning(self, "Error", f"Error al cargar imagen:\n{error}")
            return
        
        pixmap = QPixmap.fromImage(image)
        
        self._current_pixmap = pixmap
        self._update_image()
        self.stack.setCurrentIndex(0)

    def resizeEvent(self, event):
        """Handle window resize for image scaling"""
        super().resizeEvent(event)
        
        # Defer image update to avoid Wayland protocol errors
        if self.stack.currentIndex() == 0 and self._current_pixmap:
            QTimer.singleShot(10, self._update_image)

    def _update_image(self):
        """Update image scaling to fit current widget size"""
        if self._current_pixmap:
            self.image_label.setPixmap(
                self._current_pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    # =================================================
    # Video handling
    # =================================================

    def _show_video(self, path: str):
        """Display a video file"""
        # Create video widget if needed
        self._create_video_widget()
        
        self.stack.setCurrentIndex(1)
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    # =================================================
    # Keyboard shortcuts
    # =================================================

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts"""
        # NAVEGACIÓN (funcionan siempre)
        if event.key() == Qt.Key_Right:
            # Siguiente archivo
            self.requestNext.emit()
            event.accept()
        elif event.key() == Qt.Key_Left:
            # Archivo anterior
            self.requestPrevious.emit()
            event.accept()
        
        # VOTACIÓN (funcionan siempre)
        elif event.key() == Qt.Key_Up:
            # Upvote
            self._vote(1)
            event.accept()
        elif event.key() == Qt.Key_Down:
            # Downvote
            self._vote(-1)
            event.accept()
        
        # CONTROLES DE VIDEO (solo cuando hay video)
        elif event.key() == Qt.Key_Space and self.stack.currentIndex() == 1:
            self.toggle_play()
            event.accept()
        elif event.key() == Qt.Key_PageUp and self.stack.currentIndex() == 1:
            # Volume up
            self.volume_slider.setValue(min(100, self.volume_slider.value() + 10))
            event.accept()
        elif event.key() == Qt.Key_PageDown and self.stack.currentIndex() == 1:
            # Volume down
            self.volume_slider.setValue(max(0, self.volume_slider.value() - 10))
            event.accept()
        else:
            super().keyPressEvent(event)

    # =================================================
    # Player controls
    # =================================================

    def toggle_play(self):
        """Toggle between play and pause"""
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_volume_changed(self, value):
        """Handle volume slider changes"""
        volume = value / 100.0
        self.audio.setVolume(volume)

    # =================================================
    # Player signal handlers
    # =================================================

    def _on_position(self, pos):
        """Update position slider when playback position changes"""
        if not self._seeking:
            self.position_slider.blockSignals(True)
            self.position_slider.setValue(pos)
            self.position_slider.blockSignals(False)
        self._update_time(pos, self._duration)

    def _on_duration(self, dur):
        """Update duration when video is loaded"""
        self._duration = dur
        self.position_slider.setRange(0, dur)

    def _on_state(self, state):
        """Update play button icon based on playback state"""
        self.play_button.setText("⏸" if state == QMediaPlayer.PlayingState else "▶")

    def _update_time(self, pos, dur):
        """Update time label with current position and duration"""
        def fmt(ms):
            s = ms // 1000
            return f"{s // 60:02d}:{s % 60:02d}"
        
        self.time_label.setText(f"{fmt(pos)} / {fmt(dur)}")

    # =================================================
    # Cleanup
    # =================================================

    def cleanup(self):
        """Clean up resources when closing"""
        self.player.stop()
        self._destroy_video_widget()