# Charoite Next — Wine29 V10 native loader / sc.exe PE entry gate

Status: V10 **source implemented on `main`** on November 7, 2026. Phone execution has **not** occurred. A signed APK is **not** established by source commits alone; consult the current handoff and latest GitHub Actions release for build verification.

## Why V10 follows preserved V9

The completed V9 one-shot Wineboot `-i` returned 0, loaded `services.exe` with `userenv.dll`, and left three nonempty registry files, but the `sc.exe query` invocation returned native subprocess exit 127, its retained query log was 0 bytes, and no `sc.exe` PE mapping or SCM response was proven. V9 scratch and logs are immutable preserved evidence.

**V10 does not retry V9 and does not query the SCM.** It isolates whether the APK-owned native Wine loader can still run and whether the verified Windows ARM64 `sc.exe` executable can at least enter its no-argument usage path.

## On-device one-shot (only after separately consenting inside a verified signed APK)

- The live System action is **Test Wine29 v10 sc.exe PE entry (one-shot)**. The V9 one-shot control and completed V9 read-only audit are archived in code and not shown.
- Verify the same immutable 34-DLL and 111-file sealed PE/NLS, three native Wine29 v6 ELF hashes, v7 services.exe, v8 userenv.dll and v9 source-built ARM64 sc.exe **BEFORE creating any V10 scratch**. No new source-binary cohort is claimed.
- Allocate **one fresh** `com.charoitx/no_backup/charoite-next-wine29-entry-v10`. If that path already exists, fail closed. Older scratch, stable `com.charoite`, games, saves, prefixes and rootfs must not be read, changed, cleaned or retried.
- In fresh V10 only, seed private C: mapping, run a bounded foreground wineserver and Wineboot `-i` (internal Wine helpers may execute). Do not claim C: creation from preseeded paths or full prefix readiness from Wineboot exit 0.
- Only if Wineboot succeeds and the same private server is alive, run bounded native `wine --version` (5-second wait; `v10-native-version.log`). If its result is not recognized, do **not** start the `sc.exe` check.
- Only if the native version gate passes and the server remains alive, invoke the source-verified `sc.exe` **with NO arguments** through the native loader. Use a 12-second deadline and 512-KiB output cap, log to `v10-sc-entry.log`. Its expected usage text, if present, is evidence that user-mode program code executed. A native exit code alone is not PE-entry proof. **No `sc.exe query`, SCM calls, games, Windows applications, Steam, Battle.net or graphics tests.**
- Foreground native/server processes have bounded cleanup; V10 scratch and logs are **retained and never retried**. Private paths and raw log text are omitted from the bounded report ending in `END OF SHORT V10 ENTRY REPORT`.

## Interpretation of possible outcomes

| Observed evidence | Allowed conclusion |
|---|---|
| Wineboot exit 0 + registry files present | Isolated bootstrap progressed; SCM not verified |
| Native `--version` failed | Native loader/environment gate failed; Windows `sc.exe` not attempted |
| Native `--version` passed, `sc.exe` exited 127 without output | Stronger focus on Windows PE-launch boundary; root cause still unproven |
| `sc.exe` produced usage output | Strong indication `sc.exe` entry executed; **not** an SCM response |
| Service status from `sc.exe query` | **Cannot occur in authorized V10 test** |

Source: [V10 Java one-shot](../next-generation/CharoiteWine29V10EntryProbe.java), [V10 consent UI](../next-generation/prepare_next.py), [V10 source-only regression](../next-generation/tests/test_wine29_v10_entry_contract.py). Corresponding old V9 evidence and consent history: [V9 postmortem](WINE29_V9_EXIT127_V10_DESIGN.md).

## Consent and preservation

Installing/building V10 does **not** authorize any phone process. The user must independently press and authorize the single live V10 System action. Do not uninstall or clear experimental `com.charoitx`; stable Portal `com.charoite` and user data remain untouched. If an action has already been run once in V10 scratch, stop and perform only read-only forensics in a future release.
