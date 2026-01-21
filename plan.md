# Home Run Bat Mod - Plan

## Goals
- Add a weapon named "Home Run Bat" that launches NPCs with a strong ragdoll impulse and can optionally kill on hit
- Provide configurable strength, kill toggle, and sound toggle via MCM
- Keep scripts loosely coupled (config, sound, weapon, MCM)
- Place the weapon in an easily accessible Whiterun location (Warmaiden's)
- Create a CK Sound record and point it at the sound file

## Decisions
- Location: Warmaiden's in Whiterun (add to vendor container or leveled list used by that shop)
- Blocked hits: still launch and still kill when kill-on-hit is enabled
- Kill credit: always attributed to the attacker
- Strength defaults: start high for dramatic distance (default 20000, range 5000-40000), tune after testing
- Sound asset: convert to Data/Sound/fx/HomeRunBat/homerun_screech.wav (or .xwm if required), then create a CK Sound record pointing to it

## Scope
In-scope:
- Papyrus scripts and MCM
- Creation Kit records and plugin (.esp)
- Test checklist for gameplay behavior

Out-of-scope (for now):
- Custom meshes or textures
- Custom animations
- Voice or quest content

## Architecture (Loose Coupling)
- HomeRunBatConfig (Quest) stores settings and exposes getters/setters
- HomeRunBatSound plays audio using config and a Sound form
- HomeRunBat weapon script applies impulse and kill logic, reads only from config/sound
- HomeRunBatMCM writes into config and never touches weapon logic directly
- Scripts only call the Sound form

## Implementation Steps (Iterative)
1. Smallest working version (knockback only)
   - Create a weapon and attach a minimal script that applies a strong impulse on hit
   - Compile and test: verify NPCs fly a long distance
2. Reliable launch behavior
   - Confirm impulse direction (away from attacker) and handle blocked hits
   - Add defensive guards and verify no errors
3. Kill-on-hit
   - Add kill logic with attacker kill credit
   - Test kill toggle behavior (always on for now)
4. Sound
   - Convert audio to Data/Sound/fx/HomeRunBat/homerun_screech.wav
   - Create a CK Sound record and call it from the hit script
5. Configuration + MCM
   - Add HomeRunBatConfig (Quest) + MCM to tune strength and toggles
   - Wire scripts so the weapon reads settings from config
6. Placement
   - Add the weapon to Warmaiden's vendor container or leveled list
7. Final test pass
   - Acquisition, launch distance, blocked hits, kill credit, sound, MCM persistence
