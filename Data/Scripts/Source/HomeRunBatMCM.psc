Scriptname HomeRunBatMCM extends SkyUIPlugin

HomeRunBatConfig Property Config Auto

Float Property MinStrength = 1000.0 Auto
Float Property MaxStrength = 10000.0 Auto
Float Property DefaultStrength = 5000.0 Auto

Int Function GetVersion()
    Return 1
EndFunction

Function OnConfigInit()
    BuildPages()
EndFunction

Function BuildPages()
    AddHeaderOption("$HOMERUNBAT_SETTINGS")
    
    AddSliderOption("$HOMERUNBAT_STRENGTH", Config.GetStrength(), "$HOMERUNBAT_STRENGTH_FORMAT")
    AddToggleOption("$HOMERUNBAT_KILL", Config.IsKillEnabled())
    AddToggleOption("$HOMERUNBAT_SOUND", Config.IsSoundEnabled())
EndFunction

Function OnSliderChange(String option, Float value)
    If option == "$HOMERUNBAT_STRENGTH"
        Config.SetStrength(value)
        SetSliderOptionValue(option, value)
    EndIf
EndFunction

Function OnToggleChange(String option, Bool value)
    If option == "$HOMERUNBAT_KILL"
        Config.SetKillEnabled(value)
        SetToggleOptionValue(option, value)
    ElseIf option == "$HOMERUNBAT_SOUND"
        Config.SetSoundEnabled(value)
        SetToggleOptionValue(option, value)
    EndIf
EndFunction
