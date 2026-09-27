# Home Run Bat restart

## Agreed behavior

- Every landed normal or power swing launches the struck actor.
- The finished weapon has an actual baseball-bat model and texture.
- No scripted death: ordinary weapon damage and falls may still kill.
- No MCM or settings menu; ship one tested launch configuration.
- Preserve essential NPC protection and use the actual wielder, not an assumed player.

Accepted defaults: two-handed greatsword animations, blocked contacts still launch,
no launch on misses or bashes, no recharge requirement, and a freely takeable placed
copy at Warmaiden's. SKSE native hit detection is approved; no custom animations.

## Implementation and gates

1. Establish an isolated development profile and disposable save.
2. Prove hit delivery and actor knockback in the actual game before final art.
   - Native `TESHitEvent` -> persistent quest -> `HRBLaunchController.OnBatHit`.
   - Filter the actual weapon and physical contact; preserve both actor identities.
   - Living actors use `attacker.PushActorAway(target, force)`. Dead actors need
     a separate ragdoll/impulse path; the APIs do not share force units.
   - Repeated, blocked, resisted, lethal, and finisher contacts remain acceptance
     gates. The removed enchantment route could be absorbed before its script ran.
3. Tune direction, distance, collision behavior, and living-actor recovery.
4. Create the finished bat mesh, textures, grip, collision, and impact sound.
5. Add acquisition and verify inventory, drop/recovery, cell changes, and save/load.
6. Package and retest from the installable archive in a clean profile.

Do not ship a renamed vanilla weapon as the finished mod. Do not add forced
death, unrelated global physics changes, actor-scanning loops, or a settings layer.

## Development build

Prerequisites: Windows, Git, Visual Studio 2026 with C++ x64/CMake tools, .NET SDK 10,
Skyrim Special Edition and the Creation Kit, including
`Papyrus Compiler/PapyrusCompiler.exe` and `Data/Source/Scripts`.
Mutagen.Bethesda.Skyrim 0.54.4 and its dependencies are pinned in
`tools/PluginBuilder/packages.lock.json`; the builder reads the installed game
master rather than redistributing it. Prepare the two official native dependencies
once, inside this project:

```powershell
git clone https://github.com/ianpatt/skse64.git .local/native/skse64
git -C .local/native/skse64 checkout 6498c52871859c92ab584ab97112f798b409698d
git clone https://github.com/ianpatt/common.git .local/native/common
git -C .local/native/common checkout 64e233c096735551f6ac9a773726a8a3960e46cd
```

The SDK pin includes the official 1.7.99 version-header and PlayerCharacter
corrections. No CommonLib or Address Library dependency is added. The native
build verifies both source revisions; it does not modify or redistribute SKSE.

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1
```

`-GamePath` overrides registry discovery. `-OutputPath` overrides the output Data
directory. The command builds the DLL, ESP, controller PEX and quest-start SEQ,
then copies the bat NIF, two DDS textures, and original impact WAV. It does not
install files into the game. Dependencies/build files stay under `.local`.
`-Diagnostics` enables native accepted-contact logging for development only.
The controller still contains development traces pending completion of playtests.

Current local FormIDs, which must remain stable:

| Record | Local FormID |
| --- | --- |
| HRBHomeRunBat | 000800 |
| Retired; never reuse | 000801, 000802 |
| HRBFirstPersonBat (STAT) | 000803 |
| HRBImpactSound (SNDR) | 000804 |
| HRBImpact (SOUN) | 000805 |
| HRBLaunchController (QUST) | 000806 |
| HRBWarmaidensBat (REFR) | 000807 |

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

`tools/package.ps1 -Version <version> -InputPath <Data-directory>` packages eight
files under `build/`: ESP, controller PEX, native DLL, SEQ, NIF, two DDS textures,
and WAV. Its root is the contents of Skyrim's Data directory. Source files, SKSE
itself, the old unlicensed MP3, and local diagnostics are excluded.
The older six-file `0.1.0-dev` ZIP predates native delivery and is not a release.

### Runtime dependency

This build supports **Steam Skyrim 1.7.99.0 only**, with **SKSE 2.3.0**. Both the
exported plugin metadata and load function reject other game runtimes. Do not use
the current SKSE 2.3.1/Skyrim 1.7.104 pair with this DLL.
Get SKSE through the [official site](https://skse.silverlock.org/); the matching
2.3.0 file is in the official Nexus archive. Launch Skyrim through SKSE.

Local verification uses an unmodified source build of SKSE at the pinned revision,
with all 62 official extended Papyrus scripts compiled. The loader's `-altexe`
and `-altdll` options keep those binaries in `.local`, outside the game directory.
MO2 provides the SKSE scripts through its isolated profile. This development
setup neither updates Skyrim nor changes installed Data files.

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

### Native delivery milestone

- The integrated DLL/ESP/SEQ/PEX build succeeded; the controller compiled with
  zero Papyrus errors or warnings. Native SDK headers emit existing MSVC warnings.
- The actual game reported `SKSE64 version: 2.3.0, release idx 74, runtime 01070630`.
  The native sink identified the VM's hit dispatcher uniquely at holder+`0x5D8`.
- Loading the pre-native `HRBProbeStage` save started quest `07000806`;
  `sqv HRBLaunchController` reported Enabled/Running.
- A target with both `absorbchance=100` and `magicresist=100` visibly launched
  from normal and power swings. Each produced one physical diagnostic hit, one
  native submission, and one controller launch.
- An NPC using the bat launched the player on a contact logged `blocked=TRUE`;
  a subsequent unblocked NPC hit also reached the controller. Each of these four
  living-target contacts produced one native submission and one controller launch.
- A bash and a steel-warhammer strike produced ordinary hit/damage diagnostics
  without native bat delivery. A missed bat swing produced no delivery.
- Evidence: `skse-1-7-99.png`, `native-absorption-first.gif`,
  `native-absorption-power.gif`, `native-other-weapon.gif`, `native-miss.gif`,
  `native-npc-blocked.gif`, and `native-delivery-first-run.log` in `.local/evidence`.
- A normal killing blow left health at `-6.40`, reported `GetDead=1`, and visibly
  propelled the corpse into the room's ceiling. A paired finisher also completed
  its death and visibly launched the body afterward. Evidence:
  `native-ordinary-lethal.gif`, `native-lethal-1000.gif`, and
  `native-corpse-midflight.png`. The corpse impulse is now 1000; the initial 100
  was insufficient. These are indoor checks, not outdoor distance acceptance.
- The full 30-contact run, outdoor distance, actor/terrain matrix, and clean ZIP
  install remain open; do not interpret this milestone as release acceptance.
- Acquisition is implemented as one non-respawning, player-owned bat atop barrel
  `Skyrim.esm:034EB0` outside Warmaiden's, in `WhiterunPLainsDistrict03` (`01A27A`).
  Player ownership avoids shop-cell/inherited theft. Placement, pickup and
  acquisition persistence still need in-game verification.

### Earlier prototype and asset evidence

- Earlier enchantment-prototype default/separate-output builds and the six-file
  ZIP passed their build/CRC checks. Those checks do not cover the new native
  package; clean-profile archive installation remains pending.
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
  targets alive. The native controller now waits while either actor is in a
  finisher; the tested finisher completed its death before the corpse launch.
- Full magic resistance suppressed the original hostile enchantment. Neutral
  flags fixed resistance but not absorption: `absorbchance=100` canceled the
  effect before its script started. The enchantment, effect and old script have
  now been removed, rather than treating absorption as an accepted exception.
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

### Why delivery changed

Native API references:
[MagicItem](https://ryan.commonlib.dev/MagicItem_8h_source.html),
[EnchantmentItem](https://ryan.commonlib.dev/EnchantmentItem_8h_source.html),
[SpellItem](https://ryan.commonlib.dev/SpellItem_8h_source.html), and
[vanilla AddPerk limitations](https://ck.uesp.net/wiki/AddPerk_-_Actor).

The contact-enchantment prototype could not satisfy the agreed every-hit rule
against spell absorption. Native class definitions expose no absorption bypass
for enchantments; actual spells support it, but dynamically adding a hit-spell
perk does not work for arbitrary NPC wielders in vanilla Papyrus. The user approved
SKSE; direct hit events now bypass that delivery failure without changing target
resistance/absorption values or adding a settings menu.

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
