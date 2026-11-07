# Wine29 v6 — isolated native child loader APK integration

**Date:** November 7, 2026. **Package:** experimental Next `com.charoitx`.
**Release target:** `11.2-next.0.81` / versionCode 112. **No phone execution was performed by CI.**
**Stable Charoite Portal `com.charoite`: unchanged.**

## Why v6

Owner's original v5 one-shot phone report confirmed the sealed 34 DLL + Wineboot + 76 NLS cohort and native hashes PASS; a private C: relative link worked, Wine created Windows/user directories and registry files, and directly launching ARM64 Wineboot.exe `-i` exited 0. However Wine's internal `NtCreateUserProcess(C:\\windows\\system32\\wineboot.exe --init)` failed with a status `0x1`. That is a *startup status*, not a demonstrated Wineboot process exit code. No runnable Windows environment has been proven.

Source analysis indicates that Wine's native `init_paths()` computes its own `WINELOADER` based on native NTDLL's compiled bindir; child process creation calls `exec_wineloader()` and `execv()`. The actual on-device exec errno/path has NOT yet been observed. V6 tests the alternative of using a canonical, APK-owned native child-loader executable.

## Native source generation, provenance, and verified CI

- Pinned Wine source: `The412Banner/proton-wine` commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`; original `dlls/ntdll/unix/loader.c` Git blob `2f978520af6c216586baa081caa4c1db38207fd4`.
- The exact same upstream Android/ARM64EC prerequisite series and Charoite patches is applied to a new throwaway source tree. Only this new tree is patched further for v6.
- `analysis/wine29_bootstrap/patch_v6_child_loader.py`: Android-only canonical `CHAROITE_WINE29_V6_LOADER_EXEC` enforced before Wine exports `WINELOADER`. Rejects absent, symlink, unexpected, noncanonical or nonexecutably mapped paths; does NOT fall back to built-in bindir. Child `execv()` failure produces a fixed `CHAROITE_WINE29_V6_CHILD_EXECV_FAILURE errno=<integer>` diagnostic (not a full device path).
- `loader/main.c` is source-patched to require `CHAROITE_WINE29_V6_NATIVE_DIR` and load ONLY the matching new `libcharoite_wine29_v6_ntdll.so`, fail-closed rather than using a legacy Wine29/Wine28 fallback.
- New-source PE and NLS selectors are independent: `CHAROITE_WINE29_V6_PE_DIR`, `CHAROITE_WINE29_V6_DATA_DIR`, replacing the older Wine28/Wine26 names inside new native NTDLL and wineserver. Windows PE/NLS staged on phone are sourced separately from the existing immutable 111-file sealed generation.
- New native Android 35 ARM64 ELF cohort, 16KiB PT_LOAD compatibility, explicit embedded selector strings and SHA-256 complete: **[Actions run 42387905132](https://github.com/rgarn023/CharoitePortal/actions/runs/42387905132) SUCCESS**, code commit `c069cd0f857823c8177d1237ee42d43d691f72c6`; **[native source artifact 13580905064](https://github.com/rgarn023/CharoitePortal/actions/runs/42387905132/artifacts/13580905064)**, ZIP digest `sha256:2111491b9040c85c8c08c3a55f81f682f95057bb9b6e5a9ad848c2d8b6299d19`. **This source artifact is NOT an Android APK**.

## APK integration (pending signed verification)

`next-generation/stage_wine29_v6_native.py` pins the completed source Actions run, head commit, artifact ID and artifact digest; confirms exact nine-file candidate payload, source-patch evidence and SHA list, ELF AArch64 and ET_DYN headers, 16KiB PT_LOAD, and all native selector literals before copying the 3 new ELF files into `jniLibs/arm64-v8a`. It writes an APK-owned `assets/charoite-next/wine29-v6/wine29-v6-native-index.json` with the 3 sizes and SHA-256 values. **All existing Wine29 v0.80 native library filenames and sealed PE/NLS assets remain unchanged.**

`.github/workflows/charoite-next.yml` checks GitHub artifact's pinned commit/digest and expiry, downloads pinned artifact, stages the separate ELF and index, and verifies the same three libraries and hashes in the resulting APK. It validates Gradle versionCode 112 / versionName 11.2-next.0.81, signs with the persisted experimental Next certificate, checks licenses and publishes GitHub Actions artifacts. If the run fails, the artifact must not be described as installable.

The app's new `next-generation/CharoiteWine29V6ChildLoaderProbe.java` verifies all sealed PE/NLS assets and the v6 source index and three installed native ELF hashes BEFORE creating fresh scratch `charoite-next-wine29-child-loader-v6`. It then makes only the private C: mapping, starts v6 wineserver followed by the matched ARM64 `aarch64-windows/wineboot.exe -i`, and records bounded logs including the numeric child execv errno marker, internal auto-init status and independently Wine-created folders and registries. The test is one-shot: it refuses already present scratch, never retries, preserves evidence and kills only its own processes. **No prior Wine29 v1-v5, Wine28, stable Portal, user's game files, saves or Wine prefix is accessed or cleared.**

The System UI archives v5 execution and adds only `Wine29 v6 native child-loader smoke (one-shot)`, with a separate informed consent prompt before executing any Wine code. This is a diagnostic, **not** a new default game engine or proof that Windows programs now run.

## Exact remaining gate

1. Review [signed APK workflow 42388622713](https://github.com/rgarn023/CharoitePortal/actions/runs/42388622713) or its latest superseding run and confirm all 138 stable, Next regression, v6 consent/source, Gradle, AAPT, signature and artifact steps passed. If a failure occurs, update only exact offending source/tests and rebuild; report the new precise run/commit and artifact ID, not a guessed link.
2. After a fully verified signed APK is available, install **in place** over existing `com.charoitx`, never uninstall/clear data. The v6 diagnostic still requires an explicit *on-device* confirmation; no user authorization to rerun any previous diagnostic is implied.
3. For new phone report, distinguish v6 loader/NTDLL hash PASS, child `execv` errno (if any), internal `run_wineboot` startup marker, PE/kernel32 errors, actual Wine-created folders/registry, and parent process exit. A parent `-i` exit 0 or directory presence alone is not a successful child process or runnable Windows environment.
