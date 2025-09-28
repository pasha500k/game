"""In-game text console that can execute developer commands."""

from __future__ import annotations

from collections import deque
from typing import Callable, Dict, Iterable

from ursina import Entity, Text, camera, color

from . import settings


CommandFunc = Callable[[Iterable[str]], str]


class CommandConsole(Entity):
    """Simple overlay console that captures keyboard characters when opened."""

    def __init__(self) -> None:
        super().__init__(parent=camera.ui, enabled=False)
        self._history: deque[str] = deque(maxlen=settings.CONSOLE_HISTORY)
        self._commands: Dict[str, tuple[str, CommandFunc]] = {}
        self._buffer: str = ""

        self._background = Entity(
            parent=self,
            model="quad",
            color=color.rgba(15, 18, 25, 220),
            scale=(1.45, 0.55),
            position=(0, -0.35),
        )
        self._log_text = Text(
            parent=self._background,
            position=(-0.68, 0.16),
            origin=(0, 0),
            text="",
            scale=0.015,
            line_height=1.1,
            color=color.rgb(*settings.HUD_TEXT_COLOR),
        )
        self._input_text = Text(
            parent=self._background,
            position=(-0.68, -0.18),
            origin=(0, 0),
            text="> ",
            scale=0.017,
            line_height=1.0,
            color=color.rgb(180, 240, 255),
        )

    # ------------------------------------------------------------------
    # Console lifecycle
    def toggle(self) -> None:
        self.enabled = not self.enabled
        if self.enabled:
            self._buffer = ""
            self._render()

    def add_command(self, name: str, description: str, callback: CommandFunc) -> None:
        self._commands[name.lower()] = (description, callback)

    # ------------------------------------------------------------------
    def feed_key(self, key: str) -> None:
        if not self.enabled:
            return
        if key == "enter":
            self._execute_current_buffer()
        elif key == "escape":
            self.toggle()
        elif key == "backspace":
            self._buffer = self._buffer[:-1]
            self._render()
        elif key == "tab":
            self._autocomplete()
        elif len(key) == 1 and len(self._buffer) < settings.CONSOLE_MAX_COMMAND:
            self._buffer += key
            self._render()

    def _execute_current_buffer(self) -> None:
        text = self._buffer.strip()
        if not text:
            self._history.append("")
            self._render()
            return
        self._history.append(f"> {text}")
        parts = text.split()
        command, *args = parts
        command = command.lower()
        if command in self._commands:
            try:
                result = self._commands[command][1](args)
            except Exception as exc:  # pragma: no cover - debugging aid
                result = f"Error: {exc}"
        else:
            result = f"Unknown command '{command}'. Type 'help' for a list."
        if result:
            for line in result.splitlines():
                self._history.append(line)
        self._buffer = ""
        self._render()

    def _render(self) -> None:
        log_text = "\n".join(self._history)
        self._log_text.text = log_text
        self._input_text.text = f"> {self._buffer}"

    def _autocomplete(self) -> None:
        if not self._buffer:
            return
        matches = [name for name in self._commands if name.startswith(self._buffer.lower())]
        if len(matches) == 1:
            self._buffer = matches[0] + " "
            self._render()

    def describe_commands(self) -> str:
        rows = ["Available commands:"]
        for name, (description, _) in sorted(self._commands.items()):
            rows.append(f"  {name} — {description}")
        return "\n".join(rows)

    def print_text(self, text: str) -> None:
        for line in text.splitlines():
            self._history.append(line)
        self._render()
