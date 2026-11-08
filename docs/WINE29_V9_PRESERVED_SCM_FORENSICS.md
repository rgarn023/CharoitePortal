# Wine29 v9 preserved SCM-query investigation — strictly read-only

**Scope:** Only the completed one-shot Wine29 v9 private scratch `charoite-next-wine29-scm-v9` in experimental Android package `com.charoitx`. No repeat v9 execution. No previous v1–v8 scratch, Wine28, stable Portal, games, saves, user prefixes, rootfs, or application data reset.

## Owner-supplied v9 phone evidence (7 November 2026)

- Source/payload hashes and ARM64 `sc.exe` dependency closure passed.
- Private foreground wineserver socket and lock observed; `wineboot.exe -i` terminated with **exit code 0**.
- Fresh scratch had a PRESEEDED `drive_c` and relative `dosdevices/c:` symlink. These two alone are not Wine-created evidence. However, `drive_c/windows`, `windows/system32`, `users`, and `users/xuser/AppData` were observed after Wine execution, and were not precreated.
- Registry metadata after server stop: `system.reg` 1,981 bytes; `user.reg` 1,858 bytes; `userdef.reg` 123 bytes. Contents not opened or validated. Report's earlier pre-stop absent flags were time-of-check observations; do not interpret as final absence.
- Source-built ARM64 `sc.exe query` was attempted, completed inside 12 seconds, **exit code 127**. No SCM service status, RPC 1722, or SCM 1060 appeared in the short report. None of those absences proves successful SCM initialization.
- The legacy `RESULT: FAIL — C: preseed ... inspect preserved v6 evidence` text is inherited from earlier probes and is not a trustworthy v9-specific failure diagnosis; classify failure using preserved v9 `sc.exe` evidence.
- **No functional SCM or general-purpose Windows execution is verified.**

## Next safe test: signed Next 0.92

- `CharoiteWine29V9ReadOnlyForensics.java` may read ONLY three fixed files: `v9-wine-direct-init.log`, `v9-foreground-wineserver.log`, `v9-sc-query.log`, plus explicitly listed v9 metadata; registry **contents are not read**.
- Reject symlinks/out-of-root paths; 8 MiB file guard, 100,000-line and 16,384-character line bounds, 9,000-character clipboard report with END marker. No raw process paths, environment, command lines, or untrusted raw log text are copied.
- Report sc.exe PE mapping, module/DLL errors, native loader/exec failures, per-PID exits, and SCM/RPC hints using bounded event types and module basenames only.
- **No ProcessBuilder, Wine, services.exe, sc.exe, wineserver, Wineboot, retries, new scratch, writes, or cleanup.** Existing v9 evidence remains preserved. Previous v9 execution button is archived; sole current Wine29 System button is **Inspect Wine29 v9 SCM failure (read-only)**.
- The experiment only classifies preserved evidence; do not claim SCM success based solely on Wineboot exit 0 or absence of error messages.

## Owner workflow

Install signed `com.charoitx` Next 0.92 **in place** when the GitHub Actions build succeeds; never uninstall/clear data. Run the new read-only v9 audit once, copy the short report including `END OF SHORT V9 REPORT`. Based on classified error, plan a fresh separately authorized v10 experiment only if warranted, without accessing any older scratch. Keep stable `com.charoite` untouched.
