from textual.containers import Vertical
from textual.widgets import Static
from widgets.card import Card

class Column(Vertical):
    """Kanban column with cards."""
    
    def __init__(self, title: str, cards: list[str] = None, **kargs):
        super().__init__(id=f"col-{title.lower()}", classes="column", **kargs)
        
        self.mount(Static(title, classes="column-title"))
        
        if cards: 
            for card in cards:
                self.mount(Card(card))