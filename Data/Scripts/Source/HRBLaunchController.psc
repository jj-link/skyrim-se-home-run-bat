Scriptname HRBLaunchController extends Quest

Float Property LaunchForce = 30.0 Auto
Sound Property ImpactSound Auto

Bool Function QueueDragonLaunch(Actor akTarget, Actor akAttacker) Native

Event OnBatHit(Actor akTarget, Actor akAttacker, Bool abDragonTarget, Bool abDragonQueued)
    If !akTarget || !akAttacker || akTarget == akAttacker
        Return
    EndIf

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
            akTarget.ApplyHavokImpulse(awayX, awayY, 0.75, 1000.0)
        EndIf
    ElseIf abDragonTarget
        ; Native launch was already submitted on physical contact. A finisher
        ; or temporarily unavailable controller gets one post-finisher retry.
        If !abDragonQueued && !QueueDragonLaunch(akTarget, akAttacker)
            akAttacker.PushActorAway(akTarget, LaunchForce)
        EndIf
    Else
        akAttacker.PushActorAway(akTarget, LaunchForce)
    EndIf
EndEvent
