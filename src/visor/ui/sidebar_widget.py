from PySide6.QtWidgets import QWidget, QVBoxLayout


class SidebarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)
