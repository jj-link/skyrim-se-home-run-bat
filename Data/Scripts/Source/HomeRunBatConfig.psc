Scriptname HomeRunBatConfig extends ObjectReference

GlobalVariable Property HOMERUNBAT_Strength Auto
GlobalVariable Property HOMERUNBAT_KillEnabled Auto
GlobalVariable Property HOMERUNBAT_SoundEnabled Auto

Float Property DefaultStrength = 5000.0 Auto
Bool Property DefaultKillEnabled = True Auto
Bool Property DefaultSoundEnabled = True Auto

Function Initialize()
    If !HOMERUNBAT_Strength
        HOMERUNBAT_Strength = Game.GetGlobalForm(0x1F4) as GlobalVariable
    EndIf
    If !HOMERUNBAT_KillEnabled
        HOMERUNBAT_KillEnabled = Game.GetGlobalForm(0x1F5) as GlobalVariable
    EndIf
    If !HOMERUNBAT_SoundEnabled
        HOMERUNBAT_SoundEnabled = Game.GetGlobalForm(0x1F6) as GlobalVariable
    EndIf
EndFunction

Float Function GetStrength()
    Initialize()
    If HOMERUNBAT_Strength.GetValue() == 0.0
        SetStrength(DefaultStrength)
        Return DefaultStrength
    EndIf
    Return HOMERUNBAT_Strength.GetValue()
EndFunction

Function SetStrength(Float value)
    Initialize()
    HOMERUNBAT_Strength.SetValue(value)
EndFunction

Bool Function IsKillEnabled()
    Initialize()
    If HOMERUNBAT_KillEnabled.GetValue() == 0.0
        SetKillEnabled(DefaultKillEnabled)
        Return DefaultKillEnabled
    EndIf
    Return HOMERUNBAT_KillEnabled.GetValue() == 1.0
EndFunction

Function SetKillEnabled(Bool value)
    Initialize()
    HOMERUNBAT_KillEnabled.SetValue(value as Float)
EndFunction

Bool Function IsSoundEnabled()
    Initialize()
    If HOMERUNBAT_SoundEnabled.GetValue() == 0.0
        SetSoundEnabled(DefaultSoundEnabled)
        Return DefaultSoundEnabled
    EndIf
    Return HOMERUNBAT_SoundEnabled.GetValue() == 1.0
EndFunction

Function SetSoundEnabled(Bool value)
    Initialize()
    HOMERUNBAT_SoundEnabled.SetValue(value as Float)
EndFunction
