from PySide6.QtWidgets import QMainWindow
from .central_widget import CentralWidget

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor Multimedia")
        self.resize(800, 600)


        central = CentralWidget()
        self.setCentralWidget(central)