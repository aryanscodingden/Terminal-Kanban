from textual.widgets import Static


class Card(Static):
    """Kanban board card"""
    
    def __init__(self, text: str, **kwargs):
        super().__init__(text, classes="card", **kwargs)
        self.text = text
        
    def select(self):
        self.add_class("selected")
    
    def deselect(self):
        self.remove_class("selected")



