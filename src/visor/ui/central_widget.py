from PySide6.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from .sidebar_widget import SidebarWidget
from .viewer_container import ViewerContainer

class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        splitter = QSplitter(Qt.Horizontal)

        self.sidebar = SidebarWidget()
        self.viewer = ViewerContainer()

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.viewer)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)

        # Conexión clave
        self.sidebar.fileSelected.connect(self.viewer.show_file)
