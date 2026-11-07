# Wine29 v8 retained bootstrap postmortem — short read-only report

**Date:** November 7, 2026  
**Scope:** Charoite Next experimental package `com.charoitx`; v8 retained scratch only.  
**Decision:** Do not rerun the completed v8 Wineboot attempt. Read existing evidence first.

## Received v8 on-device evidence

The user's one-shot source-verified v8 test confirmed SHA-256/PE/native checks and foreground wineserver socket and lock. Direct `wineboot.exe -i` returned **exit code 0 within 45 seconds**. Wineboot and NTDLL PE mapping and API-set loading were visible, and new private `drive_c/windows`, `windows/system32`, `users` and `users/xuser/AppData` directories appeared. The `C:` link and `drive_c` were **preseeded**, therefore not evidence that Wine created them.

When the v8 probe checked metadata **before its final foreground wineserver termination**, `system.reg`, `user.reg`, `userdef.reg`, and `Program Files` were absent. The report stated `V8 PE services.exe mention: false` and `PE trace c0000135 seen: false`. Those absence flags are not proof that services.exe never ran, that registry files were never flushed later, or that the entire trace was error-free. Complete prefix initialization, SCM, Windows applications and games are NOT verified.

The report copied to chat was unusually long: a single PE trace segment stated approximately 601,313 bytes and the separately appended foreground wineserver trace followed **after** the result line. Android clipboard/chat pasting cut off the ending, making forensic review unreliable. Do not ask the owner to paste raw 600KB+ trace dumps again.

## Current implementation — Next 0.89 source candidate

`next-generation/CharoiteWine29V8ReadOnlyForensics.java` is a newly added **strictly read-only** auditor of precisely these retained v8 names:

- `v8-wine-direct-init.log`
- `v8-foreground-wineserver.log`

Only explicitly named v8 prefix/runtime entries are inspected for **metadata**, never registry contents. `dosdevices/c:` is checked using `lstat/readlink` and never followed. Both log reads fail closed outside an 8 MiB per-file ceiling, cap lines at 100,000 and skip oversized lines, and render sanitized PID/exit/module/event counts. No paths, raw traces, unsanitized command lines or registry contents enter the clipboard. The complete report is capped at **9,000 characters** and ends with `END OF SHORT V8 REPORT`.

No Wine, wineserver, Wineboot, services.exe, games, native code, Android process launch, cleanup, prefix creation, writes or retries are performed. The v8 one-shot button is archived; the **sole Wine29 System test** is `Inspect Wine29 v8 bootstrap (short read-only report)`. Stable Portal, older scratch, user prefixes, games, saves and rootfs must remain untouched.

`next-generation/prepare_next.py` targets **versionCode 120 / versionName 11.2-next.0.89** for the experimental `com.charoitx` APK, using its existing persistent signing identity. The CI test `test_wine29_v8_short_forensics_contract.py` and Android workflow explicitly verify the no-write/no-process contract and inclusion in the build. Source edits are NOT proof that a signed APK has finished building.

## Next step

1. Verify the latest GitHub Actions **Charoite Core Next Android** run, signing certificate and downloadable APK artifact. Do not label a candidate as successful until the run and checks finish.
2. Install IN PLACE over `com.charoitx` — never uninstall, clear storage or rerun v8.
3. On the phone, tap **System → Inspect Wine29 v8 bootstrap (short read-only report)** and copy the short output including the END marker.
4. Correlate per-PID PE termination with services/userenv lookup and read-only registry presence **after server shutdown**. Only then decide whether an explicitly authorized fresh v9 scratch is justified.

**Interpretation:** Direct Wineboot exit 0 is a real bootstrap improvement but is **not** proof that a usable Windows compatibility environment exists.
