# Wine29 V11 completed report — preserved read-only audit and V12 gate

**Status: V11 executed once on the owner's experimental `com.charoitx` device installation. Never repeat, clean, or delete V11.** This note records only the user-supplied bounded V11 report and source review; it does not pretend to have read the retained raw logs.

## V11 observed sequence
- APK integrity gates: 34 hybrid DLLs, 111 staged PE/NLS, three native ELF and the source-built services.exe, userenv.dll, sc.exe: PASS.
- New private V11 scratch, preseeded C: link/drive_c; no older scratch or user game/prefix access reported.
- Foreground wineserver socket and lock detected, no startup timeout; Wineboot -i completed within 45 seconds, exit 0.
- Wine-created windows, windows/system32, users, users/xuser/AppData directories present; Program Files absent.
- Native version check with WINELOADERNOEXEC=1 returned exit 127 and 0 output bytes. An independent native version call with WINELOADERNOEXEC removed returned exit 0 and 10 bytes, recognized as Wine.
- After the two version checks, the foreground server was no longer alive and the guarded no-argument ARM64 sc.exe invocation was skipped. **No sc PE-entry, SCM query, SCM ready, gaming, or user app proof.**
- Registry files were absent at the earlier pre-shutdown check, then present after server shutdown: system.reg 1,981 B; user.reg 1,858 B; userdef.reg 123 B. Metadata only; do not inspect their contents or infer fully initialized registry.

## Interpretation
The native version contrast isolates a problematic environment difference. The prior exit-127 native `--version` gate is not valid proof of native Wine failure when WINELOADERNOEXEC=1 is forced. The exit mechanism is not conclusively identified.

The foreground server was available after Wineboot and unavailable after the version probes. **This is a sequence, not proof that either version call killed the server.** Review the preserved server lifecycle, Wineboot PE exits and process request/reply event *types* before choosing a new execution probe. The presence of nonempty registry files post-shutdown is meaningful partial bootstrap evidence, not proof of a complete prefix.

## V11 read-only scope (Next v0.96 candidate)
- Exact private directory: `charoite-next-wine29-entry-v11` via `getNoBackupFilesDir()` only.
- Exactly five log names: `v11-wine-direct-init.log`, `v11-foreground-wineserver.log`, `v11-native-version-noexec-set.log`, `v11-native-version-noexec-unset.log`, `v11-sc-entry.log`.
- Logs have per-file byte caps, per-line length and line-count caps. Summarize process IDs, mapped executable *basenames*, PE exit values, module errors, wineserver request/reply/shutdown markers, and native version error categories. Never reproduce raw log lines, paths or registry contents.
- Allowlisted V11 path/registry metadata and `lstat/readlink` of the C: relative symlink without following it. No enumeration of older prefixes or scanning unrelated data.
- **No** ProcessBuilder, Wine, Windows PE, wineserver start, network call, writes, deletion, retry, cleanup or scratch creation.
- Output limited to 9,000 characters and terminates with `END OF SHORT V11 READ-ONLY REPORT`.
- All past execution controls are archived, including V11. Only the V11 read-only action should be shown in System.

## Future V12 decision — NOT YET AUTHORIZED
After receiving the V11 preserved read-only findings, decide whether a *separately consented*, one-shot test in a **brand-new private V12 prefix** should make a bounded no-argument sc.exe PE-entry attempt **before** auxiliary native version-only probes, with explicit foreground wineserver lifecycle checks. Never use the V11 scratch for execution again. No SCM query or other application test unless an earlier independent PE-entry milestone is established. Do not modify stable Portal, Wine28, Wine29 v1–v11, user prefixes, games, saves or rootfs.

## Release requirements
Next v0.96 candidate is `com.charoitx`, versionCode 127, versionName `11.2-next.0.96`. Require Android Gradle, source/regression and preserved-evidence isolation tests, AAPT identity and experimental signing key comparison, and SHA/digest-backed GitHub Actions artifact verification before calling any APK installable. A signed APK may only be installed **in place**, never uninstall or clear app data. CI must not claim phone Wine execution.
