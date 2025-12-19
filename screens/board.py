from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Label
from textual.containers import Horizontal, Vertical, Container
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from widgets.card import Card

class Column(Vertical):
    """Kanban column"""
    
    def __init__(self, title: str, **kwargs):
        super().__init__(classes="column", **kwargs)
        self.column_title = title
        self.cards = []
    
    def compose(self) -> ComposeResult:
        yield Static(self.column_title, classes="column-header")
        yield Container(classes="column-body", id=f"{self.id}-body")
    
    async def add_card(self, card: Card):
        self.cards.append(card)
        try:
            body = self.query_one(f"#{self.id}-body")
            await body.mount(card)
        except:
            pass
    
    async def remove_card(self, card: Card):
        if card in self.cards:
            self.cards.remove(card)
            await card.remove()

class BoardScreen(Screen):
    """Kanban Board"""
    
    BINDINGS = [
        ("escape", "back", "Back to menu"),
        ("a", "add_card", "Add Card"),
        ("up", "move_up", "Move Up"),
        ("down", "move_down", "Move Down"),
        ("left", "move_left", "Move Card Left"),
        ("right", "move_right", "Move Card Right"),
        ("d", "delete_card", "Delete Card"),
    ]
    
    def __init__(self):
        super().__init__()
        self.selected_column_idx = 0
        self.selected_card_idx = 0
        self.selected_card: Optional[Card] = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        self.todo_col = Column("To Do", id="todo")
        self.doing_col = Column("Doing", id="doing")
        self.done_col = Column("Done", id="done")
        
        self.columns = [self.todo_col, self.doing_col, self.done_col]
        
        yield Horizontal(
            self.todo_col,
            self.doing_col,
            self.done_col,
            id="board-container"
        )
        
        yield Container(
            Label("Add New Card", id="dialog-title"),
            Input(placeholder="Enter task name", id="card-input"),
            Horizontal(
                Button("Add", id="btn-add", variant="success"),
                Button("Cancel", id="btn-cancel", variant="error"),
                id="dialog-buttons"
            ),
            id="add-dialog",
            classes="hidden"
        )
        
        yield Footer()
    
    async def on_mount(self):
        await self.todo_col.add_card(Card("Task 1: Setup project"))
        await self.todo_col.add_card(Card("Task 2: Design UI"))
        await self.doing_col.add_card(Card("Task 3: Implement features"))
        await self.done_col.add_card(Card("Task 4: Initial commit"))
        
        self._update_selection()
    
    def _update_selection(self):
        for col in self.columns:
            for card in col.cards:
                card.deselect()
        
        current_col = self.columns[self.selected_column_idx]
        if current_col.cards:
            self.selected_card_idx = min(self.selected_card_idx, len(current_col.cards) - 1)
            self.selected_card = current_col.cards[self.selected_card_idx]
            self.selected_card.select()
        else:
            self.selected_card = None
    
    def action_move_up(self):
        current_col = self.columns[self.selected_column_idx]
        if current_col.cards and self.selected_card_idx > 0:
            self.selected_card_idx -= 1
            self._update_selection()
    
    def action_move_down(self):
        current_col = self.columns[self.selected_column_idx]
        if current_col.cards and self.selected_card_idx < len(current_col.cards) - 1:
            self.selected_card_idx += 1
            self._update_selection()
    
    async def action_move_left(self):
       if self.selected_column_idx > 0:
           if self.selected_card:
               current_col = self.columns[self.selected_column_idx]
               new_col = self.columns[self.selected_column_idx - 1]
               
               card_to_move = self.selected_card
               if card_to_move in current_col.cards:
                   current_col.cards.remove(card_to_move)
               await card_to_move.remove()
               
               new_card = Card(card_to_move.text)
               await new_col.add_card(new_card)
               
               self.selected_column_idx -= 1
               self.selected_card_idx = len(new_col.cards) - 1
           else:
               self.selected_column_idx -= 1
               self.selected_card_idx = 0
               
           self._update_selection()
    
    async def action_move_right(self):
        if self.selected_column_idx < len(self.columns) - 1:
            if self.selected_card:
                current_col = self.columns[self.selected_column_idx]
                new_col = self.columns[self.selected_column_idx + 1]
                
                card_to_move = self.selected_card
                if card_to_move in current_col.cards:
                    current_col.cards.remove(card_to_move)
                await card_to_move.remove()
                
                new_card = Card(card_to_move.text)
                await new_col.add_card(new_card)
                
                self.selected_column_idx += 1
                self.selected_card_idx = len(new_col.cards) - 1
            else:
                self.selected_column_idx += 1
                self.selected_card_idx = 0
                
            self._update_selection()
    
    async def action_delete_card(self):
        if self.selected_card:
            current_col = self.columns[self.selected_column_idx]
            await current_col.remove_card(self.selected_card)
            self.selected_card_idx = max(0, self.selected_card_idx - 1)
            self._update_selection()
    
    def action_back(self):
        self.app.pop_screen()
    
    def action_add_card(self):
        dialog = self.query_one("#add-dialog")
        dialog.remove_class("hidden")
        input_field = self.query_one("#card-input", Input)
        input_field.focus()
        self.set_focus(input_field)
    
    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-add":
            input_widget = self.query_one("#card-input", Input)
            task_name = input_widget.value.strip()
            
            if task_name:
                new_card = Card(task_name)
                current_col = self.columns[self.selected_column_idx]
                await current_col.add_card(new_card)
                self.selected_card_idx = len(current_col.cards) - 1
                self._update_selection()
            
            input_widget.value = ""
            self.query_one("#add-dialog").add_class("hidden")
            self.set_focus(None)
            
        elif event.button.id == "btn-cancel":
            self.query_one("#card-input", Input).value = ""
            self.query_one("#add-dialog").add_class("hidden")
            self.set_focus(None)
    
    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "card-input":
            input_widget = self.query_one("#card-input", Input)
            task_name = input_widget.value.strip()
            
            if task_name:
                new_card = Card(task_name)
                current_col = self.columns[self.selected_column_idx]
                await current_col.add_card(new_card)
                self.selected_card_idx = len(current_col.cards) - 1
                self._update_selection()
            
            input_widget.value = ""
            self.query_one("#add-dialog").add_class("hidden")
            self.set_focus(None)
            