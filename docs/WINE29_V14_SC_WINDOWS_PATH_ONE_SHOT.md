# Wine29 V14 — source-verified Windows C: path, one-shot sc.exe diagnostic

## Evidence from the completed V13 preserved read-only audit (November 8, 2026)
The owner supplied `END OF SHORT V13 READ-ONLY REPORT` from signed Next v0.100:
- V13 private PE trace **604,395 bytes / 3,936 lines**, two wineboot PID 0x0024/0x002c and services PID 0x0034; one services.exe PE mapping and userenv.dll present. Three child-create requests (one Wineboot --init, two services.exe), **0 observed sc.exe requests/maps in this Wineboot trace**, zero module errors / missing DLL markers, six zero PE exit events. The sc.exe native launch used **a separate log**; absent sc.exe in Wineboot's earlier log is not proof its launch never mapped.
- V13 sc.exe *separate* entry log **0 B**, with independently reported process exit **127** and no output/usage, despite `WINELOADERNOEXEC` UNSET only for sc.exe. Native cause and sc.exe PE mapping remain **UNVERIFIED**.
- V13 private wineserver trace **487,973 B / 5,143 lines**, two process requests/responses, **0 sc.exe mentions**; server remained alive immediately before/after the sc.exe attempt. No process-creation marker uniquely attributed to sc.exe. No SCM query was executed.
- Three registry files **1,981/1,858/123 B** metadata after shutdown; completeness and SCM unverified. All V13 scratch/logs are consumed and untouched. No old generations opened.

## V14 controlled Windows path hypothesis
The previously launched `sc.exe` was a source-verified **ARM64 Windows PE** in the Wine DLL tree and supplied to the native loader using its **absolute Unix pathname**. V14 retains the V13 source cohort and Wineboot environment, but once NEW V14 Wineboot has created `drive_c/windows/system32`, V14 writes an additional **SHA-256-verified copy of that same ARM64 sc.exe** into the NEW private Windows system32 path. It then attempts just one no-subcommand `sc.exe` launch using **`C:\windows\system32\sc.exe`** as the loader argument instead of the Unix absolute path. This tests Windows-path placement and resolution as one coupled launch-form change; it is not evidence the old cause is known.

The exact `WINELOADERNOEXEC` V13 setting remains **UNSET only for the sc.exe launch**, while Wineboot/private server use their previous settings. Foreground wineserver, source-pinned DLLs/PE/NLS, C: private mapping, bounded Wineboot `-i`, Windows-created folders and log/timeout behavior remain based on the same verified inputs. Source gate verifies the copied `sc.exe` SHA-256 against signed assets and rejects any preexisting target. No native `--version`, SCM query/start/stop, games, Steam, Battle.net, graphics, installers, user applications or old-prefix reads.

### Safety
V14 uses **`charoite-next-wine29-entry-v14`** only, under experimental app `com.charoitx` no-backup data. The app refuses a second attempt if that scratch already exists; the newly copied C: executable is never written into existing user game prefixes. V1–V13, Wine28, stable Portal `com.charoite`, user games/saves/rootfs untouched. Every device test requires a NEW explicit consent dialog; canceled tests execute nothing. After V14 is used, its scratch must NEVER be rerun, deleted or cleaned. Preserve all logs. CI never runs the phone experiment.

## Release candidate
Next v0.101: `com.charoitx`, versionCode **132**, versionName **`11.2-next.0.101`**. Candidate only until exact GitHub Actions tests/build, AAPT and original signing fingerprint `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`, artifact and success are independently confirmed.

**On-device (after signed verification):** Install in place without uninstall/clear data. In System select ONLY `Test Wine29 v14 sc.exe Windows C: path (one-shot)`, read the scope, then separately authorize one fresh test. Copy report ending `END OF SHORT V14 ENTRY REPORT`. Do NOT infer SCM or gaming readiness from Wineboot success or an exit code.
