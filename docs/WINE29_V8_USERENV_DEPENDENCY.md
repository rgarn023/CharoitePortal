# Wine29 v7 services.exe userenv.dll failure and isolated v8 source-only candidate

**Date:** November 7, 2026. **Status:** V7 phone read-only diagnostic received. Source-candidate CI proposed; no v8 device execution.

## Evidence and limits

The owner's preserved v7 PID 0x0034 log audit identified an explicit `userenv.dll` DLL_NOT_FOUND and module error (PE lines 1440–1441), followed by a module error for `services.exe` (line 1526), and PID 0x0034 exiting `0xC0000135`. Wineboot processes 0x0024/0x002c both exited 0. `services.exe` was mapped in 0x0034, with NTDLL/kernel32/API sets present. The failed load is correlated with userenv.dll, but whether the DLL itself is absent versus one of its dependencies or path resolution is not yet proven without cohort verification. Wine service initialization, complete prefix and applications remain unverified.

## Safe next action in CI

The new `.github/workflows/wine29-v8-userenv-candidate.yml` runs ONLY in GitHub Actions on a fresh ephemeral runner, never on Android. It retrieves existing PINNED sealed 34 DLL/76 NLS + Wineboot source-data artifact and the original independently source-built v7 `services.exe` candidate, verifies immutable integrity and Windows PE imports, and **fails closed** if `userenv.dll` is already in the sealed 34-DLL provider set. Only when absent, it checks out the **same pinned Wine10 source commit** and native toolchain previously used for v7, cross-compiles `dlls/userenv/aarch64-windows/userenv.dll`, checks ARM64 machine and reports its actual ordinary/delay import graph (including any further gaps). A bounded SHA-256/PE manifest accompanies a **noninstallable source candidate artifact**.

No CI step starts Wine/Wineboot/services.exe/wineserver or any Windows PE, and nothing reads, rewrites, retries, or cleans old phone scratch. No change to stable Portal, user data, games, saves, prefixes, v7 files or already installed Next APK. If the source candidate succeeds and its dependency closure is understood, the future test must be a **separately authorized NEW v8 private scratch**, never reuse v7. Only a subsequent verified signed Next APK and explicit on-device consent can validate runtime behavior.

**Release status:** v0.87 remains the last verified signed APK ([Actions run 42413522887](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887), [artifact 13590806127](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887/artifacts/13590806127)). This source-only workflow does NOT generate a new APK.
