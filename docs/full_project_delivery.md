# Full Production Delivery Requirements

Producing a "ready to play" Unreal Engine 5.5.4 project that authentically recreates the entire Chernobyl Exclusion Zone requires
significant content creation, tooling, and team bandwidth that cannot be stored directly in this lightweight repository. The
sections below summarize the scope of work, recommended asset sources, and integration workflow needed to turn the existing
prototype scaffold into a shipping-quality build.

## 1. Core Content Expectations

| Domain | Minimum Deliverables | Notes |
| --- | --- | --- |
| **World Geography** | 30×30 km landscape with World Partition cells, Nanite meshes for hero areas, optimized HLOD for distant terrain. | Import DEM/heightmap data via Houdini or Gaea; bake blended landscape materials with runtime virtual textures. |
| **Infrastructure** | Complete road and rail networks, checkpoints, electrical substations, six RBMK units, turbine halls, cooling towers, NSC sarcophagus. | Recommend using modular kits for industrial structures; rely on vertex-painted decals for wear and damage. |
| **Settlements** | Pripyat city blocks, Chernobyl town, surrounding villages, industrial yards, harbor, and river port. | Utilize photogrammetry packs for building facades; integrate megascan foliage for overgrowth. |
| **Gameplay Systems** | Chaos vehicle pawn, radiation simulation, AI patrols, stealth tools, inventory, mission scripting, cinematics. | Break features into network of feature plugins to keep core module maintainable. |
| **Audio & UI** | Spatialized ambience, vehicle foley, Geiger counter, dynamic soundtrack, diegetic HUD and mission briefings. | Implement Wwise or Unreal Audio Mixer with data tables for region-specific ambience. |

## 2. Recommended Plugins & Middleware

1. **Chaos Vehicle Advanced** – Foundation for multi-axle transport physics, tire blowouts, suspension tuning.
2. **Lyra Starter Game Components** – Modular gameplay ability system, input mapping context, camera handling.
3. **Houdini Engine** – Procedural generation for roads, debris fields, and prop scattering.
4. **World Partition Editor Utilities** – Automate cell streaming profiles for exploration vs. mission scenarios.
5. **Radiation Simulation Plugin (Custom)** – C++ module exposing radiation volumes, inverse-square falloff, gear modifiers.
6. **AI Behavior Toolkit** – Use Behavior Trees, EQS, and smart objects for checkpoints, search patterns, and diversions.
7. **Niagara FX Libraries** – Weather FX (rain, fog), radiation particle cues, vehicle exhaust.

> **Source Control Note:** All binary assets and plugins should be tracked with Git LFS or Perforce. Keep this public repository focused on
text-based configuration, documentation, and build scripts.

## 3. Build & Integration Pipeline

1. **Project Cloning**: Fork this repository and enable Git LFS (`git lfs install`) before adding binary assets.
2. **Engine Setup**: Install Unreal Engine 5.5.4 via Epic Games Launcher. Enable listed plugins in `Edit → Plugins` and restart.
3. **Landscape Import**:
   - Acquire DEM data (SRTM, Copernicus) and satellite imagery.
   - Process in Houdini to generate tiled heightmaps and masks.
   - Import into Unreal using World Partition + Landscape system with auto-material.
4. **Streaming Configuration**:
   - Define streaming sources for vehicle spawn, mission hubs, and high-density POIs.
   - Bake HLOD for large structures; validate memory footprint in `Stat Streaming`.
5. **Gameplay Modules**:
   - Implement vehicle, radiation, and AI systems as separate C++ modules to decouple dependencies.
   - Expose Blueprint-accessible components for designers (e.g., `URadiationFieldComponent`, `UVehicleVitalsComponent`).
6. **Mission Scripting**:
   - Author mission flow in Level Sequences and Data Assets.
   - Use Gameplay Ability System for stealth tools (jammers, disguises, noise makers).
7. **Testing & Optimization**:
   - Profile with Unreal Insights; capture GPU/CPU baselines per zone.
   - Perform streaming stress tests by driving across entire map; adjust cell size and distance-based activation.
8. **Packaging**:
   - Configure build settings in `Config/DefaultGame.ini` and `DefaultEngine.ini` for shipping builds.
   - Automate nightly builds with Unreal Automation Tool (UAT) scripts stored under `Build/`.

## 4. Staffing & Timeline Snapshot

| Phase | Key Roles | Duration Estimate |
| --- | --- | --- |
| Preproduction | Technical art, environment art, systems design, tools | 6 weeks |
| World Building | Environment art team, lighting, tech art | 16 weeks |
| Systems & Gameplay | Gameplay programmers, AI engineers, UI/UX | 12 weeks |
| Missions & Polish | Narrative, design, QA, optimization | 10 weeks |

Total production scope exceeds 10 months with a 20-person multidisciplinary team. Budget and scheduling should be planned accordingly.

## 5. Current Repository Deliverables

- Unreal Engine project stub with module and target definitions (`UnrealProject/`).
- Importable `Chernobyl_Ingress.t3d` scene stub outlining sarcophagus approach, reactor alignment, and rail guide points.
- Production roadmap and import instructions in `/docs`.

This repository is intentionally lightweight to keep it compatible with standard Git hosting constraints. A full playable build with
the required map, plugins, and scripts must be produced inside a dedicated Perforce or Git LFS workspace following the guidance
above.
