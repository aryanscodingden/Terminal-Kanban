from textual.app import App
from screens.main_menu import MenuScreen
from screens.board import BoardScreen
class KanbanApp(App):
    """The main App controller."""
    
    CSS_PATH = "kanban.tcss"
    
    SCREENS = {
        "menu": MenuScreen,
        "board": BoardScreen,
    }
    
    BINDINGS = [
        ("a", "board_add_card", "Add Card"),
        ("e", "board_edit_card", "Edit Card"),
        ("d", "board_delete_card", "Delete Card")
    ]
    
    def on_mount(self) -> None:
        self.push_screen("menu")
        
    def action_board_add_card(self) -> None:
        from screens.board import BoardScreen
        if isinstance(self.screen, BoardScreen):
            self.screen.action_add_card()
            
    def action_board_edit_card(self) -> None:
        from screens.board import BoardScreen
        if isinstance(self.screen, BoardScreen):
            self.screen.action_edit_card()
    
    def action_board_delete_card(self) -> None:
        from screens.board import BoardScreen
        if isinstance(self.service, BoardScreen):
            self.screen.action_delete_card()
            
if __name__ == "__main__":
    app = KanbanApp()
    app.run()