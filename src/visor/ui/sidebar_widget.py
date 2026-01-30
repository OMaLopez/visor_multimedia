from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QFileDialog, QLabel,
    QProgressBar, QMenu
)
from PySide6.QtCore import Qt, Signal, QThread, QMutex, QMutexLocker
from PySide6.QtGui import QAction, QColor


# Supported extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".webm", ".mov"}
ALL_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS


class FileScanner(QThread):
    """Thread to scan directories without blocking UI"""
    
    # Signals
    fileFound = Signal(str)  # Emits each file found
    progress = Signal(int, int)  # (current, total)
    finished = Signal(int)  # Total files found
    
    def __init__(self, directories):
        super().__init__()
        self.directories = directories
        self._is_cancelled = False
        self._mutex = QMutex()
    
    def cancel(self):
        """Cancel scanning"""
        with QMutexLocker(self._mutex):
            self._is_cancelled = True
    
    def run(self):
        """Scan directories recursively"""
        total_files = 0
        processed = 0
        
        # First pass: count files (optional, for progress bar)
        # Commented out for faster speed on huge directories
        
        # Second pass: emit files
        for directory in self.directories:
            path = Path(directory)
            if not path.exists() or not path.is_dir():
                continue
            
            try:
                # Use rglob for recursive search
                for file_path in path.rglob("*"):
                    # Check cancellation
                    with QMutexLocker(self._mutex):
                        if self._is_cancelled:
                            return
                    
                    # Only files with valid extensions
                    if file_path.is_file() and file_path.suffix.lower() in ALL_EXTENSIONS:
                        self.fileFound.emit(str(file_path))
                        total_files += 1
                        processed += 1
                        
                        # Emit progress every 100 files
                        if processed % 100 == 0:
                            self.progress.emit(processed, processed)
                
            except PermissionError:
                # Ignore directories without permissions
                continue
        
        self.finished.emit(total_files)


class SidebarWidget(QWidget):
    """Sidebar to select directories and display multimedia files"""
    
    fileSelected = Signal(str)  # File selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._scanner_thread = None
        self._selected_directories = []
        self._all_files = []
        self._nav_system = None  # Navigation system for votes
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # --- Directory buttons ---
        btn_layout = QHBoxLayout()
        
        self.add_dir_btn = QPushButton("Add")
        self.add_dir_btn.setToolTip("Add directory(s)")
        self.add_dir_btn.clicked.connect(self._add_directories)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setToolTip("Clear list")
        self.clear_btn.clicked.connect(self._clear_all)
        
        btn_layout.addWidget(self.add_dir_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        # --- Info label ---
        self.info_label = QLabel("No files")
        self.info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.info_label)
        
        # --- Progress bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # --- File list ---
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        self.file_list.itemClicked.connect(self._on_item_clicked)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.file_list)
        
        # Configure size
        self.setMinimumWidth(250)
        
    # ========================================
    # Directory management
    # ========================================
    
    def _add_directories(self):
        """Add one or more directories"""
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        # Allow multiple selection
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        # Hack to allow multiple directory selection
        file_view = dialog.findChild(QListWidget)
        if file_view:
            file_view.setSelectionMode(QListWidget.MultiSelection)
        
        if dialog.exec():
            directories = dialog.selectedFiles()
            if directories:
                self._selected_directories.extend(directories)
                self._scan_directories(directories)
    
    def _scan_directories(self, directories):
        """Scan directories in background"""
        # Cancel previous scan if exists
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()
        
        # Show progress
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.info_label.setText("Scanning...")
        
        # Create and configure thread
        self._scanner_thread = FileScanner(directories)
        self._scanner_thread.fileFound.connect(self._add_file_to_list)
        self._scanner_thread.progress.connect(self._update_progress)
        self._scanner_thread.finished.connect(self._scan_finished)
        self._scanner_thread.start()
    
    def _add_file_to_list(self, file_path):
        """Add file to list (called by thread)"""
        self._all_files.append(file_path)
        
        # Add to UI
        path = Path(file_path)
        
        item = QListWidgetItem(path.name)
        item.setData(Qt.UserRole, file_path)
        
        # Apply background color if navigation system exists
        if self._nav_system:
            vote = self._nav_system.get_vote(file_path)
            if vote == 1:  # Positive
                item.setBackground(QColor(76, 175, 80, 100))  # Light green
            elif vote == -1:  # Negative
                item.setBackground(QColor(244, 67, 54, 100))  # Light red
        
        self.file_list.addItem(item)
        
        # Update counter
        self.info_label.setText(f"{len(self._all_files)} files")
    
    def _update_progress(self, current, total):
        """Update progress bar"""
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
    
    def _scan_finished(self, total):
        """Scan completed"""
        self.progress_bar.hide()
        self.info_label.setText(f"{total} files found")
        
        if total == 0:
            self.info_label.setText("No multimedia files found")
        
        # Update navigation system with new file list
        if self._nav_system:
            self._nav_system.update_file_list(self._all_files)
            self.refresh_votes()
    
    def _clear_all(self):
        """Clear list and directories"""
        # Cancel scan if in progress
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()
        
        self._selected_directories.clear()
        self._all_files.clear()
        self.file_list.clear()
        self.info_label.setText("No files")
        self.progress_bar.hide()
        
        # Update navigation system with empty list
        if self._nav_system:
            self._nav_system.update_file_list([])
            self._nav_system.reset_history()
    
    # ========================================
    # File selection
    # ========================================
    
    def _on_item_clicked(self, item):
        """File selected in list"""
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.fileSelected.emit(file_path)
    
    def _show_context_menu(self, position):
        """Context menu in list"""
        item = self.file_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu(self)
        
        # Action: Open in file manager
        open_action = QAction("Open location", self)
        open_action.triggered.connect(lambda: self._open_file_location(item))
        menu.addAction(open_action)
        
        # Action: Copy path
        copy_action = QAction("Copy path", self)
        copy_action.triggered.connect(lambda: self._copy_path(item))
        menu.addAction(copy_action)
        
        menu.exec(self.file_list.mapToGlobal(position))
    
    def _open_file_location(self, item):
        """Open file location in file manager"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        file_path = Path(item.data(Qt.UserRole))
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))
    
    def _copy_path(self, item):
        """Copy path to clipboard"""
        from PySide6.QtWidgets import QApplication
        
        file_path = item.data(Qt.UserRole)
        QApplication.clipboard().setText(file_path)
    
    # ========================================
    # Voting system
    # ========================================
    
    def set_navigation_system(self, nav_system):
        """Set navigation system to display votes"""
        self._nav_system = nav_system
        self.refresh_votes()
    
    def refresh_votes(self):
        """Refresh vote colors in list"""
        if not self._nav_system:
            return
        
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            file_path = item.data(Qt.UserRole)
            
            if file_path:
                vote = self._nav_system.get_vote(file_path)
                
                # Apply background color based on vote
                if vote == 1:  # Positive
                    item.setBackground(QColor(76, 175, 80, 100))  # Light green
                elif vote == -1:  # Negative
                    item.setBackground(QColor(244, 67, 54, 100))  # Light red
                else:  # Neutral
                    item.setBackground(QColor(0, 0, 0, 0))  # Transparent
    
    # ========================================
    # Public API
    # ========================================
    
    def get_all_files(self):
        """Get complete list of files"""
        return self._all_files.copy()
    
    def get_current_index(self):
        """Get current file index"""
        return self.file_list.currentRow()
    
    def select_next(self):
        """Select next file"""
        current = self.file_list.currentRow()
        if current < self.file_list.count() - 1:
            self.file_list.setCurrentRow(current + 1)
            item = self.file_list.currentItem()
            if item:
                self.fileSelected.emit(item.data(Qt.UserRole))
    
    def select_previous(self):
        """Select previous file"""
        current = self.file_list.currentRow()
        if current > 0:
            self.file_list.setCurrentRow(current - 1)
            item = self.file_list.currentItem()
            if item:
                self.fileSelected.emit(item.data(Qt.UserRole))
    
    def cleanup(self):
        """Clean up resources"""
        if self._scanner_thread and self._scanner_thread.isRunning():
            self._scanner_thread.cancel()
            self._scanner_thread.wait()