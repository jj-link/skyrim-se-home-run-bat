cmake_minimum_required(VERSION 3.25)

set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded")
project(HomeRunBat VERSION 1.0.0 LANGUAGES CXX)

if(NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
    message(FATAL_ERROR "HomeRunBat requires MSVC targeting x64.")
endif()
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "Use tools/build-native.ps1; native build products belong under .local.")
endif()

set(SKSE_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../.local/native/skse64" CACHE PATH "Official SKSE source checkout")
set(XSE_COMMON_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../.local/native/common" CACHE PATH "Official ianpatt/common checkout")
set(HRB_DATA_OUTPUT "${CMAKE_CURRENT_SOURCE_DIR}/../Data" CACHE PATH "Destination mod Data directory")
option(HRB_DIAGNOSTICS "Log accepted physical contacts and resolved dispatcher offset (development only)" OFF)

find_package(Git REQUIRED)
function(require_revision source expected)
    execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${source}" rev-parse HEAD
        OUTPUT_VARIABLE actual OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_VARIABLE error RESULT_VARIABLE result)
    if(NOT result EQUAL 0 OR NOT actual STREQUAL expected)
        message(FATAL_ERROR "Expected ${source} at ${expected}; got '${actual}'. ${error}")
    endif()
endfunction()
require_revision("${SKSE_SOURCE_DIR}" "6498c52871859c92ab584ab97112f798b409698d")
require_revision("${XSE_COMMON_SOURCE_DIR}" "64e233c096735551f6ac9a773726a8a3960e46cd")

# Build only the official common library and the engine wrappers actually used
# by this plugin, never SKSE's DLL, hooks, loader, Papyrus extensions or Xbyak.
add_subdirectory("${XSE_COMMON_SOURCE_DIR}" "xse-common" EXCLUDE_FROM_ALL)
add_library(hrb_sdk STATIC
    "${SKSE_SOURCE_DIR}/skse64/GameAPI.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameBSExtraData.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameData.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameEvents.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameExtraData.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameFormComponents.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameForms.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameReferences.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameRTTI.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameTypes.cpp"
    "${SKSE_SOURCE_DIR}/skse64/GameUtilities.cpp"
    "${SKSE_SOURCE_DIR}/skse64/HashUtil.cpp"
    "${SKSE_SOURCE_DIR}/skse64/NiObjects.cpp"
    "${SKSE_SOURCE_DIR}/skse64/PapyrusArgs.cpp"
    "${SKSE_SOURCE_DIR}/skse64/PapyrusInterfaces.cpp"
    "${SKSE_SOURCE_DIR}/skse64/PapyrusVM.cpp"
    "${SKSE_SOURCE_DIR}/skse64_common/Relocation.cpp"
)
target_include_directories(hrb_sdk PUBLIC "${SKSE_SOURCE_DIR}")
target_link_libraries(hrb_sdk PUBLIC xse::common)
target_compile_features(hrb_sdk PUBLIC cxx_std_17)
target_compile_definitions(hrb_sdk PUBLIC RUNTIME RUNTIME_VERSION=0x01070630)
# SDK translation units also contain unused helpers. Function/data sections let
# the linker discard these rather than pulling unrelated engine implementations.
target_compile_options(hrb_sdk PRIVATE /Gy /Gw /W3 /EHsc)

add_library(HomeRunBat SHARED HomeRunBat.cpp DragonLaunch.cpp)
target_link_libraries(HomeRunBat PRIVATE hrb_sdk)
target_compile_options(HomeRunBat PRIVATE /Gy /Gw /W4 /EHsc)
target_compile_definitions(HomeRunBat PRIVATE HRB_DIAGNOSTICS=$<BOOL:${HRB_DIAGNOSTICS}>)
target_link_options(HomeRunBat PRIVATE /OPT:REF /OPT:ICF /INCREMENTAL:NO)
set_target_properties(HomeRunBat PROPERTIES
    OUTPUT_NAME HomeRunBat
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/$<CONFIG>"
)

# install emits only our DLL; upstream SKSE/common targets are excluded above.
install(TARGETS HomeRunBat RUNTIME DESTINATION "${HRB_DATA_OUTPUT}/SKSE/Plugins")
