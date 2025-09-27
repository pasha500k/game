"""Configuration values for the 3D Elarian Skies adventure."""

from __future__ import annotations

GAME_TITLE = "Elarian Skies: Lumite Horizon"
WORLD_SEED = 1047

# Terrain configuration
WORLD_SIZE = 480.0  # total width/depth of the explored island in world units
TERRAIN_STEP = 3.0  # distance between vertices used to build the terrain mesh
TERRAIN_AMPLITUDE = 18.0  # height scale of the noise-based terrain
TERRAIN_NOISE_SCALE = 0.0125

# Player configuration
PLAYER_WALK_SPEED = 6.2
PLAYER_SPRINT_MULTIPLIER = 1.65
PLAYER_JUMP_HEIGHT = 1.45
PLAYER_STAMINA_MAX = 120.0
PLAYER_STAMINA_DRAIN = 32.0
PLAYER_STAMINA_REGEN = 20.0
PLAYER_MAX_HEALTH = 120.0
PLAYER_HEAL_RATE = 5.0
PLAYER_INTERACT_DISTANCE = 6.5

# Lighting / time of day
DAY_LENGTH_SECONDS = 960.0  # sixteen-minute day/night cycle
SUNRISE_COLOR = (255, 210, 150)
MIDDAY_COLOR = (255, 255, 230)
SUNSET_COLOR = (255, 120, 120)
NIGHT_COLOR = (120, 150, 255)
NIGHT_AMBIENT = 0.12
MIDDAY_AMBIENT = 0.35

# Story and exploration
LUMITE_BEACON_COUNT = 6
BEACON_ACTIVATION_RADIUS = 8.0
GUIDE_DIALOGUE_COOLDOWN = 7.0
JOURNAL_MAX_ENTRIES = 9

# Console configuration
CONSOLE_HISTORY = 12
CONSOLE_MAX_COMMAND = 80

# UI
COMPASS_UPDATE_INTERVAL = 0.5
RETICLE_COLOR = (255, 255, 255)
HUD_TEXT_COLOR = (230, 230, 240)

__all__ = [name for name in globals() if name.isupper()]
