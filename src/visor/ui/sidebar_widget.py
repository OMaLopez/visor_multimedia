from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SidebarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Sidebar"))
        self.setLayout(layout)

        # Depuración visual
        self.setMinimumWidth(150)
        self.setStyleSheet("background-color: darkblue;")
