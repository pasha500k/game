"""Story orchestration for Lumite Horizon."""

from __future__ import annotations

from collections import deque
from typing import Iterable, List

from . import settings
from .entities import DialogueLine, NPC, Player
from .world import LumiteBeacon


class StoryManager:
    """Keeps track of story beats, quest journal, and notifications."""

    def __init__(self, beacons: Iterable[LumiteBeacon], guides: Iterable[NPC]) -> None:
        self.beacons: List[LumiteBeacon] = list(beacons)
        self.guides: List[NPC] = list(guides)
        self.state = "introduction"
        self._journal: deque[str] = deque(maxlen=settings.JOURNAL_MAX_ENTRIES)
        self._notifications: deque[tuple[str, float]] = deque(maxlen=4)
        self.add_journal_entry("Find Sage Aria in the Radiant encampment.")

    # ------------------------------------------------------------------
    def add_journal_entry(self, text: str) -> None:
        self._journal.appendleft(text)
        self._notifications.appendleft((text, 6.0))

    def notify(self, text: str, duration: float = 5.0) -> None:
        self._notifications.appendleft((text, duration))

    def journal_entries(self) -> List[str]:
        return list(self._journal)

    def notifications(self) -> List[str]:
        return [text for text, _ in self._notifications]

    def update(self, dt: float, player: Player) -> None:
        # Update beacon proximity
        for beacon in self.beacons:
            if not beacon.activated and beacon.distance_to(player.position) <= settings.BEACON_ACTIVATION_RADIUS:
                beacon.activate()
                self.add_journal_entry(f"Lumite Beacon at {beacon.name} rekindled!")
                if self.state == "seeking_beacons":
                    remaining = len([b for b in self.beacons if not b.activated])
                    if remaining == 0:
                        self.state = "return_to_sage"
                        self.add_journal_entry("All beacons blaze again — return to Sage Aria.")
                elif self.state == "introduction":
                    self.state = "seeking_beacons"
                    self.add_journal_entry("Sage Aria's words echo — rekindle every Lumite beacon.")

        # Reduce notification timers
        trimmed: deque[tuple[str, float]] = deque(maxlen=self._notifications.maxlen)
        for text, timer in self._notifications:
            timer -= dt
            if timer > 0:
                trimmed.append((text, timer))
        self._notifications = trimmed

        for guide in self.guides:
            guide.cooldown = max(0.0, guide.cooldown - dt)

    def interact_with_npc(self, npc: NPC) -> DialogueLine | None:
        if npc.cooldown > 0.0:
            return None
        npc.cooldown = settings.GUIDE_DIALOGUE_COOLDOWN
        line = npc.speak()
        if line:
            self.notify(f"{line.speaker}: {line.text}")
            if npc.name == "Sage Aria" and self.state == "introduction":
                self.state = "seeking_beacons"
                self.add_journal_entry("The Sage gifted a Radiant Compass — seek the beacons.")
            elif npc.name == "Sage Aria" and self.state == "return_to_sage":
                self.state = "victory"
                self.add_journal_entry("Elaria is reborn. Enjoy the celebration fireworks!")
        return line

    def quest_summary(self) -> List[str]:
        if self.state == "introduction":
            hint = "Meet Sage Aria."
        elif self.state == "seeking_beacons":
            remaining = len([b for b in self.beacons if not b.activated])
            hint = f"Rekindle remaining beacons ({remaining})."
        elif self.state == "return_to_sage":
            hint = "Return to Sage Aria in the Radiant encampment."
        else:
            hint = "Explore the skies and enjoy the serenity."
        return [hint]

    def activated_beacons(self) -> int:
        return len([b for b in self.beacons if b.activated])

    def total_beacons(self) -> int:
        return len(self.beacons)
