from textual.app import App
from screens.main_menu import MenuScreen
from screens.board import BoardScreen

class KanbanApp(App):
    """The main App controller."""
    
    css_path = "kanban.tcss"
    
    SCREENS = {
    "menu": MenuScreen,
    "board": BoardScreen,
    }
    
    def on_mount(self) -> None:
        self.push_screen("menu")
        
if __name__ == "__main__":
    app = KanbanApp()
    app.run()