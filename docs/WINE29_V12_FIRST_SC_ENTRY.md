# Wine29 V12 — first ARM64 sc.exe PE-entry gate

## Verified signed APK — November 8, 2026

[GitHub Actions 42451472112](https://github.com/rgarn023/CharoitePortal/actions/runs/42451472112) **SUCCESS** for exact APK source `f2851b8ab3e799d91dd2807074907edfd11263dd`. **138 stable / 220 Next tests PASS**, including V12 one-shot consent/isolation gate. Gradle **BUILD SUCCESSFUL**; package `com.charoitx`, versionCode **128**, versionName **`11.2-next.0.97`**. Original experimental signing certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` **MATCH**. [Signed APK artifact 13605753049](https://github.com/rgarn023/CharoitePortal/actions/runs/42451472112/artifacts/13605753049), ZIP **461,559,968 B** / SHA-256 `0b64d0ddc8f676c614d2f7c07430b3948f3ba41f44f2f85bf043487ef3978cee`, expires **2027-02-06T05:36:57Z**. [Source/LGPL attribution](https://github.com/rgarn023/CharoitePortal/actions/runs/42451472112/artifacts/13606256058) includes V12 Java. Install **in place**, no uninstall/clear data. Owner may separately authorize exactly one V12 run through the System dialog; no Wine or Windows PE was executed by CI or by this handoff.


**Release scope:** Experimental Next `com.charoitx` v0.97 (versionCode 128), separately signed from stable Portal. **Source candidate — no signed release or device execution claimed until independently verified.** V11 audit was completed and preserved (V11 scratch immutable, no replay).

## Why V12 is different
V11 demonstrated Wineboot `-i` exit 0, services.exe/userenv DLL mappings and no observed PE module errors, but the foreground server was gone after native `--version` probes; sc.exe was never attempted. Both native probes are deliberately removed from V12's run sequence. The goal is to determine whether no-argument ARM64 `sc.exe` is actually mapped while the same private wineserver is alive after successful Wineboot.

## Execution boundary
- The user chooses the **only active Wine29 System action**, `Test Wine29 v12 sc.exe PE entry (one-shot)`, and accepts an explicit consent dialog. Nothing starts automatically.
- Immutable input: exact original Wine29 sealed 111-file PE/NLS cohort, 34 hybrid DLLs, v6 native 3 ELFs, source-matched v7 services.exe, v8 userenv.dll and v9 sc.exe. All preflight hash/gate checks execute before creating any new scratch.
- One new and never reused `getNoBackupFilesDir()/charoite-next-wine29-entry-v12` directory, isolated `prefix`, C: mapping, runtime staging and log files. Abort if scratch already exists; never retry, delete or clean it.
- At most one foreground wineserver, one source-built ARM64 Wineboot `-i` operation (which may create its internal helpers) and **one** no-argument ARM64 `sc.exe` invocation following successful Wineboot only if the foreground server is alive. `sc.exe` is bounded to 12 seconds / 512 KiB; process logs remain local. Captures foreground server liveness before and after attempted PE entry.
- **No** native `--version` comparisons, SCM query/start/stop, user programs, installers, games, Steam/Battle.net, graphics, stable Portal or existing Wine28/Wine29 V1–V11/user prefixes/rootfs. Never treat no-argument usage text or exit code by itself as PE-map proof.

## Required evidence before moving to SCM
The phone report ends `END OF SHORT V12 ENTRY REPORT`. Preserve the V12 scratch and raw private logs. Examine bounded process trace evidence separately (new preserved V12 read-only forensic code, if necessary) to distinguish (1) PE loader started, (2) sc.exe mapped, (3) application entrypoint/usage observed, (4) server remained live. These milestones do not imply SCM or game readiness.

## Build and install gates
GitHub Actions must show new V12 static one-shot isolation/consent tests, complete Next regression and stable regression, Android Gradle success, AAPT identity `com.charoitx`/128/`11.2-next.0.97`, and original experimental Next signer certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`. Verify the exact Actions run and artifact before handing out an APK. Install *in place* over existing `com.charoitx`, never uninstall or clear app data. Do not touch stable `com.charoite` or saved games.
