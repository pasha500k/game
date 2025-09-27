"""Procedurally generated open world."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import pygame

from . import settings


@dataclass(frozen=True)
class TileType:
    """Describes a type of tile in the overworld."""

    name: str
    color: pygame.Color
    walkable: bool
    movement_cost: float = 1.0


TILE_TYPES: Dict[str, TileType] = {
    "deep_water": TileType("Deep Water", pygame.Color(12, 34, 120), False),
    "water": TileType("Water", pygame.Color(20, 80, 180), False),
    "sand": TileType("Sandy Shore", pygame.Color(210, 190, 120), True, 1.1),
    "grass": TileType("Grassland", pygame.Color(60, 160, 70), True),
    "forest": TileType("Forest", pygame.Color(40, 110, 50), True, 1.2),
    "mountain": TileType("Mountain", pygame.Color(110, 100, 110), True, 1.6),
    "snow": TileType("Snow Peaks", pygame.Color(240, 245, 250), True, 1.8),
    "town": TileType("Settled Grounds", pygame.Color(190, 120, 90), True, 0.9),
}


def _smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)


def _value_noise(x: float, y: float, seed: int) -> float:
    """Generate deterministic noise in [0, 1)."""

    x0 = math.floor(x)
    y0 = math.floor(y)
    xf = x - x0
    yf = y - y0

    def _rand(ix: int, iy: int) -> float:
        m = 0x5bd1e995
        n = (ix * 374761393 + iy * 668265263 + seed * 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        n = (n ^ (n >> 13)) * m & 0xFFFFFFFFFFFFFFFF
        n = (n ^ (n >> 15)) * m & 0xFFFFFFFFFFFFFFFF
        n = n ^ (n >> 13)
        return ((n & 0xFFFFFFFF) / 0xFFFFFFFF)

    v00 = _rand(x0, y0)
    v10 = _rand(x0 + 1, y0)
    v01 = _rand(x0, y0 + 1)
    v11 = _rand(x0 + 1, y0 + 1)

    u = _smoothstep(xf)
    v = _smoothstep(yf)

    i1 = v00 + (v10 - v00) * u
    i2 = v01 + (v11 - v01) * u
    return i1 + (i2 - i1) * v


def _fractal_noise(x: float, y: float, seed: int, octaves: int = 4, lacunarity: float = 2.0, persistence: float = 0.5) -> float:
    value = 0.0
    amplitude = 1.0
    frequency = 1.0
    for _ in range(octaves):
        value += amplitude * _value_noise(x * frequency, y * frequency, seed)
        amplitude *= persistence
        frequency *= lacunarity
    return value


class World:
    """Procedural world made of tiles with points of interest."""

    def __init__(self, width: int, height: int, seed: int | None = None) -> None:
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.tiles: List[List[TileType]] = [[TILE_TYPES["grass"] for _ in range(height)] for _ in range(width)]
        self.points_of_interest: List[Tuple[Tuple[int, int], str]] = []
        self.story_beacons: List[Tuple[int, int]] = []
        self.villages: List[Tuple[int, int]] = []
        self._generate()

    def _generate(self) -> None:
        for x in range(self.width):
            for y in range(self.height):
                nx = x / self.width - 0.5
                ny = y / self.height - 0.5
                height_noise = _fractal_noise(nx * 4, ny * 4, self.seed)
                moisture_noise = _fractal_noise(nx * 4 + 40, ny * 4 + 40, self.seed // 2 + 7)

                height_value = height_noise / 2.0  # Normalize roughly between 0-1
                moisture_value = moisture_noise / 2.0

                tile = self._select_tile(height_value, moisture_value)
                self.tiles[x][y] = tile

        self._stamp_regions()
        self._place_story_beacons()

    def _select_tile(self, height_value: float, moisture_value: float) -> TileType:
        if height_value < 0.20:
            return TILE_TYPES["deep_water"]
        if height_value < 0.27:
            return TILE_TYPES["water"]
        if height_value < 0.32:
            return TILE_TYPES["sand"]
        if height_value > 0.75:
            if height_value > 0.9:
                return TILE_TYPES["snow"]
            return TILE_TYPES["mountain"]
        if moisture_value > 0.75:
            return TILE_TYPES["forest"]
        return TILE_TYPES["grass"]

    def _stamp_regions(self) -> None:
        random.seed(self.seed)
        for _ in range(12):
            tx = random.randint(6, self.width - 6)
            ty = random.randint(6, self.height - 6)
            for x in range(tx - 3, tx + 4):
                for y in range(ty - 3, ty + 4):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if random.random() < 0.7:
                            self.tiles[x][y] = TILE_TYPES["town"]
            self.villages.append((tx, ty))
            self.points_of_interest.append(((tx * settings.TILE_SIZE, ty * settings.TILE_SIZE), "Village of Emberdale"))

        mountain_candidates = [(random.randint(2, self.width - 2), random.randint(2, self.height - 2)) for _ in range(5)]
        for mx, my in mountain_candidates:
            for x in range(mx - 2, mx + 3):
                for y in range(my - 2, my + 3):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.tiles[x][y] = TILE_TYPES["mountain"]
            self.points_of_interest.append(((mx * settings.TILE_SIZE, my * settings.TILE_SIZE), "Crystal Ridge"))

        forest_centers = [(random.randint(4, self.width - 4), random.randint(4, self.height - 4)) for _ in range(8)]
        for fx, fy in forest_centers:
            for x in range(fx - 4, fx + 5):
                for y in range(fy - 4, fy + 5):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        if random.random() < 0.6:
                            self.tiles[x][y] = TILE_TYPES["forest"]
            self.points_of_interest.append(((fx * settings.TILE_SIZE, fy * settings.TILE_SIZE), "Whispering Woods"))

    def _place_story_beacons(self) -> None:
        random.seed(self.seed + 42)
        candidates: List[Tuple[int, int]] = []
        while len(candidates) < 5:
            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)
            tile = self.tiles[x][y]
            if tile.walkable:
                candidates.append((x, y))
        self.story_beacons = candidates
        for idx, (bx, by) in enumerate(self.story_beacons, start=1):
            self.points_of_interest.append(((bx * settings.TILE_SIZE, by * settings.TILE_SIZE), f"Beacon {idx}"))

    def get_tile(self, tile_x: int, tile_y: int) -> TileType:
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            return self.tiles[tile_x][tile_y]
        return TILE_TYPES["water"]

    def is_walkable(self, tile_x: int, tile_y: int) -> bool:
        return self.get_tile(tile_x, tile_y).walkable

    def draw(self, surface: pygame.Surface, camera_rect: pygame.Rect) -> None:
        start_x = max(camera_rect.left // settings.TILE_SIZE, 0)
        end_x = min((camera_rect.right // settings.TILE_SIZE) + 2, self.width)
        start_y = max(camera_rect.top // settings.TILE_SIZE, 0)
        end_y = min((camera_rect.bottom // settings.TILE_SIZE) + 2, self.height)

        tile_rect = pygame.Rect(0, 0, settings.TILE_SIZE, settings.TILE_SIZE)
        for tile_x in range(start_x, end_x):
            for tile_y in range(start_y, end_y):
                tile = self.tiles[tile_x][tile_y]
                tile_rect.topleft = (
                    tile_x * settings.TILE_SIZE - camera_rect.left,
                    tile_y * settings.TILE_SIZE - camera_rect.top,
                )
                pygame.draw.rect(surface, tile.color, tile_rect)

                if tile.name == "Forest" and (tile_x + tile_y) % 3 == 0:
                    pygame.draw.circle(
                        surface,
                        pygame.Color(20, 70, 30),
                        tile_rect.center,
                        settings.TILE_SIZE // 3,
                    )
                elif tile.name == "Settled Grounds" and (tile_x + tile_y) % 4 == 0:
                    house_rect = tile_rect.inflate(-settings.TILE_SIZE // 3, -settings.TILE_SIZE // 3)
                    pygame.draw.rect(surface, pygame.Color(180, 90, 60), house_rect)
                    pygame.draw.rect(surface, pygame.Color(80, 40, 30), house_rect.move(0, house_rect.height // 3))
                elif tile is TILE_TYPES["mountain"] and (tile_x + tile_y) % 5 == 0:
                    pygame.draw.polygon(
                        surface,
                        pygame.Color(200, 200, 220),
                        [
                            (tile_rect.centerx, tile_rect.top),
                            (tile_rect.left + tile_rect.width * 0.2, tile_rect.bottom),
                            (tile_rect.right - tile_rect.width * 0.2, tile_rect.bottom),
                        ],
                    )
                elif tile is TILE_TYPES["snow"] and (tile_x + tile_y) % 4 == 0:
                    pygame.draw.circle(
                        surface,
                        pygame.Color(255, 255, 255),
                        (tile_rect.centerx, tile_rect.top + settings.TILE_SIZE // 4),
                        settings.TILE_SIZE // 5,
                    )

    def get_spawn_point(self) -> Tuple[int, int]:
        return (self.width // 2 * settings.TILE_SIZE, self.height // 2 * settings.TILE_SIZE)

    def iter_points_of_interest(self) -> Iterable[Tuple[Tuple[int, int], str]]:
        return list(self.points_of_interest)

