# Wine29 v7 services.exe userenv.dll failure and isolated v8 source-only candidate

**Date:** November 7, 2026. **Status:** V7 phone read-only diagnostic received. Source-candidate CI proposed; no v8 device execution.

## Evidence and limits

The owner's preserved v7 PID 0x0034 log audit identified an explicit `userenv.dll` DLL_NOT_FOUND and module error (PE lines 1440–1441), followed by a module error for `services.exe` (line 1526), and PID 0x0034 exiting `0xC0000135`. Wineboot processes 0x0024/0x002c both exited 0. `services.exe` was mapped in 0x0034, with NTDLL/kernel32/API sets present. The failed load is correlated with userenv.dll, but whether the DLL itself is absent versus one of its dependencies or path resolution is not yet proven without cohort verification. Wine service initialization, complete prefix and applications remain unverified.

## Safe next action in CI

The new `.github/workflows/wine29-v8-userenv-candidate.yml` runs ONLY in GitHub Actions on a fresh ephemeral runner, never on Android. It retrieves existing PINNED sealed 34 DLL/76 NLS + Wineboot source-data artifact and the original independently source-built v7 `services.exe` candidate, verifies immutable integrity and Windows PE imports, and **fails closed** if `userenv.dll` is already in the sealed 34-DLL provider set. Only when absent, it checks out the **same pinned Wine10 source commit** and native toolchain previously used for v7, cross-compiles `dlls/userenv/aarch64-windows/userenv.dll`, checks ARM64 machine and reports its actual ordinary/delay import graph (including any further gaps). A bounded SHA-256/PE manifest accompanies a **noninstallable source candidate artifact**.

No CI step starts Wine/Wineboot/services.exe/wineserver or any Windows PE, and nothing reads, rewrites, retries, or cleans old phone scratch. No change to stable Portal, user data, games, saves, prefixes, v7 files or already installed Next APK. If the source candidate succeeds and its dependency closure is understood, the future test must be a **separately authorized NEW v8 private scratch**, never reuse v7. Only a subsequent verified signed Next APK and explicit on-device consent can validate runtime behavior.

**Release status:** v0.87 remains the last verified signed APK ([Actions run 42413522887](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887), [artifact 13590806127](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887/artifacts/13590806127)). This source-only workflow does NOT generate a new APK.

## Active source-only CI

[GitHub Actions run 42418556136](https://github.com/rgarn023/CharoitePortal/actions/runs/42418556136) completed its pinned inputs download and static provider/import correlation preflight successfully. The true ARM64 source build and import graph are not yet verified, so no artifact SHA or binary integration is claimed. This run is triggered only by adding the new workflow on main, commit `927d864542a0a0f1a9f73c5ba75e195fc6dd6e45`.

## Header-format postmortem

The initial source CI run 42418556136 failed an architecture assertion **after** successfully cross-building `userenv.dll`; the next diagnostic run 42419132691 printed independent raw PE COFF machine `0xAA64` while `llvm-readobj --file-headers` described its ARM64X hybrid container as `IMAGE_FILE_MACHINE_ARM64X (0xA64E)`. These are distinct header views. The previous test incorrectly expected `AA64` in the LLVM container report. Commit `523e66511a3504f0705eee508c0fc935999dca2f` now requires both the original raw AA64 executable-view check and exact independently reported ARM64X/A64E container format, rather than relaxing either validation. Subsequent source CI run [42419386776](https://github.com/rgarn023/CharoitePortal/actions/runs/42419386776) is in progress; do not yet infer a packaged or running DLL. The original v7 scratch remains preserved.

## Verified ARM64X source build and v8 Android integration

[Source candidate run 42419386776](https://github.com/rgarn023/CharoitePortal/actions/runs/42419386776) completed SUCCESS at exact source-build commit `523e66511a3504f0705eee508c0fc935999dca2f` and published non-APK [artifact 13593275372](https://github.com/rgarn023/CharoitePortal/actions/runs/42419386776/artifacts/13593275372), artifact ZIP digest `sha256:524ed4e41b418095c8cb546e31f0754522ce6c3b8501c643feea826c661fc887`. The candidate has a true ARM64 executable-view PE machine AA64 and hybrid LLVM ARM64X container A64E; **zero unbundled ordinary or delayed imports** against source-verified 34 DLL cohort. No Wine/PE or device execution.

New separate `next-generation/stage_wine29_v8_userenv.py` source-pins this exact artifact; new `CharoiteWine29V8UserenvProbe.java` hash-verifies existing source-built services.exe plus v8 userenv.dll before creating a fresh private `charoite-next-wine29-userenv-v8` scratch. Only after an in-app explicit authorization can it copy SHA-matched modules and run Wineboot/services on that NEW scratch. The v7 read-only button is archived, prior one-shot buttons remain hidden, prior v7 logs untouched. Version target: experimental `com.charoitx` v0.88, Android versionCode 119. Current APK CI candidate [Actions 42420335521](https://github.com/rgarn023/CharoitePortal/actions/runs/42420335521) may still be running. **No verified signed v0.88 artifact, phone test, Wine services manager or game result yet; never confuse CI compilation with Android execution.**

## Final signed Next v0.88 release (verified November 7, 2026)

GitHub Actions [42420335521](https://github.com/rgarn023/CharoitePortal/actions/runs/42420335521) **SUCCESS**, exact APK source commit `96f850db094a9e9411d23fe8bae7b3ecd4d542df`. **138 stable and 194 Next regression tests PASS.** APK Gradle build, v8 stage SHA/PE/import closure, v7 services preservation, native v6 and original 111 PE/NLS hashes all PASS. AAPT: experimental `com.charoitx` **versionCode 119 / versionName 11.2-next.0.88**. Signing certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`, matching the prior Next install identity.

[Verified signed Android APK artifact 13592992734](https://github.com/rgarn023/CharoitePortal/actions/runs/42420335521/artifacts/13592992734), ZIP 461,545,549 bytes, `sha256:b3d41cd5339817790bbd4f7f3159b643a974802b25ef1a40df31b042b8872026`, expiry 2027-02-05. Upgrade IN PLACE over existing `com.charoitx`, NEVER uninstall or clear storage.

Only the new **System → Test Wine29 v8 userenv.dll services bootstrap (one-shot)** is shown. It must be separately approved in the app; creates fresh private `charoite-next-wine29-userenv-v8`, verifies userenv/services/module hashes before writes, never reuses old preserved v7 scratch or any games. The one-shot is not run by CI or by installation. If the owner elects to execute, preserve its entire new report and do not retry v8 afterward; first next action is a bounded **read-only v8 postmortem** modeled on v7, without any new process. Full Windows prefix, Service Control Manager and game execution remain UNVERIFIED until actual on-device observations.
