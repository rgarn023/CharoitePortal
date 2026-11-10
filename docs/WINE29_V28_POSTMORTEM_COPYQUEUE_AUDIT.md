[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V28 — permanently consumed preserved postmortem and source-only copy-queue audit

## Observed bounded OWNER evidence (not a fresh phone test)

The owner supplied the complete fixed-marker V28 preserved read-only report. V28 was **not executed, retried, cleaned, written or reopened** during this investigation. V1–V27 and Wine28, stable Portal `com.charoite`, rootfs, games, user prefixes and saves were never accessed.

- The V28 foreground wineserver trace is **2,737,711 bytes**, above the unchanged 256-KiB read cap. Its contents and internal `--init`/RpcSs mentions remain **UNKNOWN**; do not enlarge the cap or read the file.
- The separately bounded Wineboot/helper/SCM logs are 1,009,446 / 1,800,949 / 66,175 bytes respectively. The historical helper reports InstallHinfSection, ARM64 DefaultInstall and RpcSs mentions; it has 16 `err:setupapi:` lines, of which a **file copy/rename category is true** and eight lines are unclassified.
- The bounded `system.reg` is 123,091 bytes and contains one exact RpcSs service root with ImagePath, Start and Type. The Start mode is **DEMAND_START**.
- The independent `sc.exe query RpcSs` identified exactly one RpcSs service block and one anchored `STATE : 1 STOPPED`. The Windows exit-code class remains **UNKNOWN/AMBIGUOUS**. This is **historical state only**; a query does not start RpcSs.
- No 1060, 1722 or kernel32-module error marker was reported by this scoped query. These negative markers do not prove a functional service, a completed INF copy queue, or Windows program compatibility.

## Verified pinned Wine 10 source mechanics

The exact Charoite upstream is [The412Banner/proton-wine commit c74acb09d](https://github.com/The412Banner/proton-wine/tree/c74acb09d51b447f5d5ac56c87608d3ec565a767), not an arbitrary host Wine version.

Its [`loader/wine.inf.in`](https://github.com/The412Banner/proton-wine/blob/c74acb09d51b447f5d5ac56c87608d3ec565a767/loader/wine.inf.in) has `[DefaultInstall.ntarm64]` with `CopyFiles=ColorFiles,EtcFiles,InfFiles,NlsFiles,SortFiles`. Its `[DefaultInstall.ntarm64.Services]` includes `AddService=RpcSs`, and `[RpcSsService]` defines `StartType=3`. The observed DEMAND_START registry DWORD therefore agrees with the pinned source. The historical STOPPED state alone **is not an error** for an on-demand service.

In pinned [`dlls/setupapi/queue.c`](https://github.com/The412Banner/proton-wine/blob/c74acb09d51b447f5d5ac56c87608d3ec565a767/dlls/setupapi/queue.c), default SetupAPI callback handlers log `copy error` or `rename error` and return `FILEOP_SKIP` for the affected file operation. This can leave an individual source file uncopied without necessarily aborting every other INF step. The V28 report's combined marker does **not** tell us whether the observed error was copy or rename, nor which error code/file was involved; no paths or raw log lines may be disclosed.

## New no-execution CI copy-queue coverage audit

The proposed (source-only) [`analysis/wine29_bootstrap/audit_inf_copyqueue.py`](https://github.com/rgarn023/CharoitePortal/blob/main/analysis/wine29_bootstrap/audit_inf_copyqueue.py) is designed to compare:

1. Previously produced **generated** Wine INF from successful source-only [run 42552476223](https://github.com/rgarn023/CharoitePortal/actions/runs/42552476223), pinned SHA-256 `5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a`;
2. The *immutable source-only* 111-file sealed PE/NLS archive from [run 41947164001](https://github.com/rgarn023/CharoitePortal/actions/runs/41947164001), pinned archive SHA-256 `ada8bd980722deba16e89231652a25a27a7e197a7638abc9d38a61e0614e412e`.

The audit inventories the five ARM64 `CopyFiles` sections, required NLS entries, and embedded-resource provider PE names. It computes coverage against ONLY the 34 DLL + 76 NLS sealed cohort; absent providers might be provided by other Wine mechanisms. It **must not** conclude a V28 file-copy root cause from a coverage gap.

The dedicated [source-audit workflow](https://github.com/rgarn023/CharoitePortal/blob/main/.github/workflows/wine29-v28-copyqueue-source-audit.yml) downloads only existing GitHub artifacts into a disposable CI workspace, verifies exact hashes, runs synthetic unit tests, produces a **source-only JSON report**, and uploads that as a GitHub artifact. It NEVER runs Wine, sc.exe, Windows PE, Gradle APK builds, or phone experiments; nor does it touch consumed V28 evidence.

## Next engineering decision

First inspect the verified static copy-queue coverage and any missing provider classes. If the sealed data omission makes a narrowly justified source-packaging correction possible, cross-build/verify source candidates without running Wine. Only after that should a separate **new V29 private-prefix test** be designed, and it must require explicit owner consent, distinct generation scratch, bounded logging and no prior generation accesses. Do not convert V28's preserved review button into a new execution button or conflate static source coverage with service-start proof.

**No new APK is necessary for this source-only audit.** Full service-start behavior, game compatibility and 1.0 completion remain unproven. The current 1.0 estimate remains **~30% complete**.
