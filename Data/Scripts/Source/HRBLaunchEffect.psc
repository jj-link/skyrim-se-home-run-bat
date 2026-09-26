Scriptname HRBLaunchEffect extends ActiveMagicEffect

Float Property LaunchForce = 15.0 Auto
Sound Property ImpactSound Auto

Event OnEffectStart(Actor akTarget, Actor akCaster)
    If !akTarget || !akCaster || akTarget == akCaster
        Return
    EndIf
    ImpactSound.Play(akTarget)

    ; Interrupting a paired finisher can cancel its ordinary lethal damage.
    ; Only this hit waits; normal contacts have no delay or shared cooldown.
    If akTarget.IsInKillMove() || akCaster.IsInKillMove()
        Debug.Trace("HRB waiting for finisher: target=" + akTarget)
        While akTarget.IsInKillMove() || akCaster.IsInKillMove()
            Utility.Wait(0.1)
        EndWhile
    EndIf
    If !akTarget.Is3DLoaded() || !akCaster.Is3DLoaded()
        Return
    EndIf

    Debug.Trace("HRB launch: target=" + akTarget + " caster=" + akCaster + " dead=" + akTarget.IsDead())
    akCaster.PushActorAway(akTarget, LaunchForce)
EndEvent
