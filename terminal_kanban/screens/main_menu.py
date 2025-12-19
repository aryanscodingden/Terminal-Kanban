from textual.app import ComposeResult, Screen
from textual.containers import Container, Vertical
from textual.widgets import Button, Label, Static
from textual.reactive import reactive
from textual import events

class MenuItem(Static):
    """Menu item"""
    selected = reactive(False)
    def __init__(self, label:str, action: str):
        super().__init__(label, classes="menu-item")
        self.label = label
        self.action_name = action
        
    def render(self):
        if self.selected:
            return f"[reverse]{self.label}[/reverse]"
        return self.label 

class MenuScreen(Screen):
    """Start menu."""

    BINDINGS = [
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
        ("enter", "activate", "Activate"),
        ("space", "activate", "Activate"),
    ]
        
    def compose(self) -> ComposeResult:
        title = Static("TERMINAL-KANBAN", classes="title")
        self.new = MenuItem("New Kanban Board", "new")
        self.load = MenuItem("Load Existing Board", "load")
        self.quit = MenuItem("Quit", "quit")

        yield Container(
            Vertical(
                title,
                self.new,
                self.load,
                self.quit,
                classes="menu-list",
            ),
            id="menu-container",
        )
        
    def on_mount(self):
        self.items = [self.new, self.load, self.quit]
        self.index = 0 
        self._update_selection()
        
    def action_move_up(self):
        self.index = (self.index - 1) % len(self.items)
        self._update_selection()
        
    def action_move_down(self):
        self.index = (self.index + 1) % len(self.items)
        self._update_selection()
    def _update_selection(self):
        for i, item in enumerate(self.items):
            item.selected = (i == self.index)
            
    def action_activate(self):
        chosen = self.items[self.index].action_name
        
        if chosen == "new":
            self.app.push_screen("board")
        elif chosen == "load":
            pass  
        elif chosen == "quit":
            self.app.exit()
                
    async def on_click(self, event: events.Click):
        for item in self.items:
            if item.region.contains(event.x, event.y):
                item.selected = True
                self.index = self.items.index(item)
                self.action_activate()

