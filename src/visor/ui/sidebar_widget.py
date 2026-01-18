from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QFileDialog, QLabel,
    QProgressBar, QMenu, QStyle
)
from PySide6.QtCore import Qt, Signal, QThread, QMutex, QMutexLocker
from PySide6.QtGui import QAction


# Extensiones soportadas
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


class FileScanner(QThread):
    """Thread para escanear directorios sin bloquear la UI"""
    
    # Señales
    fileFound = Signal(str)  # Emite cada archivo encontrado
    progress = Signal(int, int)  # (current, total)
    finished = Signal(int)  # Total de archivos encontrados
    
    def __init__(self, directories):
        super().__init__()
        self.directories = directories
        self._is_cancelled = False
        self._mutex = QMutex()
    
    def cancel(self):
        """Cancelar el escaneo"""
        with QMutexLocker(self._mutex):
            self._is_cancelled = True
    
    def run(self):
        """Escanear directorios de forma recursiva"""
        total_files = 0
        processed = 0
        
        # Primera pasada: contar archivos (opcional, para la barra de progreso)
        # Comentada para mayor velocidad en directorios enormes
        
        # Segunda pasada: emitir archivos
        for directory in self.directories:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                continue
            
            try:
                # Usar rglob para búsqueda recursiva
                for file_path in path.rglob("*"):
                    # Verificar cancelación
                    with QMutexLocker(self._mutex):
                        if self._is_cancelled:
                            return
                    
                    # Solo archivos con extensiones válidas
                    if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
                        self.fileFound.emit(str(file_path))
                        total_files += 1
                        processed += 1
                        
                        # Emitir progreso cada 100 archivos
                        if processed % 100 == 0:
                            self.progress.emit(processed, processed)
                
            except PermissionError:
                # Ignorar directorios sin permisos
                continue
        
        self.finished.emit(total_files)


class SidebarWidget(QWidget):
    """Sidebar para seleccionar directorios y mostrar archivos multimedia"""
    
    fileSelected = Signal(str)  # Archivo seleccionado
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._scanner_thread = None
        self._selected_directories = []
        self._all_files = []  # Lista completa de archivos
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configurar interfaz"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # --- Botones de directorios ---
        btn_layout = QHBoxLayout()
        
        self.add_dir_btn = QPushButton("📁 Añadir")
        self.add_dir_btn.setToolTip("Añadir directorio(s)")
        self.add_dir_btn.clicked.connect(self._add_directories)
        
        self.clear_btn = QPushButton("🗑️ Limpiar")
        self.clear_btn.setToolTip("Limpiar lista")
        self.clear_btn.clicked.connect(self._clear_all)
        
        btn_layout.addWidget(self.add_dir_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        # --- Info label ---
        self.info_label = QLabel("Sin archivos")
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # --- Barra de progreso ---
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # --- Lista de archivos ---
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemClicked.connect(self._on_item_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.file_list)
        
        # Configurar tamaño
        self.setMinimumWidth(250)
        
    # ========================================
    # Gestión de directorios
    # ========================================
    
    def _add_directories(self):
        """Añadir uno o varios directorios"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        # Permitir selección múltiple
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        # Hack para permitir selección múltiple de directorios
        file_view = dialog.findChild(QListWidget)
        if file_view:
            file_view.setSelectionMode(QListWidget.MultiSelection)
        
        if dialog.exec():
            directories = dialog.selectedFiles()
            if directories:
                self._selected_directories.extend(directories)
                self._scan_directories(directories)
    
    def _scan_directories(self, directories):
        """Escanear directorios en segundo plano"""
        # Cancelar escaneo anterior si existe
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()
        
        # Mostrar progreso
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Modo indeterminado
        self.info_label.setText("Escaneando...")
        
        # Crear y configurar thread
        self._scanner_thread = FileScanner(directories)
        self._scanner_thread.fileFound.connect(self._add_file_to_list)
        self._scanner_thread.progress.connect(self._update_progress)
        self._scanner_thread.finished.connect(self._scan_finished)
        self._scanner_thread.start()
    
    def _add_file_to_list(self, file_path):
        """Añadir archivo a la lista (llamado por el thread)"""
        self._all_files.append(file_path)
        
        # Añadir a la UI
        path = Path(file_path)
        item = QListWidgetItem(path.name)
        item.setData(Qt.UserRole, file_path)
        
        # Icono según tipo usando QStyle
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            icon = self.style().standardIcon(QStyle.SP_FileDialogContentsView)
        else:
            icon = self.style().standardIcon(QStyle.SP_MediaPlay)
        
        item.setIcon(icon)
        self.file_list.addItem(item)
        
        # Actualizar contador
        self.info_label.setText(f"{len(self._all_files)} archivos")
    
    def _update_progress(self, current, total):
        """Actualizar barra de progreso"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
    
    def _scan_finished(self, total):
        """Escaneo completado"""
        self.progress_bar.hide()
        self.info_label.setText(f"{total} archivos encontrados")
        
        if total == 0:
            self.info_label.setText("No se encontraron archivos multimedia")
    
    def _clear_all(self):
        """Limpiar lista y directorios"""
        # Cancelar escaneo si está en curso
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()
        
        self._selected_directories.clear()
        self._all_files.clear()
        self.file_list.clear()
        self.info_label.setText("Sin archivos")
        self.progress_bar.hide()
    
    # ========================================
    # Selección de archivos
    # ========================================
    
    def _on_item_clicked(self, item):
        """Archivo seleccionado en la lista"""
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.fileSelected.emit(file_path)
    
    def _show_context_menu(self, position):
        """Menú contextual en la lista"""
        item = self.file_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Acción: Abrir en explorador
        open_action = QAction("Abrir ubicación", self)
        open_action.triggered.connect(lambda: self._open_file_location(item))
        menu.addAction(open_action)
        
        # Acción: Copiar ruta
        copy_action = QAction("Copiar ruta", self)
        copy_action.triggered.connect(lambda: self._copy_path(item))
        menu.addAction(copy_action)
        
        menu.exec(self.file_list.mapToGlobal(position))
    
    def _open_file_location(self, item):
        """Abrir ubicación del archivo en el explorador"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        file_path = Path(item.data(Qt.UserRole))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))
    
    def _copy_path(self, item):
        """Copiar ruta al portapapeles"""
        from PySide6.QtWidgets import QApplication
        
        file_path = item.data(Qt.UserRole)
        QApplication.clipboard().setText(file_path)
    
    # ========================================
    # API pública
    # ========================================
    
    def get_all_files(self):
        """Obtener lista completa de archivos"""
        return self._all_files.copy()
    
    def get_current_index(self):
        """Obtener índice del archivo actual"""
        return self.file_list.currentRow()
    
    def select_next(self):
        """Seleccionar siguiente archivo"""
        current = self.file_list.currentRow()
        if current < self.file_list.count() - 1:
            self.file_list.setCurrentRow(current + 1)
            item = self.file_list.currentItem()
            if item:
                self.fileSelected.emit(item.data(Qt.UserRole))
    
    def select_previous(self):
        """Seleccionar archivo anterior"""
        current = self.file_list.currentRow()
        if current > 0:
            self.file_list.setCurrentRow(current - 1)
            item = self.file_list.currentItem()
            if item:
                self.fileSelected.emit(item.data(Qt.UserRole))
    
    def cleanup(self):
        """Limpiar recursos"""
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()