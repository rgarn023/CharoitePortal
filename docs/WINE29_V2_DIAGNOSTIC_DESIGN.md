# Wine29 v2: isolated kernel32 loader-diagnosis design (NOT enabled)

**Date:** November 6, 2026. **State:** design only; no new Wine, Wineboot,
wineserver, Windows PE, FEX, graphics or prefix execution authorized.

## Verified baseline

Wine29 .0.7 native ELFs and the .0.12 PE/NLS source data have passed their
respective immutable hash/staging gates. Preserved v1 on the Galaxy S26 Ultra
reached a mapped ARM64 Wineboot, mapped NTDLL and loaded API-set, but later
reported kernel32.dll status c0000135; Wineboot --help exited 53 and no valid
drive_c prefix appeared. The read-only 0.75 source call-site gate verifies
initial Wine29 NTDLL/API-set selectors and the ARM64 /aarch64-windows
WINEDLLPATH lookup rule. This does NOT explain why kernel32 failed.

## First use read-only v0.75 diagnostics

Use existing System → Inspect preserved Wine29 v1 kernel32 failure (read-only).
It reads only v1's two bounded logs and five named source-hash-verified PE
copies, and now reports focused find_dll_file/load_dll/import_dll counts and
small sanitized context windows around the last kernel32/c0000135 lines.

Do not assume that a missing mapping line proves a missing DLL. First classify
observed loader attempts, PE header/machine evidence, transitive dependencies
and nearby NTSTATUS values. Unknowns must remain explicitly unknown.

## Proposal for a *future*, separately authorized new scratch

- New unique versioned scratch under the experimental com.charoitx private
  noBackupFilesDir; refuse if it already exists. Never enter v1, Wine28,
  stable com.charoite or any game/rootfs/user prefix.
- Require explicit in-app consent naming exactly the one-shot Wine29 native
  loader, foreground wineserver and ARM64 Wineboot help probe. Warn that Wine
  may run internal --init only inside the new private test prefix.
- Verify each staged PE, NLS and native module by immutable source SHA-256,
  size and architecture before any process starts. Do not mix generations,
  rewrite the old source archive or silently fall back to older modules.
- Supply sealed WINEDLLPATH, native/PE/data selectors and private HOME,
  TMPDIR and WINEPREFIX only. Do not inherit unrelated environment variables.
- Capture bounded, redacted +module/+loaddll/+process/+seh and relevant native
  diagnostic output, including module search candidate, machine, attempted
  mapping, transitive importer and exact returned NTSTATUS where available.
  A more granular loader trace may require a newly compiled, separately
  verified native debug generation: do not assert it is already present.
- Bound process and output sizes; terminate only processes launched by the
  new opt-in scratch; retain the scratch and its logs after success or failure.
  Never automate cleanup, retries or a second execution.
- Categorize outcomes: path missing; wrong PE machine / ABI; dependency
  rejected; module mapped; Wineboot help marker; prefix initialized. Report
  unsupported/inconclusive whenever the recorded traces cannot prove a cause.

**Release gate:** No modern Wine29 runtime activation, module installer,
automatic selection, game launch, anti-cheat claims or migration follows
from a source audit, an ELF marker, or a version-only probe. Require successful
isolated Wineboot, a complete prefix, ordinary Windows app smoke tests and
end-to-end graphics/input/audio device tests plus a reversible Portal upgrade
plan before promoting experimental functionality.

See CURRENT_HANDOFF.md and WINE29_KERNEL32_LOADER_AUDIT.md.


## Verified bootstrap-mode distinction for future v2 (still design only)

Pinned [source-flow audit 42320572066](https://github.com/rgarn023/CharoitePortal/actions/runs/42320572066)
supports treating TWO outcomes separately: internal auto wineboot --init
(exit 1 despite its temporary WINEBOOTSTRAPMODE) and explicit wineboot --help
(kernel32 c0000135 after bootstrap mode restoration). A future separately
authorized test in a NEW scratch should record boolean bootstrap-mode
presence for both subprocesses, verify WINEDLLDIRn lookup candidates and
module mapping status, and distinguish missing path, ABI rejection and
transitive dependency failures. Log only bounded/redacted traces, never
raw environment or credentials. Replacing the production environment with
WINEBOOTSTRAPMODE=1 is NOT a general fix. Existing v1 scratch must remain
untouched. No new v2 test or process is authorized by this document.
