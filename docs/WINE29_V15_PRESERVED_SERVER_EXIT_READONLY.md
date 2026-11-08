# Wine29 V15 — preserved PE-entry / wineserver-exit forensic audit (read-only)

## Owner V15 execution results — November 8, 2026
The owner supplied `END OF SHORT V15 ENTRY REPORT` from the signed Next v0.103 diagnostic on the Galaxy S26 Ultra. Exact source/hashed checks passed for the 34 hybrid DLLs, 111 PE/NLS files, three APK-native ELFs, and pinned sc.exe/services.exe/userenv.dll. A NEW, independent V15 private scratch was created. The C: drive and dosdevices/c: link were **preseeded** (not Wine results). Wineboot `-i` returned **0** within 45 seconds; the Windows/system32 and users/xuser/AppData directories were created by Wine. After wineserver stopped, system.reg/user.reg/userdef.reg were present at **1,981 / 1,858 / 123 bytes** (metadata only; contents/completeness NOT verified).

One SHA-256-verified Windows-path `C:\\windows\\system32\\sc.exe` launch was attempted with `WINELOADERNOEXEC=1` only for that launch. It returned **127** within 12 seconds, with **0 output bytes** and no usage marker. **sc.exe PE mapping remains unverified; SCM was never queried.** The foreground wineserver was alive before the sc.exe launch but **NOT alive immediately afterward**; V12–V14 had stayed alive across their corresponding sc.exe attempts. This difference is a lead, **not evidence that sc.exe ran, crashed, or killed the server**. The original Wineboot direct-init PE trace cannot establish sc.exe mapping on the separate subsequent invocation.

The V15 scratch is permanently consumed and preserved. **NEVER rerun, delete, clean or change V15**. Never uninstall or clear app storage or touch V1–V14, Wine28, stable `com.charoite`, user prefixes, games/saves or rootfs.

## New v0.104 read-only implementation
- Scope: only three fixed V15 logs (`v15-wine-direct-init.log`, `v15-sc-entry.log`, `v15-foreground-wineserver.log`) and named V15 metadata including private system32/sc.exe and registry **sizes**, not contents. C: symlink inspected with `lstat/readlink`; never traversed.
- Bounds: 8 MiB/file, 100,000 lines/file, 16,384 characters/line, 9,000-character short report. Raw traces, paths and registry content never copied.
- Counts: per-PID Wineboot/services mappings/exits, explicit sc.exe PE maps and child-create mentions **in their own trace scope**, entry-output markers, separate server process requests/replies, shutdown and registry references. Correlate cautiously: traces may not cover the separate sc.exe invocation or explain the server stop. Preserve **unknown** where evidence is missing.
- No execution, writes, retries, new scratch, cleanup, SCM commands or network. Source in `next-generation/CharoiteWine29V15ReadOnlyForensics.java`; System button **Inspect Wine29 v15 sc.exe + server (read-only)**. The V15 one-shot control is hidden and unreachable in UI; all older historical diagnostic buttons remain retired.
- Copy report ending `END OF SHORT V15 READ-ONLY REPORT`. Report includes [Current Handoff](CURRENT_HANDOFF.md).
- Package stays experimental `com.charoitx`; candidate versionName `11.2-next.0.104`, versionCode `135`. CI build/signing is not proof of any phone execution.
- Charoite Portal 1.0 readiness: **~30% complete / ~70% remaining**, unchanged until independent PE startup, SCM, game, graphics/audio/input and Portal integration show functional progress.

## Next safe decision
If the V15 preserved traces show no conclusive sc.exe lifecycle, do **not** replay V15 or infer an error cause from exit 127. A future V16 one-shot may instrument Android native launcher / exec-return and bounded independent sc.exe PE trace in a **new private V16** scratch with renewed consent. Avoid game execution until standalone PE entry is demonstrated.
