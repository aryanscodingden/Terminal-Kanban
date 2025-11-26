from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Static, Input, Button
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual import events

BOARD_FILE = Path("kanban_board.json")


class Card(Static):
    """Single kanban card"""
    
    selected = reactive(False)
    
    def __init__(self, title: str, meta: str = ""):
        super().__init__(classes="card")
        self.title = title
        self.meta = meta
        self.column: Optional[Column] = None
        
    def render(self):
        prefix = "▶ " if self.selected else ""
        if self.meta:
            return f"{prefix}{self.title}\n{self.meta}"
        return f"{prefix}{self.title}"
    
    async def on_click(self, event: events.Click) -> None:
        board: BoardScreen = self.app.get_screen("board")
        board.select_card(self)
        
        
class Column(Vertical):
    """Columns in kanban"""
    
    def __init__(self, title: str, column_id: str):
        super().__init__(id=column_id, classes="column")
        self.title = title 
        self.cards: List[Card] = []
        
    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="column-header")
        yield Container(id=f"{self.id}-body")
        
    def body(self) -> Container:
        return self.query_one(f"#{self.id}-body", Container)
            
    def add_card(self, card: Card, index: Optional[int] = None) -> None:
        card.column = self
        if index is None or index >= len(self.cards):
            self.cards.append(card)
            self.body().mount(card)
        else:
            self.cards.insert(index, card)
            self.body().remove_children()
            for c in self.cards:
                self.body().mount(c)
                
    def remove_card(self, card: Card) -> None:
        if card in self.cards:
            self.cards.remove(card)
            card.remove()
            

class BoardScreen(Screen):
    """Kanban Board screen"""
    
    BINDINGS = [
        ("escape", "back", "Back to menu"),
        ("up", "move_up", "Select up"),
        ("down", "move_down", "Select down"),
        ("left", "move_col_left", "Move card to left column"),
        ("right", "move_col_right", "Move card to right column"),
        ("a", "add_card", "Add Card"),
        ("e", "edit_card", "Edit Card"), 
        ("d", "delete_card", "Delete Card"),
    ]
    
    dialog_open = reactive(False)
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        # Create columns first
        self.todo = Column("To Do", "todo")
        self.doing = Column("Doing", "doing")
        self.done = Column("Done", "done")
        
        yield Horizontal(
            self.todo,
            self.doing,
            self.done,
            id="board"
        )
        yield Footer()
        
        yield Container(
            Label("Card Editor", id="dialog-title"),
            Input(placeholder="Title", id="title-input"),
            Input(placeholder="Meta / description (optional)", id="meta-input"),
            Horizontal(
                Button("Save", id="dlg-save", variant="success"),
                Button("Cancel", id="dlg-cancel", variant="error"),
                id="dlg-buttons",
            ),
            id="dialog",
            classes="hidden",
        )
        
    def on_mount(self) -> None:
        self.columns: List[Column] = [self.todo, self.doing, self.done]
        self.selected_card: Optional[Card] = None
        
        self._dialog_mode: Optional[str] = None
        self._dialog_target_column: Optional[Column] = None
        self._dialog_target_card: Optional[Card] = None
        
        self.load_board()
        
        for col in self.columns:
            if col.cards:
                self.select_card(col.cards[0])
                break
        
        # Ensure the board container has focus so key bindings work
        try:
            board_container = self.query_one("#board")
            board_container.focus()
        except:
            pass 
        
    def select_card(self, card: Optional[Card]) -> None: 
        if self.selected_card: 
            self.selected_card.selected = False
        self.selected_card = card
        if card: 
            card.selected = True
            
    def action_back(self) -> None:
        """Handle ESC key - close dialog if open, otherwise go back to menu"""
        dialog = self.query_one("#dialog")
        if "hidden" not in dialog.classes:
            self.close_dialog()
        else:
            self.app.pop_screen()
        
    def action_move_up(self) -> None:
        if not self.selected_card:
            for col in self.columns:
                if col.cards:
                    self.select_card(col.cards[0])
                    return

    def action_move_down(self) -> None:
       if not self.selected_card:
            return
        col = self.selected_card.column
        idx = col.cards.index(self.selected_card)
        if idx < len(col.cards) - 1: 
            self.select_card(col.cards[idx + 1])
            
    def action_move_col_left(self) -> None:
        self._move_card_between_columns(-1)
        
    def action_move_col_right(self) -> None:
        self._move_card_between_columns(1)
        
    def _move_card_between_columns(self, direction: int) -> None:
        if not self.selected_card: 
            return
        col = self.selected_card.column
        src_index = self.columns.index(col)
        dst_index = src_index + direction
        if not (0 <= dst_index < len(self.columns)):
            return
            
        dst_col = self.columns[dst_index]
        col.remove_card(self.selected_card)
        dst_col.add_card(self.selected_card)
        self.select_card(self.selected_card)
        self.save_board()
        
    def action_add_card(self) -> None:
        self.open_dialog_for_add()

    def action_edit_card(self) -> None:
        if self.selected_card:
            return  
            self.open_dialog_for_edit()
            
    def action_delete_card(self) -> None:
        if self.selected_card:
            return
            col = self.selected_card.column
            idx = col.cards.index(self.selected_card)
            col.remove_card(self.selected_card)
            
            # Select next card
            if col.cards:
                new_idx = min(idx, len(col.cards) - 1)
                self.select_card(col.cards[new_idx])
            else:
                self.selected_card = None
                
            self.save_board()
        
    def open_dialog_for_add(self) -> None:
        col = self.selected_card.column if self.selected_card else self.todo
        self._dialog_mode = "add"
        self._dialog_target_column = col
        self._dialog_target_card = None
        
        title_input = self.query_one("#title-input", Input)
        meta_input = self.query_one("#meta-input", Input)
        title_input.value = ""
        meta_input.value = ""
        
        dialog = self.query_one("#dialog")
        dialog.remove_class("hidden")
        title_input.focus()
        
    def open_dialog_for_edit(self, card: Card) -> None:
        self._dialog_mode = "edit"
        self._dialog_target_column = None
        self._dialog_target_card = card
        
        title_input = self.query_one("#title-input", Input)
        meta_input = self.query_one("#meta-input", Input)
        title_input.value = card.title
        meta_input.value = card.meta
        
        dialog = self.query_one("#dialog")
        dialog.remove_class("hidden")
        title_input.focus()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dlg-save":
            self.save_dialog()
        elif event.button.id == "dlg-cancel":
            self.close_dialog()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle ENTER key in input fields"""
        if event.input.id in ["title-input", "meta-input"]:
            self.save_dialog()
            
    def save_dialog(self) -> None:
        title_input = self.query_one("#title-input", Input)
        meta_input = self.query_one("#meta-input", Input)
        title = title_input.value.strip()
        meta = meta_input.value.strip()
        
        if not title: 
            self.close_dialog()
            return
            
        if self._dialog_mode == "add":
            column = self._dialog_target_column or self.todo 
            card = Card(title, meta)
            column.add_card(card)
            self.select_card(card)
            
        elif self._dialog_mode == "edit" and self._dialog_target_card:
            self._dialog_target_card.title = title
            self._dialog_target_card.meta = meta
            self._dialog_target_card.refresh()
            
        self.save_board()
        self.close_dialog()
        
    def close_dialog(self) -> None:
        dialog = self.query_one("#dialog")
        dialog.add_class("hidden")
        
    def save_board(self) -> None:
        data = {}
        for col in self.columns:
            data[col.title] = [
                {"title": card.title, "meta": card.meta} for card in col.cards
            ]
            
        with BOARD_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            
    def load_board(self) -> None:
        if not BOARD_FILE.exists():
            self.todo.add_card(Card("Fix API bug", "#backend #urgent"))
            self.todo.add_card(Card("Email client", "#followup"))
            self.doing.add_card(Card("Write Report", "#docs"))
            self.done.add_card(Card("Initial setup", "#env"))
            return
            
        with BOARD_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        for col in self.columns:
            items = data.get(col.title, [])
            for item in items:
                title = item.get("title", "")
                meta = item.get("meta", "")
                if title:
                    col.add_card(Card(title, meta))


async def on_key(self, event: events.Key) -> None: 
    if self.dialog_open:
        if event.key == "events":
            self.close_dialog()
        elif event.key == "enter":
            save = self.query_one("#dlg-save", Button)
            await save.press()
        return 
    
async def on_focus(self, event: events.Focus) -> None: 
    board: BoardScreen = self.app.get_screen("board")
    board.select_card(self)
    
async def on_blur(self, event: events.Blur) -> None: 
    self.refresh()
    
    