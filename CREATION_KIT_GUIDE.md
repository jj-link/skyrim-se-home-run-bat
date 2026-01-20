# Creation Kit Quick Reference - Home Run Bat

## Opening Creation Kit
1. Launch "CreationKit.exe" from your Skyrim SE folder
2. Wait for "Load Master" prompt - click OK
3. Create new plugin: File → New

---

## Step 1: Create Sound Record

1. In Object Window, expand "Sound"
2. Right-click → "New"
3. Name: `HRB_HitSound`
4. Browse for file: `Data\Sound\fx\homerun_screech.wav`
5. Click "Play" to test
6. OK to save

---

## Step 2: Create Weapon Record

1. In Object Window, expand "Weapon"
2. Right-click → "New"
3. **Editor ID**: `HRB_HomeRunBat`
4. **Name**: "Home Run Bat"
5. **Model**: `Weapons\Club\Club.nif` (uses vanilla club mesh)
6. **Icon**: `Weapons\Club\Club.dds` (or create custom)
7. **Script**: Click and select `HomeRunBat`
8. **Sound - Impact**: Link to `HRB_HitSound`

### Weapon Stats
| Field | Value |
|-------|-------|
| Damage | 15 |
| Weight | 2.0 |
| Value | 100 |
| Reach | 55 |
| Speed | 1.0 |

---

## Step 3: Assign Script Properties

With weapon selected, expand "Script" section:
1. Click "Edit" on Script properties
2. **SoundHandler**: New Object → select HomeRunBatSound
3. **Config**: New Object → select HomeRunBatConfig

---

## Step 4: Create Script Instances

1. In Object Window, right-click "Scripts"
2. New → Scriptname: `HomeRunBatSound`
3. Properties:
   - Config: HomeRunBatConfig
   - HitSound: HRB_HitSound
4. New → Scriptname: `HomeRunBatConfig`
5. Properties: (defaults are fine)
6. New → Scriptname: `HomeRunBatMCM`
7. Properties:
   - Config: HomeRunBatConfig

---

## Step 5: Add to Merchant Lists

### Option A: Add to Existing Leveled List
1. Find "LItemWeaponsClub" or similar in Object Window
2. Double-click to edit
3. Add new entry:
   - Count: 1
   - Item: HRB_HomeRunBat
   - Level: 1

### Option B: Create New Shop Inventory
1. Right-click "Leveled Item" → New
2. Editor ID: `HRB_HomeRunBatShop`
3. Add entry: Count 1, Item HRB_HomeRunBat, Level 1
4. Use "Add Item to Lev. List" to add to specific shop containers

---

## Step 6: Save Plugin

1. File → Save As...
2. Name: `HomeRunBat.esp`
3. Save to Skyrim SE Data folder

---

## Step 7: Compile Scripts

### Method A: In Creation Kit
1. File → Compile Scripts
2. Wait for completion (check for errors)

### Method B: Command Line
```cmd
cd "C:\Program Files (x86)\Steam\steamapps\common\Skyrim Special Edition"
PapyrusCompiler.exe /game:SkyrimSE /script:"C:\path\to\skyrim_mod\Data\Scripts\Source" /output:"C:\path\to\skyrim_mod\Data\Scripts"
```

---

## Common Errors

| Error | Solution |
|-------|----------|
| "Script not found" | Ensure .psc files in Source folder before compiling |
| "Property not set" | Link all required properties in CK |
| "Sound won't play" | Check sound file path, try .xwm format |

---

## Testing Checklist

- [ ] Weapon appears at Belethor's shop
- [ ] Can equip and swing weapon
- [ ] Hit NPC launches them
- [ ] Sound plays on hit
- [ ] MCM menu appears in Mod Configuration
- [ ] Settings save between sessions
