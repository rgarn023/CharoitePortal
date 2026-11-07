# Wine29 v3: successful PE help, failed automatic Wineboot child creation

**Evidence:** Owner's Charoite Next v0.77, Galaxy S26 Ultra readout. v3 one-shot diagnostic ran in private `charoite-next-wine29-pe-dir-v3` with complete original logs retained in the experimental app.

**Build verification (November 7, 2026):** Charoite Next v0.78 `com.charoitx`, versionCode 109, versionName `11.2-next.0.78` signed GitHub Actions [42341443574](https://github.com/rgarn023/CharoitePortal/actions/runs/42341443574) **SUCCESS** from APK commit `932fbe4b22093d157e60a7f9bae8994c3576772b`. 138 stable + 166 Next tests PASS, read-only no-exec/no-write contract PASS, Gradle build, APK manifest and existing Next signing certificate verified. [Direct APK artifact 13561691880](https://github.com/rgarn023/CharoitePortal/actions/runs/42341443574/artifacts/13561691880), 460,791,177-byte ZIP, expires February 5, 2027. Only an **in-place update** is permitted; never uninstall or clear storage. This source-and-APK check does not establish successful Wine prefix initialization. No new Wine process was executed by development.\n\n## What v3 PROVED

- Verified native Wine29 wineserver socket/lock and 34 PE DLL + ARM64 Wineboot executable + 76 NLS sealed hash checks PASS.
- Wineboot.exe `--help` launched from `runtime/lib/wine/aarch64-windows/wineboot.exe`, beside the hash-verified kernel32.dll. This resolved the explicit Wineboot PE-help path mismatch seen in v2.
- PE NTDLL, kernel32, kernelbase, advapi32, msvcrt, ws2_32 and other DLL attach/detach steps are visible; `Usage: wineboot` appears and the explicit subprocess exit code is **0**. These demonstrate executable PE startup for this one built-in program, not general Windows app compatibility.
- The `ws2_32.so` native .so lookup warning did **not** prevent this `--help` success. Its effect on real initialization is unknown.

## What v3 DID NOT PROVE

- The startup trace still reports `err:environ:run_wineboot failed to start wineboot 1` after attempting to spawn `C:\windows\system32\wineboot.exe --init`; `drive_c`/complete prefix initialization has not been proven.
- A separate message `Cannot set the dir to C:\windows (2)` is consistent with an incomplete Windows C: layout. By itself it does not prove the cause of automatic child-creation failure.
- No regular Win32 application, actual `wineboot --init` completion, stable Windows registry, Steam/Battle.net or FEX/game graphics path succeeded.

## Critical source-level distinction

Wine 10's `dlls/ntdll/unix/env.c` `run_wineboot()` passes a Windows-process startup request to `NtCreateUserProcess()`. It checks the returned **NTSTATUS** and prints `failed to start wineboot %x` when that status is nonzero, before it resumes the new child thread. Thus literal `failed to start wineboot 1` represents a returned process-creation **status 0x1**; it is NOT a verified Wineboot child's exit code. The exact root cause of this status in our patched native Wine29 remains open. Confirmed reference for upstream Wine10 source: https://sources.debian.org/src/wine/10.0~repack-6/dlls/ntdll/unix/env.c (run_wineboot / NtCreateUserProcess source block). The unmodified upstream source is corroborating evidence, not a runtime measurement of Charoite's patched build.

## Next action: v0.78 read-only on-device forensics

- **No new Wine, Wineboot, wineserver or prefix writes**, and NO automatic retry of any past scratch.
- New class: `next-generation/CharoiteWine29V3AutoInitForensics.java` inspects only the existing v3 private scratch and bounded, preserved `v3-wine-pe-help.log` and `v3-foreground-wineserver.log`, plus five source-hash-verified PE images and named file types in the **v3** prefix (without reading prefix contents).
- Extracts bounded, redacted context around `NtCreateUserProcess`, `run_wineboot`, `Cannot set the dir`, optional native .so warnings, actual kernel32 mapping, and Wineboot help. Source file and directory never rewritten.
- UI: System → **Inspect preserved Wine29 v3 auto-init failure (read-only)**. V3 one-shot execution test archived/hidden after use. Existing v1 read-only option remains available.
- Security contract prohibits spawning processes, creating/writing/deleting files, reading old v1/v2 scratch, stable Portal `com.charoite` storage or user games, and clearing storage.
- New Next version target `11.2-next.0.78`, versionCode `109`, `com.charoitx`, same persisted signing identity for safe in-place upgrade.

This is a diagnostic release; the next source change affecting Wine child process creation must be justified by observed evidence, made in a fresh unique scratch with **separate explicit on-device consent**, and tested without globally forcing `WINEBOOTSTRAPMODE` or touching installed games/prefixes.
