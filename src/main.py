"""Entry point for the Elarian Skies 3D experience."""

from __future__ import annotations

from typing import Iterable

from ursina import Ursina, Vec3, application, time, window

from . import settings
from .console import CommandConsole
from .entities import DialogueLine, NPC, Player
from .story import StoryManager
from .ui import HUD
from .world import OpenWorld


def main() -> None:
    app = Ursina(title=settings.GAME_TITLE, vsync=True, borderless=False)
    window.fullscreen = False
    window.color = (0, 0, 0, 1)

    world = OpenWorld(settings.WORLD_SEED)
    player = Player(world.spawn_point)
    hud = HUD()
    console = CommandConsole()
    story_manager = StoryManager(world.beacons, world.guides)

    _register_console_commands(console, player, world, story_manager)

    def update() -> None:  # type: ignore[override]
        dt = time.dt
        if not console.enabled:
            player.update(dt)
        world.update(dt)
        story_manager.update(dt, player)
        hud.update(dt, player, story_manager, world.beacons)

    def input(key: str) -> None:  # type: ignore[override]
        if key == "`":
            console.toggle()
            return
        if console.enabled:
            console.feed_key(key)
            return
        if key == "escape":
            application.quit()
        elif key == "f11":
            window.fullscreen = not window.fullscreen
        elif key == "e":
            _interact_with_nearby(player, world.guides, story_manager, console)

    app.update = update  # type: ignore[assignment]
    app.input = input  # type: ignore[assignment]
    app.run()


def _interact_with_nearby(player: Player, guides: Iterable[NPC], story_manager: StoryManager, console: CommandConsole) -> None:
    nearest = None
    nearest_distance = settings.PLAYER_INTERACT_DISTANCE
    for guide in guides:
        distance = (guide.world_position - player.position).length()
        if distance <= nearest_distance:
            nearest_distance = distance
            nearest = guide
    if nearest is None:
        console.print_text("No one nearby to talk to.")
        return
    line = story_manager.interact_with_npc(nearest)
    if line:
        console.print_text(f"{line.speaker}: {line.text}")


def _register_console_commands(console: CommandConsole, player: Player, world: OpenWorld, story_manager: StoryManager) -> None:
    console.add_command("help", "Show available commands.", lambda args: console.describe_commands())
    console.add_command("heal", "heal [amount] — restore vitality.", lambda args: _cmd_heal(args, player))
    console.add_command("give", "give <item> [count] — add inventory items.", lambda args: _cmd_give(args, player))
    console.add_command("teleport", "teleport <x> <z> — warp to a surface coordinate.", lambda args: _cmd_teleport(args, player, world))
    console.add_command("time", "time <hours[:minutes]> — set the world time.", lambda args: _cmd_time(args, world))
    console.add_command("whereami", "Display current world coordinates.", lambda args: _cmd_whereami(player))
    console.add_command("quest", "Display the current objective list.", lambda args: _cmd_quest(story_manager))
    console.add_command("spawn", "spawn <name> — summon a guide.", lambda args: _cmd_spawn(args, player, world, story_manager))


def _cmd_heal(args: Iterable[str], player: Player) -> str:
    parts = list(args)
    amount = float(parts[0]) if parts else 40.0
    player.heal(amount)
    return f"Healed {amount:.0f} vitality."


def _cmd_give(args: Iterable[str], player: Player) -> str:
    parts = list(args)
    if not parts:
        raise ValueError("Usage: give <item> [count]")
    item = parts[0].title()
    count = int(parts[1]) if len(parts) > 1 else 1
    player.add_item(item, count)
    return f"Added {count}x {item}."


def _cmd_teleport(args: Iterable[str], player: Player, world: OpenWorld) -> str:
    parts = list(args)
    if len(parts) < 2:
        raise ValueError("Usage: teleport <x> <z>")
    x = float(parts[0])
    z = float(parts[1])
    y = world.height_at(x, z) + 3.0
    player.teleport(Vec3(x, y, z))
    return f"Teleported to ({x:.1f}, {y:.1f}, {z:.1f})."


def _cmd_time(args: Iterable[str], world: OpenWorld) -> str:
    parts = list(args)
    if not parts:
        raise ValueError("Usage: time <hours[:minutes]>")
    token = parts[0]
    if ":" in token:
        hour_str, minute_str = token.split(":", 1)
        hours = int(hour_str)
        minutes = int(minute_str)
    else:
        hours = int(token)
        minutes = 0
    total_seconds = ((hours % 24) + minutes / 60.0) / 24.0 * settings.DAY_LENGTH_SECONDS
    world.time_of_day = total_seconds
    return f"Set time to {hours:02d}:{minutes:02d}."


def _cmd_whereami(player: Player) -> str:
    pos = player.position
    return f"Position — x:{pos.x:.1f} y:{pos.y:.1f} z:{pos.z:.1f}"


def _cmd_quest(story_manager: StoryManager) -> str:
    lines = [f"Beacons lit: {story_manager.activated_beacons()}/{story_manager.total_beacons()}"]
    lines.extend(story_manager.quest_summary())
    return "\n".join(lines)


def _cmd_spawn(args: Iterable[str], player: Player, world: OpenWorld, story_manager: StoryManager) -> str:
    parts = list(args)
    if not parts:
        raise ValueError("Usage: spawn <name>")
    name = " ".join(word.capitalize() for word in parts)
    offset = Vec3(4.0, 0, 4.0)
    target = player.position + offset
    target_y = world.height_at(target.x, target.z) + 1.2
    dialogue = [
        DialogueLine(name, "I answer your call, Pathfinder."),
        DialogueLine(name, "Lead the way; the beacons await."),
    ]
    npc = NPC(name, Vec3(target.x, target_y, target.z), (255, 255, 255), dialogue)
    world.guides.append(npc)
    story_manager.guides.append(npc)
    return f"{name} joins you on the trail."


if __name__ == "__main__":
    main()
