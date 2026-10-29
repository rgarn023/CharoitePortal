# Charoite Wine / Proton integration audit
Status: 2026-10-29 · Source/audit specification, not runtime readiness

## Verified lineage

Our derivative is **not Wine authored from scratch**. It is built from pinned
[The412Banner/proton-wine](https://github.com/The412Banner/proton-wine)
commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`.
`prepare-source.sh` applies, in order:

1. The upstream Android/Bionic/ARM64EC/FEX prerequisite patch list parsed
   from the pinned ARM64EC build script (70 patches in the verified source run).
2. The pinned upstream `build-scripts/apply-ge-patches.sh`
   `android/ge-patches/game-fixes` tier (10 in the verified source run).
   Its own script explicitly excludes the separate `ge-video-rework` port.
3. Eight active Charoite-maintained/attributed Wine patches in
   `patches/SERIES` (0100, 0002, 0200, 0300, 0400, 0500, 0600, 0700).

Keep original authorship/attribution. Never infer all features from patch count.
Source-build evidence is separate from actual on-phone behavior. On 2026-10-29
the Samsung S26 Ultra reported `APK-installed ELF hash: PASS`,
`APK-installed native ntdll hash: PASS`, exit code 0 and `wine-10.0`
for the native Charoite Wine `--version` probe. That proves the native loader
and its ntdll fallback worked on Android. It does **not** create a prefix or
demonstrate Windows PE execution, a running wineserver session or gaming support.

## What belongs inside Charoite Wine

- Keep platform fixes around Android/Bionic, ARM64EC ABI, ntdll, wineserver,
  Wine RPC/COM and PE/Unix module loading as reviewed source patches.
- Review additional upstream Proton Wine fixes against the **exact pinned
  source** and existing patches, one at a time. Import only fixes relevant to
  Charoite's Android/ARM64EC target; preserve origin, license and regression tests.
- Gate optional Wine process synchronization (esync, fsync, ntsync) behind
  detection of supported Android kernel facilities, not assumptions.
- Review media pipeline and controller functionality only after Wine PE/Unix,
  wineserver, basic window/display and input have actual device tests.

## What must be separate, versioned components

| Layer | Charoite owner / purpose | Current state |
|---|---|---|
| Wine native & Windows API | Modified Charoite Wine 10, PE/Unix modules, wineserver, prefix/wineboot | loader --version PASS; prefix not run |
| CPU architecture bridge | FEX x86/x64 and ARM64EC interoperability | not integrated |
| D3D9/10/11 | DXVK → Vulkan | not integrated with new runner |
| D3D12 | VKD3D-Proton → Vulkan | not integrated with new runner |
| Vulkan stack | Mesa/Turnip and supported Android ICD/driver integration | not integrated with new runner |
| Audio/media | Codec and Windows multimedia API integration | untested in new runner |
| Steam-specific compatibility | Per-title overrides, Steam integration as supported by vendor/client | not integrated |
| UX / environments | Charoite Portal/Core prefix isolation, assets, input and display | new engine stays disabled |

The Proton Linux/Steam Runtime container cannot be copied verbatim into
Android and expected to work. Use the *appropriate compatibility behavior*,
rather than blindly porting Linux-specific launch scripts or runtimes.
Neither Steam nor Battle.net, Diablo, Windows 11 apps or anti-cheat support is
demonstrated by the current native version probe. Never bypass vendor controls.

## Ordered engineering checks

1. **Native loader done**: on-device `wine --version` yields `wine-10.0`.
2. **Native server version probe (v0.7 code)**: stage the exact same source
   bundle's verified AArch64 `wineserver` as APK-managed native library code.
   Hash-check it in a user-triggered `--version`-only command with no prefix,
   HOME, inherited Wine variables or existing game data. The fact that a
   binary prints its version does not mean a server session started.
3. Complete a sealed Next-only versioned **native/PE/NLS/Windows dependency**
   layout; audit all imported DLLs and `DT_NEEDED` entries and ABI versions.
   The current 22-component, 76-NLS archive has 24 sampled Windows PE
   import names not bundled; it is not complete.
4. Add explicit opt-in `wineboot` smoke test with a **new, strictly isolated
   Next test prefix**, dedicated verified wineserver path and local logs.
   Never touch existing prefixes, installers, games or saves. No automatic
   wineboot on install.
5. Run a simple known-safe ARM64 Windows PE application and verify basic
   display, Unicode/Japanese CP932 text and input; record exact device errors.
6. Only after reliable basic runtime behavior, add FEX, DXVK/VKD3D-Proton,
   Turnip graphics, audio, Steam and Battle.net incrementally, maintaining
   separate driver/translation/compatibility ownership.

## Release rule

Packaging, CI cross-compilation and source-level tests do not prove Android
device success. Publish the exact CI run, source commit, signing provenance and
APK artifact only after a successful job; otherwise keep status "unverified".
Do not make `proton-arm64ec-fex` selectable until on-device readiness criteria
are met. The stable `com.charoite` package and data are out of scope.
