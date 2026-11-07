# Wine29 v5 — child native loader source audit and isolated rebuild gate

**Date:** November 7, 2026. **Status:** PINNED SOURCE AUDIT PASS; **native loader path fix NOT YET BUILT**. The current signed APK remains Next v0.80 (`11.2-next.0.80`, code 111). No new APK, native Wine execution, scratch, or data mutation was part of this audit.

## Confirmed v5 phone result

On the user's Galaxy S26 Ultra, source-verified Wine29 native loader, wineserver and sealed 34 ARM64 PE/76-NLS data all passed their hashes. The newly isolated `charoite-next-wine29-c-drive-v5` mapped `dosdevices/c: -> ../drive_c` and Wine itself created `drive_c/windows`, `drive_c/windows/system32`, `drive_c/users`, `drive_c/users/xuser/AppData`, plus `system.reg`, `user.reg`, `userdef.reg`. Direct `wineboot.exe -i` returned 0, but `Program Files` was absent, and internal automatic `C:\\windows\\system32\\wineboot.exe --init` child creation still logged `run_wineboot failed to start wineboot 1`. The C: symlink is fixed; **a complete Windows initialization is NOT proven**.

## New source-verified finding

GitHub Actions [run 42383786893](https://github.com/rgarn023/CharoitePortal/actions/runs/42383786893) **SUCCESS**; [read-only source-evidence artifact 13578189466](https://github.com/rgarn023/CharoitePortal/actions/runs/42383786893/artifacts/13578189466) created. Six source unit tests PASS, `WINE29_BOOTSTRAP_SOURCE_FLOW=PASS_READ_ONLY`, `WINE29_CHILD_LOADER_SOURCE_AUDIT=PASS_READ_ONLY`. Exact source commit `c74acb09d51b447f5d5ac56c87608d3ec565a767` from `The412Banner/proton-wine`; pinned Git blob SHA-1 `dlls/ntdll/unix/loader.c`: `2f978520af6c216586baa081caa4c1db38207fd4`; `dlls/ntdll/unix/process.c`: `01286e119067567d1a8c7d3c8d5d61407ab43750`. Source code and existing Android v5 Java source were read ONLY; no Wine/PE/wineserver ran.

The exact Wine10 native control flow:
1. `init_paths(argv)` finds the native NTDLL shared-library directory via `dladdr(init_paths)`; **on Android** the `/proc/self/exe` shortcut is intentionally disabled. It derives a native `bin_dir` via `build_relative_path(dll_dir, LIBDIR "/wine", BINDIR)`, creates `wineloader = build_path(bin_dir, basename)`, and exports it as `WINELOADER`.
2. Initial `WINELOADERNOEXEC=1` only skips `__wine_main()`'s **first-time pre-exec**, not Wine's later child process creation.
3. `NtCreateUserProcess()` calls `spawn_process()` and forks a grandchild; that grandchild calls `exec_wineloader()` which invokes `loader_exec()`, attempts `execv()` on the derived `wineloader`, and falls through to `_exit(1)` when it returns without a new process.
4. If Wine's wineserver reports unsuccessful child startup, `NtCreateUserProcess()` can return `reply->exit_code`, explaining how an internal creation status `0x1` can surface before any Windows Wineboot child succeeds.

Charoite Next v0.80 launches a source-verified `libcharoite_wine29_loader.so` from Android's APK `context.getApplicationInfo().nativeLibraryDir`. The native `init_paths()` calculation may derive an entirely different executable under Wine's traditional bindir. **This is the leading cause to investigate, NOT a proved exact `execv` path/errno**. `WINEDLLPATH` points Wine to PE DLLs, not the native child-loader executable. Merely setting `WINELOADER` in Java is insufficient because `init_paths` computes and overwrites it.

## Implementation requirements for the NEXT generation

- Source-build a **new, isolated Wine native loader+NTDLL+wineserver cohort** using the pinned Wine10 source; leave existing Wine29/Wine28 source archives, ELF SHA checks and Next v0.80 APK identity **immutable**.
- In the new cohort's `dlls/ntdll/unix/loader.c` `init_paths`, select a **full canonical path to a SHA-verified APK-owned ARM64 loader** before `WINELOADER` is assigned. Fail closed on missing/inconsistent native selectors, non-executable target, path escaping, mismatched ELF and any legacy fallback. Keep the original first-stage Wine29 native cohort untouched.
- Validate source patch anchor identity on exact pinned commit, check source delta and verify rebuilt **three native ELF hashes** plus 34 source-coherent PE and 76 NLS assets; do not combine new native with unverified old PE/NLS generations. Preserve native signing identity for in-place APK updates.
- Only when built and released: expose a separate explicit **new one-shot child-process smoke** in an entirely fresh uniquely named private prefix. Report native child `execv` outcome/errno separately from Windows `wineboot.exe` result and `drive_c` markers; bound log/process time. Do not touch Wine29 v1-v5 scratch, stable Portal, rootfs, games, saves or installed prefixes. Do NOT run automatically or repeat previous tests.
- The readiness gate requires a successful child process plus subsequent real Windows PE smoke test. Directory creation and zero exit for a parent `wineboot.exe -i` do not themselves prove a runnable Windows compatibility layer.

Auditor: `analysis/wine29_bootstrap/audit_child_loader.py`; unit tests: `analysis/wine29_bootstrap/tests/test_child_loader_audit.py`; workflow: `.github/workflows/wine29-bootstrap-source-audit.yml`. It is intentionally **NO APK** and does NOT attempt a runtime patch. Subsequent work must use a separate source build + matching APK CI before claiming a fix.
