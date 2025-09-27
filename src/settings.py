"""Game configuration values."""

import pygame

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# World settings
TILE_SIZE = 64
WORLD_WIDTH = 80
WORLD_HEIGHT = 80
CAMERA_MARGIN = 160

# Player settings
PLAYER_SPEED = 220  # pixels per second
PLAYER_SPRINT_MULTIPLIER = 1.6
PLAYER_COLOR = pygame.Color(240, 230, 200)

# Lighting / day-night cycle
DAY_LENGTH_SECONDS = 480  # 8 minutes per full cycle
NIGHT_TINT = pygame.Color(30, 20, 60, 140)
DUSK_TINT = pygame.Color(90, 60, 120, 90)

# Story pacing
STORY_BEACON_RADIUS = 100
STORY_DIALOGUE_TIME = 5.0

# Console settings
CONSOLE_FONT_SIZE = 20
CONSOLE_HISTORY = 50
