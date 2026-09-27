#include "common/IPrefix.h"
#include "skse64/PluginAPI.h"
#include "skse64/GameData.h"
#include "skse64/GameEvents.h"
#include "skse64/PapyrusArgs.h"
#include "skse64/PapyrusVM.h"
#include "skse64_common/skse_version.h"

#include <cstddef>
#include <cwchar>
#include <share.h>
#include <type_traits>

namespace
{
// This plugin supports exactly the Steam 1.7.99.0 ABI, not another SDK target.
// Keep the value explicit in both the exported metadata and the load guard.
constexpr UInt32 kRuntime = MAKE_EXE_VERSION_EX(1, 7, 99, 0);
constexpr UInt32 kPluginVersion = 1;
constexpr char kPluginFile[] = "HomeRunBat.esp";
constexpr UInt32 kWeaponLocalID = 0x800;
constexpr UInt32 kQuestLocalID = 0x806;
FILE* g_log = nullptr;

void Log(const char* format, ...)
{
    char text[512];
    va_list args;
    va_start(args, format);
    vsnprintf_s(text, sizeof(text), _TRUNCATE, format, args);
    va_end(args);
    OutputDebugStringA("HomeRunBat: ");
    OutputDebugStringA(text);
    OutputDebugStringA("\n");
    if (g_log) {
        fprintf(g_log, "%s\n", text);
        fflush(g_log);
    }
}

void OpenLog()
{
    HMODULE module = nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
            GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(&OpenLog), &module)) {
        return;
    }
    wchar_t path[32768];
    const DWORD length = GetModuleFileNameW(module, path, static_cast<DWORD>(_countof(path)));
    if (!length || length >= _countof(path)) {
        return;
    }
    wchar_t* filename = wcsrchr(path, L'\\');
    if (!filename) {
        return;
    }
    wcscpy_s(filename + 1, _countof(path) - (filename + 1 - path), L"HomeRunBat.log");
    g_log = _wfsopen(path, L"w", _SH_DENYWR);
}

void InitializationFailure(const char* reason)
{
    Log("DISABLED: %s", reason);
    MessageBoxA(nullptr, reason, "Home Run Bat could not initialize", MB_OK | MB_ICONERROR);
}

// GameEvents.h:29-38 declares these exact fields, but keeps them private.
// This read-only snapshot is used only to identify the otherwise unnamed hit
// dispatcher. No dispatcher index, relocated address, or trailing extent is guessed.
struct DispatcherArrays
{
    tArray<void*> sinks;
    tArray<void*> additions;
    tArray<void*> removals;
};
static_assert(sizeof(DispatcherArrays) == 0x48);
static_assert(sizeof(EventDispatcher<void>) == 0x58);
static_assert(std::is_standard_layout<EventDispatcherList>::value);
static_assert(sizeof(EventDispatcherList) % sizeof(EventDispatcher<void>) == 0);
static_assert(offsetof(SkyrimVM, eventSinks) == 0x10);
static_assert(offsetof(TESHitEvent, sourceFormID) == 0x10);
static_assert(offsetof(TESHitEvent, projectileFormID) == 0x14);
static_assert(offsetof(TESHitEvent, flags) == 0x18);
static_assert(sizeof(TESHitEvent) == 0x20);

bool Contains(const tArray<void*>& array, const void* sink)
{
    for (UInt32 index = 0; index < array.count; ++index) {
        if (array.entries[index] == sink) {
            return true;
        }
    }
    return false;
}

EventDispatcher<TESHitEvent>* FindHitDispatcher(SkyrimVM* vm)
{
    auto* sources = GetEventDispatcherList();
    if (!sources) {
        return nullptr;
    }

    // eventSinks[] contains inline sink vtables, not pointers to separately
    // allocated sinks. PapyrusVM.h:320-379 names their types and their extent.
    const void* vmHitSink = &vm->eventSinks[SkyrimVM::kEventSink_Hit];
    auto* bytes = reinterpret_cast<unsigned char*>(sources);
    EventDispatcher<TESHitEvent>* result = nullptr;
    UInt32 matches = 0;
    for (std::size_t offset = 0; offset < sizeof(EventDispatcherList);
         offset += sizeof(EventDispatcher<void>)) {
        bool containsHitSink;
        {
            // The lock follows the three arrays in the official SDK layout.
            auto* lock = reinterpret_cast<SimpleLock*>(bytes + offset + sizeof(DispatcherArrays));
            SimpleLocker guard(lock);
            DispatcherArrays arrays;
            memcpy(&arrays, bytes + offset, sizeof(arrays));
            containsHitSink = (Contains(arrays.sinks, vmHitSink) || Contains(arrays.additions, vmHitSink)) &&
                !Contains(arrays.removals, vmHitSink);
        }
        if (containsHitSink) {
            ++matches;
            result = reinterpret_cast<EventDispatcher<TESHitEvent>*>(bytes + offset);
        }
    }
    if (matches != 1) {
        Log("Hit dispatcher lookup expected one VM hit sink match; found %u", matches);
        return nullptr;
    }
#if HRB_DIAGNOSTICS
    Log("Resolved TESHitEvent dispatcher at holder+0x%zX; VM hit sink=%p",
        static_cast<std::size_t>(reinterpret_cast<unsigned char*>(result) - bytes), vmHitSink);
#endif
    return result;
}

// QueueEvent consumes Copy synchronously, as in SDK PapyrusEvents.cpp's stack
// EventQueueFunctor2. Only the VM-owned typed identifiers survive this call;
// no actor pointer, registry pointer, or borrowed argument functor is deferred.
class BatHitArguments final : public IFunctionArguments
{
public:
    BatHitArguments(VMClassRegistry* registry, Actor* target, Actor* attacker) :
        registry_(registry), target_(target), attacker_(attacker) {}

    bool Copy(Output* output) override
    {
        output->Resize(2);
        auto* targetValue = output->Get(0);
        auto* attackerValue = output->Get(1);
        if (!targetValue || !attackerValue) {
            return false;
        }
        PackValue(targetValue, &target_, registry_);
        PackValue(attackerValue, &attacker_, registry_);
        return targetValue->IsIdentifier() && targetValue->data.id &&
            attackerValue->IsIdentifier() && attackerValue->data.id;
    }

private:
    VMClassRegistry* registry_;
    Actor* target_;
    Actor* attacker_;
};

class BatHitSink final : public BSTEventSink<TESHitEvent>
{
public:
    void Initialize(TESForm* weapon, TESQuest* quest, BSFixedString* eventName)
    {
        weaponID_ = weapon->formID;
        quest_ = quest;
        eventName_ = eventName;
    }

    EventResult ReceiveEvent(TESHitEvent* hit, EventDispatcher<TESHitEvent>*) override
    {
        if (!hit || hit->sourceFormID != weaponID_ || hit->projectileFormID != 0 ||
            (hit->flags & TESHitEvent::kFlag_Bash) || !hit->target || !hit->caster ||
            hit->target == hit->caster || hit->target->formType != Actor::kTypeID ||
            hit->caster->formType != Actor::kTypeID) {
            return kEvent_Continue;
        }

        // Do not test health, death, blocking, power attack, essential status,
        // equipment owner, or player identity. The physical contact is sufficient.
        auto* vm = *g_skyrimVM;
        auto* registry = vm ? vm->GetClassRegistry() : nullptr;
        auto* policy = registry ? registry->GetHandlePolicy() : nullptr;
        if (!policy) {
            return kEvent_Continue;
        }
        const UInt64 handle = policy->Create(TESQuest::kTypeID, quest_);
        if (handle == policy->GetInvalidHandle()) {
            return kEvent_Continue;
        }
        // A quest handle is obtained from the current VM, never retained over
        // save/new-game reverts. QueueEvent owns its queued values after return.
        policy->AddRef(handle);
        BatHitArguments args(registry, static_cast<Actor*>(hit->target), static_cast<Actor*>(hit->caster));
        registry->QueueEvent(handle, eventName_, &args);
        policy->Release(handle);
#if HRB_DIAGNOSTICS
        Log("Accepted contact: target=%08X attacker=%08X source=%08X projectile=%08X flags=%08X; submitted OnBatHit",
            hit->target->formID, hit->caster->formID, hit->sourceFormID, hit->projectileFormID, hit->flags & 0xFu);
#endif
        return kEvent_Continue;
    }

private:
    UInt32 weaponID_ = 0;
    TESQuest* quest_ = nullptr;
    BSFixedString* eventName_ = nullptr;
};

BatHitSink g_hitSink;
bool g_registered = false;

void OnSKSEMessage(SKSEMessagingInterface::Message* message)
{
    if (!message || message->type != SKSEMessagingInterface::kMessage_DataLoaded || g_registered) {
        return;
    }
    auto* data = DataHandler::GetSingleton();
    const auto* mod = data ? data->LookupModByName(kPluginFile) : nullptr;
    if (!mod || !mod->IsActive()) {
        InitializationFailure("HomeRunBat.esp is not loaded. Physical hit delivery is disabled.");
        return;
    }
    auto* weapon = LookupFormByID(mod->GetFormID(kWeaponLocalID));
    auto* quest = LookupFormByID(mod->GetFormID(kQuestLocalID));
    if (!weapon || weapon->formType != TESObjectWEAP::kTypeID ||
        !quest || quest->formType != TESQuest::kTypeID) {
        InitializationFailure("HomeRunBat.esp must contain weapon 000800 and quest 000806. Install matching ESP, DLL and scripts.");
        return;
    }
    auto* vm = *g_skyrimVM;
    auto* dispatcher = vm ? FindHitDispatcher(vm) : nullptr;
    if (!vm || !vm->GetClassRegistry() || !dispatcher) {
        InitializationFailure("The Skyrim 1.7.99 TESHitEvent dispatcher could not be uniquely identified. See HomeRunBat.log beside the DLL.");
        return;
    }

    // Deliberately initialized after DataLoaded, never during DLL static init.
    // BSFixedString has no destructor; this single interned name lives until exit.
    static BSFixedString eventName("OnBatHit");
    g_hitSink.Initialize(weapon, static_cast<TESQuest*>(quest), &eventName);
    dispatcher->AddEventSink(&g_hitSink);
    g_registered = true;
    Log("Registered physical hit sink: weapon=%08X quest=%08X; OnBatHit(Actor target, Actor attacker)",
        weapon->formID, quest->formID);
}
}

extern "C"
{
__declspec(dllexport) SKSEPluginVersionData SKSEPlugin_Version = {
    SKSEPluginVersionData::kVersion,
    kPluginVersion,
    "HomeRunBat",
    "jj-link",
    "",
    0,
    0,
    { kRuntime, 0 },
    MAKE_EXE_VERSION(2, 3, 0)
};

__declspec(dllexport) bool SKSEPlugin_Load(const SKSEInterface* skse)
{
    OpenLog();
    if (!skse || skse->isEditor || skse->runtimeVersion != kRuntime ||
        skse->skseVersion < MAKE_EXE_VERSION(2, 3, 0)) {
        Log("Rejected runtime: requires Skyrim 1.7.99.0 (0x%08X) and SKSE 2.3.0 or newer; received runtime=0x%08X SKSE=0x%08X",
            kRuntime, skse ? skse->runtimeVersion : 0, skse ? skse->skseVersion : 0);
        return false;
    }
    auto* messaging = static_cast<SKSEMessagingInterface*>(skse->QueryInterface(kInterface_Messaging));
    if (!messaging || messaging->interfaceVersion < SKSEMessagingInterface::kInterfaceVersion ||
        !messaging->RegisterListener(skse->GetPluginHandle(), "SKSE", OnSKSEMessage)) {
        Log("SKSE messaging interface registration failed");
        return false;
    }
    Log("Loaded for Skyrim 1.7.99.0; waiting for DataLoaded (contact diagnostics=%d)", HRB_DIAGNOSTICS);
    return true;
}
}
