[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V17 — independent Wineboot positive control versus sc.exe

**Status: source candidate; not proof of an installable APK or device execution until verified.**
**Device action is NOT read-only and is disabled until owner explicitly authorizes it in System.**

## Completed V16 evidence and open hypothesis

The owner provided the complete V16 preserved read-only report. V16 Wineboot PIDs 0x0024/0x002c and services.exe PID 0x0034 had six observed zero-valued PE exit events. services.exe mapped userenv.dll, and the preseeded C: registry files had metadata sizes 1,981/1,858/123 B after shutdown. These observations do not prove registry completeness or SCM readiness. The independently requested Windows-path sc.exe never appeared in the preserved Wineboot PE trace, its own log was empty, and Android's accepted native loader returned exit 127 after ~201 ms. Foreground server was alive at launch acceptance but not at sc completion. No causal relationship or PE mapping was established. V16 is **permanently consumed**.

The prior V12–V16 experiments varied Unix/Windows target paths and NOEXEC but did not include a **matched independently launched control after successful Wineboot**. The proposed V17 control tests whether a second native-loader invocation can run the already-known Wineboot executable in the same private prefix and live server before attempting sc.exe.

## V17 one-shot scope

- **Only new private scratch**: `charoite-next-wine29-entry-v17`. Refuse if scratch already exists, even after a partial run. No retry, cleanup, data reset or removal. Stable `com.charoite`, games, saves, rootfs, user prefixes, Wine28 and Wine29 V1–V16 scratch are never accessed.
- Recheck the immutable 34 hybrid DLLs, 111 PE/NLS files, three original APK-native ELF hashes and source-pinned services.exe, userenv.dll, sc.exe before scratch creation. No replacement native ELF cohort is introduced.
- Start only the bounded **V17-private** foreground wineserver and Wineboot -i; its Wineboot trace remains a separate file.
- If the initial gates pass, run **one** independent `wineboot.exe --help` control with the same verified APK-native loader, private prefix, server and `WINELOADERNOEXEC=1`. Record native return, elapsed duration, bounded output bytes and server liveness.
- Only if that control finishes within the cap and the private server is still alive, attempt **one** no-argument Windows `C:\\windows\\system32\\sc.exe` via the same native loader, private prefix/server/NOEXEC flag. Record its distinct native outcome and liveness. No `sc query`, SCM request, installer, game, Battle.net or Steam.
- Preserve `v17-wine-direct-init.log`, `v17-independent-wineboot-help.log`, `v17-sc-entry.log`, `v17-foreground-wineserver.log`. A normal native exit/usage string is **not proof of a mapped PE image**, nor is a failure a diagnosis. The control and sc.exe paths/PE targets differ, so this is a discriminating probe, not a definitive single-variable causal experiment.

## System tab and release gate

Under **System → CURRENT WINE29 ACTION — V17 CONTROL COMPARISON**, all scope and warning instructions are immediately beside **Test Wine29 v17 control vs sc.exe (one-shot)** and **Open current project handoff**. Testing requires a second explicit **Authorize ONE fresh v17 test** tap. Cancel remains safe. The V16 execution and read-only inspection actions are archived. The report starts with the handoff URL and ends with **END OF SHORT V17 ENTRY REPORT**. Copy the complete report to a new chat.

Candidate identity `com.charoitx`, **versionCode 139 / versionName 11.2-next.0.108**. Source gates and CI signing are not phone execution. **Do not install a candidate until exact successful Actions run, original signing certificate and signed APK artifact are verified.** Install in place; never uninstall/clear data.

**Charoite 1.0 readiness: ~30% complete / ~70% remaining (unchanged).** Only verified functional independent PE/SCM and playable graphics/audio/input plus Portal/Core integration justify advancing.

## VERIFIED signed V17 candidate — November 8, 2026

- **[Actions run 42523239609](https://github.com/rgarn023/CharoitePortal/actions/runs/42523239609): SUCCESS**, source commit [d55cd15fd53b02d70011ec3877bdf80d5e054d4e](https://github.com/rgarn023/CharoitePortal/commit/d55cd15fd53b02d70011ec3877bdf80d5e054d4e).
- **[Signed experimental Next APK artifact 13634382659](https://github.com/rgarn023/CharoitePortal/actions/runs/42523239609/artifacts/13634382659)**, one ZIP with one APK; 461,561,378 bytes ZIP; SHA-256 `295d7625033e3f975bb28316833f815f3e52327922a2f07eb46ee06e877b7e05`, expires 2027-02-06.
- **[LGPL/source artifact 13634675974](https://github.com/rgarn023/CharoitePortal/actions/runs/42523239609/artifacts/13634675974)**, 581,704 bytes, `sha256:b98f976cc1ed56d8d65da766f40dbfa437e6b6fdb36484f45409d7002da99e41`.
- 138 stable tests + 253 Next tests PASS, V17 source-only isolation/consent contract PASS, Android Java/native compilation and APK staging PASS; AAPT `com.charoitx`, `versionCode 139`, `versionName 11.2-next.0.108` confirmed.
- APK certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` MATCHED the persisted experimental signing key, consistent with the previous released Next signer.
- **CI did not execute V17 on the owner's phone**. No independent Wineboot --help/sc.exe mapping or SCM/game functionality is proven. Test remains owner-initiated, fresh V17-only, one-shot. Read all System instructions beside both V17 action/handoff buttons and never uninstall/reset previous data.

**Readiness remains ~30% / 70% remaining**, despite build success.
