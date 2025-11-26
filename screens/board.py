from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static

BOARD_FILE = Path("kanban_board.json")


class Card(Static):
    """Single kanban card widget."""

    selected = reactive(False)

    def __init__(self, title: str, meta: str = ""):
        super().__init__(classes="card")
        self.title = title
        self.meta = meta
        self.column: Optional[Column] = None

    def render(self) -> str:
        prefix = "▶ " if self.selected else ""
        if self.meta:
            return f"{prefix}{self.title}\n{self.meta}"
        return f"{prefix}{self.title}"

    async def on_click(self, event: events.Click) -> None:
        board = self.screen
        if isinstance(board, BoardScreen):
            board.select_card(self)


class Column(Vertical):
    """Column containing a list of cards."""

    def __init__(self, title: str, column_id: str):
        super().__init__(id=column_id, classes="column")
        self.title = title
        self.cards: List[Card] = []
        self.can_focus = False

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="column-header")
        yield Container(id=f"{self.id}-body", classes="column-body")

    def body(self) -> Container:
        return self.query_one(f"#{self.id}-body", Container)

    async def add_card(self, card: Card, index: Optional[int] = None) -> None:
        card.column = self
        if index is None or index >= len(self.cards):
            self.cards.append(card)
        else:
            self.cards.insert(index, card)
        await self._refresh_body()

    async def remove_card(self, card: Card) -> None:
        if card in self.cards:
            self.cards.remove(card)
            await self._refresh_body()

    async def _refresh_body(self) -> None:
        container = self.body()
        await container.remove_children()
        if self.cards:
            await container.mount(*self.cards)


class BoardScreen(Screen):
    """Main Kanban board screen."""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.can_focus = True

    def compose(self) -> ComposeResult:
        self.todo = Column("To Do", "todo")
        self.doing = Column("Doing", "doing")
        self.done = Column("Done", "done")

        yield Header()
        yield Horizontal(
            self.todo,
            self.doing,
            self.done,
            id="board",
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

    async def on_mount(self) -> None:
        self.columns: List[Column] = [self.todo, self.doing, self.done]
        self.selected_card: Optional[Card] = None
        self.set_focus(self)
        self.focus()
        self._dialog_mode: Optional[str] = None
        self._dialog_target_column: Optional[Column] = None
        self._dialog_target_card: Optional[Card] = None
        await self.load_board()
        for col in self.columns:
            if col.cards:
                self.select_card(col.cards[0])
                break
        try:
            self.query_one("#board").focus()
        except Exception:
            pass

    async def on_key(self, event):
        print("KEY:", event.key)

    def select_card(self, card: Optional[Card]) -> None:
        if self.selected_card:
            self.selected_card.selected = False
        self.selected_card = card
        if card:
            card.selected = True
            card.focus()
            
    def action_back(self) -> None:
        if self._dialog_visible:
            self.close_dialog()
        else:
            self.app.pop_screen()

    def action_move_up(self) -> None:
        if not self._ensure_selection():
            return
        col = self.selected_card.column
        idx = col.cards.index(self.selected_card)
        if idx > 0:
            self.select_card(col.cards[idx - 1])

    def action_move_down(self) -> None:
        if not self._ensure_selection():
            return
        col = self.selected_card.column
        idx = col.cards.index(self.selected_card)
        if idx < len(col.cards) - 1:
            self.select_card(col.cards[idx + 1])

    async def action_move_col_left(self) -> None:
        await self._move_card_between_columns(-1)

    async def action_move_col_right(self) -> None:
        await self._move_card_between_columns(1)

    async def _move_card_between_columns(self, direction: int) -> None:
        if not self._ensure_selection():
            return
        col = self.selected_card.column
        src_index = self.columns.index(col)
        dst_index = src_index + direction
        if not (0 <= dst_index < len(self.columns)):
            return
        dst_col = self.columns[dst_index]
        await col.remove_card(self.selected_card)
        await dst_col.add_card(self.selected_card)
        self.select_card(self.selected_card)
        self.save_board()

    def action_add_card(self) -> None:
        target = self.selected_card.column if self.selected_card else self.todo
        self._open_dialog(mode="add", column=target)

    def action_edit_card(self) -> None:
        if self._ensure_selection():
            self._open_dialog(mode="edit", card=self.selected_card)

    async def action_delete_card(self) -> None:
        if not self._ensure_selection():
            return
        col = self.selected_card.column
        idx = col.cards.index(self.selected_card)
        await col.remove_card(self.selected_card)
        if col.cards:
            self.select_card(col.cards[min(idx, len(col.cards) - 1)])
        else:
            self.select_card(None)
        self.save_board()

    def _open_dialog(self, mode: str, column: Optional[Column] = None, card: Optional[Card] = None) -> None:
        self._dialog_mode = mode
        self._dialog_target_column = column
        self._dialog_target_card = card
        title_input = self.query_one("#title-input", Input)
        meta_input = self.query_one("#meta-input", Input)
        if mode == "edit" and card:
            title_input.value = card.title
            meta_input.value = card.meta
        else:
            title_input.value = ""
            meta_input.value = ""
        self.query_one("#dialog").remove_class("hidden")
        title_input.focus()
        self.dialog_open = True

    def close_dialog(self) -> None:
        self.query_one("#dialog").add_class("hidden")
        self.dialog_open = False

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "dlg-save":
            await self._save_dialog()
        elif event.button.id == "dlg-cancel":
            self.close_dialog()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in {"title-input", "meta-input"}:
            await self._save_dialog()

    async def _save_dialog(self) -> None:
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
            await column.add_card(card)
            self.select_card(card)
        elif self._dialog_mode == "edit" and self._dialog_target_card:
            self._dialog_target_card.title = title
            self._dialog_target_card.meta = meta
            self._dialog_target_card.refresh()
        self.save_board()
        self.close_dialog()

    def save_board(self) -> None:
        data = {
            col.title: [
                {"title": card.title, "meta": card.meta}
                for card in col.cards
            ]
            for col in self.columns
        }
        with BOARD_FILE.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    async def load_board(self) -> None:
        if not BOARD_FILE.exists():
            await self.todo.add_card(Card("Fix API bug", "#backend #urgent"))
            await self.todo.add_card(Card("Email client", "#followup"))
            await self.doing.add_card(Card("Write Report", "#docs"))
            await self.done.add_card(Card("Initial setup", "#env"))
            return
        with BOARD_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
        for col in self.columns:
            for item in data.get(col.title, []):
                title = item.get("title", "")
                meta = item.get("meta", "")
                if title:
                    await col.add_card(Card(title, meta))

    @property
    def _dialog_visible(self) -> bool:
        return self.dialog_open and "hidden" not in self.query_one("#dialog").classes

    def _ensure_selection(self) -> bool:
        if self.selected_card:
            return True
        for col in self.columns:
            if col.cards:
                self.select_card(col.cards[0])
                return True
        return False
    
    