from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label

class BoardScreen(Screen):
    """Kan-ban Board"""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Label('Board will go here(Press esc to go back)', id="placeholder-text")
        yield Footer()
        
    def on_key(self, event):
        if event.key == 'escape':
            self.app.pop_screen()