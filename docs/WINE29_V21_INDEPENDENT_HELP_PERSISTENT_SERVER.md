[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V21 — independent Wineboot --help with persistent private wineserver

**SIGNED APK VERIFIED — OWNER PHONE V21 EXECUTION NOT YET PERFORMED.** Experimental `com.charoitx`, versionCode **144**, versionName **11.2-next.0.113**. [**Successful GitHub Actions run 42540331427**](https://github.com/rgarn023/CharoitePortal/actions/runs/42540331427), exact APK source commit [**849db3b7733ac96d2456863b9a26cc6e5e49c661**](https://github.com/rgarn023/CharoitePortal/commit/849db3b7733ac96d2456863b9a26cc6e5e49c661), [**direct signed APK artifact 13640633583**](https://github.com/rgarn023/CharoitePortal/actions/runs/42540331427/artifacts/13640633583). Android build, package, V21 source/consent, signer continuity and source-attribution artifact PASS. CI never ran the V21 phone probe. V20 scratch is permanently consumed.

## Evidence and reason for V21

The owner completed V20 in one fresh private scratch: source-matched direct Wineboot `-i` exited **0**, foreground `wineserver -f -d -p` had socket + lock, was alive immediately after `-i`, and survived every actual elapsed checkpoint at approximately 0, 1000, 3001, 8001 and 12001 ms. No independent loader/PE, sc.exe, SCM or games were attempted. V18 had exited about 200 ms into idle without `-p`; V20's survival supports but does not prove ordinary idle-shutdown causality. V20 is PERMANENTLY CONSUMED and must not be rerun, inspected without a separately scoped read-only inspection, deleted or repurposed.

V20's registry presence checks immediately after direct init reported `system.reg`, `user.reg` and `userdef.reg` absent, whereas final *metadata only* after stopping the private server showed **1981 B, 1858 B, 123 B** respectively. This could reflect delayed registry persistence during private server shutdown; timing/cause **not proven**, contents **never read**. A nonzero file size alone does not validate completeness.

## V21 exact consented experiment

1. Separate **one-shot on-device approval**. Preflight identical pinned 34 hybrid DLL imports, 111 PE/NLS hashes, source-matched ARM64 Wineboot, source-built ARM64 services/sc and ARM64X userenv, and three original V6 native ELF hashes **before** any new scratch. Fail closed if `charoite-next-wine29-entry-v21` already exists.
2. Create ONLY the brand-new private `com.charoitx` no-backup V21 scratch, private C: drive, exact relative `dosdevices/c:` mapping, verified scratch-local PE/NLS and HOME/TMP, and a source-verified foreground `wineserver -f -d -p` with capped log and socket/lock handshake. No V20/V1–V19 scratch, Wine28, stable Portal, user prefixes, games, saves, original rootfs or network.
3. Execute exactly ONE `wineboot.exe -i` via the APK-native verified loader, bounded 45 s/2 MiB. Wine may launch *internal* Wineboot/services. If direct init succeeds (exit 0, private server alive, C: path correct, Windows directories created, no observed internal child-creation marker), invoke exactly ONE **independent** source-verified `wineboot.exe --help` through the same verified native loader and PE, bounded 20 s/2 MiB. No retry, no `sc.exe`, SCM, arbitrary programs, games or installers. Record process completion/exit code, nonempty output, module/DLL failure/exec errno markers, and pre/post-control server survival. A nonzero second exit does not prove SCM or prefix failure; preserve logs for separately scoped read-only analysis.
4. Record registry file *presence* immediately after direct init, and only *filename/byte size* after the V21-owned server is intentionally stopped; never read registry contents or report raw paths/process logs. Preserve V21 evidence forever; only bounded V21-owned child/server processes may be stopped in finalization. Never clean, reset, retry or reenter V21.

**Interpretation:** A second independent help result with exit 0 and nonempty output is evidence of a successful separate invocation. No SCM query or game readiness is proven. A failed help command should be evaluated via a *future read-only V21 postmortem*, not rerun.

## System action / handoff

In **System → CURRENT WINE29 ACTION — V21 INDEPENDENT WINEBOOT HELP**, instructions are grouped with **Test Wine29 v21 independent help (one-shot)** and **Open current project handoff**. After extracting the linked verified signed v0.113 APK **in place** over experimental `com.charoitx`, tap Test, read the separate consent dialog and choose **Authorize ONE fresh v21 test** or **Cancel — do not execute**. Afterwards tap **Copy short report**, paste the COMPLETE report from Handoff through **END OF SHORT V21 INDEPENDENT HELP REPORT**. Never uninstall or clear app data; never run old-generation probes.

**Readiness estimate: ~30% complete / ~70% remaining**, unchanged until independent PE control, SCM, real Windows apps and gaming functionality are validated on device.
