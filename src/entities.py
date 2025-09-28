"""Entity definitions for the 3D adventure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from ursina import Entity, Text, Vec3, color, held_keys
from ursina.prefabs.first_person_controller import FirstPersonController

from . import settings


@dataclass
class DialogueLine:
    speaker: str
    text: str


class Player:
    """Wrapper around Ursina's first person controller with RPG stats."""

    def __init__(self, position: Vec3) -> None:
        self.controller = FirstPersonController(position=position, speed=settings.PLAYER_WALK_SPEED)
        self.controller.cursor.visible = False
        self.controller.gravity = 1.0
        self.controller.jump_height = settings.PLAYER_JUMP_HEIGHT
        self.controller.mouse_sensitivity = Vec3(120, 120, 120)

        self.health = settings.PLAYER_MAX_HEALTH
        self.stamina = settings.PLAYER_STAMINA_MAX
        self.inventory: Dict[str, int] = {}
        self._sprinting: bool = False

    # ------------------------------------------------------------------
    @property
    def position(self) -> Vec3:
        return self.controller.position

    @position.setter
    def position(self, value: Vec3) -> None:
        self.controller.position = value

    def update(self, dt: float) -> None:
        moving = any(held_keys[key] for key in ("w", "a", "s", "d"))
        sprinting = moving and held_keys["shift"] and self.stamina > 0.0
        self._sprinting = sprinting
        target_speed = settings.PLAYER_WALK_SPEED * (settings.PLAYER_SPRINT_MULTIPLIER if sprinting else 1.0)
        self.controller.speed = target_speed

        if sprinting:
            self.stamina = max(0.0, self.stamina - settings.PLAYER_STAMINA_DRAIN * dt)
        else:
            regen = settings.PLAYER_STAMINA_REGEN * (1.4 if self.controller.grounded else 0.6)
            self.stamina = min(settings.PLAYER_STAMINA_MAX, self.stamina + regen * dt)

    def heal(self, amount: float) -> None:
        self.health = min(settings.PLAYER_MAX_HEALTH, self.health + amount)

    def apply_damage(self, amount: float) -> None:
        self.health = max(0.0, self.health - amount)

    def add_item(self, name: str, count: int = 1) -> None:
        self.inventory[name] = self.inventory.get(name, 0) + max(1, count)

    def teleport(self, destination: Vec3) -> None:
        self.position = destination

    def stamina_ratio(self) -> float:
        return self.stamina / settings.PLAYER_STAMINA_MAX

    def health_ratio(self) -> float:
        return self.health / settings.PLAYER_MAX_HEALTH


class NPC(Entity):
    """A guide or quest giver the player can interact with."""

    def __init__(self, name: str, position: Vec3, tint: tuple[int, int, int], dialogue: Iterable[DialogueLine]) -> None:
        super().__init__(model="cube", color=color.rgb(*tint), scale=(1.2, 2.4, 1.2), position=position)
        self.name = name
        self._lines: List[DialogueLine] = list(dialogue)
        self._index = 0
        self._label = Text(parent=self, text=name, color=color.white, y=1.6, billboard=True, origin=(0, 0))
        self.cooldown = 0.0

    def speak(self) -> DialogueLine | None:
        if not self._lines:
            return None
        line = self._lines[self._index % len(self._lines)]
        self._index += 1
        return line
