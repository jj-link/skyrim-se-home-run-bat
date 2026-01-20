# Home Run Bat Mod for Skyrim SE

A weapon mod that launches NPCs across the map with physics-based ragdoll impulses, featuring configurable strength and the iconic Super Smash Bros. home-run bat sound effect.

## Features

- Physics-based ragdoll launch using Havok impulse
- Configurable knockback strength (1000-10000)
- Toggle kill-on-hit mode
- Toggle sound effects
- MCM configuration menu
- Loose-coupled architecture for maintainability

## Installation

1. Extract all files to your Skyrim SE Data folder:
   ```
   Data/
   ├── Scripts/
   │   ├── HomeRunBatConfig.pex
   │   ├── HomeRunBatSound.pex
   │   ├── HomeRunBat.pex
   │   └── HomeRunBatMCM.pex
   ├── Sound/
   │   └── fx/
   │       └── homerun_screech.wav
   └── HomeRunBat.esp
   ```

2. Enable `HomeRunBat.esp` in your load order (e.g., via LOOT)

3. Find the Home Run Bat at:
   - Belethor's General Goods (Solitude)
   - General goods merchants throughout Skyrim

4. Configure via MCM (Mod Configuration Menu) under "Home Run Bat"

## Requirements

- Skyrim Special Edition
- SKSE64
- SkyUI

## Configuration

Access MCM menu to adjust:
- **Strength**: How hard NPCs are launched (1000-10000, default: 5000)
- **Kill on Hit**: Instantly kill NPCs on impact (default: ON)
- **Sound**: Play SSB home-run screech on hit (default: ON)

## Manual Setup Required

The `.pex` compiled scripts and `.esp` plugin file require Creation Kit to generate:

### To Compile Scripts:
1. Open Creation Kit
2. Go to File > Compile Scripts
3. Or use command line: `PapyrusCompiler.exe /g <game_path> /i <script_path> /o <output_path>`

### To Create Plugin (ESP):
1. Open Creation Kit
2. Create new plugin: File > New
3. Create Weapon record based on Wooden Club
4. Assign scripts to weapon
5. Create Sound record from `homerun_screech.wav`
6. Add weapon to merchant leveled lists
7. Save plugin as `HomeRunBat.esp`

### Script Properties to Set:
In Creation Kit, select the weapon record and set:
- `SoundHandler`: Link to HomeRunBatSound script instance
- `Config`: Link to HomeRunBatConfig script instance
- `HitSound`: Link to sound record

## Architecture

```
HomeRunBatMCM.psc     ← Settings UI (SkyUI)
        ↓
HomeRunBatConfig.psc  ← Settings storage (globals)
        ↓
┌───────┴───────┐
↓               ↓
HomeRunBat    HomeRunBatSound
  .psc            .psc
   ↓               ↓
 Physics       Sound playback
   └───────┬───────┘
           ↓
      Hit detection
```

## Files Included

| File | Purpose |
|------|---------|
| `HomeRunBat.psc` | Core weapon script - handles hit detection & physics |
| `HomeRunBatConfig.psc` | Configuration layer - manages settings |
| `HomeRunBatSound.psc` | Sound handler - plays effects |
| `HomeRunBatMCM.psc` | MCM interface - user settings |
| `homerun_screech.wav` | SSB home-run bat sound effect |

## Troubleshooting

**Weapon not appearing in game:**
- Verify .esp is enabled in load order
- Check script compilation succeeded
- Ensure scripts are in `Data/Scripts/` (not Source/)

**Sound not playing:**
- Confirm sound file at `Data/Sound/fx/homerun_screech.wav`
- Check sound is not disabled in MCM
- Verify Sound property is linked in Creation Kit

**NPCs not launching:**
- Ensure SKSE64 is installed and working
- Check knockback strength in MCM (try increasing)
- Verify weapon script is attached

**MCM menu not showing:**
- Confirm SkyUI is installed
- Check MCM script compiled correctly
- Look for "Home Run Bat" in Mod Configuration Menu

## Credits

- Sound effect: Super Smash Bros. Ultimate
- Architecture: Loose coupling principles

## License

Personal use only. Do not redistribute without permission.
