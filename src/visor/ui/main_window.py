from PySide6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout,
    QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt
import json
from pathlib import Path

from .viewer_container import ViewerContainer
from .sidebar_widget import SidebarWidget
from .config_widget import ConfigWidget
from ..services.navigation_system import NavigationSystem


class MainWindow(QMainWindow):
    """Main window with integrated navigation system"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Multimedia Viewer with Smart Navigation")
        self.setGeometry(100, 100, 1400, 800)
        
        # Navigation system
        self.nav_system = None
        self._loaded_settings = None

        # Load saved configuration
        self._load_settings()
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup interface"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar with tabs
        sidebar_tabs = QTabWidget()
        sidebar_tabs.setMaximumWidth(400)
        
        self.sidebar = SidebarWidget()
        sidebar_tabs.addTab(self.sidebar, "Files")

        # Create temporary nav_system with saved votes
        if self._loaded_settings and 'votes' in self._loaded_settings:
            temp_nav = NavigationSystem([], max_history=100)
            temp_nav.votes = self._loaded_settings['votes'].copy()
            self.sidebar.set_navigation_system(temp_nav)
        
        self.config_widget = ConfigWidget()
        sidebar_tabs.addTab(self.config_widget, "⚙️ Configuration")
        
        # Apply loaded configuration
        if self._loaded_settings:
            if 'positive_cooldown' in self._loaded_settings:
                self.config_widget.set_config(
                    self._loaded_settings.get('positive_cooldown', 5),
                    self._loaded_settings.get('neutral_cooldown', 20),
                    self._loaded_settings.get('negative_cooldown', 0),
                    self._loaded_settings.get('max_history', 1000)
                )
        
        # Viewer
        self.viewer = ViewerContainer()
        
        # Add to splitter
        main_splitter.addWidget(sidebar_tabs)
        main_splitter.addWidget(self.viewer)
        main_splitter.setSizes([300, 1100])
        
        main_layout.addWidget(main_splitter)
        
        self.statusBar().showMessage("Ready - Add directories to begin")
    
    def _connect_signals(self):
        """Connect signals"""
        self.sidebar.fileSelected.connect(self._on_file_selected_from_list)
        self.viewer.requestNext.connect(self._next_random)
        self.viewer.requestPrevious.connect(self._go_back)
        self.viewer.voteChanged.connect(self._on_vote_changed)
        self.config_widget.configChanged.connect(self._on_config_changed)
        self.config_widget.resetPositive.connect(self._on_reset_positive)
        self.config_widget.resetNegative.connect(self._on_reset_negative)
        self.config_widget.resetAll.connect(self._on_reset_all)
        self.config_widget.historyLimitChanged.connect(self._on_history_limit_changed)
    
    def _on_file_selected_from_list(self, file_path: str):
        """File selected from list"""
        if self.nav_system is None:
            files = self.sidebar.get_all_files()
            if not files:
                return
            
            pos, neu, neg, hist = self.config_widget.get_config()
            
            # Check if sidebar already has a temporary nav_system
            if self.sidebar._nav_system is not None:
                # Reuse temporary (which already has votes)
                self.nav_system = self.sidebar._nav_system
                self.nav_system.update_file_list(files)
                self.nav_system.max_history = hist
                self.nav_system.set_positive_cooldown(pos)
                self.nav_system.set_neutral_cooldown(neu)
                self.nav_system.set_negative_cooldown(neg)
            else:
                # Create new
                self.nav_system = NavigationSystem(
                    files,
                    positive_cooldown=pos,
                    neutral_cooldown=neu,
                    negative_cooldown=neg,
                    max_history=hist
                )
                
                # Load saved votes if they exist
                if self._loaded_settings and 'votes' in self._loaded_settings:
                    self.nav_system.import_data(self._loaded_settings)
                
                # Connect sidebar with nav_system
                self.sidebar.set_navigation_system(self.nav_system)
        
        self.viewer.show_file(file_path)
        
        if self.nav_system:
            vote = self.nav_system.get_vote(file_path)
            self.viewer.set_current_vote(vote)
        
        self._update_status()
    
    def _next_random(self):
        """Next random file"""
        if not self.nav_system:
            files = self.sidebar.get_all_files()
            if not files:
                QMessageBox.warning(self, "No files", "Add directories first")
                return
            
            pos, neu, neg, hist = self.config_widget.get_config()
            
            # Check if sidebar already has a temporary nav_system
            if self.sidebar._nav_system is not None:
                # Reuse temporary (which already has votes)
                self.nav_system = self.sidebar._nav_system
                self.nav_system.update_file_list(files)
                self.nav_system.max_history = hist
                self.nav_system.set_positive_cooldown(pos)
                self.nav_system.set_neutral_cooldown(neu)
                self.nav_system.set_negative_cooldown(neg)
            else:
                # Create new
                self.nav_system = NavigationSystem(
                    files,
                    positive_cooldown=pos,
                    neutral_cooldown=neu,
                    negative_cooldown=neg,
                    max_history=hist
                )
                
                # Load saved votes if they exist
                if self._loaded_settings and 'votes' in self._loaded_settings:
                    self.nav_system.import_data(self._loaded_settings)
                
                # Connect sidebar with nav_system
                self.sidebar.set_navigation_system(self.nav_system)
        
        next_file = self.nav_system.next_random()
        
        if next_file:
            self.viewer.show_file(next_file)
            vote = self.nav_system.get_vote(next_file)
            self.viewer.set_current_vote(vote)
            self._update_status()
            
            # Preload next
            if self.nav_system.can_go_forward_in_history():
                future_pos = self.nav_system.history_position + 1
                if future_pos < len(self.nav_system.history):
                    next_to_preload = self.nav_system.history[future_pos]
                    self.viewer.preload_next(next_to_preload)
        else:
            QMessageBox.information(
                self,
                "No files available",
                "No files available.\n\nAdjust cooldown configuration."
            )
    
    def _go_back(self):
        """Go back to previous file"""
        if not self.nav_system:
            return
        
        prev_file = self.nav_system.go_back()
        
        if prev_file:
            self.viewer.show_file(prev_file)
            vote = self.nav_system.get_vote(prev_file)
            self.viewer.set_current_vote(vote)
            self._update_status()
    
    def _on_vote_changed(self, file_path: str, vote: int):
        """Handle vote change"""
        if not self.nav_system:
            return
        
        if vote == 1:
            self.nav_system.vote_positive(file_path)
        elif vote == -1:
            self.nav_system.vote_negative(file_path)
        else:
            self.nav_system.clear_vote(file_path)
        
        self._update_status()
        self._save_settings()
        self.sidebar.refresh_votes()
    
    def _on_config_changed(self, positive: int, neutral: int, negative: int):
        """Apply new configuration"""
        if self.nav_system:
            self.nav_system.set_positive_cooldown(positive)
            self.nav_system.set_neutral_cooldown(neutral)
            self.nav_system.set_negative_cooldown(negative)
            
            self.statusBar().showMessage(
                f"Configuration updated: 👍={positive}, ⚪={neutral}, 👎={negative}",
                3000
            )
        self._save_settings()
    
    def _on_history_limit_changed(self, limit: int):
        """Change history limit"""
        if self.nav_system:
            self.nav_system.set_max_history(limit)
            self.statusBar().showMessage(
                f"History limit: {limit} files",
                3000
            )
        self._save_settings()
    
    def _update_status(self):
        """Update status bar"""
        if not self.nav_system:
            return
        
        stats = self.nav_system.get_stats()
        current = self.nav_system.get_current()
        
        if current:
            file_name = Path(current).name
            vote_symbol = self.nav_system.get_vote_symbol(current)
            position = stats['history_position']
            total = stats['history_length']
            eligible = stats['eligible_now']
            
            self.statusBar().showMessage(
                f"{vote_symbol} {file_name} | "
                f"Position: {position}/{total} | "
                f"Available: {eligible}/{stats['total_files']} | "
                f"👍 {stats['positive_voted']} | "
                f"⚪ {stats['neutral_voted']} | "
                f"👎 {stats['negative_voted']}"
            )
    
    def _save_settings(self):
        """Save configuration and votes"""
        settings_path = Path.home() / ".visor_multimedia_settings.json"
        
        try:
            # Read existing data if it exists
            existing_data = {}
            if settings_path.exists():
                try:
                    with open(settings_path, 'r') as f:
                        existing_data = json.load(f)
                except:
                    pass
            
            if self.nav_system:
                # If navigation system exists, export everything
                data = self.nav_system.export_data()
            else:
                # If no system, preserve existing votes
                pos, neu, neg, hist = self.config_widget.get_config()
                data = {
                    'votes': existing_data.get('votes', {}),
                    'positive_cooldown': pos,
                    'neutral_cooldown': neu,
                    'negative_cooldown': neg,
                    'max_history': hist
                }
            
            with open(settings_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def _load_settings(self):
        """Load saved configuration"""
        settings_path = Path.home() / ".visor_multimedia_settings.json"
        
        if not settings_path.exists():
            return
        
        try:
            with open(settings_path, 'r') as f:
                data = json.load(f)
            
            # Save loaded data
            self._loaded_settings = data
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
    
    def _on_reset_positive(self):
        """Reset positive votes"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Reset all positive votes to neutral?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_positive_votes()
            self._save_settings()
            self.sidebar.refresh_votes()
            self.statusBar().showMessage("✓ Positive votes reset", 3000)

    def _on_reset_negative(self):
        """Reset negative votes"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Reset all negative votes to neutral?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_negative_votes()
            self._save_settings()
            self.sidebar.refresh_votes()
            self.statusBar().showMessage("✓ Negative votes reset", 3000)

    def _on_reset_all(self):
        """Reset ALL votes"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.warning(
            self,
            "⚠️ Confirm Action",
            "Reset ALL votes to neutral?\n\nThis action CANNOT be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_votes()
            self._save_settings()
            self.sidebar.refresh_votes()
            self.statusBar().showMessage("✓ All votes reset", 3000)

    def closeEvent(self, event):
        """Save on close"""
        self._save_settings()
        
        if hasattr(self, 'sidebar'):
            self.sidebar.cleanup()
        if hasattr(self, 'viewer'):
            self.viewer.cleanup()
        
        event.accept()