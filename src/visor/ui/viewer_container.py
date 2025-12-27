from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
import os

class ViewerContainer(QWidget):

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov"}

    MAX_IMAGE_SIZE_MB = 200  # política del visor (soft limit)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.label = QLabel("Selecciona un archivo multimedia")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: black; color: white;")

        layout.addWidget(self.label)

    def show_file(self, path: str):
        if not os.path.isfile(path):
            return

        _, ext = os.path.splitext(path)
        ext = ext.lower()

        if ext in self.IMAGE_EXTENSIONS:
            self._show_image(path)
        elif ext in self.VIDEO_EXTENSIONS:
            self._show_placeholder("Vídeo (pendiente de implementar)")
        else:
            self._show_placeholder("Formato no soportado")

    def _show_image(self, path: str):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb > self.MAX_IMAGE_SIZE_MB:
            self._show_placeholder("Imagen demasiado grande")
            return

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._show_placeholder("No se pudo cargar la imagen")
            return

        self.label.setPixmap(
            pixmap.scaled(
                self.label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def _show_placeholder(self, text: str):
        self.label.setPixmap(QPixmap())
        self.label.setText(text)

    def resizeEvent(self, event):
        pixmap = self.label.pixmap()
        if pixmap:
            self.label.setPixmap(
                pixmap.scaled(
                    self.label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )
        super().resizeEvent(event)
