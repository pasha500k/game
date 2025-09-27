"""Lightweight developer console that understands simple commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple

import pygame

from . import settings


CommandHandler = Callable[[List[str]], str]


@dataclass
class Command:
    name: str
    description: str
    handler: CommandHandler


class Console:
    def __init__(self, font: pygame.font.Font) -> None:
        self.font = font
        self.active = False
        self.current_input: str = ""
        self.history: List[str] = []
        self.output: List[str] = []
        self.history_index: int | None = None
        self.commands: Dict[str, Command] = {}

    def toggle(self) -> None:
        self.active = not self.active
        self.history_index = None

    def add_command(self, name: str, description: str, handler: CommandHandler) -> None:
        self.commands[name.lower()] = Command(name.lower(), description, handler)

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.toggle()
                return
            if event.key == pygame.K_RETURN:
                self._commit_command()
                return
            if event.key == pygame.K_BACKSPACE:
                self.current_input = self.current_input[:-1]
                return
            if event.key == pygame.K_TAB:
                self._auto_complete()
                return
            if event.key == pygame.K_UP:
                self._history_previous()
                return
            if event.key == pygame.K_DOWN:
                self._history_next()
                return
            if event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_CTRL:
                try:
                    clipboard = pygame.scrap.get(pygame.SCRAP_TEXT)
                    if clipboard:
                        self.current_input += clipboard.decode("utf-8")
                except pygame.error:
                    pass
                return
            if event.unicode and event.unicode.isprintable():
                self.current_input += event.unicode

    def _history_previous(self) -> None:
        if not self.history:
            return
        if self.history_index is None:
            self.history_index = len(self.history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)
        self.current_input = self.history[self.history_index]

    def _history_next(self) -> None:
        if self.history_index is None:
            return
        self.history_index += 1
        if self.history_index >= len(self.history):
            self.history_index = None
            self.current_input = ""
        else:
            self.current_input = self.history[self.history_index]

    def _auto_complete(self) -> None:
        if not self.current_input:
            return
        parts = self.current_input.split()
        if len(parts) == 1:
            matches = [name for name in self.commands if name.startswith(parts[0].lower())]
            if len(matches) == 1:
                self.current_input = matches[0] + " "
            elif matches:
                self.output.append("Possible: " + ", ".join(matches))
        else:
            # Later support sub-command hints
            pass

    def _commit_command(self) -> None:
        text = self.current_input.strip()
        if not text:
            return
        self.history.append(text)
        if len(self.history) > settings.CONSOLE_HISTORY:
            self.history = self.history[-settings.CONSOLE_HISTORY :]
        self.output.append(f"> {text}")
        self.current_input = ""
        self.history_index = None

        parts = text.split()
        command_name = parts[0].lower()
        args = parts[1:]
        if command_name not in self.commands:
            self.output.append("Unknown command. Type 'help' for a list.")
            return
        try:
            response = self.commands[command_name].handler(args)
        except Exception as exc:  # noqa: BLE001 - we want robust console handling
            response = f"Error: {exc}"
        if response:
            for line in response.splitlines():
                self.output.append(line)

    def draw(self, surface: pygame.Surface) -> None:
        if not self.active:
            return

        overlay = pygame.Surface((surface.get_width(), surface.get_height() // 3), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, surface.get_height() - overlay.get_height()))

        y = surface.get_height() - overlay.get_height() + 10
        for line in self.output[-8:]:
            text_surface = self.font.render(line, True, pygame.Color(220, 220, 220))
            surface.blit(text_surface, (20, y))
            y += text_surface.get_height() + 4

        caret_surface = self.font.render("> " + self.current_input + ("_" if pygame.time.get_ticks() % 1000 < 500 else ""), True, pygame.Color(255, 255, 255)
        )
        surface.blit(caret_surface, (20, y + 6))

    def describe_commands(self) -> str:
        lines = [f"{cmd.name}: {cmd.description}" for cmd in self.commands.values()]
        return "\n".join(sorted(lines))

