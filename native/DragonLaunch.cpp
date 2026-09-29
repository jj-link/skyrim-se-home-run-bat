#include "DragonLaunch.h"

#include "skse64/GameData.h"
#include "skse64/GameReferences.h"
#include "skse64/PluginAPI.h"
#include "skse64/gamethreads.h"

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace hrb
{
#if HRB_DIAGNOSTICS
void LogDragonImpact(const Actor* target, const void* controller, UInt32 previousMode, float x, float y, float z);
#endif

namespace
{
constexpr UInt32 kActorTypeDragon = 0x00035D59;
constexpr UInt32 kSpectralDragonLocalID = 0x01F98F;
constexpr std::uintptr_t kProxyVtableRVA = 0x01A89558;
constexpr float kWorldToHavok = 0.0142875f;
constexpr float kImpactSeconds = 1.0f;
constexpr UInt32 kGroundedMode = 0;
constexpr UInt32 kAirborneMode = 2;
constexpr UInt32 kStableState = 11;

using GetController = void* (*)(Actor*);
using GetKillMove = bool (*)(const Actor*);
SKSETaskInterface* g_tasks = nullptr;
UInt32 g_spectralDragonRaceID = 0;

struct alignas(16) HavokVector
{
    float x, y, z, w;
};
static_assert(sizeof(HavokVector) == 16);
static_assert(offsetof(TESObjectREFR, pos) == 0x54);
static_assert(offsetof(Actor, actorState) + offsetof(ActorState, flags04) == 0xC8);
// SDK member offsets, checked against the exact x64 class layout compiled here.
static_assert(offsetof(Actor, race) == 0x1F8);
static_assert(offsetof(TESRace, keyword) == 0x70);

bool CodeMatches(std::uintptr_t rva, std::size_t length, UInt64 expected)
{
    const auto* bytes = reinterpret_cast<const unsigned char*>(RelocationManager::s_baseAddr + rva);
    UInt64 hash = 14695981039346656037ULL;
    for (std::size_t index = 0; index < length; ++index) {
        hash = (hash ^ bytes[index]) * 1099511628211ULL;
    }
    return hash == expected;
}

unsigned char* EligibleController(Actor* target)
{
    if (!target || target->IsDead(1) || !target->GetNiNode() ||
        ((target->actorState.flags04 >> 18) & 7) != 0) {
        return nullptr;
    }
    RelocAddr<GetController> getController(0x006750B0);
    auto* controller = static_cast<unsigned char*>(getController(target));
    if (!controller || *reinterpret_cast<const std::uintptr_t*>(controller) !=
            RelocationManager::s_baseAddr + kProxyVtableRVA) {
        return nullptr;
    }
    UInt32 mode, state, flags;
    memcpy(&mode, controller + 0x200, sizeof(mode));
    memcpy(&state, controller + 0x21C, sizeof(state));
    memcpy(&flags, controller + 0x218, sizeof(flags));
    if (state != kStableState || (mode != kAirborneMode &&
            (mode != kGroundedMode || !(flags & 0x100)))) {
        return nullptr;
    }
    return controller;
}

class DragonImpact final : public TaskDelegate
{
public:
    DragonImpact(Actor* target, Actor* attacker) : target_(target), attacker_(attacker) {}

    void Run() override
    {
        if (!IsDragon(target_) || !attacker_->GetNiNode() ||
            IsInKillMove(target_) || IsInKillMove(attacker_)) {
            return;
        }
        auto* controller = EligibleController(target_);
        if (!controller) {
            return;
        }
        float x = target_->pos.x - attacker_->pos.x;
        float y = target_->pos.y - attacker_->pos.y;
        const float distance = std::sqrt(x * x + y * y);
        if (distance > 0.01f) {
            x /= distance;
            y /= distance;
        } else {
            x = std::sin(attacker_->rot.z);
            y = std::cos(attacker_->rot.z);
        }

        // Grounded dragons hold positive impact Z but their character proxy
        // discards it. Mode 2 is the same per-controller airborne transition
        // observed on a real player jump. The engine returns it to mode 0 on
        // landing; no actor flag, race, gravity, or AI state is changed.
        UInt32 mode;
        memcpy(&mode, controller + 0x200, sizeof(mode));
        if (mode == kGroundedMode) {
            memcpy(controller + 0x200, &kAirborneMode, sizeof(kAirborneMode));
        }
        const HavokVector impact{
            x * 3000.0f * kWorldToHavok / kImpactSeconds,
            y * 3000.0f * kWorldToHavok / kImpactSeconds,
            4500.0f * kWorldToHavok / kImpactSeconds, 0.0f };
        memcpy(controller + 0x220, &kImpactSeconds, sizeof(kImpactSeconds));
        memcpy(controller + 0xA0, &impact, sizeof(impact));
#if HRB_DIAGNOSTICS
        LogDragonImpact(target_, controller, mode, impact.x, impact.y, impact.z);
#endif
        // The stock controller decays this envelope and clears both fields;
        // replacing it per hit admits equal-force overlapping contacts.
    }

    void Dispose() override { delete this; }

private:
    NiPointer<Actor> target_;
    NiPointer<Actor> attacker_;
};
}

bool InitializeDragonPhysics(const SKSEInterface* skse)
{
    if (!CodeMatches(0x006750B0, 19, 0x558698A61C170E62ULL) ||
        !CodeMatches(0x00721EB0, 18, 0x59434955A0BF91F1ULL) ||
        !CodeMatches(0x0033C358, 18, 0x9822504EFDE2654CULL) ||
        !CodeMatches(0x006CC690, 12, 0x1F9CB86483C334E4ULL) ||
        !CodeMatches(0x0106527F, 31, 0xA1DAB4D6AEB6B4AAULL) ||
        !CodeMatches(0x010654AF, 23, 0x7353356D1621B2B0ULL) ||
        !CodeMatches(0x010C880A, 65, 0x88816E6B5C6DEE1FULL) ||
        !CodeMatches(0x01065CF0, 190, 0x33CACC3834258943ULL) ||
        !CodeMatches(0x01065DC0, 72, 0x60729E9497907EAEULL) ||
        !CodeMatches(0x010657A0, 49, 0x3475BC50B3EBA3C4ULL) ||
        !CodeMatches(0x017FDE5C, 4, 0xCAF63137721CE2C3ULL)) {
        return false;
    }
    g_tasks = static_cast<SKSETaskInterface*>(skse->QueryInterface(kInterface_Task));
    return g_tasks && g_tasks->interfaceVersion >= SKSETaskInterface::kInterfaceVersion;
}

void LoadDragonRaceIDs()
{
    auto* data = DataHandler::GetSingleton();
    const auto* dlc = data ? data->LookupModByName("Dragonborn.esm") : nullptr;
    g_spectralDragonRaceID = dlc && dlc->IsActive() ?
        dlc->GetFormID(kSpectralDragonLocalID) : 0;
}

bool IsDragon(const Actor* actor)
{
    const auto* race = actor ? actor->race : nullptr;
    if (!race) {
        return false;
    }
    if (g_spectralDragonRaceID && race->formID == g_spectralDragonRaceID) {
        return true;
    }
    const auto& keyword = race->keyword;
    for (UInt32 index = 0; keyword.keywords && index < keyword.numKeywords; ++index) {
        const auto* item = keyword.keywords[index];
        if (item && item->formID == kActorTypeDragon) {
            return true;
        }
    }
    return false;
}

bool IsInKillMove(const Actor* actor)
{
    RelocAddr<GetKillMove> getKillMove(0x006CC690);
    return getKillMove(actor);
}

DragonContact QueueDragonLaunch(Actor* target, Actor* attacker)
{
    if (!IsDragon(target)) {
        return DragonContact::NotDragon;
    }
    if (!g_tasks || !attacker || target == attacker ||
        !attacker->GetNiNode() || IsInKillMove(target) ||
        IsInKillMove(attacker) || !EligibleController(target)) {
        return DragonContact::Deferred;
    }
    g_tasks->AddTask(new DragonImpact(target, attacker));
    return DragonContact::Queued;
}
}
