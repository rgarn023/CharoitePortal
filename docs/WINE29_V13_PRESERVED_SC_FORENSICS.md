# Wine29 V13 — preserved sc.exe exit-127 forensic audit

## Owner's completed V13 one-shot (November 8, 2026)
Owner installed the signed experimental Next v0.99 and completed the single expressly authorized V13 execution. Preflight verified 34 hybrid DLLs, 111 source-pinned PE/NLS, 3 native ELF hashes, ARM64 sc.exe, services.exe and ARM64X userenv.dll. In **new private V13 scratch**, wineserver socket and lock were observed, and server remained live before and after the sc.exe attempt. Wineboot `-i` completed with exit 0, Windows-created `windows/system32` and `users/xuser/AppData` directories present. The C: directory/symlink were deliberately preseeded, and `Program Files` was absent.

The **one no-argument ARM64 sc.exe** subprocess had `WINELOADERNOEXEC` **UNSET** only for that launch; Wineboot retained the old setting. sc.exe still returned **exit 127**, generated **zero stdout/stderr** and no usage marker. This *disconfirms the flag-only explanation for the changed result* but does not establish any native-loader error, PE mapping or SCM readiness. Both the V12 and V13 sc.exe attempts produced exit 127, despite the one-variable difference.

Registry timing matters: `system.reg`, `user.reg`, `userdef.reg` were absent in the pre-shutdown snapshot but had metadata-only post-shutdown sizes **1,981 / 1,858 / 123 bytes**. These sizes do not establish complete/valid prefix initialization. No registry contents accessed.

**V13 is consumed. Never rerun or clean V13**, modify its logs, or access older scratch. All prior Wine29 V1–V12/Wine28, stable Portal `com.charoite`, rootfs, user games/saves/prefixes remain out of scope.

## Read-only postmortem scope
Source-only `next-generation/CharoiteWine29V13ReadOnlyForensics.java` inspects exactly THREE fixed V13 private logs:
1. `v13-wine-direct-init.log`
2. `v13-sc-entry.log`
3. `v13-foreground-wineserver.log`

It reports bounded per-PID PE mapping/exit and module failures, wineserver process request/reply/lifecycle, sc.exe mentions, entry-log state and named V13 metadata. It reads at most **8 MiB per log**, **100,000 lines per log**, **16,384 chars per line**, with a **9,000-character sanitized report**, no raw paths. The C: mapping is inspected with `lstat/readlink` but not followed. Registry metadata (size and file presence) only; **registry contents never opened**.

It performs **NO process creation, Wine/Wineboot/sc.exe/services.exe/wineserver, reads of other generations, writes, scratch creation, cleanup, deletion or retries**. An empty sc.exe log or missing PE mapping marker cannot prove the native cause. No SCM query, program or game runs. The report ends `END OF SHORT V13 READ-ONLY REPORT`.

## Version / release gate
New source candidate **11.2-next.0.100 / versionCode 131**, experimental `com.charoitx`. Before providing any v0.100 APK: verify full Next+stable tests, Android Gradle, package identity/version, unchanged experimental signing SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`, exact Actions run and downloadable signed APK artifact. Until then the latest verified signed build is v0.99 [Actions 42453554339](https://github.com/rgarn023/CharoitePortal/actions/runs/42453554339), [artifact 13607130952](https://github.com/rgarn023/CharoitePortal/actions/runs/42453554339/artifacts/13607130952); **DO NOT run its retired V13 execution control again**.

When signed v0.100 is verified, install **IN PLACE** over `com.charoitx` without uninstall or storage clearing, and select the sole current Wine29 System diagnostic **Inspect Wine29 v13 sc.exe exit (read-only)**. Copy the complete bounded report. Any future V14 execution requires separately reviewed evidence, new scratch, explicit new consent and cannot be inferred from exit code alone.
