Scriptname HRBLaunchEffect extends ActiveMagicEffect

Float Property LaunchForce = 15.0 Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
    If !akTarget || !akCaster || akTarget == akCaster
        Return
    EndIf
    If !akTarget.Is3DLoaded() || !akCaster.Is3DLoaded()
        Return
    EndIf

    Debug.Trace("HRB launch: target=" + akTarget + " caster=" + akCaster + " dead=" + akTarget.IsDead())
    akCaster.PushActorAway(akTarget, LaunchForce)
EndEvent
