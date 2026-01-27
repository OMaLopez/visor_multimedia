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
    """Ventana principal con sistema de navegación integrado"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Visor Multimedia con Navegación Inteligente")
        self.setGeometry(100, 100, 1400, 800)
        
        # Sistema de navegación
        self.nav_system = None
        self._loaded_settings = None

        # Intentar cargar configuración guardada
        self._load_settings()
        
        self._setup_ui()
        self._connect_signals()
        
        
    
    def _setup_ui(self):
        """Configurar interfaz"""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Sidebar con tabs
        sidebar_tabs = QTabWidget()
        sidebar_tabs.setMaximumWidth(400)
        

        self.sidebar = SidebarWidget()
        sidebar_tabs.addTab(self.sidebar, "📁 Archivos")

        # CREAR NAV_SYSTEM TEMPORAL CON VOTOS GUARDADOS
        if self._loaded_settings and 'votes' in self._loaded_settings:
            from ..services.navigation_system import NavigationSystem
            temp_nav = NavigationSystem([], max_history=100)
            temp_nav.votes = self._loaded_settings['votes'].copy()
            self.sidebar.set_navigation_system(temp_nav)

        
        self.config_widget = ConfigWidget()
        sidebar_tabs.addTab(self.config_widget, "⚙️ Configuración")
        
        # Visor
        self.viewer = ViewerContainer()
        
        # Añadir al splitter
        main_splitter.addWidget(sidebar_tabs)
        main_splitter.addWidget(self.viewer)
        main_splitter.setSizes([300, 1100])
        
        main_layout.addWidget(main_splitter)
        
        self.statusBar().showMessage("Listo - Añade directorios para comenzar")
    
    def _connect_signals(self):
        """Conectar señales"""
        self.sidebar.fileSelected.connect(self._on_file_selected_from_list)
        self.viewer.requestNext.connect(self._next_random)
        self.viewer.requestPrevious.connect(self._go_back)
        self.viewer.voteChanged.connect(self._on_vote_changed)
        self.config_widget.configChanged.connect(self._on_config_changed)
        self.config_widget.resetPositive.connect(self._on_reset_positive)
        self.config_widget.resetNegative.connect(self._on_reset_negative)
        self.config_widget.resetAll.connect(self._on_reset_all)
        # Config: límite de historial
        self.config_widget.historyLimitChanged.connect(self._on_history_limit_changed)
    
    def _on_file_selected_from_list(self, file_path: str):
        """Archivo seleccionado desde la lista"""
        if self.nav_system is None:
            files = self.sidebar.get_all_files()
            if not files:
                return
            
            pos, neu, neg, hist = self.config_widget.get_config()
            self.nav_system = NavigationSystem(
                files,
                positive_cooldown=pos,
                neutral_cooldown=neu,
                negative_cooldown=neg,
                max_history=hist
            )
            
            # Cargar votos guardados si existen
            if self._loaded_settings and 'votes' in self._loaded_settings:
                self.nav_system.import_data(self._loaded_settings)
            # CONECTAR SIDEBAR CON NAV_SYSTEM
            self.sidebar.set_navigation_system(self.nav_system)
        
        self.viewer.show_file(file_path)
        
        if self.nav_system:
            vote = self.nav_system.get_vote(file_path)
            self.viewer.set_current_vote(vote)
        
        self._update_status()
    
    def _next_random(self):
        """Siguiente archivo aleatorio"""
        if not self.nav_system:
            files = self.sidebar.get_all_files()
            if not files:
                QMessageBox.warning(self, "Sin archivos", "Añade directorios primero")
                return
            
            pos, neu, neg, hist = self.config_widget.get_config()
            self.nav_system = NavigationSystem(
                files,
                positive_cooldown=pos,
                neutral_cooldown=neu,
                negative_cooldown=neg,
                max_history=hist
            )
            if self._loaded_settings and 'votes' in self._loaded_settings:
                self.nav_system.import_data(self._loaded_settings)

            # CONECTAR SIDEBAR CON NAV_SYSTEM ← AÑADIR
            self.sidebar.set_navigation_system(self.nav_system)
            
            if self._loaded_settings and 'votes' in self._loaded_settings:
                self.nav_system.import_data(self._loaded_settings)
        
        next_file = self.nav_system.next_random()
        
        if next_file:
            self.viewer.show_file(next_file)
            vote = self.nav_system.get_vote(next_file)
            self.viewer.set_current_vote(vote)
            self._update_status()
        
            if self.nav_system.can_go_forward_in_history():
                # Hay futuro, pre-cargar el siguiente del historial
                future_pos = self.nav_system.history_position + 1
                if future_pos < len(self.nav_system.history):
                    next_to_preload = self.nav_system.history[future_pos]
                    self.viewer.preload_next(next_to_preload)

        else:
            QMessageBox.information(
                self,
                "Sin archivos disponibles",
                "No hay archivos disponibles.\n\nAjusta la configuración de cooldowns."
            )
    
    def _go_back(self):
        """Volver al archivo anterior"""
        if not self.nav_system:
            return
        
        prev_file = self.nav_system.go_back()
        
        if prev_file:
            self.viewer.show_file(prev_file)
            vote = self.nav_system.get_vote(prev_file)
            self.viewer.set_current_vote(vote)
            self._update_status()
    
    def _on_vote_changed(self, file_path: str, vote: int):
        """Manejar cambio de voto"""
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
        """Aplicar nueva configuración"""
        if self.nav_system:
            self.nav_system.set_positive_cooldown(positive)
            self.nav_system.set_neutral_cooldown(neutral)
            self.nav_system.set_negative_cooldown(negative)
            
            self.statusBar().showMessage(
                f"Configuración actualizada: 👍={positive}, ⚪={neutral}, 👎={negative}",
                3000
            )
        self._save_settings()
    def _on_history_limit_changed(self, limit: int):
        """Cambiar límite de historial"""
        if self.nav_system:
            self.nav_system.set_max_history(limit)
            self.statusBar().showMessage(
                f"Límite de historial: {limit} archivos",
                3000
            )
        self._save_settings()
    
    def _update_status(self):
        """Actualizar barra de estado"""
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
                f"Posición: {position}/{total} | "
                f"Disponibles: {eligible}/{stats['total_files']} | "
                f"👍 {stats['positive_voted']} | "
                f"⚪ {stats['neutral_voted']} | "
                f"👎 {stats['negative_voted']}"
            )
    
    def _save_settings(self):
        """Guardar configuración y votos"""
        settings_path = Path.home() / ".visor_multimedia_settings.json"
        
        try:
            # Leer datos existentes si existen
            existing_data = {}
            if settings_path.exists():
                try:
                    with open(settings_path, 'r') as f:
                        existing_data = json.load(f)
                except:
                    pass  # Si hay error leyendo, usar vacío
            
            if self.nav_system:
                # Si hay sistema de navegación, exportar todo
                data = self.nav_system.export_data()
            else:
                # Si no hay sistema, solo actualizar configuración
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
            print(f"Error guardando configuración: {e}")
    
    def _load_settings(self):
        """Cargar configuración guardada"""
        settings_path = Path.home() / ".visor_multimedia_settings.json"
        
        if not settings_path.exists():
            return
        
        try:
            with open(settings_path, 'r') as f:
                data = json.load(f)
            
            if 'positive_cooldown' in data:
                self.config_widget.set_config(
                    data.get('positive_cooldown', 5),
                    data.get('neutral_cooldown', 20),
                    data.get('negative_cooldown', 0),
                    data.get('max_history', 1000)
                )
            if 'max_history' in data:
                self.config_widget.set_history_limit(data['max_history'])
            
            self._loaded_settings = data
            
        except Exception as e:
            print(f"Error cargando configuración: {e}")
    
    def _on_reset_positive(self):
        """Resetear votos positivos"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Resetear todos los votos positivos a neutral?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_positive_votes()
            self._save_settings()
            self.statusBar().showMessage("✓ Votos positivos reseteados", 3000)

    def _on_reset_negative(self):
        """Resetear votos negativos"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar",
            "¿Resetear todos los votos negativos a neutral?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_negative_votes()
            self._save_settings()
            self.statusBar().showMessage("✓ Votos negativos reseteados", 3000)

    def _on_reset_all(self):
        """Resetear TODOS los votos"""
        if not self.nav_system:
            return
        
        reply = QMessageBox.warning(
            self,
            "⚠️ Confirmar Acción",
            "¿Resetear TODOS los votos a neutral?\n\nEsta acción NO se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.nav_system.reset_votes()
            self._save_settings()
            self.statusBar().showMessage("✓ Todos los votos reseteados", 3000)

    def closeEvent(self, event):
        """Guardar al cerrar"""
        self._save_settings()
        
        if hasattr(self, 'sidebar'):
            self.sidebar.cleanup()
        if hasattr(self, 'viewer'):
            self.viewer.cleanup()
        
        event.accept()