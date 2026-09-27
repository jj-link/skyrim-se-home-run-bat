Scriptname HRBLaunchController extends Quest

Float Property LaunchForce = 15.0 Auto
Sound Property ImpactSound Auto

Event OnBatHit(Actor akTarget, Actor akAttacker)
    If !akTarget || !akAttacker || akTarget == akAttacker
        Return
    EndIf

    Debug.Trace("HRB native contact: target=" + akTarget + " attacker=" + akAttacker)
    ImpactSound.Play(akTarget)

    Float awayX = akTarget.GetPositionX() - akAttacker.GetPositionX()
    Float awayY = akTarget.GetPositionY() - akAttacker.GetPositionY()
    Float horizontalDistance = Math.Sqrt(awayX * awayX + awayY * awayY)
    If horizontalDistance > 0.01
        awayX /= horizontalDistance
        awayY /= horizontalDistance
    Else
        awayX = Math.Sin(akAttacker.GetAngleZ())
        awayY = Math.Cos(akAttacker.GetAngleZ())
    EndIf

    ; Let paired finishers deliver their ordinary damage before changing physics.
    While (akTarget.IsInKillMove() || akAttacker.IsInKillMove()) && akTarget.Is3DLoaded() && akAttacker.Is3DLoaded()
        Utility.Wait(0.1)
    EndWhile
    If !akTarget.Is3DLoaded() || !akAttacker.Is3DLoaded()
        Return
    EndIf

    If akTarget.IsDead()
        akTarget.ForceAddRagdollToWorld()
        ; Give the newly attached rigid bodies a physics step before the impulse.
        Utility.Wait(0.1)
        If akTarget.Is3DLoaded() && akTarget.IsDead()
            Debug.Trace("HRB corpse impulse: target=" + akTarget)
            akTarget.ApplyHavokImpulse(awayX, awayY, 0.75, 1000.0)
        EndIf
    Else
        Debug.Trace("HRB living launch: target=" + akTarget)
        akAttacker.PushActorAway(akTarget, LaunchForce)
    EndIf
EndEvent
