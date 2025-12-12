from PySide6.QtWidgets import QMainWindow, QWidget, QLabel, QVBoxLayout


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visor Multimedia")
        self.resize(800, 600)


        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Ventana base del visor multimedia"))
        self.setCentralWidget(central)