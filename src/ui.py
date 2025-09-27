"""Heads-up display elements for the adventure."""

from __future__ import annotations

import math
from typing import Iterable

from ursina import Entity, Text, camera, color

from . import settings
from .entities import Player
from .story import StoryManager
from .world import LumiteBeacon


class HUD(Entity):
    def __init__(self) -> None:
        super().__init__(parent=camera.ui)
        self.reticle = Text(text="✦", color=color.rgb(*settings.RETICLE_COLOR), origin=(0, 0), position=(0, 0))
        self.reticle.scale = 0.018

        self.health_bg = Entity(parent=self, model="quad", color=color.rgba(120, 20, 20, 200), position=(-0.7, -0.45), scale=(0.32, 0.028))
        self.health_fill = Entity(parent=self.health_bg, model="quad", color=color.rgb(255, 60, 60), scale=(1, 1), origin=(-0.5, 0))
        self.stamina_bg = Entity(parent=self, model="quad", color=color.rgba(20, 80, 20, 200), position=(-0.7, -0.50), scale=(0.32, 0.028))
        self.stamina_fill = Entity(parent=self.stamina_bg, model="quad", color=color.rgb(80, 220, 120), scale=(1, 1), origin=(-0.5, 0))

        self.notification_text = Text(parent=self, text="", position=(-0.7, 0.45), origin=(0, 0), scale=0.015, color=color.rgb(*settings.HUD_TEXT_COLOR))
        self.quest_text = Text(parent=self, text="", position=(0.55, 0.4), origin=(0.5, 0), scale=0.015, color=color.rgb(*settings.HUD_TEXT_COLOR))
        self.journal_text = Text(parent=self, text="", position=(0.65, 0.05), origin=(0.5, 0), scale=0.012, color=color.rgb(180, 220, 255), line_height=1.1)
        self.compass_text = Text(parent=self, text="", position=(0, -0.45), origin=(0, 0), scale=0.016, color=color.rgb(220, 230, 255))

        self._compass_timer = 0.0

    def update(self, dt: float, player: Player, story: StoryManager, beacons: Iterable[LumiteBeacon]) -> None:
        self.health_fill.scale_x = max(0.02, player.health_ratio())
        self.stamina_fill.scale_x = max(0.02, player.stamina_ratio())

        notifications = story.notifications()
        self.notification_text.text = "\n".join(notifications[:3])
        quest_lines = [f"Beacons lit: {story.activated_beacons()}/{story.total_beacons()}"] + story.quest_summary()
        self.quest_text.text = "\n".join(quest_lines)

        journal_lines = story.journal_entries()[:settings.JOURNAL_MAX_ENTRIES]
        if journal_lines:
            self.journal_text.text = "Journal:\n" + "\n".join(journal_lines)
        else:
            self.journal_text.text = ""

        self._compass_timer -= dt
        if self._compass_timer <= 0.0:
            self._compass_timer = settings.COMPASS_UPDATE_INTERVAL
            target = self._nearest_inactive_beacon(player.position, beacons)
            if target is None:
                self.compass_text.text = "Compass: All beacons restored"
            else:
                heading, distance = _heading_to_target(player.position, target.position)
                self.compass_text.text = f"Compass: {heading} — {int(distance)}m"

    def _nearest_inactive_beacon(self, position, beacons: Iterable[LumiteBeacon]) -> LumiteBeacon | None:
        inactive = [b for b in beacons if not b.activated]
        if not inactive:
            return None
        return min(inactive, key=lambda b: (b.world_position - position).length())


def _heading_to_target(origin, target):
    direction = target - origin
    distance = direction.length()
    angle = math.degrees(math.atan2(direction.x, direction.z)) % 360
    headings = [
        (0, "N"),
        (45, "NE"),
        (90, "E"),
        (135, "SE"),
        (180, "S"),
        (225, "SW"),
        (270, "W"),
        (315, "NW"),
    ]
    closest = min(headings, key=lambda item: abs(angle - item[0]))[1]
    return closest, distance
