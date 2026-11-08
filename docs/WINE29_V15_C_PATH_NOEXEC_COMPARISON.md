# Wine29 V15 — fresh Windows C: sc.exe with scoped WINELOADERNOEXEC=1

## V14 owner evidence (November 8, 2026)
The owner supplied the completed V14 preserved read-only report: Wineboot PIDs 0x0024/0x002c and services.exe PID 0x0034 had six observed zero PE exit events, with mapped services.exe and userenv.dll. The direct-init PE trace was 604,395 bytes / 3,936 lines; private wineserver trace 487,973 bytes / 5,143 lines. Neither traced sc.exe PE mapping. The **separate** Windows-path sc.exe attempt returned 127 and zero output. That attempt's log was 0 bytes. Absence of sc.exe mappings in the Wineboot trace does **not** rule out separate-entry mapping. Registry files were 1,981/1,858/123 bytes after shutdown; contents and integrity not inspected. No SCM or game operation has been proved.

V14 has been consumed. Do not rerun, read, delete, or clean V14 again. Prior V1–V13, Wine28, stable Portal, games, saves, user prefixes and rootfs remain untouched.

## One-variable V15 hypothesis
The three observed test combinations are: V12 Unix sc.exe path and NOEXEC=1; V13 Unix path and NOEXEC unset; V14 Windows C: path and NOEXEC unset. All returned exit 127 with no output. The untested fourth combination is **Windows C: path with NOEXEC=1**. This is not a known fix. V15 retains V14's Windows C: pathname and SHA-256-verified copy to the **NEW v15-only** private system32 folder; only sc.exe's WINELOADERNOEXEC setting changes to 1.

The NEW one-shot test verifies the original sealed 34 DLLs, 111 PE/NLS source inputs, three APK-native ELF modules and source-built services/userenv/sc, creates ONLY `charoite-next-wine29-entry-v15` when absent, runs one bounded foreground private wineserver and direct Wineboot -i then (only if the bootstrap gates pass) ONE no-argument sc.exe entry attempt. It preserves separate Wineboot, sc entry, and server traces. It never queries SCM, starts/stops services explicitly, plays games, accesses old scratch or runs any installer. An existing V15 scratch blocks all retries. No scratch cleanup or data reset is permitted.

## Release / verification gate
Candidate Next v0.103, versionCode 134, package `com.charoitx`; original signing key, in-place install and exact Actions success/artifact must be verified before device use. CI cannot test Wine on the owner's phone. When explicitly consented on device, copy the complete `END OF SHORT V15 ENTRY REPORT`; do **not** claim sc.exe PE mapping, SCM readiness or gaming compatibility from exit status alone.

Charoite 1.0 readiness stays at approximately 30% complete / 70% remaining until verified functional milestones, independent of diagnostic or APK version numbering.

## Verified signed v0.103 GitHub Actions release — November 8, 2026

[Actions run 42470144968](https://github.com/rgarn023/CharoitePortal/actions/runs/42470144968) **SUCCESS**, exact source commit [8e5352c7cf19767842373ecf9568c95cfda4912c](https://github.com/rgarn023/CharoitePortal/commit/8e5352c7cf19767842373ecf9568c95cfda4912c). **138 stable + 238 Next tests passed**, V15 source-only one-shot/consent gate PASS, Android Gradle BUILD SUCCESSFUL. AAPT package `com.charoitx`, code 134, name `11.2-next.0.103`. Original experimental signer SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` MATCH.

- [Signed APK artifact 13613600705](https://github.com/rgarn023/CharoitePortal/actions/runs/42470144968/artifacts/13613600705), ZIP 461,562,900 B, `sha256:d0cae5fd9106a03edbcea766113a671631b5c33c591b920867aedb8f96b5d5f9`, expires 2027-02-06T10:08:33Z.
- [Source/LGPL artifact 13612638562](https://github.com/rgarn023/CharoitePortal/actions/runs/42470144968/artifacts/13612638562), ZIP 538,243 B, `sha256:437ff1e209dacf61d7f7a3027b90f56c7c4ca2ba03dfce29355a5019c12a9576`.

Install **in place** only; choose System's V15 one-shot and separately consent once if you want to run it. V14 remains consumed and untouched, and no previous Wine29/Wine28 scratch, game/save/user prefix/rootfs may be accessed. CI did not run the device experiment or prove sc.exe PE mapping, SCM or gaming readiness. The first run 42469966010 failed a stale escaped AAPT version assertion; it is not an APK release.
