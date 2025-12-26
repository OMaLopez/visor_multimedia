from PySide6.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PySide6.QtCore import Qt

from .sidebar_widget import SidebarWidget
from .viewer_container import ViewerContainer

class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        splitter = QSplitter(Qt.Horizontal)

        sidebar = SidebarWidget()
        viewer = ViewerContainer()

        splitter.addWidget(sidebar)
        splitter.addWidget(viewer)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)
        self.setLayout(layout)
        