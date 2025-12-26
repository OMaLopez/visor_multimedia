from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel
from PySide6.QtCore import QDir, Signal

class SidebarWidget(QWidget):
    # Señal pública: emite la ruta seleccionada
    fileSelected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Modelo del sistema de archivos
        self.model = QFileSystemModel(self)
        self.model.setRootPath(QDir.homePath())
        self.model.setNameFilters([
            "*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif",
            "*.mp4", "*.mkv", "*.avi", "*.mov"
        ])
        self.model.setNameFilterDisables(False)

        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)


        # Vista en árbol
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.homePath()))
        self.tree.setHeaderHidden(True)

        layout.addWidget(self.tree)

        self.setMinimumWidth(200)

        # Conectar selección
        self.tree.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

    def _on_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            return

        index = indexes[0]
        path = self.model.filePath(index)

        # Emitir señal
        self.fileSelected.emit(path)
