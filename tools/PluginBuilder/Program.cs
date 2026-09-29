using Mutagen.Bethesda;
using Mutagen.Bethesda.Plugins;
using Mutagen.Bethesda.Skyrim;
using Mutagen.Bethesda.Plugins.Assets;
using Mutagen.Bethesda.Skyrim.Assets;
using Noggog;

if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: PluginBuilder <Skyrim Data directory> <output Data directory>");
    return 2;
}

var gameData = Path.GetFullPath(args[0]);
var outputData = Path.GetFullPath(args[1]);
using var skyrim = SkyrimMod.CreateFromBinaryOverlay(
    Path.Combine(gameData, "Skyrim.esm"), SkyrimRelease.SkyrimSE);
var mod = new SkyrimMod(ModKey.FromFileName("HomeRunBat.esp"), SkyrimRelease.SkyrimSE);
mod.ModHeader.Author = "jj-link";
mod.ModHeader.Description = "Home Run Bat: actor knockback on contact, without scripted death.";

// Explicit FormKeys preserve save identity. Retired MGEF 801 / ENCH 802 stay unused.
var template = skyrim.Weapons.Single(w => w.EditorID == "IronGreatsword");
var bat = mod.Weapons.DuplicateInAsNewRecord(template, new FormKey(mod.ModKey, 0x000800));
var firstPerson = mod.Statics.AddNew(new FormKey(mod.ModKey, 0x000803));
var impact = mod.SoundDescriptors.AddNew(new FormKey(mod.ModKey, 0x000804));
var impactMarker = mod.SoundMarkers.AddNew(new FormKey(mod.ModKey, 0x000805));
var controller = mod.Quests.AddNew(new FormKey(mod.ModKey, 0x000806));
var acquisition = new PlacedObject(new FormKey(mod.ModKey, 0x000807), SkyrimRelease.SkyrimSE);
mod.ModHeader.Stats.NextFormID = 0x000808;

bat.EditorID = "HRBHomeRunBat";
bat.Name = "Home Run Bat";
bat.Description = "Sends targets flying on impact.";
bat.BasicStats!.Damage = 8;
bat.BasicStats.Weight = 5;
bat.BasicStats.Value = 250;
bat.EnchantmentAmount = null;
bat.ObjectEffect.Clear();
bat.VirtualMachineAdapter = null;
bat.Model = new Model { File = @"HomeRunBat\HomeRunBat.nif" };
bat.ObjectBounds = new ObjectBounds
{
    First = new P3Int16(-5, -22, -5),
    Second = new P3Int16(5, 78, 5)
};
firstPerson.EditorID = "HRBFirstPersonBat";
firstPerson.Model = new Model { File = @"HomeRunBat\HomeRunBat.nif" };
firstPerson.ObjectBounds = new ObjectBounds
{
    First = new P3Int16(-5, -22, -5),
    Second = new P3Int16(5, 78, 5)
};
bat.FirstPersonModel.SetTo(firstPerson.FormKey);

impact.EditorID = "HRBImpactSound";
impact.Type = SoundDescriptor.DescriptorType.Standard;
impact.Category.SetTo(new FormKey(skyrim.ModKey, 0x0172A1));
impact.OutputModel.SetTo(new FormKey(skyrim.ModKey, 0x07E5DC));
impact.SoundFiles.Add(new AssetLink<SkyrimSoundAssetType>(@"fx\HomeRunBat\impact.wav"));
impact.LoopAndRumble = new SoundLoopAndRumble { Loop = SoundDescriptor.LoopType.None };
impact.Priority = 64;
impactMarker.EditorID = "HRBImpact";
impactMarker.SoundDescriptor.SetTo(impact.FormKey);

// A running, never-stopped quest keeps the native event receiver alive across saves.
// QuestAdapter supplies the quest-specific VMAD tail, even without fragments/aliases.
controller.EditorID = "HRBLaunchController";
controller.Flags = Quest.Flag.StartGameEnabled | Quest.Flag.RunOnce;
controller.Type = Quest.TypeEnum.None;
controller.NextAliasID = 0;
controller.VirtualMachineAdapter = new QuestAdapter
{
    Version = 5,
    ObjectFormat = 2,
    ExtraBindDataVersion = 2,
    FileName = string.Empty
};
var controllerScript = new ScriptEntry { Name = "HRBLaunchController" };
controllerScript.Properties.Add(new ScriptFloatProperty { Name = "LaunchForce", Data = 30.0f });
controllerScript.Properties.Add(new ScriptObjectProperty
{
    Name = "ImpactSound",
    Object = impactMarker.ToLink<ISkyrimMajorRecordGetter>()
});
controller.VirtualMachineAdapter.Scripts.Add(controllerScript);

// Skyrim.esm: barrel REFR 034EB0 (BarrelFood01, base 000845) outside Warmaiden's,
// at (21258.400390625, -7874.869140625, -3617.713134765625). Its OBND top is Z=80.
// Lay the bat east-west across its lid, centering the bat's Y bounds (-22..78).
var sourceWorld = skyrim.Worldspaces[new FormKey(skyrim.ModKey, 0x01A26F)];
var sourceBlock = sourceWorld.SubCells.Single(b => b.BlockNumberX == 0 && b.BlockNumberY == -1);
var sourceSubBlock = sourceBlock.Items.Single(b => b.BlockNumberX == 0 && b.BlockNumberY == -1);
var sourceCell = sourceSubBlock.Items.Single(c => c.FormKey.ID == 0x01A27A);
var barrel = sourceCell.Temporary.OfType<IPlacedObjectGetter>()
    .Single(r => r.FormKey.ID == 0x034EB0);
var barrelPosition = barrel.Placement!.Position;
var barrelTop = skyrim.Containers[barrel.Base.FormKey].ObjectBounds.Second.Z;
acquisition.EditorID = "HRBWarmaidensBat";
acquisition.Base.SetTo(bat.FormKey);
acquisition.Placement = new Placement
{
    Position = new P3Float(
        barrelPosition.X - 28.0f,
        barrelPosition.Y,
        barrelPosition.Z + barrelTop - bat.ObjectBounds.First.Z + 1.0f),
    Rotation = new P3Float(0, 0, MathF.PI / 2)
};
acquisition.MajorRecordFlagsRaw = (int)PlacedObject.ItemMajorFlag.NoRespawn;
// This exterior CELL has no owner; explicit Player ownership also prevents theft
// if another mod assigns a cell owner. Do not inherit the shop interior's faction.
acquisition.Owner.SetTo(new FormKey(skyrim.ModKey, 0x000007)); // Player NPC, not ACHR 14.

// Match Mutagen's parent-context copy masks: carry only the necessary WRLD/CELL
// headers, without duplicating vanilla placements, landscape, navmeshes or groups.
var world = sourceWorld.DeepCopy(new Worldspace.TranslationMask(true)
{
    SubCells = false,
    TopCell = false,
    LargeReferences = false,
    OffsetData = false,
    SubCellsUnknown = false,
    SubCellsTimestamp = false
});
var cell = sourceCell.DeepCopy(new Cell.TranslationMask(true)
{
    Persistent = false,
    Temporary = false,
    Landscape = false,
    NavigationMeshes = false,
    Timestamp = false,
    PersistentTimestamp = false,
    TemporaryTimestamp = false,
    UnknownGroupData = false,
    PersistentUnknownGroupData = false,
    TemporaryUnknownGroupData = false
});
var block = new WorldspaceBlock
{
    BlockNumberX = sourceBlock.BlockNumberX,
    BlockNumberY = sourceBlock.BlockNumberY,
    GroupType = GroupTypeEnum.ExteriorCellBlock
};
var subBlock = new WorldspaceSubBlock
{
    BlockNumberX = sourceSubBlock.BlockNumberX,
    BlockNumberY = sourceSubBlock.BlockNumberY,
    GroupType = GroupTypeEnum.ExteriorCellSubBlock
};
cell.Temporary.Add(acquisition);
subBlock.Items.Add(cell);
block.Items.Add(subBlock);
world.SubCells.Add(block);
mod.Worldspaces.Add(world);

Directory.CreateDirectory(outputData);
var outputPath = Path.Combine(outputData, mod.ModKey.FileName.String);
var masters = new[] { skyrim.ModKey };
mod.BeginWrite.ToPath(outputPath)
    .WithLoadOrder(masters)
    .WithDataFolder(gameData)
    .Write();
Console.WriteLine($"Wrote {outputPath}");

// Like xEdit's SEQ writer: little-endian, file-local FormID (one Skyrim.esm master),
// not a runtime load-order FormID. This initializes the new SGE quest on old saves.
var sequenceDirectory = Path.Combine(outputData, "SEQ");
Directory.CreateDirectory(sequenceDirectory);
var sequencePath = Path.Combine(sequenceDirectory, $"{mod.ModKey.Name}.seq");
using (var sequence = new BinaryWriter(File.Create(sequencePath)))
{
    sequence.Write(controller.FormKey.ID | ((uint)masters.Length << 24));
}
Console.WriteLine($"Wrote {sequencePath}");
foreach (var record in mod.EnumerateMajorRecords())
{
    Console.WriteLine($"{record.EditorID}: {record.FormKey}");
}
return 0;
