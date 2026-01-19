import os
import sys
import platform
from pathlib import Path

# Configuración específica por plataforma
if platform.system() == "Linux":
    # Verificar si libxcb-cursor está disponible
    xcb_cursor_available = False
    
    # Rutas comunes donde buscar la librería
    lib_paths = [
        "/usr/lib/x86_64-linux-gnu",
        "/usr/lib",
        "/usr/lib64",
        "/lib/x86_64-linux-gnu",
        "/lib",
        "/lib64"
    ]
    
    for lib_path in lib_paths:
        if Path(lib_path).exists():
            # Buscar libxcb-cursor.so*
            for file in Path(lib_path).glob("libxcb-cursor.so*"):
                xcb_cursor_available = True
                break
        if xcb_cursor_available:
            break
    
    # Solo usar X11 si la librería está disponible
    if xcb_cursor_available:
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
        print("✓ Usando X11 (xcb)")
    else:
        # Dejar que Qt use Wayland
        print("⚠ libxcb-cursor no encontrada, usando Wayland")
        # No establecer QT_QPA_PLATFORM, Qt elegirá automáticamente

from PySide6.QtWidgets import QApplication
from .main_window import MainWindow


class VisorApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        # Configuraciones multiplataforma
        self.setApplicationName("Visor Multimedia")
        self.setOrganizationName("TuNombre")
        
        # Información de depuración
        print(f"Sistema: {platform.system()}")
        print(f"Plataforma Qt: {self.platformName()}")
        
        self.main_window = MainWindow()
    
    def run(self):
        self.main_window.show()
        return self.exec()


if __name__ == "__main__":
    app = VisorApp(sys.argv)
    sys.exit(app.run())