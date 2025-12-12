from PySide6.QtWidgets import QApplication
from .main_window import MainWindow
import sys


class VisorApp(QApplication):

    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = MainWindow()


    def run(self):
        self.main_window.show()
        return self.exec()




    if __name__ == "__main__":
        app = VisorApp(sys.argv)
        sys.exit(app.run())
