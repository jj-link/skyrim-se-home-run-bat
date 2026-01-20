Scriptname HomeRunBatSound extends ObjectReference

HomeRunBatConfig Property Config Auto
Sound Property HitSound Auto

Function PlayHitSound(ObjectReference target)
    If Config.IsSoundEnabled() && HitSound && target
        target.PlaySound(HitSound)
    EndIf
EndFunction
