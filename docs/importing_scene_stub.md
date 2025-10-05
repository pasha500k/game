# Unreal Scene Stub

This repository now includes a minimal Unreal Engine 5.5.4 project stub in `UnrealProject/`. The goal is to provide a starting
point for building the large-scale Chernobyl map described in `docs/chernobyl_game_plan.md`.

## Contents
- `ChernobylInfiltration.uproject` – associates the stub project with Unreal Engine 5.5.4 and registers the runtime module.
- `Source/ChernobylInfiltration/*.cs` – standard C++ module and target definitions required for generated project files.
- `Config/DefaultEngine.ini` – points both the editor and game startup maps to the included `Chernobyl_Ingress` scene.
- `Content/Maps/Chernobyl_Ingress.t3d` – a text-based T3D export that can be imported as a level. It includes placeholders for
  the sarcophagus entrance, the six reactor blocks, and the primary railway axis.

## Using the Scene Stub
1. Copy the `UnrealProject` directory into your Unreal workspace (e.g., alongside your `.uproject`).
2. In Unreal Editor 5.5.4, choose **File → New Level → Empty Level** to create a project, then import `Content/Maps/Chernobyl_Ingress.t3d`
   into the `/Game/Maps/` folder. UE will convert the T3D file into a `.umap` asset.
3. Replace the placeholder geometry with Nanite-enabled meshes that match the GIS layouts defined in the production plan.
4. Use the world partition data layers referenced in the plan to divide the map into zones (Pripyat, Enerhodar, checkpoints, etc.).
5. Commit the generated binary assets to a Perforce depot or Git LFS store rather than this documentation repository.

## Next Steps
- Replace the default pawn and game mode with the vehicle + infantry hybrid controller described in the roadmap.
- Populate runtime data layers with foliage, debris, and patrol routes before hooking up the AI behavior tree.
- Integrate radiation volumes and Geiger counter feedback using Unreal's environmental query system and gameplay cues.

This stub is intentionally lightweight so that designers have a concrete Unreal scene file to build upon without bloating the
repository with binary assets.
