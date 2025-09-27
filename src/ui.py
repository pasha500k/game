"""Heads-up display and overlay rendering."""

from __future__ import annotations

from typing import List

import pygame

from . import settings, story, world


class UIOverlay:
    def __init__(self) -> None:
        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.large_font = pygame.font.SysFont("georgia", 32)

    def draw_hud(self, surface: pygame.Surface, player, current_time: float) -> None:
        self._draw_bars(surface, player)
        self._draw_clock(surface, current_time)

    def _draw_bars(self, surface: pygame.Surface, player) -> None:
        bar_width = 280
        bar_height = 20
        margin = 20

        def draw_bar(label: str, ratio: float, color: pygame.Color, offset: int) -> None:
            pygame.draw.rect(surface, pygame.Color(30, 30, 30), (margin, margin + offset, bar_width, bar_height), border_radius=8)
            inner_width = int(bar_width * max(0.0, min(1.0, ratio)))
            pygame.draw.rect(surface, color, (margin, margin + offset, inner_width, bar_height), border_radius=8)
            text = self.small_font.render(label, True, pygame.Color(255, 255, 255))
            surface.blit(text, (margin + 6, margin + offset - 2))

        draw_bar("Vitality", player.health / player.max_health, pygame.Color(200, 60, 60), 0)
        draw_bar("Stamina", player.energy / player.max_energy, pygame.Color(70, 200, 150), bar_height + 10)

    def _draw_clock(self, surface: pygame.Surface, current_time: float) -> None:
        day_progress = (current_time % settings.DAY_LENGTH_SECONDS) / settings.DAY_LENGTH_SECONDS
        hours = int(day_progress * 24)
        minutes = int((day_progress * 24 - hours) * 60)
        clock_text = self.font.render(f"Elarian Time {hours:02d}:{minutes:02d}", True, pygame.Color(255, 255, 255))
        surface.blit(clock_text, (settings.SCREEN_WIDTH - clock_text.get_width() - 20, 20))

    def draw_story_prompt(self, surface: pygame.Surface, story_manager: story.StoryManager) -> None:
        if not story_manager.active_event:
            return
        event = story_manager.active_event
        overlay = pygame.Surface((surface.get_width(), 140), pygame.SRCALPHA)
        overlay.fill((10, 10, 30, 180))
        surface.blit(overlay, (0, surface.get_height() - overlay.get_height() - 20))
        title_surface = self.large_font.render(event.title, True, pygame.Color(255, 210, 150))
        description_surface = self.font.render(event.description, True, pygame.Color(220, 220, 230))
        surface.blit(title_surface, (40, surface.get_height() - overlay.get_height()))
        surface.blit(description_surface, (40, surface.get_height() - overlay.get_height() + 50))

    def draw_journal(self, surface: pygame.Surface, story_manager: story.StoryManager) -> None:
        lines = story_manager.quest_journal_text()
        journal_width = 340
        journal_height = 200
        panel = pygame.Surface((journal_width, journal_height), pygame.SRCALPHA)
        panel.fill((10, 10, 10, 170))
        surface.blit(panel, (surface.get_width() - journal_width - 20, surface.get_height() - journal_height - 20))

        y = surface.get_height() - journal_height - 10
        for line in lines:
            text_surface = self.small_font.render(line, True, pygame.Color(230, 230, 240))
            surface.blit(text_surface, (surface.get_width() - journal_width + 10, y))
            y += text_surface.get_height() + 2

    def draw_minimap(self, surface: pygame.Surface, tile_map: world.World, player_rect: pygame.Rect, camera_rect: pygame.Rect) -> None:
        map_size = 200
        minimap = pygame.Surface((map_size, map_size))
        minimap.fill((0, 0, 0))

        scale_x = map_size / tile_map.width
        scale_y = map_size / tile_map.height

        for x in range(tile_map.width):
            for y in range(tile_map.height):
                tile = tile_map.tiles[x][y]
                color = tile.color
                minimap.set_at((int(x * scale_x), int(y * scale_y)), color)

        player_pos = (
            int(player_rect.centerx / settings.TILE_SIZE * scale_x),
            int(player_rect.centery / settings.TILE_SIZE * scale_y),
        )
        pygame.draw.circle(minimap, pygame.Color(255, 255, 255), player_pos, 4)

        surface.blit(minimap, (20, surface.get_height() - map_size - 20))
        border_rect = pygame.Rect(20, surface.get_height() - map_size - 20, map_size, map_size)
        pygame.draw.rect(surface, pygame.Color(255, 255, 255), border_rect, 2)

