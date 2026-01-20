Scriptname HomeRunBat extends ObjectReference

HomeRunBatSound Property SoundHandler Auto
HomeRunBatConfig Property Config Auto

Event OnHit(ObjectReference akTarget, Form akSource, Projectile akProjectile, bool abPowerAttack, bool abSneakAttack, bool abBashAttack, bool abHitBlocked)
    Actor targetActor = akTarget as Actor
    
    If targetActor && akSource as Weapon
        SoundHandler.PlayHitSound(akTarget)
        
        targetActor.PushActorAway(targetActor, 0.0)
        targetActor.ApplyHavokImpulse(0.0, 1.0, 0.3, Config.GetStrength())
        
        If Config.IsKillEnabled()
            targetActor.Kill(Game.GetPlayer())
        EndIf
    EndIf
EndEvent
