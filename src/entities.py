"""Game entities such as the player and NPCs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import pygame

from . import settings, world


@dataclass
class DialogueLine:
    speaker: str
    text: str


@dataclass
class NPC:
    name: str
    position: pygame.Vector2
    color: pygame.Color
    dialogue: List[DialogueLine] = field(default_factory=list)
    dialogue_index: int = 0
    talk_radius: float = 80.0

    def interact(self) -> DialogueLine | None:
        if not self.dialogue:
            return None
        line = self.dialogue[self.dialogue_index]
        self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)
        return line

    def draw(self, surface: pygame.Surface, camera_rect: pygame.Rect) -> None:
        radius = 20
        screen_pos = (
            int(self.position.x - camera_rect.left),
            int(self.position.y - camera_rect.top),
        )
        pygame.draw.circle(surface, self.color, screen_pos, radius)
        name_font = pygame.font.SysFont("arial", 18)
        text_surface = name_font.render(self.name, True, pygame.Color(255, 255, 255))
        text_rect = text_surface.get_rect(center=(screen_pos[0], screen_pos[1] - radius - 12))
        surface.blit(text_surface, text_rect)


class Player:
    """The player's avatar exploring the world."""

    def __init__(self, position: Tuple[int, int]) -> None:
        self.position = pygame.Vector2(position)
        self.radius = 20
        self.speed = settings.PLAYER_SPEED
        self.health = 100
        self.max_health = 100
        self.energy = 100
        self.max_energy = 100
        self.inventory: Dict[str, int] = {"Lumite": 0, "Herbs": 0}
        self.active_effects: Dict[str, float] = {}
        self.facing = pygame.Vector2(1, 0)
        self.sprint_cooldown = 0.0

    def handle_input(self, dt: float, tile_map: world.World, keys: pygame.key.ScancodeWrapper) -> None:
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            direction.x += 1

        sprinting = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.facing = direction
        else:
            direction = pygame.Vector2(0, 0)

        speed = self.speed
        if sprinting and self.energy > 0:
            speed *= settings.PLAYER_SPRINT_MULTIPLIER
            self.energy = max(0, self.energy - 35 * dt)
        else:
            self.energy = min(self.max_energy, self.energy + 20 * dt)

        self.sprint_cooldown = max(0.0, self.sprint_cooldown - dt)

        self._move(direction * speed * dt, tile_map)

    def _move(self, movement: pygame.Vector2, tile_map: world.World) -> None:
        if movement.length_squared() == 0:
            return

        new_position = self.position + movement
        if self._is_position_walkable(new_position, tile_map):
            self.position = new_position
        else:
            # Try horizontal and vertical separately for sliding along edges
            horizontal = pygame.Vector2(movement.x, 0)
            vertical = pygame.Vector2(0, movement.y)
            if horizontal.length_squared() and self._is_position_walkable(self.position + horizontal, tile_map):
                self.position += horizontal
            elif vertical.length_squared() and self._is_position_walkable(self.position + vertical, tile_map):
                self.position += vertical

    def _is_position_walkable(self, position: pygame.Vector2, tile_map: world.World) -> bool:
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = (int(position.x), int(position.y))
        for sample in (
            rect.center,
            rect.topleft,
            rect.topright,
            rect.bottomleft,
            rect.bottomright,
        ):
            tile_x = int(sample[0] // settings.TILE_SIZE)
            tile_y = int(sample[1] // settings.TILE_SIZE)
            if not tile_map.is_walkable(tile_x, tile_y):
                return False
        return True

    def take_damage(self, amount: float) -> None:
        self.health = max(0, self.health - amount)

    def heal(self, amount: float) -> None:
        self.health = min(self.max_health, self.health + amount)

    def add_item(self, name: str, amount: int = 1) -> None:
        self.inventory[name] = self.inventory.get(name, 0) + amount

    def apply_effect(self, name: str, duration: float) -> None:
        self.active_effects[name] = duration

    def update(self, dt: float) -> None:
        to_remove = []
        for effect, time_left in self.active_effects.items():
            time_left -= dt
            if time_left <= 0:
                to_remove.append(effect)
        for effect in to_remove:
            del self.active_effects[effect]

    def draw(self, surface: pygame.Surface, camera_rect: pygame.Rect) -> None:
        screen_pos = (
            int(self.position.x - camera_rect.left),
            int(self.position.y - camera_rect.top),
        )
        pygame.draw.circle(surface, settings.PLAYER_COLOR, screen_pos, self.radius)
        pygame.draw.circle(surface, pygame.Color(60, 60, 60), screen_pos, self.radius, 2)

    def get_rect(self) -> pygame.Rect:
        rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        rect.center = (int(self.position.x), int(self.position.y))
        return rect

