Scriptname HomeRunBat extends ObjectReference

Float Property Strength = 20000.0 Auto

Event OnHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)
    Actor targetActor = akTarget as Actor
    If !targetActor
        Return
    EndIf

    Actor attacker = Game.GetPlayer()
    If attacker
        Float dx = targetActor.GetPositionX() - attacker.GetPositionX()
        Float dy = targetActor.GetPositionY() - attacker.GetPositionY()
        Float dz = targetActor.GetPositionZ() - attacker.GetPositionZ()
        Float dist = Math.Sqrt((dx * dx) + (dy * dy) + (dz * dz))
        If dist > 0.0
            dx = dx / dist
            dy = dy / dist
            dz = dz / dist
        EndIf
        targetActor.ApplyHavokImpulse(dx, dy, dz + 0.2, Strength)
    Else
        targetActor.ApplyHavokImpulse(0.0, 1.0, 0.2, Strength)
    EndIf
EndEvent
