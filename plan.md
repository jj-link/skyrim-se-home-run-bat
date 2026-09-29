# Home Run Bat restart

## Agreed behavior

- Every landed normal or power swing launches the struck actor.
- The finished weapon has an actual baseball-bat model and texture.
- No scripted death: ordinary weapon damage and falls may still kill.
- No MCM or settings menu; ship one tested launch configuration.
- Preserve essential NPC protection and use the actual wielder, not an assumed player.
- Dragons are included. A failed dragon launch is a defect, not an accepted exception.

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
build verifies both source revisions; it does not modify or redistribute SKSE
runtime binaries. The plugin source is public in this repository, as required
by the SDK's plugin-use terms; Ian Patterson's common library is also unmodified.

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build.ps1
```

`-GamePath` overrides registry discovery. `-OutputPath` overrides the output Data
directory. The command builds the DLL, ESP, controller PEX and quest-start SEQ,
then copies the bat NIF, two DDS textures, and original impact WAV. It does not
install files into the game. Dependencies/build files stay under `.local`.
`-Diagnostics` enables native accepted-contact logging for development only.
The shipped controller and native DLL have no per-hit diagnostic traces.

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

### Install release 0.1.1

`build/HomeRunBat-0.1.1.zip` (SHA-256
`3DD5F52F062ECECAF427347DD30293F4565DF258F722700CD121B61A26641E08`)
contains eight files rooted at Skyrim's `Data` directory; it does not include
SKSE. Install matching SKSE 2.3.0 separately. Install the ZIP with a mod manager
as Data-root content, or extract its contents into
`Skyrim Special Edition\Data`; enable `HomeRunBat.esp` and launch via SKSE.
With a new game, take the free bat from the barrel outside Warmaiden's in
Whiterun. The quest's launch force is serialized in existing saves: use a new
game to obtain the verified 30-force release configuration rather than relying
on an earlier test save's stored value.

Prior host-side verification used an unmodified source build of SKSE at the pinned
revision, with all 62 official extended Papyrus scripts compiled. The loader's
`-altexe` and `-altdll` options kept those binaries in `.local`; MO2 supplied the
scripts through its isolated profile. That profile is now staging material, not
permission to launch or automate the host game. Neither setup updates Skyrim
or changes the host's installed Data files.

## Isolated test setup

### Preserved staging profile

The preserved portable Mod Organizer 2 environment is under `.local/mo2`, with
profile `HomeRunBat-Dev`, profile-specific saves and profile-specific INI files.
Its mod directory is a junction to this project's `Data` directory. Do not use
host keyboard/mouse automation; the replacement runtime is the VM below.

The original MO2 setup required Skyrim to initialize
`%LOCALAPPDATA%/Skyrim Special Edition` before plugin-list redirection worked.
The VM instead provisions its own plugin list, INI files and disposable saves.

For development only, enable Papyrus logging/tracing in the profile's INI.
Use disposable saves, not existing playthroughs. The launch script currently
contains a development trace; remove that trace from the release build.

### Guest-only automation

The original `HomeRunBat-Win11` VirtualBox 7.2.20 VM is powered off and preserved,
including its TPM/NVRAM and VDI. Its disk was cloned to
`.local/vm/HomeRunBat-Workstation/HomeRunBat-Workstation.vmdk`. The replacement VM
uses VMware Workstation Pro 26.0.1 (build 25688693), 4 vCPUs, 8 GiB RAM,
EFI/Secure Boot, 3D SVGA with 2 GiB graphics memory, and no virtual network
adapter. It runs headlessly. Windows 11 Pro 25H2 remains unactivated by choice;
Skyrim remains 1.7.99.0. Host Hyper-V, physical GPUs, drivers and mining are
unchanged. VMware Tools 13.1.5 replaced VirtualBox Guest Additions in the clone.
The game has already run in this clone without a virtual TPM or VM encryption.

Clipboard, drag-and-drop, shared folders, USB and sound are disabled on the
replacement. Some staged base-game files outside the guest are hard links to
installed assets: **never edit those staged files**. The guest has its own copied
game under `C:\Games\Steam\steamapps\common\Skyrim Special Edition`, plus
disposable saves and INIs. All 115 manifest files were rehashed after the
VMware migration with zero mismatches; VC++ and June 2010 DirectX prerequisites
remain installed.

For gameplay, the guest now uses Microsoft's WARP software Direct3D renderer.
The SVGA path rendered scenes but failed texture cleanup during cell/save
transitions, including an untouched vanilla control. Microsoft's `d3dconfig.exe`
is staged at `C:\HRB\debugger\d3dconfig.exe` inside the guest. Its application list
was initially empty; only the guest game's full executable path was registered:

```powershell
C:\HRB\debugger\d3dconfig.exe apps --add "C:\Games\Steam\steamapps\common\Skyrim Special Edition\SkyrimSE.exe"
C:\HRB\debugger\d3dconfig.exe device force-warp=true
```

These are guest-user settings, not host or release-mod settings. The running
game loaded `d3d10warp.dll` and no VMware graphics-driver module. Indoor-to-outdoor
save switching rendered successfully and ordinary `qqq` exit returned code 0.
Software-rendered loading takes longer; a temporary black loading frame is not
a completed transition. Guest-only preferences now use 800×450, reduced shadow
and scenery distances, and disabled TAA, SSAO, reflections, volumetric lighting
and depth of field. Actor fade distance is unchanged. Original preferences are
preserved privately. This is renderer configuration, not a patched engine
release call or a swallowed exception.

Control only `.local/vm/control.py`; the obsolete VirtualBox automation has
been removed. `start` resumes/boots headlessly; `shutdown` requests a soft guest
shutdown; `key 0x15 8` sends guest Win+R using USB-HID usage/modifier bits;
`text "..."` sends guest keystrokes; `mouse X Y --clicks 2` uses `user32` **in
the guest interactive session**, not on the host; `screenshot FILE` captures
the VM framebuffer. `held-key SCAN MILLISECONDS`, `attack MILLISECONDS` and
`relative-mouse DX DY` use guest-side `SendInput` for held scan codes, attack
buttons and relative motion. The held path executes console Enter reliably
where instantaneous USB-HID presses were dropped. `powershell SCRIPT` and
`copy-from GUEST HOST` use VMware Tools. Child processes use `.local/vm/work`
for host TEMP/TMP; guest work uses `C:\HRB\work`. The guest password, disks and
screenshots remain under ignored `.local/vm/` and must never be published.
No host cursor/focus injection is used. Measured desktop clicks and the first
normal/power attacks left host foreground and cursor unchanged. Guest input
has now exercised normal attacks, a held power attack, movement, free-camera
translation and console actor selection. Injected relative mouse-look is not
verified. Interactive launch uses the guest Run dialog with
`C:\HRB\launch-game.cmd`.

The interactive mouse action can initially fail while the guest desktop is
visible but the user VMware Tools session has not yet registered after boot;
once `hrb`'s `vmtoolsd.exe` was present and logon settled, the same desktop
double-click opened Recycle Bin without host input.

VMware Tools result `.local/vm/evidence/workstation-tools-ready.json` reports
the core `Common`, `Toolbox`, `VMCI` and `SVGA` MSI features local, running
VMTools service and healthy VMware SVGA 3D driver 9.17.11.4. Firmware capsule
and optional network/introspection features were not installed. The bootstrap
script and private ISO are in `.local/vm/exchange/` and the replacement VM
directory. `workstation-preflight.json` records no game-file mismatches;
`workstation-skyrim-first-attempt.png` shows a rendered main menu, and
`workstation-skyrim-loaded-save.png` plus
`workstation-skyrim-camera-toggle.png` show the rendered outdoor 3D world,
equipped bat and guest-keyboard camera toggle. `workstation-live-game.json`
records the responsive game process loading SKSE and `HomeRunBat.dll`.
The initial instantaneous console quit did not execute. A subsequent held-input
quit left that guest game process unresponsive; only that process was stopped
before restarting through SKSE. This is not evidence of a clean game shutdown.

The [official Steam client](https://store.steampowered.com/about/), verified as
signed by Valve Corp., is installed and was authenticated by the user inside the
guest. Host Steam session files were not copied. Steam is set to Offline Mode
for testing, avoiding game updates and cloud-save synchronization.

The authenticated launch initially failed with Steam application-load error
`6:0000065432`: the copied game was outside a registered Steam library. Moving
the guest copy into the library and importing its installed-depot metadata
resolved that error without updating Skyrim. The guest registry and SKSE
launcher now use the library path above.

Under VirtualBox 7.2.2, the next launch loaded `skse64_1_7_99.dll`,
`HomeRunBat.dll` and `VBoxDX.dll`, but the visible game surface remained black.
VirtualBox's host process then aborted with `0xc0000005` in host `d3d11.dll`,
following stalled VMSVGA screen updates.
The unmodified crash log is `.local/vm/evidence/VBox-first-game-crash.log`;
`guest-skse-loader.log` confirms runtime 1.7.99.0 and successful injection.
The user reported toggling mining off/on, then confirmed those changes were
finished. An unchanged-configuration retry and a cold-start test using the game's
bundled Low preset at 960x540 both failed with stalled VMSVGA updates and the same
host instruction/near-null write. Logs are `VBox-stable-gpu-retry.log` and
`VBox-low-preset-crash.log` in the same evidence directory. The original guest
preferences were restored and hash-checked afterward; runtime remains 1.7.99.0.

The 7.2.2 renderer reports `VERR_NO_MEMORY`, but that alone does not establish exhausted
VRAM: a post-stop host-GPU snapshot showed about 87 GiB free, and the
[7.2.2 DX11 backend](https://github.com/VirtualBox/virtualbox/blob/v7.2.2/src/VBox/Devices/Graphics/DevVGA-SVGA3d-dx-dx11.cpp)
also maps several generic D3D resource failures to that status.

RTSSHooks64.dll was loaded into VBoxHeadless. Installed RTSS templates already
exclude VirtualBox.exe and VirtualBoxVM.exe, but not VBoxHeadless.exe. With user
approval, a `Profiles\VBoxHeadless.exe.cfg` override was created through the RTSS
SDK with `AppDetectionLevel=0` (None), followed by its profile-refresh API.
An independent SDK reader confirmed the effective value changed from 1 to 0.
Only that application's profile was saved; RTSS and mining were not restarted.

The fresh VM launch with this exclusion still produced graphics errors and the
same host `d3d11.dll` access violation. The setting did not solve the failure;
RTSSHooks64.dll remained listed in the crash's module map, which alone does not
establish whether graphics hooks were active. Evidence: `rtss-exclusion-result.json`
and `VBox-rtss-excluded-crash.log` under `.local/vm/evidence`.

With user approval, the shared host installation was upgraded to
`7.2.20r175154`, followed by matching Guest Additions in the test VM. The official
installer's SHA-256 and Oracle signature were verified. The first MSI attempt
removed 7.2.2 but could not replace the loaded USB-monitor driver: `usbipd`
depended on it. After a separately approved brief stop of USBIP Device Host,
installation completed with exit code 0 and no reboot requirement. USBIP Device
Host was restarted; its Razer headset remained Shared, not Attached. All four
VM registrations were preserved. The host was not rebooted.

After a guest-only reboot, Guest Additions reported `7.2.20.175154` and the guest
WDDM driver reported `7.2.20.25154`. Skyrim remained `1.7.99.0`.
Evidence: `virtualbox-upgrade-result.json`, `virtualbox-upgrade.log` and
`guest-additions-update.json` under `.local/vm/evidence`.

The first post-upgrade game launch through guest control failed with Steam
application-load error `5:0000065432`. Launching the same SKSE command from the
guest desktop passed that error while Steam remained in Offline Mode; no game
files were changed. The game again loaded SKSE, HomeRunBat and VBoxDX, but its
window stayed black. The updated renderer reported `VERR_INVALID_STATE`, an
unset DX shader and stalled screen updates. During attempted game cleanup,
the host VMSVGA FIFO thread crashed at the same `d3d11.dll+0x19afc7` instruction,
with `0xc0000005` writing address `0xE0`.
Evidence: `VBox-7.2.20-skse-render-stall.log`,
`VBox-7.2.20-render-crash.log` and `guest-skyrim-7.2.20-interactive.png`.

Guest cleanup timed out, and the VM remained Running after a 90-second ACPI
shutdown wait. The user approved forced power-off and pausing further tests.
VirtualBox's power-off command also hung, so only the test VM's process,
identified by VirtualBox's `SessionPID`, was terminated. No VBoxHeadless
processes or running VMs remained afterward.

Post-stop inspection reported `VERR_VFS_UNKNOWN_FORMAT` while opening the UEFI
variable store. After the user authorized repair, inspection found a truncated
NVRAM archive: the TPM member was intact, but the EFI member's payload was absent.
The original archive was backed up privately; the TPM bytes were preserved
unchanged while VirtualBox regenerated the EFI store and enrolled Secure Boot
keys. Installation media were detached to prevent an accidental unattended
reinstall. Windows then booted to its desktop without a recovery prompt.

The virtual disk remains BitLocker-encrypted. A read-only check successfully
unlocked it using its existing clear-key protector and confirmed an NTFS boot
sector; no recovery-password protector was present. Evidence:
`bitlocker-recovery-check.json` and `guest-firmware-recovery.png`. Private NVRAM
backups contain TPM state and must not be published.

A reversible Windows per-application minimum-power GPU preference was then
applied to `VBoxHeadless.exe`. This affects that executable for the current host
user, not just this VM. DXGI preference enumeration and the new VM process's GPU
engine LUID identified the AMD integrated GPU; the prior preference was absent.
The native control launcher matched SKSE's `SteamGameId`/`SteamAppID` environment
without injecting SKSE. Skyrim loaded `d3d11.dll` and `VBoxDX.dll`, with neither
SKSE nor HomeRunBat loaded, but remained black. The host renderer again crashed
at `d3d11.dll+0x19afc7`. AMD driver modules were present in that crash log.
Evidence: `host-gpu-selection-before.json`,
`host-dxgi-minimum-power-adapters.json`, `vbox-amd-process-gpu-engines.json`,
`VBox-7.2.20-amd-native-crash.log` and `guest-amd-native-with-steam-context.png`.
No main-menu rendering or gameplay has been verified in the VM.

Guest shutdown and VirtualBox power-off again failed to finish after this crash,
so only the VirtualBox-reported test VM process (PID 84916) was terminated.
The stopped VM is marked Aborted; no VMs remain running. This time both NVRAM
archive members remained complete. The temporary GPU preference was removed,
restoring its original absence. `amd-native-test-result.json` records the result.

A subsequent desktop-only maintenance boot temporarily disabled 3D acceleration.
The requested filesystem/hash check produced no result before Guest Control
timed out, and the guest later stopped responding to keyboard input as well.
No post-crash disk-health or renewed file-integrity pass is claimed. VirtualBox
power-off completed for that session; the original 3D setting was restored while
stopped, Secure Boot remained enabled, and both firmware archive members were
complete. The original VirtualBox VM remains powered off; its VMware clone is separate.

VMware Workstation Pro 26.0.1 was installed by the user. No account/download
step, host reboot, driver change or VirtualBox replacement was needed. The
separate clone booted, cleanly shut down, replaced guest drivers with locally
available signed Tools media, rebooted and rendered both Skyrim's main menu
and outdoor gameplay under 3D acceleration. The original VirtualBox graphics
failure remains reproducible only on the original platform; it is not a
current VMware blocker. Normal/power combat and actor recovery have now been
observed in the clone; the full acceptance matrix has not passed.

The clone's read-only preflight
`.local/vm/evidence/workstation-bitlocker-status.json` reports `C:` fully
encrypted, unlocked, protection **Off**, no listed key protectors, Secure Boot
enabled, and no TPM present. No change to BitLocker, virtual TPM, or VMware
encryption is needed for this game's VM tests. An unused generated VMware
encryption-password file was deleted; no VMware encryption was applied.

Physical-GPU drivers, Hyper-V, mining and global overlay settings remain
unchanged. The approved RTSS headless-only override remains installed for
the preserved VirtualBox VM. The full mod acceptance matrix is still pending.

## Verification status

Observed in the disposable game profiles on 2026-09-26 through 2026-09-28,
with Skyrim/Creation Kit 1.7.99.0, SKSE 2.3.0, and MO2 2.5.2:

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
- The 30-contact humanoid run passed: 20 player contacts (10 normal,
  10 power) and 10 NPC contacts (7 normal, 3 power), including four blocked
  contacts. Each matched one native submission and one living launch call.
  The target survived and the player recovered after the NPC series. This
  earlier save had a serialized launch force predating 0.1.1; the run verifies
  contact delivery, not the release distance. Evidence:
  `native-30-contact.log`, `native-30-papyrus.log`, `native-repeat-01.gif`
  through `native-repeat-20.gif`, and `native-npc-series-01.gif` through
  `native-npc-series-06.gif` in `.local/evidence`.
- Release source and ESP both set living launch force to 30. A standard
  humanoid hit normally on the marked outdoor lane traveled from
  (4499.97, -1034.49) to (4498.37, -2125.03) at 1.5 seconds: 1,090.54
  horizontal world units, past a marker placed 1,024 units from the start.
  Its Z rose about 226 units; successive frames show an airborne tumble.
  The target landed near y=-4144 alive, then walked back and resumed attacking
  the player. Evidence: `workstation-release011-exact-straight-1024flight.log`,
  `workstation-release011-exact-1024-straight-flight-82frame-grid.png`, and
  `workstation-release011-straight-lane-target-recovered-after-landing.png`
  in `.local/vm/evidence/`. Landing was farther along the same test area.
- A low-health essential test actor launched and remained alive after damage
  reduced health below zero (`native-essential-low-health.gif`). Its essential
  flag was restored in the disposable test state, not changed by the mod.
- Two different actors struck roughly one second apart each launched
  (`native-multiple-targets.gif`). A later force-30 diagnostic run recorded
  seven actual physical bat contacts on the same player target, including
  normal/power attacks and a second contact two seconds after the first while
  the initial ragdoll was still in progress: seven native deliveries, seven
  `OnBatHit` calls, seven living pushes, no duplicates or swallowed contacts.
  The temporary hit probe was removed and the release PEX restored afterward.
  Evidence: `workstation-release011-true-rapid-event-evidence.log`.
- Draugr, wolf, and giant contacts reached the native/controller path and visibly
  displaced the actors; subsequent checks found them alive and upright.
  Evidence: `native-draugr.gif`, `native-wolf.gif`, `native-giant.gif`, and the
  corresponding `*-recovered.png` captures.
- The earlier grounded-dragon attempt did not launch
  (`native-dragon-grounded.gif`); the final version uses the dragon's own
  guarded character controller rather than humanoid `PushActorAway`.
  Two subsequent physical bat contacts with the same living, grounded dragon
  each submitted one controller launch, displaced it into the air, and returned
  it to the ground alive without permanent flight or AI changes. Evidence:
  `workstation-repeated-dragon-native.log`,
  `workstation-dragon-physical-flight-and-recovery.png`, and
  `workstation-dragon-repeat-alive-after-physics.png`.
- Outdoor rocks, slopes, trees, water, and indoor low ceilings were exercised.
  The tested living targets recovered after ragdoll and resumed behavior.
- Acquisition is one non-respawning, player-owned bat atop barrel
  `Skyrim.esm:034EB0` outside Warmaiden's, in `WhiterunPLainsDistrict03` (`01A27A`).
  The actual placement is visible and stable. The white `Take Home Run Bat`
  prompt, ordinary E-key pickup, inventory model, and keyboard equip were
  verified. A save/load preserved exactly one acquired bat. Evidence:
  `warmaidens-placement-first.png`, `warmaidens-take-prompt.png`,
  `warmaidens-acquired-equipped.png`, and `warmaidens-save-loaded.png`.
  The equipped state also survived the guest save/reload and transitions through
  Riverwood and QASmoke; ordinary drop, pickup, and re-equip worked. The acquired
  copy then delivered a real, ordinary-damage physical hit and visibly launched
  the test NPC indoors. Guest evidence: `workstation-acquired-equipped-after-reload-inventory.png`,
  `workstation-acquired-riverwood-settled.png`, `workstation-acquired-qasmoke-stable.png`,
  `workstation-acquired-combat-impact-native.log`, and `workstation-acquired-combat-impact.png`.

### VMware Workstation Pro gameplay continuation

- Guest-held input reproduced a normal launch and a power launch on the outdoor
  humanoid. Ordinary contact damage was approximately 7.574 and 15.148 health,
  respectively. The target remained alive and returned to standing.
- Two subsequent normal contacts on the recovered actor reached the native and
  controller paths. `workstation-repeat-normal-frame-0.png` visibly captures the
  second of these launches; later frames show landing/recovery. These are
  consecutive contacts, not proof of overlapping same-target hits.
- `workstation-human-sequence-native.log` contains five submissions: the normal
  and power observations above, two subsequent normals, and one earlier power
  contact made with target AI disabled. The AI-disabled contact is excluded
  from successful visual-launch evidence.
- Earlier dragon ragdoll and velocity probes failed against a grounded dragon;
  those diagnostic paths are not shipped. The shipping native path recognizes
  dragon races, validates the exact runtime's controller layout/code, queues
  a per-contact airborne impulse on the game thread, and lets the engine decay
  it on landing. The repeated grounded-dragon contacts above are the actual
  gameplay acceptance evidence, not the preliminary probe's movement estimate.
- Save switching failed without invoking a dragon probe, with the bat DLL
  absent, and without SKSE. A fresh vanilla session with both mod plugins
  disabled also exited during `coc qasmoke` -> `coc Riverwood`. This establishes
  a guest-runtime failure independent of the running mod and old mod saves.
  Original plugin activation was restored after the controls.
- Captured exit statuses include `0xC0000005` and `0xC0000409`. ProcDump did not
  receive an exception event; its termination dump contains only a surviving
  input thread, not a causal crash stack. A separate guest-only first-chance
  recorder later captured an execute access violation at address 1. Matching
  Microsoft symbols unwind it through Direct3D's contained-object `Release`
  and Skyrim's texture-resource cleanup (`SkyrimSE+0x100EF8C`). That identifies
  the failing path, not the underlying ownership defect.
- The WARP control completed the previously failing modded save transition and
  a normal exit without an access violation. The crash-recording DLL was then
  removed from the plugin directory and the temporary per-application Windows
  Error Reporting dump setting removed. An uninstrumented vanilla control then
  loaded `HRBCleanBaseIndoor`, changed to Riverwood, dismissed the Survival
  prompt, saved `HRBWarpRiver`, reloaded the indoor save, and reloaded the new
  outdoor save in one process. Both reloads rendered their expected scenes.
  Its module record contains WARP and no SKSE, bat, crash-recorder or VMware
  graphics module. No Skyrim engine instructions were patched.
  A separate vanilla `qqq` stall was captured after main-loop termination:
  `BSPlatform::BSBethesdaPlatform` destruction was waiting indefinitely for a
  worker thread. It is an exit-only platform-cleanup limitation, not a captured
  gameplay/render/save hang. That disposable guest process was stopped after
  preserving the dump; no platform-shutdown patch was made.
- New continuation evidence is private under `.local/vm/evidence/`; older
  accepted host-side evidence is retained, but host gameplay remains prohibited.

### Earlier prototype and asset evidence

- The older six-file enchantment-prototype ZIP is not a release. The new
  eight-file 0.1.1 archive was installed into a guest with no private probe
  plugin or control override; its entries were rehashed against the ZIP after
  play and matched byte-for-byte.
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

The 0.1.1 archive has been built and exercised in the disposable guest.

## Release acceptance matrix

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

The instrumentation runs above cover normal/power/blocked hits, misses,
bashes, other weapons, rapid same-target/multiple-target contacts, NPC
wielders, full resistance/absorption, lethal/essential targets, and draugr,
wolf, giant, and grounded-dragon impacts. Paired finishers complete before
corpse impulse. One original impact WAV onset was recorded without clipping
or looping; its trigger occurs once per accepted native contact.

The 0.1.1 ZIP's eight Data-relative entries matched their installed hashes
after a clean-profile run. With only `HomeRunBat.esp` active, the game loaded
`HRBRelease011CleanPickup`, placed the free bat at Warmaiden's, accepted an
ordinary E-key pickup and inventory equip, retained the equipped bat through
save/restart and cell changes, and animated an actual normal bat swing.
`workstation-release011-final-pristine-install.txt`,
`workstation-release011-final-restored-checksum-report.txt`,
`workstation-release011-final-restored-after-stair-checksum-report.txt`,
`workstation-release011-clean-archive-E-picked-free-bat.png`,
`workstation-release011-clean-archive-restarted-save-weapon-equipped-one.png`,
and `workstation-release011-clean-archive-rebooted-K-normal-swing-24frame-grid.png`
preserve this evidence under `.local/vm/evidence/`. Guest-only K-to-attack
remapping compensated for synthetic mouse clicks not reaching the low-frame-rate
VM; it was removed after play and is not in the archive. The clean run's SKSE
log contains only the released DLL and confirms quest/hit-sink registration;
its Papyrus log has base-game/DLC warnings but no Home Run Bat script errors.

The exact 1,024-unit marked-lane gate passed with the release PEX and force-30
ESP; prior 30-contact, dragon, corpse, and repeat probes used the same release
gameplay code with private instrumentation, which is not packaged. In the
archive-only guest, a normal bat swing struck a living bandit standing on
Whiterun's broad wooden stair flight: it left its starting tread after the
attack, and gameplay continued. The stair victim's landing and subsequent
movement were out of view, so recovery for that isolated strike was not
separately established. The other exercised collision cases were flat ground,
slopes, rocks, water, walls, and indoor low ceilings. Evidence:
`workstation-release011-broad-staircase-contact-18.png`,
`workstation-release011-broad-staircase-contact-after-physics-stair-collision.png`,
and `workstation-release011-stairs-broad-flight-frozen-bandit-spawn-on-treads.png`
in `.local/vm/evidence/`.

One later release-only guest `coc Riverwood` transition exited to the Steam
window before rendering Riverwood. The process was absent afterward; no causal
exception stack was captured. The same guest previously exited during cell
transitions without either mod plugin, while other WARP vanilla and bat-enabled
transitions succeeded. This occurrence is not attributed to the mod, nor is
guest transition stability claimed. Evidence:
`workstation-release011-stairs-test-Riverwood-cell-arrival.png` and
`workstation-release011-stairs-cell-switch-state.txt`.

Commit and push coherent verified milestones. Preserve evidence, distinguish
observed results from untested behavior, and package only finished assets.
