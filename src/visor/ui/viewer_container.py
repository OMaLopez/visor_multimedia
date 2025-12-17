from PySide6.QtWidgets import QWidget, QVBoxLayout


class ViewerContainer(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
