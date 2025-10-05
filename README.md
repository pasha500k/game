# Chernobyl Infiltration Game Documentation

This repository contains high-level design documentation for a proposed Unreal Engine 5.5.4 project focused on infiltrating the Chernobyl Nuclear Power Plant while managing vehicle traversal, radiation hazards, and security forces.

## Contents
- `docs/chernobyl_game_plan.md` – Production roadmap, feature pillars, risk assessment, and milestone checklist.
- `docs/importing_scene_stub.md` – Instructions for using the provided Unreal Engine scene stub.
- `UnrealProject/` – Minimal Unreal Engine 5.5.4 project scaffold with an importable level layout.

## Getting Started
1. Review the master plan document to understand scope, timeline, and team needs.
2. Copy the `UnrealProject/` stub into your workspace and import the `Content/Maps/Chernobyl_Ingress.t3d` level as described in the scene stub guide.
3. Create an Unreal Engine 5.5.4 project using the plan's recommendations for World Partition, Nanite, and Lumen.
4. Establish source control (Git LFS or Perforce) and continuous integration before importing large assets.

## Contribution Guidelines
- Use feature branches for major tasks.
- Update the plan document after each milestone to keep scope, risks, and deliverables current.
- Store large binary assets (e.g., textures, meshes) outside of Git or with LFS to prevent repository bloat.

## License
See [LICENSE](LICENSE) for licensing details.
