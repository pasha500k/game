"""3D world generation and environmental systems."""

from __future__ import annotations

import math
import random
from typing import Iterable, List

from perlin_noise import PerlinNoise
from ursina import (
    AmbientLight,
    DirectionalLight,
    Entity,
    Mesh,
    PointLight,
    Sky,
    Vec3,
    color,
)

from . import settings
from .entities import DialogueLine, NPC


class LumiteBeacon(Entity):
    """A crystalline spire the player must ignite."""

    def __init__(self, name: str, position: Vec3) -> None:
        super().__init__(
            model="cube",
            color=color.rgb(50, 180, 255),
            scale=(2.2, 6.5, 2.2),
            position=position,
        )
        self.name = name
        self.activated = False
        self._light = PointLight(parent=self, y=3.4, color=color.rgb(90, 200, 255), intensity=1.2)
        self._light.enabled = False
        self._core = Entity(parent=self, model="sphere", color=color.rgb(200, 255, 255), scale=1.4, y=2.4)

    def activate(self) -> None:
        if self.activated:
            return
        self.activated = True
        self.color = color.rgb(220, 255, 255)
        self._light.enabled = True
        self._core.color = color.rgb(255, 255, 200)

    def distance_to(self, position: Vec3) -> float:
        return (self.world_position - position).length()

    def update(self, dt: float) -> None:
        self.rotation_y += dt * 18
        if self.activated:
            self._core.y = 2.4 + math.sin(self.rotation_y * 0.2) * 0.3


class OpenWorld:
    """Procedurally generated island with day/night cycle."""

    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed if seed is not None else settings.WORLD_SEED
        self.random = random.Random(self.seed)
        self.noise = PerlinNoise(octaves=5, seed=self.seed)
        self.size = settings.WORLD_SIZE
        self.step = settings.TERRAIN_STEP
        self.half = self.size / 2
        self.water_level = -3.0
        self.time_of_day = 0.0

        self.resolution = int(self.size / self.step) + 1
        self.height_map: List[List[float]] = [
            [self._sample_height(ix, iz) for iz in range(self.resolution)] for ix in range(self.resolution)
        ]

        self.terrain = Entity(
            model=self._build_mesh(),
            collider="mesh",
        )
        self.water = Entity(
            model="plane",
            scale=(self.size, self.size, 1),
            position=Vec3(0, self.water_level, 0),
            color=color.rgba(40, 80, 140, 160),
            double_sided=True,
        )
        self.sky = Sky(color=color.rgb(100, 150, 200))
        self.sun = DirectionalLight(direction=Vec3(0.3, -0.8, -0.3), color=color.rgb(*settings.SUNRISE_COLOR))
        self.ambient = AmbientLight(color=color.rgba(120, 150, 200, int(settings.MIDDAY_AMBIENT * 255)))

        self.decorations: List[Entity] = []
        self.beacons: List[LumiteBeacon] = []
        self.guides: List[NPC] = []
        self._scatter_foliage()
        self._place_encampments()
        self._place_beacons()

        self.spawn_point = self._find_spawn_point()

    # ------------------------------------------------------------------
    def _sample_height(self, ix: int, iz: int) -> float:
        x = ix * self.step - self.half
        z = iz * self.step - self.half
        nx = x * settings.TERRAIN_NOISE_SCALE
        nz = z * settings.TERRAIN_NOISE_SCALE
        elevation = self.noise([nx, nz])
        hill = math.cos(nx * 2.2) * math.sin(nz * 2.0) * 0.2
        height = (elevation + hill) * settings.TERRAIN_AMPLITUDE
        if height < self.water_level + 1.5:
            height = self.water_level + self.random.uniform(0.0, 1.4)
        return height

    def _build_mesh(self) -> Mesh:
        vertices: List[Vec3] = []
        triangles: List[int] = []
        colors: List[Vec3] = []
        for ix in range(self.resolution):
            for iz in range(self.resolution):
                x = ix * self.step - self.half
                z = iz * self.step - self.half
                y = self.height_map[ix][iz]
                vertices.append(Vec3(x, y, z))
                colors.append(self._color_for_height(y))
        row = self.resolution
        for ix in range(row - 1):
            for iz in range(row - 1):
                i = ix * row + iz
                triangles.extend([i, i + row, i + 1, i + 1, i + row, i + row + 1])
        return Mesh(vertices=vertices, triangles=triangles, colors=colors, mode="triangle")

    def _color_for_height(self, height: float) -> Vec3:
        if height < self.water_level + 0.6:
            return Vec3(0.2, 0.35, 0.55)
        if height < self.water_level + 2.5:
            return Vec3(0.65, 0.6, 0.45)
        if height < 8:
            return Vec3(0.2, 0.55, 0.25)
        if height < 14:
            return Vec3(0.35, 0.45, 0.35)
        return Vec3(0.75, 0.75, 0.8)

    def _scatter_foliage(self) -> None:
        for _ in range(250):
            pos = self._random_surface_point(radius_range=(30, self.half - 10))
            tree_height = self.random.uniform(3.5, 6.5)
            trunk = Entity(
                model="cube",
                position=pos + Vec3(0, tree_height * 0.5, 0),
                scale=(1.0, tree_height, 1.0),
                color=color.rgb(90, 60, 35),
            )
            canopy = Entity(
                parent=trunk,
                model="sphere",
                position=Vec3(0, tree_height * 0.55, 0),
                scale=tree_height * 0.9,
                color=color.rgb(40, self.random.randint(120, 170), 40),
            )
            self.decorations.extend([trunk, canopy])

    def _place_encampments(self) -> None:
        camp_positions = [self._random_surface_point(radius_range=(15, 70)) for _ in range(3)]
        for index, pos in enumerate(camp_positions):
            fire = Entity(
                model="sphere",
                position=pos + Vec3(0, 1.0, 0),
                color=color.rgb(255, 150, 60),
                scale=1.2,
            )
            brazier = Entity(model="cylinder", position=pos, color=color.rgb(80, 50, 30), scale=(2.4, 0.8, 2.4))
            self.decorations.extend([fire, brazier])
            if index == 0:
                self.encampment_center = pos
                self._create_guides(pos)

    def _create_guides(self, center: Vec3) -> None:
        base_height = center.y + 1.2
        sage_dialogue = [
            DialogueLine("Sage Aria", "The Lumite dimmed when the sky-rifts opened."),
            DialogueLine("Sage Aria", "Follow the compass glow on your wrist; it points to the nearest beacon."),
        ]
        scout_dialogue = [
            DialogueLine("Scout Ryn", "Glide down ridges to conserve stamina, sprint on the plains."),
            DialogueLine("Scout Ryn", "The crystal caverns eastward shimmer brighter at dusk."),
        ]
        tinkerer_dialogue = [
            DialogueLine("Tinkerer Lio", "I've tuned the jump coils on your boots — try leaping at the aurora spires."),
            DialogueLine("Tinkerer Lio", "If you gather shards, bring them and I'll craft sky lanterns."),
        ]
        self.guides.append(
            NPC("Sage Aria", Vec3(center.x + 4.0, base_height, center.z - 2.0), (220, 190, 255), sage_dialogue)
        )
        self.guides.append(
            NPC("Scout Ryn", Vec3(center.x - 3.5, base_height, center.z + 3.5), (160, 210, 255), scout_dialogue)
        )
        self.guides.append(
            NPC("Tinkerer Lio", Vec3(center.x + 2.5, base_height, center.z + 5.0), (255, 210, 160), tinkerer_dialogue)
        )

    def _place_beacons(self) -> None:
        used_positions: List[Vec3] = []
        for idx in range(settings.LUMITE_BEACON_COUNT):
            pos = self._random_surface_point(radius_range=(70, self.half - 12))
            if any((pos - other).length() < 25 for other in used_positions):
                pos = pos + Vec3(self.random.uniform(-10, 10), 0, self.random.uniform(-10, 10))
            used_positions.append(pos)
            beacon = LumiteBeacon(name=f"Beacon {idx + 1}", position=pos + Vec3(0, 4.0, 0))
            self.beacons.append(beacon)

    def _random_surface_point(self, radius_range: tuple[float, float]) -> Vec3:
        radius = self.random.uniform(*radius_range)
        angle = self.random.uniform(0, math.tau)
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius
        y = self.height_at(x, z)
        return Vec3(x, y, z)

    def _find_spawn_point(self) -> Vec3:
        if hasattr(self, "encampment_center"):
            base = self.encampment_center
        else:
            base = Vec3(0, self.height_at(0, 0), 0)
        return base + Vec3(0, 4.0, 0)

    # ------------------------------------------------------------------
    def height_at(self, x: float, z: float) -> float:
        sx = (x + self.half) / self.step
        sz = (z + self.half) / self.step
        x0 = max(0, min(int(math.floor(sx)), self.resolution - 2))
        z0 = max(0, min(int(math.floor(sz)), self.resolution - 2))
        tx = sx - x0
        tz = sz - z0
        h00 = self.height_map[x0][z0]
        h10 = self.height_map[x0 + 1][z0]
        h01 = self.height_map[x0][z0 + 1]
        h11 = self.height_map[x0 + 1][z0 + 1]
        h0 = h00 * (1 - tx) + h10 * tx
        h1 = h01 * (1 - tx) + h11 * tx
        return h0 * (1 - tz) + h1 * tz

    def update(self, dt: float) -> None:
        self.time_of_day = (self.time_of_day + dt) % settings.DAY_LENGTH_SECONDS
        phase = self.time_of_day / settings.DAY_LENGTH_SECONDS
        theta = phase * math.tau
        sun_y = math.sin(theta)
        self.sun.direction = Vec3(math.cos(theta) * 0.5, -max(0.1, sun_y), math.sin(theta) * 0.5)
        color_mix = self._sun_color_for_phase(phase)
        self.sun.color = color_mix
        ambient_value = settings.NIGHT_AMBIENT + max(0.0, sun_y) * (settings.MIDDAY_AMBIENT - settings.NIGHT_AMBIENT)
        self.ambient.color = color.rgba(150, 170, 220, int(ambient_value * 255))
        self.sky.color = color_mix.tint(0.5)
        for beacon in self.beacons:
            beacon.update(dt)

    def _sun_color_for_phase(self, phase: float):
        if phase < 0.25:
            t = phase / 0.25
            return color.rgb(*_lerp_color(settings.SUNRISE_COLOR, settings.MIDDAY_COLOR, t))
        if phase < 0.5:
            t = (phase - 0.25) / 0.25
            return color.rgb(*_lerp_color(settings.MIDDAY_COLOR, settings.SUNSET_COLOR, t))
        if phase < 0.75:
            t = (phase - 0.5) / 0.25
            return color.rgb(*_lerp_color(settings.SUNSET_COLOR, settings.NIGHT_COLOR, t))
        t = (phase - 0.75) / 0.25
        return color.rgb(*_lerp_color(settings.NIGHT_COLOR, settings.SUNRISE_COLOR, t))

    def guides_for_story(self) -> Iterable[Entity]:
        return self.guides


def _lerp_color(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(ax + (bx - ax) * t) for ax, bx in zip(a, b))
