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

// Preserve these allocation positions: existing saves identify records by FormID.
var template = skyrim.Weapons.Single(w => w.EditorID == "IronGreatsword");
var bat = mod.Weapons.DuplicateInAsNewRecord(template);
var launch = mod.MagicEffects.AddNew();
var enchantment = mod.ObjectEffects.AddNew();
var firstPerson = mod.Statics.AddNew();
var impact = mod.SoundDescriptors.AddNew();
var impactMarker = mod.SoundMarkers.AddNew();

bat.EditorID = "HRBHomeRunBat";
bat.Name = "Home Run Bat";
bat.Description = "Sends targets flying on impact.";
bat.BasicStats!.Damage = 8;
bat.BasicStats.Weight = 5;
bat.BasicStats.Value = 250;
bat.EnchantmentAmount = 0;
bat.ObjectEffect.SetTo(enchantment.FormKey);
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

launch.EditorID = "HRBLaunchEffect";
launch.Name = "Home Run";
launch.Archetype = new MagicEffectArchetype(MagicEffectArchetype.TypeEnum.Script);
launch.CastType = CastType.FireAndForget;
launch.TargetType = TargetType.Touch;
launch.ResistValue = ActorValue.None;
launch.Flags = MagicEffect.Flag.NoDuration | MagicEffect.Flag.NoMagnitude
    | MagicEffect.Flag.NoArea | MagicEffect.Flag.HideInUI
    | MagicEffect.Flag.NoDeathDispel;
launch.VirtualMachineAdapter = new VirtualMachineAdapter();
var launchScript = new ScriptEntry { Name = "HRBLaunchEffect" };
launchScript.Properties.Add(new ScriptFloatProperty { Name = "LaunchForce", Data = 15.0f });
launchScript.Properties.Add(new ScriptObjectProperty
{
    Name = "ImpactSound",
    Object = impactMarker.ToLink<ISkyrimMajorRecordGetter>()
});
launch.VirtualMachineAdapter.Scripts.Add(launchScript);

enchantment.EditorID = "HRBEnchantment";
enchantment.Name = "Home Run";
enchantment.Flags = ObjectEffect.Flag.NoAutoCalc;
enchantment.CastType = CastType.FireAndForget;
enchantment.TargetType = TargetType.Touch;
enchantment.EnchantType = ObjectEffect.EnchantTypeEnum.Enchantment;
enchantment.EnchantmentCost = 0;
enchantment.EnchantmentAmount = 0;
enchantment.Effects.Add(new Effect
{
    BaseEffect = launch.ToLink<IMagicEffectGetter>().AsNullable(),
    Data = new EffectData { Magnitude = 0, Area = 0, Duration = 0 }
});

Directory.CreateDirectory(outputData);
var outputPath = Path.Combine(outputData, mod.ModKey.FileName.String);
mod.BeginWrite.ToPath(outputPath)
    .WithLoadOrder(new[] { skyrim.ModKey })
    .WithDataFolder(gameData)
    .Write();
Console.WriteLine($"Wrote {outputPath}");
foreach (var record in mod.EnumerateMajorRecords())
{
    Console.WriteLine($"{record.EditorID}: {record.FormKey}");
}
return 0;
