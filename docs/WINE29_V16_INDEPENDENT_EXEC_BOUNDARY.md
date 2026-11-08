[**Handoff — open first**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V16 — independent Android native exec-boundary diagnostic

## Why V16 exists
The owner's completed V15 postmortem observed source-verified Wineboot (-i, exit 0) and a mapped services.exe/userenv.dll with no observed module errors in its **Wineboot-only** PE trace. The **separate** no-argument Windows-path C:\windows\system32\sc.exe attempt returned **127**, emitted **0 bytes**, and was followed by the foreground wineserver no longer being alive. Nothing establishes that sc.exe mapped a PE image, reached SCM, or caused the server to stop. Repeating V15 or inferring a cause from the bootstrap trace is prohibited.

## V16 isolated experiment, not a proposed fix
- Source: next-generation/CharoiteWine29V16ExecBoundaryProbe.java, new **private** charoite-next-wine29-entry-v16 scratch and matching prefix, created only if absent.
- Reuses the original source-pinned assets and sealed 34-DLL + 111-file PE/NLS + native 3-ELF SHA-256 source gates, with source-built services/userenv/sc. Copies source-verified files only into **new V16** scratch. Old V1–V15 scratch and Wine28, stable Portal, games, saves, user prefixes and rootfs are never read, rewritten, cleaned, deleted or replayed.
- Only after isolated private wineserver/socket and Wineboot -i gates pass, it attempts **one** no-argument C:\windows\system32\sc.exe via verified APK-native loader; WINELOADERNOEXEC=1 is retained from V15. There is **NO** sc query, explicit SCM/service action, installer, game or external network operation.
- V16 adds independent **Android native process-start** observations: executable permission check, ProcessBuilder.start() returned versus threw, sanitized Java exception type/errno when available, elapsed launch and process time, bounded exit status and output-byte count, and server alive states before/after spawn/completion. Wineboot PE trace, separate sc-entry log, and private server trace remain distinct and preserved.
- Important: Android accepting a subprocess establishes only the native launch boundary; it does **not** prove the Windows PE image was mapped. Exit 127, an empty sc log, or wineserver disappearance cannot establish a crash, missing DLL, SCM success, or game readiness.
- The private V16 scratch is **one-shot**: if present, even after a partial failure, it must be preserved. **Never retry, uninstall, clear storage, delete or clean any previous scratch.** No test runs automatically when the APK is installed or opened.

## Owner instructions (all controls under System)
Install only a **verified signed** v0.106 artifact in place over experimental com.charoitx after CI success and signing identity check. Open **System → CURRENT WINE29 ACTION — V16 NATIVE EXEC BOUNDARY**. Its instructions, **Test Wine29 v16 sc.exe native boundary (one-shot)** and **Open current project handoff** buttons appear together. Tap the test, read the separate confirmation, choose **Authorize ONE fresh v16 test** once, then copy the full short report through END OF SHORT V16 ENTRY REPORT into a new chat. The **first line** of the report is the handoff URL. Cancel if you do not wish to execute Wine.

Completed V15 execution/inspection and historical execution buttons are no longer shown. No new V15 action is requested. Stable com.charoite and existing com.charoitx app data must remain installed.

## Verification requirements
The GitHub Actions build checks source-only Python isolation contracts, Android compile, independent source/ABI/package/signing identity, and direct artifact issuance. **CI does not execute Wine on the owner's phone.** Do not call V16 a successful device diagnostic before the owner's report. Report Charoite 1.0 readiness **~30% / 70% remaining** until actual functional PE entry, SCM and gaming/Portal integration milestones are confirmed.

Candidate release: experimental com.charoitx, **versionCode 137**, **versionName 11.2-next.0.106**. Signed build/artifact status must be established separately from source commits.
