# Wine29 v4 — isolated direct `wineboot.exe -i` test

State: **VERIFIED SIGNED Android Next v0.79 diagnostic APK**; source commit `d3f5276162d98d07d89f76a8900b8c31bec080be` built by [GitHub Actions run 42343528123](https://github.com/rgarn023/CharoitePortal/actions/runs/42343528123) SUCCESS. **138 stable + 169 Next tests passed**, v4 one-shot safety gate PASS, Gradle/AAPT `com.charoitx` code 110/name `11.2-next.0.79` and unchanged signing cert verified. **[APK artifact 13562782885](https://github.com/rgarn023/CharoitePortal/actions/runs/42343528123/artifacts/13562782885)** unexpired ZIP 460,816,284 bytes, expires 2027-02-05. Nothing from v4 runs on install, start, or app switch. **No v4 phone execution or verified initialized prefix yet.** Requires separate user-authorized one-shot confirmation; install in place only; never clear app data.

## v3 evidence (Galaxy S26 Ultra)

The preserved source-verified PE stage, native wineserver socket and PE DLL hashes all passed. Launching Wineboot.exe `--help` from the matched `aarch64-windows` PE directory succeeded, loaded kernel32.dll/kernelbase.dll, and exited 0. The v3 private prefix contains registry files but **no `drive_c`**, so it is not initialized. Its loader reported `run_wineboot failed to start wineboot 1` when attempting an automatic `C:\windows\system32\wineboot.exe --init` child process.

## Source-level scope and uncertainty

Wine 10 `dlls/ntdll/unix/env.c` logs the **nonzero return value from `NtCreateUserProcess()`**; it is not a verified Wineboot child exit. In `dlls/ntdll/unix/process.c`, the process-creation return can reflect an early child failure: `spawn_process()` forks a child which calls `exec_wineloader()` to relaunch Wine's native loader, then `get_new_process_info` supplies the new child's `exit_code` when startup did not succeed. Therefore **status `0x1` is compatible with a child native-loader exit 1**, but the current v3 logs cannot prove the exact failure, the correct loader path, or which substage failed. See [Wine 10 process.c](https://sources.debian.org/src/wine/10.0~repack-6/dlls/ntdll/unix/process.c) and [Wine 10 env.c](https://sources.debian.org/src/wine/10.0~repack-6/dlls/ntdll/unix/env.c).

The Wine trace `get_pe_file_info assuming aa64 builtin` after absent `C:\windows\system32\wineboot.exe` is normal **bootstrap fallback behavior**, not by itself proof of a missing sealed Wineboot executable; the original matched `aarch64-windows/wineboot.exe` was source-hash-verified and later loaded for `--help`.

## Narrow next v4 experiment (no automatic execution)

- New, never previously used private directory **`getNoBackupFilesDir()/charoite-next-wine29-direct-init-v4`**; refuse if it already exists, never delete/retry; the old v1/v2/v3 scratch, stable Portal `com.charoite`, user games/saves/rootfs/prefixes are not accessed.
- Reuse exact source verified Wine29 cohort: 34 hybrid PE DLLs, ARM64 Wineboot.exe, 76 NLS files; preflight checks and APK native three-ELF identity run before scratch. Source-hash-verified matched alias `aarch64-windows/wineboot.exe` beside kernel32.dll.
- Only in the new private scratch, start matched native foreground wineserver and invoke the **same verified Wineboot EXE explicitly with `-i`** rather than `--help`. Wine may also attempt an **internal** auto `--init` before that explicit command. This v4 does not change the native child loader cohort or force `WINEBOOTSTRAPMODE`; a positive result cannot be guaranteed.
- The sole allowable process write scope is the **new v4 scratch** (new prefix and logs), with a 45s process deadline, 2MiB log cap, bounded sanitizer and private launcher environment. Stop only the v4 processes; never touch earlier runs.
- Observe `drive_c`, `system.reg`, `user.reg`, `userdef.reg` **presence only** and report separately from PE exit status, without claiming Windows games are runnable.
- User must explicitly approve **System → Wine29 v4 direct prefix initialization (one-shot)**. The prior execution buttons v1–v3 are archived/hidden; v1 and v3 read-only forensics remain.
- Target experimental `com.charoitx` v0.79, versionCode 110, `11.2-next.0.79`. Do not uninstall or clear data; in-place install only after signed artifact verification.

Interpretation: success means the specific fresh scratch developed the necessary drive_c and registries under one bounded v4 direct -i attempt. A failure is diagnostic, not proof Wineboot can never initialize; investigate preserved v4 process/server evidence in new read-only follow-up. No Steam/Battle.net, anti-cheat, Windows desktop, FEX or graphics claims.
