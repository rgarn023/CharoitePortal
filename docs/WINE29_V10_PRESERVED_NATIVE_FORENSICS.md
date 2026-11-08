# Charoite Next — preserved V10 native loader failure, read-only audit

Date: November 7, 2026. Status: **v0.94 source candidate**, not verified signed APK until Actions completes.

## V10 owner one-shot evidence (already performed; DO NOT repeat)

- The V10 Wine29 sealed 34 DLL / 111 PE-NLS / native ELF cohort and source-matched ARM64 `services.exe`, `userenv.dll`, `sc.exe` hash/PE checks passed.
- The isolated foreground wineserver socket and lock were observed. Direct Wineboot `-i` exited 0 within 45 seconds, with Wine-created `windows`, `system32`, `users` and `xuser/AppData`.
- The private `drive_c` directory and `dosdevices/c:` symlink were **preseeded** and are not Wine-created proof.
- Registry files were absent at the **pre-server-shutdown** sample, but present and nonempty **after shutdown**: `system.reg` 1,981 B, `user.reg` 1,858 B, `userdef.reg` 123 B. Contents/integrity/SCM readiness not verified.
- A distinct native loader `--version` test completed with exit **127**, produced **0 bytes** of retained output, and failed the version recognition gate. The V10 `sc.exe` entry check was **not executed**. No SCM query or service response is proven.
- **Exit 127 is unclassified**. Neither shell “command not found,” native linker failure, a missing DLL, nor SCM unavailability is established from the short report alone.

## v0.94 read-only audit design

Previous V10 execution UI is archived behind `showArchivedWine29V10Execution = false`. The **sole current Wine29 System action** is:

**Inspect Wine29 v10 native loader failure (read-only)**

It reads only the following existing files, never recreating or altering them:

1. `v10-wine-direct-init.log` — bounded PE trace; PID/module map/exit event categories, no raw command lines or paths
2. `v10-foreground-wineserver.log` — bounded server/process/registry event categories, no raw process data
3. `v10-native-version.log` — metadata byte size and, only if nonempty and within 256 KiB, bounded native-loader error *categories*; V10 reported zero bytes
4. `v10-sc-entry.log` — existence/size, and only if present and within 8 MiB, bounded PE-entry or usage markers; V10 reported this was never attempted

The only additional checks are explicitly named **V10** scratch metadata paths: `prefix/drive_c`, selected named Windows folders, four source-staged PE executable/module entries and registry file lengths. The `prefix/dosdevices/c:` link is inspected with `lstat/readlink` and **never followed**; registry **contents are never opened**. Reports are bounded to **9,000 characters** and end in `END OF SHORT V10 READ-ONLY REPORT`.

**No ProcessBuilder, Runtime.exec, native/Wine/PE execution, scratch creation, writes, cleanup, deletion, retry, or other-generation file access** is performed by the audit. The preserved V10 one-shot and **all V1–V9/Wine28**, stable `com.charoite`, games/saves/user prefixes and rootfs remain untouched.

## Interpretive gates

The preserved PE trace can establish whether Wineboot and internal service helpers reached module mapping or exit stages. The zero-byte native-version file cannot reveal why the separate Android native subprocess exited 127. A new V11 execution test, including any modified native environment or `sc.exe` launch, must be independently designed, built and expressly authorized in a **new untouched scratch**, not run by this read-only audit.

Building, installing or opening v0.94 does not authorize Wine execution. If CI verifies the signed APK, **install in place over `com.charoitx`**; do not uninstall or clear storage. Copy only the short postmortem through the new System action. No complete Wine runtime, SCM, Steam/Battle.net or Windows game functionality is claimed.

Source: [audit code](../next-generation/CharoiteWine29V10ReadOnlyForensics.java), [System UI/archive](../next-generation/prepare_next.py), [contract](../next-generation/tests/test_wine29_v10_readonly_contract.py).
