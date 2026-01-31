import random
from typing import List, Optional, Dict
from collections import deque


class NavigationSystem:
    """
    Navigation system with votes and configurable cooldowns
    
    Votes: +1 (positive), 0 (neutral), -1 (negative)
    Cooldowns: Global configuration per vote category
    """
    
    def __init__(
        self, 
        file_list: List[str],
        positive_cooldown: int = 5,   # Cooldown for positively voted files
        neutral_cooldown: int = 20,   # Cooldown for files without vote
        negative_cooldown: int = 0,   # Cooldown for negatively voted files (0 = blocked)
        max_history: int = 1000
    ):
        """
        Args:
            file_list: List of files
            positive_cooldown: Files before repeating positively voted ones
            neutral_cooldown: Files before repeating unvoted ones
            negative_cooldown: Files before repeating negative ones (0 = never)
            max_history: Maximum files in history
        """
        self.all_files = file_list.copy()
        self.max_history = max_history
        
        # Cooldown configuration per category
        self.positive_cooldown = positive_cooldown
        self.neutral_cooldown = neutral_cooldown
        self.negative_cooldown = negative_cooldown
        
        # Votes: {file_path: vote}
        # vote: 1 (positive), 0 (neutral - no vote), -1 (negative)
        self.votes: Dict[str, int] = {}
        
        # Navigation history
        self.history: List[str] = []
        self.history_position = -1
        
        # Caches of recent files per category
        self.recent_positive = deque(maxlen=positive_cooldown)
        self.recent_neutral = deque(maxlen=neutral_cooldown)
        self.recent_negative = deque(maxlen=negative_cooldown if negative_cooldown > 0 else 1)
    
    # ========================================
    # Votes
    # ========================================
    
    def vote_positive(self, file_path: str):
        """Vote positive (👍)"""
        self.votes[file_path] = 1
    
    def vote_negative(self, file_path: str):
        """Vote negative (👎)"""
        self.votes[file_path] = -1
    
    def clear_vote(self, file_path: str):
        """Remove vote (returns to neutral ⚪)"""
        if file_path in self.votes:
            del self.votes[file_path]
    
    def get_vote(self, file_path: str) -> int:
        """Get vote: 1, 0, or -1"""
        return self.votes.get(file_path, 0)
    
    def toggle_vote(self, file_path: str, vote_type: int):
        """
        Toggle vote
        
        Args:
            vote_type: 1 (positive) or -1 (negative)
        """
        current = self.get_vote(file_path)
        if current == vote_type:
            self.clear_vote(file_path)  # If already has that vote, remove it
        else:
            self.votes[file_path] = vote_type
    
    def get_vote_symbol(self, file_path: str) -> str:
        """Get vote symbol"""
        vote = self.get_vote(file_path)
        return "👍" if vote == 1 else "👎" if vote == -1 else "⚪"
    
    # ========================================
    # Cooldown Configuration
    # ========================================
    
    def set_positive_cooldown(self, cooldown: int):
        """Configure cooldown for positives"""
        self.positive_cooldown = max(0, cooldown)
        # Create new deque with new maxlen and preserve items
        maxlen = self.positive_cooldown if self.positive_cooldown > 0 else 1
        items = list(self.recent_positive)
        self.recent_positive = deque(items[-maxlen:], maxlen=maxlen)
    
    def set_neutral_cooldown(self, cooldown: int):
        """Configure cooldown for neutrals"""
        self.neutral_cooldown = max(0, cooldown)
        # Create new deque with new maxlen and preserve items
        maxlen = self.neutral_cooldown if self.neutral_cooldown > 0 else 1
        items = list(self.recent_neutral)
        self.recent_neutral = deque(items[-maxlen:], maxlen=maxlen)
    
    def set_negative_cooldown(self, cooldown: int):
        """
        Configure cooldown for negatives
        0 = permanently blocked
        >0 = repeat after N files
        """
        self.negative_cooldown = max(0, cooldown)
        maxlen = self.negative_cooldown if self.negative_cooldown > 0 else 1
        # Create new deque with new maxlen and preserve items
        items = list(self.recent_negative)
        self.recent_negative = deque(items[-maxlen:], maxlen=maxlen)

    def set_max_history(self, max_history: int):
        """Change maximum history limit"""
        self.max_history = max(100, max_history)  # Minimum 100
        
        # If current history exceeds new limit, truncate
        if len(self.history) > self.max_history:
            overflow = len(self.history) - self.max_history
            self.history = self.history[overflow:]
            self.history_position = max(0, self.history_position - overflow)
    
    def get_cooldown_for_file(self, file_path: str) -> int:
        """Get effective cooldown for a file"""
        vote = self.get_vote(file_path)
        if vote == 1:
            return self.positive_cooldown
        elif vote == -1:
            return self.negative_cooldown
        else:
            return self.neutral_cooldown
    
    # ========================================
    # Navigation
    # ========================================
    
    def get_current(self) -> Optional[str]:
        """Get current file"""
        if 0 <= self.history_position < len(self.history):
            return self.history[self.history_position]
        return None
    
    def can_go_back(self) -> bool:
        """Can go back?"""
        return self.history_position > 0
    
    def can_go_forward_in_history(self) -> bool:
        """Can go forward in history?"""
        return self.history_position < len(self.history) - 1
    
    def go_back(self) -> Optional[str]:
        """Go back to previous file"""
        if self.can_go_back():
            self.history_position -= 1
            return self.get_current()
        return None
    
    def go_forward_in_history(self) -> Optional[str]:
        """Go forward in history"""
        if self.can_go_forward_in_history():
            self.history_position += 1
            return self.get_current()
        return None
    
    def next_random(self) -> Optional[str]:
        """Get next file (history or random)"""
        # If there's future in history, advance through it
        if self.can_go_forward_in_history():
            return self.go_forward_in_history()
        
        # If no future, generate random
        candidates = self._get_eligible_files()
        
        if not candidates:
            # Reset caches and retry
            self.recent_positive.clear()
            self.recent_neutral.clear()
            self.recent_negative.clear()
            candidates = self._get_eligible_files()
            
            if not candidates:
                return None
        
        # Random selection
        next_file = random.choice(candidates)
        
        # Since we're at the end of history, add normally
        self.history.append(next_file)
        self.history_position = len(self.history) - 1
        
        # Limit history size
        if len(self.history) > self.max_history:
            overflow = len(self.history) - self.max_history
            self.history = self.history[overflow:]
            self.history_position -= overflow
        
        # Add to corresponding cache
        vote = self.get_vote(next_file)
        if vote == 1 and self.positive_cooldown > 0:
            self.recent_positive.append(next_file)
        elif vote == -1 and self.negative_cooldown > 0:
            self.recent_negative.append(next_file)
        elif vote == 0 and self.neutral_cooldown > 0:
            self.recent_neutral.append(next_file)
        
        return next_file
    
    def _get_eligible_files(self) -> List[str]:
        """Get files that can be shown"""
        eligible = []
        
        for file_path in self.all_files:
            vote = self.get_vote(file_path)
            
            # Negatives
            if vote == -1:
                if self.negative_cooldown == 0:
                    continue  # Permanently blocked (Never show)
                if file_path in self.recent_negative:
                    continue  # In cooldown
            
            # Positives
            elif vote == 1:
                if self.positive_cooldown == 0:
                    continue  # Never show positives (blocked)
                if file_path in self.recent_positive:
                    continue  # In cooldown
            
            # Neutrals
            else:
                if self.neutral_cooldown == 0:
                    continue  # Never show neutrals (blocked)
                if file_path in self.recent_neutral:
                    continue  # In cooldown
            
            eligible.append(file_path)
        
        return eligible
    
    # ========================================
    # Management
    # ========================================
    
    def update_file_list(self, new_file_list: List[str]):
        """Update file list"""
        self.all_files = new_file_list.copy()
    
    # ========================================
    # Statistics
    # ========================================
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        positive = sum(1 for v in self.votes.values() if v == 1)
        negative = sum(1 for v in self.votes.values() if v == -1)
        neutral = len(self.all_files) - positive - negative
        
        eligible = len(self._get_eligible_files())
        
        # Counters in cooldown
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
        """File information"""
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
    # Persistence
    # ========================================
    
    def export_data(self) -> Dict:
        """Export votes and configuration"""
        return {
            'votes': self.votes.copy(),
            'positive_cooldown': self.positive_cooldown,
            'neutral_cooldown': self.neutral_cooldown,
            'negative_cooldown': self.negative_cooldown,
            'max_history': self.max_history
        }
    
    def import_data(self, data: Dict):
        """Import saved data"""
        if 'votes' in data:
            self.votes = data['votes'].copy()
        if 'positive_cooldown' in data:
            self.set_positive_cooldown(data['positive_cooldown'])
        if 'neutral_cooldown' in data:
            self.set_neutral_cooldown(data['neutral_cooldown'])
        if 'negative_cooldown' in data:
            self.set_negative_cooldown(data['negative_cooldown'])
        if 'max_history' in data:
            self.set_max_history(data['max_history'])
    
    def reset_history(self):
        """Clear history"""
        self.history.clear()
        self.history_position = -1
        self.recent_positive.clear()
        self.recent_neutral.clear()
        self.recent_negative.clear()
    
    def reset_votes(self):
        """Clear votes"""
        self.votes.clear()
    
    def reset_all(self):
        """Complete reset"""
        self.reset_history()
        self.reset_votes()
    
    def reset_positive_votes(self):
        """Reset only positive votes to neutral"""
        votes_to_remove = [path for path, vote in self.votes.items() if vote == 1]
        for path in votes_to_remove:
            del self.votes[path]
        
        # Clear positive cache
        self.recent_positive.clear()

    def reset_negative_votes(self):
        """Reset only negative votes to neutral"""
        votes_to_remove = [path for path, vote in self.votes.items() if vote == -1]
        for path in votes_to_remove:
            del self.votes[path]
        
        # Clear negative cache
        self.recent_negative.clear()

    def reset_neutral_votes(self):
        """Remove all neutral votes (keep only voted files)"""
        # Neutrals aren't in self.votes, so nothing to do
        self.recent_neutral.clear()


# ========================================
# Usage Example
# ========================================

if __name__ == "__main__":
    # Create system with configuration
    files = [f"file_{i:03d}.jpg" for i in range(30)]
    nav = NavigationSystem(
        files,
        positive_cooldown=3,   # Positives repeat after 3 files
        neutral_cooldown=15,   # Neutrals after 15
        negative_cooldown=0    # Negatives blocked (0 = never)
    )
    
    print("=== Navigation System with Votes ===")
    print(f"Configuration:")
    print(f"  👍 Positives: cooldown = {nav.positive_cooldown}")
    print(f"  ⚪ Neutrals: cooldown = {nav.neutral_cooldown}")
    print(f"  👎 Negatives: cooldown = {nav.negative_cooldown} (0 = blocked)\n")
    
    # Navigate and vote
    for i in range(25):
        file = nav.next_random()
        if not file:
            print("No files available")
            break
        
        symbol = nav.get_vote_symbol(file)
        print(f"{i+1:2d}. {symbol} {file}")
        
        # Simulate votes
        if i < 12:
            choice = random.random()
            if choice < 0.3:
                nav.vote_positive(file)
                print(f"    → Voted 👍")
            elif choice < 0.4:
                nav.vote_negative(file)
                print(f"    → Voted 👎 (blocked)")
    
    # Statistics
    print("\n" + "="*60)
    print("STATISTICS:")
    stats = nav.get_stats()
    print(f"  Total files: {stats['total_files']}")
    print(f"  👍 Positives: {stats['positive_voted']}")
    print(f"  ⚪ Neutrals: {stats['neutral_voted']}")
    print(f"  👎 Negatives: {stats['negative_voted']}")
    print(f"  Available now: {stats['eligible_now']}")
    print(f"\n  In cooldown:")
    print(f"    👍 {stats['in_cooldown']['positive']}")
    print(f"    ⚪ {stats['in_cooldown']['neutral']}")
    print(f"    👎 {stats['in_cooldown']['negative']}")
    
    # Change configuration in real time
    print("\n" + "="*60)
    print("CONFIGURATION CHANGE:")
    print("  Allowing negatives with cooldown of 30...")
    nav.set_negative_cooldown(30)
    print(f"  New available files: {nav.get_stats()['eligible_now']}")