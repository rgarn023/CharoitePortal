**Handoff:** [**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# CHAROITE NEXT — CURRENT HANDOFF | November 8, 2026

## Latest VERIFIED signed experimental APK — V21 v0.113

**LATEST VERIFIED SIGNED CHAROITE NEXT v0.113 — NOVEMBER 8, 2026 — WINE29 V21 INDEPENDENT HELP:** [**GitHub Actions run 42540331427 — SUCCESS**](https://github.com/rgarn023/CharoitePortal/actions/runs/42540331427), exact signed APK source commit [**849db3b7733ac96d2456863b9a26cc6e5e49c661**](https://github.com/rgarn023/CharoitePortal/commit/849db3b7733ac96d2456863b9a26cc6e5e49c661), [**DIRECT SIGNED CHAROITE NEXT v0.113 APK ARTIFACT 13640633583 — DOWNLOAD**](https://github.com/rgarn023/CharoitePortal/actions/runs/42540331427/artifacts/13640633583) (one ZIP containing the APK; **461,556,454 ZIP bytes**, SHA-256 **`af9c6c21fcddfefb2efe8b69547c5e60f57051c9a5022e0602c8e0852998776c`**, expires **2027-02-07T00:28:04Z**). [**Sources/LGPL licenses artifact 13641570285**](https://github.com/rgarn023/CharoitePortal/actions/runs/42540331427/artifacts/13641570285) (**636,393 ZIP bytes**, SHA-256 `9225d85cc56cf19054cdb1bb2af7399cc5d40cacc09437603c70d507cc4a45dd`).

Android Gradle **BUILD SUCCESSFUL**, 269 Next source/regression tests **PASS**, new isolated V21 source/consent gate **PASS**, original Wine29 source module checks **PASS**, AAPT verified package **`com.charoitx`**, **versionCode 144**, **versionName `11.2-next.0.113`**, and APK signature verification **MATCHES original persisted experimental keystore** (signer SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`). Signed APK and source attribution artifacts published; CI **did not execute Wine on the phone**. Supersedes verified v0.112; **V21 phone one-shot test is COMPLETE, with evidence preserved.**

Previous verified signed **v0.112 V20 artifact**: [Actions run 42536089299](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299), [artifact 13638739137](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299/artifacts/13638739137). Its one-shot phone run is complete and V20 scratch permanently consumed.

## V18 preserved owner postmortem — COMPLETE

Phone read-only report delivered in full. Only TWO V18 logs and named metadata inspected; no processes, retries, scratch creation, writes, cleanup, registry contents or older scratch. PE trace **606,645 B / 3,954 lines**, server trace **488,332 B / 5,145 lines**. Wineboot PIDs 0x0024/0x002c and services.exe PID 0x0034 had six PE exit markers, all **0**. services.exe was mapped with userenv.dll; observed module errors and DLL_NOT_FOUND markers **0**. Native Wineboot -i returned **0**. Prefix registry metadata: `system.reg` **1,981 B**, `user.reg` **1,858 B**, `userdef.reg` **123 B**; contents/completeness NOT verified. A private foreground wineserver was alive post-init and at +0ms; it exited native **1** by the nominal +1,000ms checkpoint with actual observation about **200ms** because waitFor returned early. Native server shutdown's **cause unproven**. Neither independent Wineboot --help, sc.exe, SCM nor game execution was attempted in V18. V18 scratch is permanently consumed: **NEVER retry, delete, clean or repurpose.** Prior Wine29 V1–V17, Wine28, stable Portal, games/saves/prefixes/rootfs untouched.

## V20 OWNER PHONE DIAGNOSTIC — COMPLETE (one-shot, permanently consumed)

Owner's **V20 persistent-server report** delivered November 8, 2026. On Samsung Galaxy S26 Ultra, the source-verified V20 direct Wineboot `-i` returned **0**, fresh C: mapping remained correct, Windows/users/system32 paths were created, and a socket+lock handshake succeeded. Native `wineserver -f -d -p` remained **alive 5/5 checkpoints** (measured +0, +1000, +3001, +8001, +12001 ms) and was alive *before* intentional V20-only finalization. No child exec errno marker or `c0000135` observed. **No independent Wineboot --help, sc.exe, SCM or games were executed.** V20 scratch and private logs preserved, never rerun/reset/delete. V1–V19, Wine28, stable Portal, games, saves, user prefixes/rootfs unchanged.

**Registry timing caveat:** initial V20 checks immediately after `-i` said `system.reg`, `user.reg`, `userdef.reg` absent. Final **file metadata only**, after private-server finalization, showed **1,981 B / 1,858 B / 123 B**. This may be delayed server registry flush, but exact cause and completeness are UNPROVEN; no contents were read. V20 persisting for 12 seconds vs V18's ~200 ms non-persistent exit supports an ordinary idle shutdown hypothesis, **not definitive causation** or SCM readiness.

## V21 OWNER PHONE DIAGNOSTIC — COMPLETE (one-shot, permanently consumed)

The owner supplied V21's **independent help** phone report on November 8, 2026. Direct source-verified ARM64 Wineboot `-i` returned **0**. A separate Wineboot `--help` returned **0** with nonempty output while V21's foreground `-p` wineserver was alive before and after. No observed `c0000135`, missing-builtin marker or child exec errno. Wine-created Windows folders and the relative C: link were observed. Registry files initially absent were observed as post-finalization FILE SIZE metadata **1,981 / 1,858 / 123 bytes**; contents and completeness remain unverified. No independent sc.exe/SCM/game executed. V21 is **PERMANENTLY CONSUMED**: do not re-run, read without separate read-only scope, delete, clean or repurpose scratch/logs.

## CURRENT V22 DEVELOPMENT — independent sc.exe query RpcSs

**V22 source/CI gate prepared; no verified signed V22 APK or phone execution yet.** Planned experimental `com.charoitx`, versionCode **145**, versionName **11.2-next.0.114**. Scope: [**WINE29 V22 PRIVATE PERSISTENT-SERVER SCM QUERY**](WINE29_V22_SCM_QUERY_PERSISTENT_SERVER.md).

Reuse V21's proven *method* in a **NEW private V22 scratch only**: pinned 34 hybrid imports, 111 staged PE/NLS, original APK-native trio, source-built ARM64 Wineboot/services/sc and ARM64X userenv preflight. Start private `wineserver -f -d -p`, direct Wineboot `-i`; only if the native exit, Windows path and persistent server gates pass, invoke exactly ONE independently launched source-verified `sc.exe query RpcSs` (20 s / 2 MiB bound). Require recognizable RpcSs service status, not native exit code alone. Preserve raw evidence privately. No independent Wineboot help, other SCM commands, games, installers, network, prior Wine29 scratch, Wine28, Portal, saves, user prefixes or rootfs. V22 is always one-shot; never retry or clean scratch.

### System → CURRENT WINE29 ACTION — V22 SCM QUERY — OWNER PHONE TEST AFTER VERIFIED APK

All warnings/required actions directly accompany **Test Wine29 v22 SCM query (one-shot)** and **Open current project handoff** in the **System** tab. **Only once V22 signed APK and Actions artifact are verified**, download and install **IN PLACE** over experimental `com.charoitx` (never uninstall or clear storage). Tap Test; choose **Authorize ONE fresh v22 test** or **Cancel — do not execute**. Copy the FULL report from Handoff through **END OF SHORT V22 SCM QUERY REPORT**. V1–V21 scratch never rerun, cleaned or accessed. Stable Portal/user data unaffected.

## Standing development and safety policy

Continue implementing/fixing/committing/building on **main** during active chats, without asking for routine authorization. Pause only for **phone APK install and explicit one-shot diagnostic consent**. Preserve original signing key and experimental package, stable Portal `com.charoite`, data, Wine28, all consumed Wine29 scratch, installed games, saves, and rootfs. CI source tests and Android packaging are not phone runtime proof. GitHub Actions manual workflow only; no paid OpenAI API automation. Include clearly clickable handoff link at START of every report, exact Actions APK artifact links when verified, and completion percentage with each build. Group System actions and instructions together.

**Charoite 1.0 estimate: ~30% COMPLETE / ~70% REMAINING, unchanged pending independent SCM on-device proof.** Next milestones after reliable server lifecycle: independent Wineboot control/PE mapping, sc.exe/SCM, Windows applications, graphics/audio/input and Portal/Core integration. No one of those milestones is yet proven.

## Historical record

[**Complete handoff through signed v0.111 and owner V18 execution (immutable Git revision)**](https://github.com/rgarn023/CharoitePortal/blob/18436ceb2dc90e8d11807af3a3253f6a42c32edd/docs/CURRENT_HANDOFF.md). Full historical implementation notes, provenance, source build and prior Actions artifacts remain available in that exact Git revision, without bloating the current handoff. [**V18 read-only audit scope**](WINE29_V18_PRESERVED_IDLE_READONLY.md) and [**V18 server lifecycle scope**](WINE29_V18_SERVER_IDLE_LIFECYCLE.md) are also preserved.
