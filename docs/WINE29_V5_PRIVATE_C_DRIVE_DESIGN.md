# Wine29 v5 — fresh private C: mapping bootstrap

**Status:** Source implementation staged pending signed GitHub Actions verification. No v5 on-device execution has occurred.

## Owner's v4 evidence

In a previously unused `charoite-next-wine29-direct-init-v4` scratch, Wine29 34 hybrid DLL/111 PE+NLS source checks and three native ELF hashes all passed. Foreground wineserver socket/lock started. Explicit source-verified `aarch64-windows/wineboot.exe -i` exited 0, and `system.reg`, `user.reg`, and `userdef.reg` appeared. **Nevertheless `drive_c` remained absent**, while `dosdevices` existed. Automatic `C:\windows\system32\wineboot.exe --init` child startup still returned `NtCreateUserProcess` status 0x1 (not proven child Wineboot exit), with fallback to builtin AA64. The main PE DLLs and kernel32 load. Traces repeatedly failed creating `C:\users\xuser\AppData\Local` with `c000003a` (path not found); `C:\windows` also could not be set as working directory. The directly invoked `-i` exit code is **not equivalent** to a completed Windows prefix.

## Source-reasoned next hypothesis

In upstream Wine 10 `dlls/ntdll/unix/server.c` `setup_config_dir()`, `drive_c` and the relative `dosdevices/c:` symlink are created in the branch reached when the initial `mkdir("dosdevices")` succeeds. The code skips those creations if `dosdevices` already exists. An incomplete earlier creation sequence or failed initial filesystem operation could therefore leave Wine's registry populated but C: unmapped. It is a plausible explanation for **v4's exact observed state**, not proven root cause. [Upstream source](https://sources.debian.org/src/wine/10.0~repack-12/dlls/ntdll/unix/server.c). A normal Wine prefix has `dosdevices/c: -> ../drive_c`; see [CodeWeavers' prefix overview](https://www.codeweavers.com/blog/aeikum/2019/1/10/working-on-wine-part-3-using-wine-as-a-developer).

## Minimal v5 experiment

- Experimental Android package `com.charoitx` only. **Explicit in-app consent** at System → **Wine29 v5 isolated C: mapping test (one-shot)**. Absolutely NO auto execution and NO retries.
- New child of `getNoBackupFilesDir()`: **`charoite-next-wine29-c-drive-v5`**. Refuse if present; do not enter any v1–v4 private scratch or any user prefix/save/game, stable Portal package, rootfs, Wine28 slot. Scratch is retained after success/failure.
- Source-hash-verify exactly same sealed 34 DLL + 1 matched ARM64 Wineboot + 76 NLS cohort, 3 native Wine29 APK ELFs, all original PE import preflights and selectors. Do not modify the underlying Wine source or staged files.
- Before starting native processes, create **only** `prefix/drive_c/`, `prefix/dosdevices/`, and a literal **relative** Unix symlink `prefix/dosdevices/c: -> ../drive_c`. Check `Os.lstat`, `Os.readlink`, canonical path equality and absence of pre-existing drives. No other drive mapping, no `z:` to root and no `windows` or `users` directories pre-created; their presence later will measure actual Wine action.
- Start the same bounded source-matched foreground wineserver, then explicit matched-directory `wineboot.exe -i`. No global `WINEBOOTSTRAPMODE` override. Time budget 45s; cap PE log 2MiB and server trace 256KiB; redact environment/credentials. Stop only the newly spawned server and PE process, retain v5 scratch, no file deletion.
- **Do not count preseeded drive_c as success.** Record separately: retained symlink, **Wine-created** `drive_c/windows`, `drive_c/windows/system32`, `drive_c/users`, `drive_c/users/xuser/AppData`, `Program Files`; source-generated `system.reg`, `user.reg`, `userdef.reg`; direct PE exit status; original internal `run_wineboot` failure marker. Report only **partial** result even if Windows-created folders appear. Gaming environment requires a later ordinary Windows program smoke test plus graphics/input/audio.
- New APK target version **`11.2-next.0.80`**, versionCode **111**, existing Next signing identity to allow in-place update without uninstall/clear data. Legacy one-shot v4 execution button archived, v1/v3 forensic read-only buttons remain.

**Branch promotion gate:** no automatic engine selection, game installation, anti-cheat or Battle.net/Steam launch based on C: mapping alone. If v5 still reports internal auto-init child-start status 1, investigate native `exec_wineloader` resolution separately in source and bounded new diagnostics; do not access or rerun v5.
