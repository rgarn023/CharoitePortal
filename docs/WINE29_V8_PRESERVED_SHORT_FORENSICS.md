# Wine29 v8 retained bootstrap postmortem — short read-only report

**Date:** November 7, 2026  
**Scope:** Charoite Next experimental package `com.charoitx`; v8 retained scratch only.  
**Decision:** Do not rerun the completed v8 Wineboot attempt. Read existing evidence first.

## Received v8 on-device evidence

The user's one-shot source-verified v8 test confirmed SHA-256/PE/native checks and foreground wineserver socket and lock. Direct `wineboot.exe -i` returned **exit code 0 within 45 seconds**. Wineboot and NTDLL PE mapping and API-set loading were visible, and new private `drive_c/windows`, `windows/system32`, `users` and `users/xuser/AppData` directories appeared. The `C:` link and `drive_c` were **preseeded**, therefore not evidence that Wine created them.

When the v8 probe checked metadata **before its final foreground wineserver termination**, `system.reg`, `user.reg`, `userdef.reg`, and `Program Files` were absent. The report stated `V8 PE services.exe mention: false` and `PE trace c0000135 seen: false`. Those absence flags are not proof that services.exe never ran, that registry files were never flushed later, or that the entire trace was error-free. Complete prefix initialization, SCM, Windows applications and games are NOT verified.

The report copied to chat was unusually long: a single PE trace segment stated approximately 601,313 bytes and the separately appended foreground wineserver trace followed **after** the result line. Android clipboard/chat pasting cut off the ending, making forensic review unreliable. Do not ask the owner to paste raw 600KB+ trace dumps again.

## Current implementation — verified signed Next 0.89

`next-generation/CharoiteWine29V8ReadOnlyForensics.java` is a newly added **strictly read-only** auditor of precisely these retained v8 names:

- `v8-wine-direct-init.log`
- `v8-foreground-wineserver.log`

Only explicitly named v8 prefix/runtime entries are inspected for **metadata**, never registry contents. `dosdevices/c:` is checked using `lstat/readlink` and never followed. Both log reads fail closed outside an 8 MiB per-file ceiling, cap lines at 100,000 and skip oversized lines, and render sanitized PID/exit/module/event counts. No paths, raw traces, unsanitized command lines or registry contents enter the clipboard. The complete report is capped at **9,000 characters** and ends with `END OF SHORT V8 REPORT`.

No Wine, wineserver, Wineboot, services.exe, games, native code, Android process launch, cleanup, prefix creation, writes or retries are performed. The v8 one-shot button is archived; the **sole Wine29 System test** is `Inspect Wine29 v8 bootstrap (short read-only report)`. Stable Portal, older scratch, user prefixes, games, saves and rootfs must remain untouched.

`next-generation/prepare_next.py` targets **versionCode 120 / versionName 11.2-next.0.89** for the experimental `com.charoitx` APK, using its existing persistent signing identity. The CI test `test_wine29_v8_short_forensics_contract.py` and Android workflow explicitly verify the no-write/no-process contract and inclusion in the build. **Verified signed APK:** [GitHub Actions 42423001295 SUCCESS](https://github.com/rgarn023/CharoitePortal/actions/runs/42423001295) at exact APK source commit `baa65008714f01bb6d5048b36276b623105070dc` built with **138 stable + 198 Next tests PASS**, Android Gradle PASS, AAPT `com.charoitx` versionCode **120** / versionName **11.2-next.0.89**, and persisted experimental signing certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` MATCH. [**Download signed Next v0.89 APK artifact 13594690627**](https://github.com/rgarn023/CharoitePortal/actions/runs/42423001295/artifacts/13594690627); ZIP 461,521,041 bytes, digest `sha256:4da5a593b08b6130dc3f85340ddef740777c85ef379e75a5efe4490750a85963`.

## Next step

1. Use the **verified signed v0.89** GitHub Actions artifact linked above; avoid other unverified builds.
2. Install IN PLACE over `com.charoitx` — never uninstall, clear storage or rerun v8.
3. On the phone, tap **System → Inspect Wine29 v8 bootstrap (short read-only report)** and copy the short output including the END marker.
4. Correlate per-PID PE termination with services/userenv lookup and read-only registry presence **after server shutdown**. Only then decide whether an explicitly authorized fresh v9 scratch is justified.

**Interpretation:** Direct Wineboot exit 0 is a real bootstrap improvement but is **not** proof that a usable Windows compatibility environment exists.


## Received preserved short report — after v8 server stopped

The owner completed the **signed v0.89 read-only audit**. The entire short report included the `END OF SHORT V8 REPORT` marker; no rerun or additional Wine execution occurred. Only fixed v8 logs and explicitly named metadata were inspected.

- Preserved prefix: `system.reg`, `user.reg`, and `userdef.reg` are **all present**. They had previously been absent at an earlier checkpoint before foreground wineserver stop. Their contents were **not opened**, so validity/completeness remains unknown; `Program Files` is still absent.
- PE trace: **601,313 bytes / 3,891 lines**; no overlong skips; 3 child-create requests; 1 Wineboot internal `--init` request; 2 `services.exe` requests; **1 services.exe PE mapping**; **58 userenv.dll mentions**; **0 module errors and 0 missing-DLL markers**.
- PE PIDs `0x0024` and `0x002c`: mapped Wineboot/NTDLL/kernel32/API set and each has two recorded **zero** exit events. PID `0x0034`: maps **services.exe**, **userenv.dll**, NTDLL/kernel32/API set, with **no recorded module failure** and **no recorded PE exit**. Absence of an exit event is NOT evidence that services remains active or SCM is functional.
- Wineserver: **482,538 bytes / 5,071 lines**, 1 server start, 2 process requests and 2 replies, 10 services mentions, no missing-DLL or registry-error marker, 1 shutdown mention. Log counts do not certify successful service-controller initialization.
- No full Windows prefix, functioning SCM, generic Windows process invocation, graphics or game support has been proven.

**Interpretation:** v8 resolves the specific v7 `userenv.dll` lookup failure and shows registry files **present later**; earlier assertions that the PE trace had no services mention and that registry files were absent were limited to the earlier reporting checkpoint. Later file presence does NOT by itself prove Wineboot completed all initialization tasks.

## Next candidate — v0.90 strictly read-only registry/services correlation

Source changes on `main` enhance **the same preserved v8 auditor** to obtain byte lengths of precisely the three named registry files as **metadata only** (never open files, read registry content or follow links) and summarize how many mapped `services.exe` PIDs also mapped `userenv.dll`, whether a module failure or explicit PE exit was observed. This does not run Wine or visit any other generation.

The System action is now **Inspect Wine29 v8 registry + services (read-only)**. `next-generation/prepare_next.py` targets `com.charoitx` **versionCode 121 / versionName 11.2-next.0.90**; CI source changes and read-only contract checks have been committed. **Candidate, not yet a verified installable release:** the first [Actions run 42424138119](https://github.com/rgarn023/CharoitePortal/actions/runs/42424138119) FAILED at the pre-build regression step solely on stale v0.89 package-version assertions. Forty-two older test modules have been aligned to the v0.90 identifiers through [commit 7c983758](https://github.com/rgarn023/CharoitePortal/commit/7c983758db78b412aa9d05ae62e0e81e8aade1f5). Corrected GitHub Actions compilation, signature and artifact are **not yet verified**. Until the build is independently verified, keep [signed v0.89 artifact 13594690627](https://github.com/rgarn023/CharoitePortal/actions/runs/42423001295/artifacts/13594690627) as the last verified install.

Do **not** rerun v8, delete its scratch, clear `com.charoitx` storage, or touch Portal and user-game data. A fresh v9 execution remains **unauthorized** and would require distinct consent, source-coherent dependencies, separate scratch, and a strictly scoped new validation hypothesis.
