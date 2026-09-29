#pragma once

class Actor;
struct SKSEInterface;

namespace hrb
{
bool InitializeDragonPhysics(const SKSEInterface* skse);
void LoadDragonRaceIDs();
enum class DragonContact { NotDragon, Deferred, Queued };
bool IsDragon(const Actor* actor);
bool IsInKillMove(const Actor* actor);
DragonContact QueueDragonLaunch(Actor* target, Actor* attacker);
}
