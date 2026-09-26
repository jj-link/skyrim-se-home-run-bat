# Home Run Bat restart

## Agreed behavior

- Every landed normal or power swing launches the struck actor.
- The finished weapon has an actual baseball-bat model and texture.
- No scripted death: ordinary weapon damage and falls may still kill.
- No MCM or settings menu; ship one tested launch configuration.
- Preserve essential NPC protection and use the actual wielder, not an assumed player.

Proposed defaults: two-handed greatsword animations, blocked contacts still launch,
no launch on misses or bashes, no recharge requirement, and an accessible placed
copy at Warmaiden's. Custom animations and a native runtime DLL are not planned.

## Implementation and gates

1. Establish an isolated development profile and disposable save.
2. Prove hit delivery and actor knockback in the actual game before final art.
   - Weapon -> contact enchantment -> scripted magic effect.
   - `HRBLaunchEffect.OnEffectStart(target, caster)` identifies both actors.
   - Test `caster.PushActorAway(target, force)`; do not reuse the abandoned
     script's impulse value in this different API.
   - Repeated, blocked, resisted, and lethal hits are acceptance gates, not
     assumptions. Resolve delivery failures before accepting this architecture.
3. Tune direction, distance, collision behavior, and living-actor recovery.
4. Create the finished bat mesh, textures, grip, collision, and impact sound.
5. Add acquisition and verify inventory, drop/recovery, cell changes, and save/load.
6. Package and retest from the installable archive in a clean profile.

Do not ship the temporary vanilla weapon model as the finished mod. Do not add
forced death, unrelated global physics changes, polling, or a configuration layer.

## Development build

Prerequisites: Windows, .NET SDK 10, Skyrim Special Edition and the Creation Kit,
including `Papyrus Compiler/PapyrusCompiler.exe` and `Data/Source/Scripts`.
Mutagen.Bethesda.Skyrim 0.54.4 and its dependencies are pinned in
`tools/PluginBuilder/packages.lock.json`; the builder reads the installed game
master rather than redistributing it.

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1
```

`-GamePath` overrides registry discovery. `-OutputPath` overrides the output Data
directory. The command builds `HomeRunBat.esp` and `Scripts/HRBLaunchEffect.pex`.
It does not install files into the game. Dependencies and build work files stay
under the ignored project-local `.local` directory.

Current local FormIDs, which must remain stable:

| Record | Local FormID |
| --- | --- |
| HRBHomeRunBat | 000800 |
| HRBLaunchEffect | 000801 |
| HRBEnchantment | 000802 |

The load-order prefix is not fixed. Use `help "Home Run Bat" 4` in the game to
find the actual weapon ID before `player.additem` and `player.equipitem`.

## Isolated test setup

The local development environment uses portable Mod Organizer 2 under
`.local/mo2`, with profile `HomeRunBat-Dev`. Enable both profile-specific save
games and profile-specific game INI files. The mod directory is a junction to
this project's `Data` directory, avoiding changes to installed game assets.

Start Skyrim once before relying on Mod Organizer's plugin-list redirection:
on the initial launch, the missing `%LOCALAPPDATA%/Skyrim Special Edition`
directory prevented that mapping. After Skyrim initialized the directory and
the game was relaunched through the profile, the plugin loaded correctly.

For development only, enable Papyrus logging/tracing in the profile's INI.
Use disposable saves, not existing playthroughs. The launch script currently
contains a development trace; remove that trace from the release build.

## Verification status

Observed on 2026-09-26 with Skyrim/Creation Kit 1.7.99.0 and MO2 2.5.2:

- The reproducible build command generated the plugin and compiled the Papyrus
  script with zero compiler errors or warnings.
- The game loaded the plugin, found the weapon through console search, and
  equipped it.
- `HRBBaseline.ess` was created under the isolated profile's `saves` directory.
- One normal melee hit on Ulfberth War-Bear invoked the effect once, identifying
  target `000D15B0` and caster `00000014`, with `dead=False`.
- The target survived and returned to standing after the knockdown. This indoor
  check does not establish the required outdoor launch distance.
- The actual attack recording is local at `.local/evidence/normal-hit-01.gif`.
- Vanilla/DLC script warnings also appear in the game log; a globally empty
  Papyrus log is not an appropriate acceptance criterion.

The current model is a vanilla greatsword, force 15 is an experimental value,
and the full gameplay matrix below has NOT passed. No release is ready yet.

## Remaining acceptance matrix

- Normal and power attacks: exactly one launch per qualifying contact.
- Blocked contacts: launch according to the selected rule.
- Misses, bashes, scenery, and other weapons: no home-run effect.
- Rapid repeats on one target and hits on multiple targets: no swallowed or
  duplicate launches; no dependence on a previous active effect ending late.
- NPC wielder: correct victim and direction, without substituting the player.
- Magic resistance and absorption: no unintended suppression of the bat effect.
- Killing blow: ordinary damage may kill, but the qualifying strike still launches.
- Essential actors: protection remains unchanged; test outside real quest saves.
- Flat ground, stairs, slopes, walls, and low ceilings: no crash or persistent
  immobilization. Living targets recover movement and combat.
- Required humanoid run: 30 normal/power/blocked contacts with no unexplained
  missed or duplicate launches. Test draugr, animals, giants, and dragons
  separately and document observed engine limitations.
- Initial outdoor distance target: at least 1,024 world units for a standard
  humanoid on an unobstructed marked lane, with the landing in the test area.
  Record actual travel visually; do not infer ragdoll position from stale values.
- Finished bat: first/third person, grip, sheathing, inventory, and dropped collision.
- Sound: once per hit, audible and free of clipping/looping. The old MP3's rights
  are unknown; establish permission or use an original/licensed replacement.
- Acquisition without console commands; save/load, cell changes, drop and re-equip.
- Clean archive installation with no missing assets, unresolved records, or
  mod-attributable script errors.

Commit and push coherent verified milestones. Preserve evidence, distinguish
observed results from untested behavior, and package only finished assets.
