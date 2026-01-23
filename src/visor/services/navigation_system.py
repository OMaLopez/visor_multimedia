import random
from typing import List, Optional, Dict
from collections import deque


class NavigationSystem:
    """
    Sistema de navegación con votos y cooldowns configurables
    
    Votos: +1 (positivo), 0 (neutral), -1 (negativo)
    Cooldowns: Configuración global por categoría de voto
    """
    
    def __init__(
        self, 
        file_list: List[str],
        positive_cooldown: int = 5,   # Cooldown para archivos con voto positivo
        neutral_cooldown: int = 20,   # Cooldown para archivos sin voto
        negative_cooldown: int = 0,   # Cooldown para archivos con voto negativo (0 = bloqueados)
        max_history: int = 1000
    ):
        """
        Args:
            file_list: Lista de archivos
            positive_cooldown: Archivos antes de repetir los votados positivamente
            neutral_cooldown: Archivos antes de repetir los sin voto
            negative_cooldown: Archivos antes de repetir los negativos (0 = nunca)
            max_history: Máximo de archivos en historial
        """
        self.all_files = file_list.copy()
        self.max_history = max_history
        
        # Configuración de cooldowns por categoría
        self.positive_cooldown = positive_cooldown
        self.neutral_cooldown = neutral_cooldown
        self.negative_cooldown = negative_cooldown
        
        # Votos: {file_path: vote}
        # vote: 1 (positivo), 0 (neutral - sin voto), -1 (negativo)
        self.votes: Dict[str, int] = {}
        
        # Historial de navegación
        self.history: List[str] = []
        self.history_position = -1
        
        # Caches de archivos recientes por categoría
        self.recent_positive = deque(maxlen=positive_cooldown)
        self.recent_neutral = deque(maxlen=neutral_cooldown)
        self.recent_negative = deque(maxlen=negative_cooldown if negative_cooldown > 0 else 1)
    
    # ========================================
    # Votos
    # ========================================
    
    def vote_positive(self, file_path: str):
        """Votar positivo (👍)"""
        self.votes[file_path] = 1
    
    def vote_negative(self, file_path: str):
        """Votar negativo (👎)"""
        self.votes[file_path] = -1
    
    def clear_vote(self, file_path: str):
        """Quitar voto (vuelve a neutral ⚪)"""
        if file_path in self.votes:
            del self.votes[file_path]
    
    def get_vote(self, file_path: str) -> int:
        """Obtener voto: 1, 0, o -1"""
        return self.votes.get(file_path, 0)
    
    def toggle_vote(self, file_path: str, vote_type: int):
        """
        Toggle de voto
        
        Args:
            vote_type: 1 (positivo) o -1 (negativo)
        """
        current = self.get_vote(file_path)
        if current == vote_type:
            self.clear_vote(file_path)  # Si ya tiene ese voto, quitarlo
        else:
            self.votes[file_path] = vote_type
    
    def get_vote_symbol(self, file_path: str) -> str:
        """Obtener símbolo del voto"""
        vote = self.get_vote(file_path)
        return "👍" if vote == 1 else "👎" if vote == -1 else "⚪"
    
    # ========================================
    # Configuración de Cooldowns
    # ========================================
    
    def set_positive_cooldown(self, cooldown: int):
        """Configurar cooldown para positivos"""
        self.positive_cooldown = max(0, cooldown)
        self._resize_deque(self.recent_positive, self.positive_cooldown)
    
    def set_neutral_cooldown(self, cooldown: int):
        """Configurar cooldown para neutrales"""
        self.neutral_cooldown = max(0, cooldown)
        self._resize_deque(self.recent_neutral, self.neutral_cooldown)
    
    def set_negative_cooldown(self, cooldown: int):
        """
        Configurar cooldown para negativos
        0 = bloqueados permanentemente
        >0 = se repiten después de N archivos
        """
        self.negative_cooldown = max(0, cooldown)
        maxlen = self.negative_cooldown if self.negative_cooldown > 0 else 1
        self._resize_deque(self.recent_negative, maxlen)
    
    def get_cooldown_for_file(self, file_path: str) -> int:
        """Obtener cooldown efectivo para un archivo"""
        vote = self.get_vote(file_path)
        if vote == 1:
            return self.positive_cooldown
        elif vote == -1:
            return self.negative_cooldown
        else:
            return self.neutral_cooldown
    
    def _resize_deque(self, dq: deque, new_size: int):
        """Redimensionar deque preservando elementos"""
        if new_size <= 0:
            new_size = 1
        items = list(dq)
        dq.clear()
        dq.maxlen = new_size
        dq.extend(items[-new_size:] if len(items) > new_size else items)
    
    # ========================================
    # Navegación
    # ========================================
    
    def get_current(self) -> Optional[str]:
        """Obtener archivo actual"""
        if 0 <= self.history_position < len(self.history):
            return self.history[self.history_position]
        return None
    
    def can_go_back(self) -> bool:
        """¿Se puede volver atrás?"""
        return self.history_position > 0
    
    def can_go_forward_in_history(self) -> bool:
        """¿Se puede avanzar en el historial?"""
        return self.history_position < len(self.history) - 1
    
    def go_back(self) -> Optional[str]:
        """Volver al archivo anterior"""
        if self.can_go_back():
            self.history_position -= 1
            return self.get_current()
        return None
    
    def go_forward_in_history(self) -> Optional[str]:
        """Avanzar en el historial"""
        if self.can_go_forward_in_history():
            self.history_position += 1
            return self.get_current()
        return None
    
    def next_random(self) -> Optional[str]:
        """Obtener siguiente archivo aleatorio"""
        candidates = self._get_eligible_files()
        
        if not candidates:
            # Resetear caches y reintentar
            self.recent_positive.clear()
            self.recent_neutral.clear()
            self.recent_negative.clear()
            candidates = self._get_eligible_files()
            
            if not candidates:
                return None
        
        # Selección aleatoria
        next_file = random.choice(candidates)
        
        # Actualizar historial
        if self.history_position < len(self.history) - 1:
            self.history = self.history[:self.history_position + 1]
        
        self.history.append(next_file)
        self.history_position = len(self.history) - 1
        
        # Limitar tamaño
        if len(self.history) > self.max_history:
            overflow = len(self.history) - self.max_history
            self.history = self.history[overflow:]
            self.history_position -= overflow
        
        # Añadir a cache correspondiente
        vote = self.get_vote(next_file)
        if vote == 1 and self.positive_cooldown > 0:
            self.recent_positive.append(next_file)
        elif vote == -1 and self.negative_cooldown > 0:
            self.recent_negative.append(next_file)
        elif vote == 0 and self.neutral_cooldown > 0:
            self.recent_neutral.append(next_file)
        
        return next_file
    
    def _get_eligible_files(self) -> List[str]:
        """Obtener archivos que pueden mostrarse"""
        eligible = []
        
        for file_path in self.all_files:
            vote = self.get_vote(file_path)
            
            # Negativos
            if vote == -1:
                if self.negative_cooldown == 0:
                    continue  # Bloqueados permanentemente
                if file_path in self.recent_negative:
                    continue  # En cooldown
            
            # Positivos
            elif vote == 1:
                if self.positive_cooldown > 0 and file_path in self.recent_positive:
                    continue  # En cooldown
            
            # Neutrales
            else:
                if self.neutral_cooldown > 0 and file_path in self.recent_neutral:
                    continue  # En cooldown
            
            eligible.append(file_path)
        
        return eligible
    
    # ========================================
    # Gestión
    # ========================================
    
    def update_file_list(self, new_file_list: List[str]):
        """Actualizar lista de archivos"""
        self.all_files = new_file_list.copy()
    
    # ========================================
    # Estadísticas
    # ========================================
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas"""
        positive = sum(1 for v in self.votes.values() if v == 1)
        negative = sum(1 for v in self.votes.values() if v == -1)
        neutral = len(self.all_files) - positive - negative
        
        eligible = len(self._get_eligible_files())
        
        # Contadores en cooldown
        in_cooldown_pos = len([f for f in self.all_files if self.get_vote(f) == 1 and f in self.recent_positive])
        in_cooldown_neg = len([f for f in self.all_files if self.get_vote(f) == -1 and f in self.recent_negative])
        in_cooldown_neu = len([f for f in self.all_files if self.get_vote(f) == 0 and f in self.recent_neutral])
        
        return {
            'total_files': len(self.all_files),
            'positive_voted': positive,
            'neutral_voted': neutral,
            'negative_voted': negative,
            'eligible_now': eligible,
            'positive_cooldown': self.positive_cooldown,
            'neutral_cooldown': self.neutral_cooldown,
            'negative_cooldown': self.negative_cooldown,
            'in_cooldown': {
                'positive': in_cooldown_pos,
                'neutral': in_cooldown_neu,
                'negative': in_cooldown_neg
            },
            'history_length': len(self.history),
            'history_position': self.history_position + 1 if self.history_position >= 0 else 0
        }
    
    def get_file_info(self, file_path: str) -> Dict:
        """Información de un archivo"""
        vote = self.get_vote(file_path)
        cooldown = self.get_cooldown_for_file(file_path)
        
        in_cooldown = False
        if vote == 1:
            in_cooldown = file_path in self.recent_positive
        elif vote == -1:
            in_cooldown = file_path in self.recent_negative
        else:
            in_cooldown = file_path in self.recent_neutral
        
        return {
            'vote': vote,
            'vote_symbol': self.get_vote_symbol(file_path),
            'cooldown': cooldown,
            'is_blocked': vote == -1 and self.negative_cooldown == 0,
            'in_cooldown': in_cooldown,
            'can_show_now': file_path in self._get_eligible_files()
        }
    
    # ========================================
    # Persistencia
    # ========================================
    
    def export_data(self) -> Dict:
        """Exportar votos y configuración"""
        return {
            'votes': self.votes.copy(),
            'positive_cooldown': self.positive_cooldown,
            'neutral_cooldown': self.neutral_cooldown,
            'negative_cooldown': self.negative_cooldown
        }
    
    def import_data(self, data: Dict):
        """Importar datos guardados"""
        if 'votes' in data:
            self.votes = data['votes'].copy()
        if 'positive_cooldown' in data:
            self.set_positive_cooldown(data['positive_cooldown'])
        if 'neutral_cooldown' in data:
            self.set_neutral_cooldown(data['neutral_cooldown'])
        if 'negative_cooldown' in data:
            self.set_negative_cooldown(data['negative_cooldown'])
    
    def reset_history(self):
        """Limpiar historial"""
        self.history.clear()
        self.history_position = -1
        self.recent_positive.clear()
        self.recent_neutral.clear()
        self.recent_negative.clear()
    
    def reset_votes(self):
        """Limpiar votos"""
        self.votes.clear()
    
    def reset_all(self):
        """Reset completo"""
        self.reset_history()
        self.reset_votes()
    def reset_positive_votes(self):
        """Reset only positive votes to neutral"""
        votes_to_remove = [path for path, vote in self.votes.items() if vote == 1]
        for path in votes_to_remove:
            del self.votes[path]
        
        # Limpiar cache de positivos
        self.recent_positive.clear()

    def reset_negative_votes(self):
        """Reset only negative votes to neutral"""
        votes_to_remove = [path for path, vote in self.votes.items() if vote == -1]
        for path in votes_to_remove:
            del self.votes[path]
        
        # Limpiar cache de negativos
        self.recent_negative.clear()

    def reset_neutral_votes(self):
        """Remove all neutral votes (keep only voted files)"""
        # Los neutrales no están en self.votes, así que no hay nada que hacer
        self.recent_neutral.clear()


# ========================================
# Ejemplo de uso
# ========================================

if __name__ == "__main__":
    # Crear sistema con configuración
    files = [f"file_{i:03d}.jpg" for i in range(30)]
    nav = NavigationSystem(
        files,
        positive_cooldown=3,   # Positivos se repiten después de 3 archivos
        neutral_cooldown=15,   # Neutrales después de 15
        negative_cooldown=0    # Negativos bloqueados (0 = nunca)
    )
    
    print("=== Sistema de Navegación con Votos ===")
    print(f"Configuración:")
    print(f"  👍 Positivos: cooldown = {nav.positive_cooldown}")
    print(f"  ⚪ Neutrales: cooldown = {nav.neutral_cooldown}")
    print(f"  👎 Negativos: cooldown = {nav.negative_cooldown} (0 = bloqueados)\n")
    
    # Navegar y votar
    for i in range(25):
        file = nav.next_random()
        if not file:
            print("No hay archivos disponibles")
            break
        
        symbol = nav.get_vote_symbol(file)
        print(f"{i+1:2d}. {symbol} {file}")
        
        # Simular votos
        if i < 12:
            choice = random.random()
            if choice < 0.3:
                nav.vote_positive(file)
                print(f"    → Votado 👍")
            elif choice < 0.4:
                nav.vote_negative(file)
                print(f"    → Votado 👎 (bloqueado)")
    
    # Estadísticas
    print("\n" + "="*60)
    print("ESTADÍSTICAS:")
    stats = nav.get_stats()
    print(f"  Total archivos: {stats['total_files']}")
    print(f"  👍 Positivos: {stats['positive_voted']}")
    print(f"  ⚪ Neutrales: {stats['neutral_voted']}")
    print(f"  👎 Negativos: {stats['negative_voted']}")
    print(f"  Disponibles ahora: {stats['eligible_now']}")
    print(f"\n  En cooldown:")
    print(f"    👍 {stats['in_cooldown']['positive']}")
    print(f"    ⚪ {stats['in_cooldown']['neutral']}")
    print(f"    👎 {stats['in_cooldown']['negative']}")
    
    # Cambiar configuración en tiempo real
    print("\n" + "="*60)
    print("CAMBIO DE CONFIGURACIÓN:")
    print("  Permitiendo negativos con cooldown de 30...")
    nav.set_negative_cooldown(30)
    print(f"  Nuevos archivos disponibles: {nav.get_stats()['eligible_now']}")