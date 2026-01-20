# Home Run Bat Mod - Implementation Plan

## Overview
Create a Skyrim SE mod that adds a home-run bat weapon which launches NPCs across the map using physics-based ragdoll impulses.

## Architecture (Loose Coupling)

```
Data Layer (Config.json, Sound.xwm)
         │
         ▼
Configuration Layer (HomeRunBatConfig.psc)
         │
    ┌────┴────┐
    ▼         ▼
Sound Layer   Weapon Layer
(Sound.psc)   (HomeRunBat.psc)
    │              │
    └──────┬───────┘
           ▼
    MCM Layer (HomeRunBatMCM.psc)
```

### Loose Coupling Benefits
- Weapon Layer is independent of UI - MCM changes don't affect weapon logic
- Sound Layer is pluggable - can swap sound handlers without touching weapon code
- Config Layer abstracts storage - can switch from globals to JContainers without breaking scripts
- Each script has single responsibility

---

## Step-by-Step Implementation

### Step 1: Asset Preparation (COMPLETED)
- [x] Extracted `smash-bros-ultimate-super-smash-bros-ultimate-home-run-bat-hit-sound-effect.zip`
- [x] Copied WAV to `Data/Sound/fx/homerun_screech.wav`
- [x] Convert audio to `.xwm` format required (TODO - requires ffmpeg or Xbox Audio Tool)

### Step 2: Script Development

#### 2.1 HomeRunBatConfig.psc (COMPLETED)
- Purpose: Load/save user settings, provide abstraction layer
- Location: `Data/Scripts/Source/HomeRunBatConfig.psc`

#### 2.2 HomeRunBatSound.psc (COMPLETED)
- Purpose: Handle sound playback independently
- Location: `Data/Scripts/Source/HomeRunBatSound.psc`

#### 2.3 HomeRunBat.psc (COMPLETED - Core Weapon Script)
- Purpose: Handle hit detection and physics
- Location: `Data/Scripts/Source/HomeRunBat.psc`

#### 2.4 HomeRunBatMCM.psc (COMPLETED)
- Purpose: Settings menu UI
- Location: `Data/Scripts/Source/HomeRunBatMCM.psc`

### Step 3: Sound File (COMPLETED - Using WAV directly)
- [x] Sound file exists at `Data/Sound/fx/homerun_screech.wav`
- [x] Skyrim SE supports loose WAV files for sound effects
- [x] No conversion to .xwm required for loose file deployment

## Remaining Steps

### A. Compile Scripts → .pex
Use **Creation Kit Guide** (`CREATION_KIT_GUIDE.md`) for detailed instructions:
1. Open Creation Kit
2. File → Compile Scripts
3. Verify no errors in output

### B. Create Plugin (.esp)
Follow `CREATION_KIT_GUIDE.md`:
1. Create Sound record from WAV file
2. Create Weapon record (HRB_HomeRunBat)
3. Assign scripts and properties
4. Add to merchant leveled list
5. Save as `HomeRunBat.esp`

### C. Install and Test
1. Move compiled .pex files to `Data/Scripts/`
2. Place `HomeRunBat.esp` in Data folder
3. Launch Skyrim SE
4. Test weapon at Belethor's shop

### Step 6: Finalize Project Structure (PENDING)
```
skyrim_mod/
├── Data/
│   ├── Scripts/
│   │   ├── Source/
│   │   │   ├── HomeRunBatConfig.psc
│   │   │   ├── HomeRunBatSound.psc
│   │   │   ├── HomeRunBat.psc
│   │   │   └── HomeRunBatMCM.psc
│   │   ├── HomeRunBatConfig.pex
│   │   ├── HomeRunBatSound.pex
│   │   ├── HomeRunBat.pex
│   │   └── HomeRunBatMCM.pex
│   ├── Sound/
│   │   └── fx/
│   │       └── homerun_screech.xwm
│   └── HomeRunBat.esp
└── plan.md
```

### Step 7: Testing Checklist (PENDING)
- [ ] Weapon appears in merchant inventory
- [ ] Weapon can be equipped and swings normally
- [ ] Hit on NPC launches them ragdoll-style
- [ ] Knockback strength scales correctly
- [ ] Kill on hit works as expected
- [ ] MCM menu opens and settings save
- [ ] Sound plays when enabled, silent when disabled
- [ ] Settings persist across game sessions
- [ ] No crashes or CTDs on impact

---

## Dependencies
| Dependency | Purpose | Required |
|------------|---------|----------|
| SKSE64 | ApplyHavokImpulse function | Yes |
| SkyUI | MCM framework | Yes |

---

## Current Project State

### Completed
- [x] Asset preparation (sound file in place)
- [x] All 4 Papyrus scripts created with loose coupling
- [x] README.md with installation instructions
- [x] CREATION_KIT_GUIDE.md with step-by-step CK instructions
- [x] Project structure organized

## Remaining (Requires User Action)
1. **Compile scripts** using Creation Kit
2. **Create .esp plugin** using Creation Kit
3. **Install and test** in-game

---

## Notes

### Sound Conversion
If direct .xwm conversion fails:
1. Use ffmpeg: `ffmpeg -i homerun_screech.wav -ac 2 -acodec adpcm_ima_wav homerun_screech.wav`
2. Then use Bethesda's xWMAEncode.exe or keep as .wav (vanilla can handle some .wav formats)

### Mesh Reuse
Using vanilla club mesh:
- Path: `Weapons/Club/Club.nif`
- No custom mesh required
- Players can use texture mods to customize appearance

### Attack Animation
The wooden club animation set provides natural pacing - no custom animation needed.
