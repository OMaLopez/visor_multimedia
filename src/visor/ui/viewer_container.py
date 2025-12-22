from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ViewerContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Viewer"))
        self.setLayout(layout)

        # Depuración visual
        self.setMinimumWidth(100)
        self.setStyleSheet("background-color: lightgreen;")
