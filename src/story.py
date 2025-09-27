"""Narrative and quest progression for the open-world adventure."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pygame

from . import settings


@dataclass
class StoryEvent:
    title: str
    description: str
    duration: float = settings.STORY_DIALOGUE_TIME


class StoryManager:
    def __init__(self, beacon_positions: List[tuple[int, int]]) -> None:
        self.beacons = beacon_positions
        self.current_stage = 0
        self.events: List[StoryEvent] = []
        self.active_timer = 0.0
        self.active_event: Optional[StoryEvent] = None
        self.objectives: List[str] = []
        self.completed_beacons: set[int] = set()
        self.artifact_energy = 0
        self._init_objectives()

    def _init_objectives(self) -> None:
        self.objectives = [
            "Talk to Sage Aria in the central village.",
            "Seek out the five Lumite beacons scattered across Elaria.",
            "Return to Sage Aria once all beacons resonate in harmony.",
        ]

    def push_event(self, title: str, description: str, duration: float | None = None) -> None:
        event = StoryEvent(title, description, duration or settings.STORY_DIALOGUE_TIME)
        self.events.append(event)

    def update(self, dt: float) -> None:
        if self.active_event:
            self.active_timer -= dt
            if self.active_timer <= 0:
                self.active_event = None
        elif self.events:
            self.active_event = self.events.pop(0)
            self.active_timer = self.active_event.duration

    def notify_npc_interaction(self, npc_name: str) -> None:
        if self.current_stage == 0 and npc_name == "Sage Aria":
            self.current_stage = 1
            self.push_event("A Call to the Lumite", "Aria entrusts you with the Radiant Compass. The beacons await.")

    def check_beacon_proximity(self, player_position: pygame.Vector2) -> None:
        for index, (bx, by) in enumerate(self.beacons):
            if index in self.completed_beacons:
                continue
            beacon_pos = pygame.Vector2(bx * settings.TILE_SIZE + settings.TILE_SIZE / 2, by * settings.TILE_SIZE + settings.TILE_SIZE / 2)
            if player_position.distance_to(beacon_pos) <= settings.STORY_BEACON_RADIUS:
                self.completed_beacons.add(index)
                self.artifact_energy += 1
                self.push_event(
                    f"Beacon {index + 1} Resonates",
                    "The Radiant Compass absorbs a surge of Lumite energy.",
                )
                if len(self.completed_beacons) == len(self.beacons):
                    self.current_stage = 2
                    self.push_event(
                        "All Beacons Aflame",
                        "Return to Sage Aria to weave the energies together.",
                    )
                break

    def quest_journal_text(self) -> List[str]:
        lines = ["Objectives:"]
        for idx, text in enumerate(self.objectives, start=1):
            completed = False
            if idx == 1 and self.current_stage > 0:
                completed = True
            if idx == 2 and len(self.completed_beacons) == len(self.beacons):
                completed = True
            if idx == 3 and self.current_stage == 3:
                completed = True
            status = "[✔]" if completed else "[ ]"
            lines.append(f" {status} {text}")
        lines.append("")
        lines.append(f"Beacons attuned: {len(self.completed_beacons)} / {len(self.beacons)}")
        return lines

    def finalize_if_ready(self, npc_name: str) -> None:
        if npc_name == "Sage Aria" and self.current_stage == 2:
            self.current_stage = 3
            self.push_event(
                "Harmony Forged",
                "Aria channels the collected Lumite, bathing Elaria in dawnlight. The darkness has been dispelled.",
            )

    def has_won(self) -> bool:
        return self.current_stage >= 3

