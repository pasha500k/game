"""Entry point for the Elarian Skies adventure."""

from __future__ import annotations

import math
from typing import List

import pygame

from . import console, entities, settings, story, ui, world


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Elarian Skies")
        self.screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        self.tile_map = world.World(settings.WORLD_WIDTH, settings.WORLD_HEIGHT)
        self.player = entities.Player(self.tile_map.get_spawn_point())
        self.npcs: List[entities.NPC] = self._create_npcs()
        self.story_manager = story.StoryManager(self.tile_map.story_beacons)
        self.story_manager.push_event(
            "Awakening",
            "You emerge in the heart of Elaria as dawn paints the sky. Find Sage Aria within the central village.",
        )

        self.ui = ui.UIOverlay()
        self.console = console.Console(pygame.font.SysFont("consolas", settings.CONSOLE_FONT_SIZE))
        self._register_console_commands()

        self.game_time = 0.0
        self.camera = pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        self.journal_visible = True
        try:
            pygame.scrap.init()
        except pygame.error:
            pass

    def _create_npcs(self) -> List[entities.NPC]:
        spawn_x, spawn_y = self.tile_map.get_spawn_point()
        sage_dialogue = [
            entities.DialogueLine("Sage Aria", "Traveller, the Lumite has dimmed. Will you rekindle the beacons?"),
            entities.DialogueLine("Sage Aria", "The Radiant Compass will guide you—follow the hum in your chest."),
            entities.DialogueLine("Sage Aria", "When all five burn bright, return to me."),
        ]
        scout_dialogue = [
            entities.DialogueLine("Scout Ryn", "I mapped a glacier north-east of here. Beautiful, but treacherous."),
            entities.DialogueLine("Scout Ryn", "Keep an eye on your stamina while sprinting."),
        ]
        tinkerer_dialogue = [
            entities.DialogueLine("Tinkerer Lio", "I once crafted gliders. Bring me Lumite and I might build another."),
        ]
        return [
            entities.NPC("Sage Aria", pygame.Vector2(spawn_x + 120, spawn_y - 40), pygame.Color(200, 160, 255), sage_dialogue),
            entities.NPC("Scout Ryn", pygame.Vector2(spawn_x - 180, spawn_y + 140), pygame.Color(120, 200, 255), scout_dialogue),
            entities.NPC("Tinkerer Lio", pygame.Vector2(spawn_x + 80, spawn_y + 200), pygame.Color(255, 200, 120), tinkerer_dialogue),
        ]

    def _register_console_commands(self) -> None:
        self.console.add_command("help", "Show available commands.", lambda args: self.console.describe_commands())
        self.console.add_command("heal", "heal <amount> — restore vitality.", self._cmd_heal)
        self.console.add_command("give", "give <item> [count] — add items to inventory.", self._cmd_give)
        self.console.add_command("teleport", "teleport <x> <y> — move to tile coordinates.", self._cmd_teleport)
        self.console.add_command("time", "time <hours[:minutes]> — set the world time.", self._cmd_time)
        self.console.add_command("whereami", "Display current tile coordinates.", self._cmd_whereami)
        self.console.add_command("quest", "Display quest journal in console.", self._cmd_quest)
        self.console.add_command("spawn", "spawn <name> — conjure a friendly guide near you.", self._cmd_spawn)

    def _cmd_heal(self, args: List[str]) -> str:
        amount = float(args[0]) if args else 50
        self.player.heal(amount)
        return f"Vitality restored by {amount:.0f}."

    def _cmd_give(self, args: List[str]) -> str:
        if not args:
            raise ValueError("Usage: give <item> [count]")
        item = args[0].title()
        count = int(args[1]) if len(args) > 1 else 1
        self.player.add_item(item, count)
        return f"Added {count}x {item}."

    def _cmd_teleport(self, args: List[str]) -> str:
        if len(args) < 2:
            raise ValueError("Usage: teleport <x> <y>")
        tile_x, tile_y = int(args[0]), int(args[1])
        if not self.tile_map.is_walkable(tile_x, tile_y):
            raise ValueError("Destination not walkable.")
        self.player.position.update(tile_x * settings.TILE_SIZE + settings.TILE_SIZE / 2, tile_y * settings.TILE_SIZE + settings.TILE_SIZE / 2)
        return f"Teleported to tile ({tile_x}, {tile_y})."

    def _cmd_time(self, args: List[str]) -> str:
        if not args:
            raise ValueError("Usage: time <hours[:minutes]>")
        part = args[0]
        if ":" in part:
            hours_str, minutes_str = part.split(":", 1)
            hours = int(hours_str)
            minutes = int(minutes_str)
        else:
            hours = int(part)
            minutes = 0
        day_fraction = ((hours % 24) + minutes / 60.0) / 24.0
        self.game_time = day_fraction * settings.DAY_LENGTH_SECONDS
        return f"Time set to {hours:02d}:{minutes:02d}."

    def _cmd_whereami(self, args: List[str]) -> str:  # noqa: ARG002 - console API
        tile_x = int(self.player.position.x // settings.TILE_SIZE)
        tile_y = int(self.player.position.y // settings.TILE_SIZE)
        return f"You are at tile ({tile_x}, {tile_y})."

    def _cmd_quest(self, args: List[str]) -> str:  # noqa: ARG002 - console API
        return "\n".join(self.story_manager.quest_journal_text())

    def _cmd_spawn(self, args: List[str]) -> str:
        if not args:
            raise ValueError("Usage: spawn <name>")
        name = " ".join(word.capitalize() for word in args)
        position = self.player.position + pygame.Vector2(80, 0)
        dialogue = [
            entities.DialogueLine(name, "I have been summoned by the Radiant Compass."),
            entities.DialogueLine(name, "Lead on; the beacons call."),
        ]
        new_npc = entities.NPC(name, position, pygame.Color(255, 255, 255), dialogue)
        self.npcs.append(new_npc)
        return f"{name} joins you as a guide."

    def run(self) -> None:
        running = True
        while running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            self.game_time = (self.game_time + dt) % settings.DAY_LENGTH_SECONDS

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self.journal_visible = not self.journal_visible
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE,):
                    if self.console.active:
                        self.console.toggle()
                    else:
                        running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()
                self.console.handle_event(event)

            keys = pygame.key.get_pressed()
            if not self.console.active:
                self.player.handle_input(dt, self.tile_map, keys)
            self.player.update(dt)
            self.story_manager.update(dt)
            self.story_manager.check_beacon_proximity(self.player.position)

            if not self.console.active and keys[pygame.K_SPACE]:
                self._handle_interaction()

            self._update_camera()
            self._render()

        pygame.quit()

    def _handle_interaction(self) -> None:
        for npc in self.npcs:
            if self.player.position.distance_to(npc.position) <= npc.talk_radius:
                line = npc.interact()
                if line:
                    self.story_manager.push_event(line.speaker, line.text)
                    self.story_manager.notify_npc_interaction(npc.name)
                    self.story_manager.finalize_if_ready(npc.name)
                break

    def _update_camera(self) -> None:
        center_x = self.player.position.x - settings.SCREEN_WIDTH / 2
        center_y = self.player.position.y - settings.SCREEN_HEIGHT / 2
        self.camera.left = int(max(0, min(center_x, self.tile_map.width * settings.TILE_SIZE - settings.SCREEN_WIDTH)))
        self.camera.top = int(max(0, min(center_y, self.tile_map.height * settings.TILE_SIZE - settings.SCREEN_HEIGHT)))

    def _render(self) -> None:
        self.screen.fill((10, 10, 16))
        self.tile_map.draw(self.screen, self.camera)

        for beacon in self.tile_map.story_beacons:
            world_pos = (
                beacon[0] * settings.TILE_SIZE + settings.TILE_SIZE / 2 - self.camera.left,
                beacon[1] * settings.TILE_SIZE + settings.TILE_SIZE / 2 - self.camera.top,
            )
            pygame.draw.circle(self.screen, pygame.Color(255, 220, 120), world_pos, 14)
            pulse = 12 + 4 * math.sin(pygame.time.get_ticks() / 300)
            pygame.draw.circle(self.screen, pygame.Color(255, 220, 120, 60), world_pos, int(pulse), 2)

        for npc in self.npcs:
            npc.draw(self.screen, self.camera)

        self.player.draw(self.screen, self.camera)
        self._apply_lighting()
        self.ui.draw_hud(self.screen, self.player, self.game_time)
        if self.journal_visible:
            self.ui.draw_journal(self.screen, self.story_manager)
        self.ui.draw_story_prompt(self.screen, self.story_manager)
        self.ui.draw_minimap(self.screen, self.tile_map, self.player.get_rect(), self.camera)
        self.console.draw(self.screen)

        if self.story_manager.has_won():
            self._draw_victory_banner()

        pygame.display.flip()

    def _apply_lighting(self) -> None:
        day_progress = (self.game_time % settings.DAY_LENGTH_SECONDS) / settings.DAY_LENGTH_SECONDS
        overlay: pygame.Surface | None = None
        if 0.7 < day_progress <= 0.85:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill(settings.DUSK_TINT)
        elif day_progress > 0.85 or day_progress < 0.25:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill(settings.NIGHT_TINT)
        if overlay:
            self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    def _draw_victory_banner(self) -> None:
        banner = pygame.Surface((self.screen.get_width(), 120), pygame.SRCALPHA)
        banner.fill((20, 80, 60, 200))
        self.screen.blit(banner, (0, self.screen.get_height() // 2 - 60))
        font = pygame.font.SysFont("georgia", 48)
        text = font.render("Elaria is reborn. Thank you for playing!", True, pygame.Color(255, 255, 255))
        text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(text, text_rect)


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
