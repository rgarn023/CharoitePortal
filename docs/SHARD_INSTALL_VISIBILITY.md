# Shard of Dreams installation not appearing in Library

Confirmed official English Shard of Dreams manual:
https://thpp.supersanctuary.net/tpdp/manual/ynk/

The expansion is its own Windows installation, normally under
`C:\\game\\FocasLens\\幻想人形演舞-ユメノカケラ-`. Its playable
Windows executable is `enbu_ap.exe`, not the original `gn_enbu.exe`.
The installer must have reached Finish and written the executable.
The Wine `notkey` path workaround is **only** relevant when launching
the installed expansion; it cannot repair an absent Library tile.

## Corrected Core/Portal behavior

1. Returning to Charoite from an installer queues an automatic scan.
   If another operation is running, the scan is deferred until it finishes.
   A transient scan error does not consume the installer-scan flag.
2. Core scans the active environment's Wine `C:\\` for recognized game
   executables, including `enbu_ap.exe`, then merges them into its
   persistent library without replacing existing games or saves.
3. **Important bug fix:** Immediately refresh the visible Library after
   saving newly discovered entries. Previously the data could be
   registered while the on-screen Library remained unchanged.
4. When an expansion executable is found, Core records its path and
   the user is shown the Library screen.
5. If a Shard-labeled installation folder exists without the playable
   executable, Core explains that the installation may be incomplete.
   If nothing is found in the active Wine drive, Core reports that the
   executable has not been detected; do not falsely claim it installed.
6. Setup displays a **SHARD OF DREAMS INSTALLATION** status panel and
   **CHECK SHARD OF DREAMS** button to rescan safely. The detailed report
   also appears under View Last Launch Diagnostics as
   `SHARD OF DREAMS INSTALLATION CHECK`.

The scan is read-only; no Wine prefix, installation, save, patch,
DLL, or graphics configuration is deleted, overwritten or reset.
Original TPDP remains the verified DXVK 1.10.3 + Turnip profile.
Build success does not prove the expansion is present on the user's
phone. Physical-device inspection of the Shard installation report
will determine whether the installer completed.
