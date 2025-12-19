from textual.app import App
from screens.main_menu import MenuScreen
from screens.board import BoardScreen
from pathlib import Path

class KanbanApp(App):
    """The main App controller."""
    
    CSS_PATH = Path(__file__).parent / "screens" / "kanban.tcss"
    
    SCREENS = {
        "menu": MenuScreen,
        "board": BoardScreen,
    }
    
    def on_mount(self) -> None:
        self.push_screen("menu")
        
        
def run():
    app = KanbanApp()
    app.run()
        
if __name__ == "__main__":
    run()