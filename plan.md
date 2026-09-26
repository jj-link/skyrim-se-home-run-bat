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

Do not ship a renamed vanilla weapon as the finished mod. Do not add forced
death, unrelated global physics changes, actor-scanning loops, or a settings layer.

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
directory. The command builds the ESP and PEX and copies the bat NIF, two DDS
textures, and original impact WAV. It does not install files into the game.
Dependencies and build work files stay under the ignored project-local `.local`.

Current local FormIDs, which must remain stable:

| Record | Local FormID |
| --- | --- |
| HRBHomeRunBat | 000800 |
| HRBLaunchEffect | 000801 |
| HRBEnchantment | 000802 |
| HRBFirstPersonBat (STAT) | 000803 |
| HRBImpactSound (SNDR) | 000804 |
| HRBImpact (SOUN) | 000805 |

The load-order prefix is not fixed. Use `help "Home Run Bat" 4` in the game to
find the actual weapon ID before `player.additem` and `player.equipitem`.

Original asset sources are in `assets/model` and the procedural generators:

```powershell
python tools/build_bat.py --fetch-exporter
python tools/create_impact.py
```

The mesh generator uses Blender 5, Pillow, NumPy, the Creation Kit texture
converter, and a SHA-256-pinned PyNifly release. It authors its own geometry,
textures, and collision; extracted vanilla models are local inspection references
only and are not packaged. The NIF includes `Prn=WeaponBack`, required for the
equipped model to attach correctly, and its inventory marker and dynamic collision.

`tools/package.ps1 -Version <version> -InputPath <Data-directory>` writes an
explicit six-file ZIP under `build/`. Its root is the contents of Skyrim's Data
directory. Source files, the old unlicensed MP3, and local diagnostics are excluded.
The development `0.1.0-dev` archive is a packaging smoke artifact, not a release.

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

- Default and separate-output builds succeeded; Papyrus reported zero errors and
  warnings. The packaging command produced exactly the six intended files and
  the ZIP passed CRC verification. Clean-profile archive installation is pending.
- An isolated diagnostic actor records physical hit flags; the player is also
  instrumented in the local-only probe plugin. Physical and enchantment hit
  callbacks can both appear for one contact; they are not two launches.
- Normal and power contacts invoked one launch each in the exercised cases.
  An NPC wielding the bat launched the player; a subsequent bat contact explicitly
  logged `blocked=TRUE`, followed by one launch with that NPC as caster.
- Living humanoids visibly ragdoll and return to standing. Indoor ceilings and
  furniture constrain travel; force 15 has not passed the outdoor distance gate.
- A killing blow logged `dead=TRUE` at effect start and subsequently `OnDeath`.
  The corpse dropped near the impact rather than visibly flying away. The
  living-only push operation is not accepted as the corpse implementation.
- Immediate pushes during paired finishers interrupted the animation and left
  targets alive. The current prototype waits while either actor is in a finisher.
  This specific deferred-finisher path still needs verification.
- Full magic resistance suppressed the original hostile effect. Removing
  Hostile/Detrimental allowed a launch with `magicresist=100`.
- **Absorption remains a delivery failure:** with `absorbchance=100`, the physical
  bat hit occurred and the absorption visual played, but the launch effect never
  started. Neutral effect flags do not solve this. Do not claim every hit works.
- The original bat now renders in first-person attacks, third-person grip,
  sheathed on the back, in inventory, and as a dropped/pickable world object.
  The missing `Prn=WeaponBack` metadata caused the initial equipped-model failure
  and was corrected against the installed native weapon convention.
- Sound binding requires a SOUN marker pointing to the SNDR descriptor, not a
  direct SNDR Papyrus property. After correction, actual system playback captured
  one matching impact onset (0.8674 correlation over its first 40 ms), with no
  clipped samples in the 12-second capture. The source WAV is original mono PCM;
  no sample from the abandoned MP3 is used.
- Local evidence includes `bat-attachment-fixed.gif`, `bat-third-person.png`,
  `bat-sheathed.png`, `bat-inventory.png`, and `bat-impact-playback.wav` under
  `.local/evidence`. Disposable saves remain under the MO2 profile.
- Vanilla/DLC script warnings also appear; an entirely empty Papyrus log is not
  an appropriate acceptance criterion. Corrected sound binding produced no
  launch-script errors in the subsequent exercised contact.

### Delivery decision required

Native API references:
[MagicItem](https://ryan.commonlib.dev/MagicItem_8h_source.html),
[EnchantmentItem](https://ryan.commonlib.dev/EnchantmentItem_8h_source.html),
[SpellItem](https://ryan.commonlib.dev/SpellItem_8h_source.html), and
[vanilla AddPerk limitations](https://ck.uesp.net/wiki/AddPerk_-_Actor).

The contact-enchantment prototype does not satisfy the agreed every-hit rule
against spell absorption. Native class definitions expose no absorption bypass
for enchantments; actual spells support it, but dynamically adding a hit-spell
perk does not work for arbitrary NPC wielders in vanilla Papyrus. A native hit
handler is the proposed route to preserve the rule; it adds an SKSE dependency
and runtime compatibility requirements. Do not silently accept absorption as an
exception or add that dependency without agreement.

The remaining matrix has NOT passed. No release is ready.

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
