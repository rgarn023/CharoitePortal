# Wine29 kernel32 startup failure: source-only loader-path audit

**November 6, 2026. No new Wine or PE execution performed by this audit.**

## Confirmed from preserved v1 S26 Ultra postmortem

- Source-verified Windows PE files include `kernel32.dll`,
  `kernelbase.dll`, `ntdll.dll`, `apisetschema.dll`, and ARM64
  `wineboot.exe`. The v1 scratch file presence and SHA-256 alone do not
  prove a module can be mapped or accepted by the Wine loader.
- Foreground wineserver socket/lock occurred. Native/PE startup reached
  a mapped ARM64 Wineboot, a mapped NTDLL, and loaded API-set schema.
- The internal auto-init Wineboot process failed; the explicit
  `wineboot.exe --help` exited 53 on `kernel32.dll` status
  `c0000135`. The prefix has registry files but lacks `drive_c`.
- No valid initialized prefix, working Wineboot, Windows app, graphics,
  FEX, Battle.net or Steam launch is proven.

## What source inspection adds

The isolated v1 Java probe explicitly set `WINEDLLPATH` to its fresh
`runtime/lib/wine` root, copied a source-verified `kernel32.dll` under
`runtime/lib/wine/aarch64-windows`, and used the ARM64
`arm64-windows/wineboot.exe`. Published Wine 10 loader source confirms that
ARM64 PE lookup uses the `/aarch64-windows` architecture suffix and searches
`WINEDLLPATH` roots. That is a consistency check, **not proof that the
specific Android-built native loader used or accepted this candidate**.

Reference (Wine 10 loader, contextual, not source-matched build proof):
https://sources.debian.org/src/wine/10.0~repack-12/dlls/ntdll/unix/loader.c

## New read-only evidence in v0.73

Existing `System → Inspect preserved Wine29 v1 kernel32 failure (read-only)`
now reports bounded PE32+ headers and raw COFF machines for the five named
v1 scratch copies *only after their immutable source SHA-256 matches*.
The header inspection reads a maximum of 4096 bytes per named PE file;
the existing bounded v1 logs additionally count explicit kernel32 PE mapping
markers. All paths and data sources remain the same. No file creation or
mutation and no process execution; no old prefixes or other scratch read.

If a header reports `AA64` that describes raw COFF machine bytes only.
It does **not** alone prove ARM64EC hybrid ABI compatibility, loader acceptance,
linking, symbol resolution or a valid memory mapping. An absent kernel32 map
marker is likewise not conclusive without a matching loader trace.

## Historical selector names need native-binary verification

A source-only review of the repository's generic Charoite Wine patches found
`CHAROITE_WINE28_PE_DIR` in the older `0900` (Windows ntdll) and `1000`
(API-set) patch files. The preserved Wine29 v1 Java test instead supplies
`CHAROITE_WINE29_PE_DIR`, `CHAROITE_WINE29_NATIVE_DIR` and
`CHAROITE_WINE29_DATA_DIR`.

**This is a versioned source-selector discrepancy to investigate, not a
demonstrated failure.** The source-matched Wine29 .0.7 native binaries are
independently built and bundled from a distinct 27-component archive; the
older patch text does not establish which selector literals are present in
the particular APK's verified native ELF files. Preserved phone evidence
also shows that ntdll PE mapped and the API-set schema loaded, so their
initial selector logic cannot simply be declared broken.

**Read-only CI audit implemented and verified (November 6, 2026):**
`next-generation/audit_wine29_07_selectors.py` runs in GitHub Actions
immediately after staging the exact Wine29 .0.7 source archive. The audit
rechecks each of the three APK-native AArch64 ELF file hashes against the
immutable same-source module index, then records literal Wine28/Wine29
selector marker presence for loader, Unix ntdll and wineserver in a bounded
JSON artifact. It compares marker coverage to the v1 Java environment names.

**Interpretation limit:** finding an ASCII selector string does not establish
that it is used at runtime, or how a DLL was searched/mapped; a missing string
also does not establish a kernel32 root cause. This is evidence gathering,
not an executable fix. No phone files, Wine process, PE, existing scratch or
user data are touched. Source code and contract tests are committed on `main`; the exact
source-matched audit and APK build both passed in run 42316771341.
The reported selector evidence below does not prove runtime readiness.

## Decision tree for the next investigation

1. Check whether the retained logs show an attempted kernel32 builtin lookup
   and what status that lookup returned; distinguish "not found" from
   "found but unsupported" or a transitive load failure.
2. Compare the new raw PE header metadata to the effective Wine process
   architecture; require exact same-source native and PE provenance.
3. If logs remain inconclusive, design a **separate opt-in new v2 scratch
   probe** with bounded module-search tracing and explicit data isolation.
   Its design must be reviewed before adding any execution button.
4. Do not rerun or erase v1 and do not alter `com.charoite` or user data.

**Current result: FAIL at kernel32 c0000135, root cause unresolved.**


## Source-matched Wine29 .0.7 ELF selector evidence (CI 42316771341)

The new CI audit step **PASSED** after independently rechecking the source
index and SHA-256 for all three exact Wine29 .0.7 APK native ELFs. The
[read-only JSON artifact](https://github.com/rgarn023/CharoitePortal/actions/runs/42316771341/artifacts/13550439347)
reports:

- `libcharoite_wine29_loader.so`, `libcharoite_wine29_ntdll.so`, and
  `libcharoite_wine29_wineserver.so` **all contain literal**
  `CHAROITE_WINE29_NATIVE_DIR`, `CHAROITE_WINE29_PE_DIR`, and
  `CHAROITE_WINE29_DATA_DIR`.
- All three ALSO contain old `CHAROITE_WINE28_NATIVE_DIR` and
  `CHAROITE_WINE28_PE_DIR` marker strings and a
  `Wine29/Wine28 selector conflict` message.
- `CHAROITE_WINE28_DATA_DIR` was not found in any of those three files.
  `WINEDLLPATH` was found in loader and ntdll, not wineserver.

**Interpretation:** The hypothesis that the Wine29 binaries completely
lack the Wine29 v1 environment selector names is **not supported** by the
observed byte strings. Shared strings or compatibility/error markers could
be present without active execution paths. Binary source match is proven;
whether the loader actually consumes a particular selector, resolves
transitive DLL dependencies, or rejects kernel32 remains **UNRESOLVED**.
Do not re-run failed v1 or enable new execution from this evidence.

Next analysis should inspect the exact source-matched Wine29 native selector
call sites, initialization order, dynamic architecture-search and the
retained v1 kernel32 mapping trace; only design new isolated v2 runtime
logging after an explicit authorization and a non-destructive review.


## Source-matched native call-site audit and focused v1 log triage (v0.75 development)

**Evidence and provenance:** the pinned Wine29 .0.7 archive (source run
41749167248, archive SHA-256
66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e)
contains source/charoite-wine29-native-source-delta.patch (SHA-256
f8122ad18663a0bedb5dde7983f6ebb690963ac1c87016fe3d4a1cdbc3061428).
A new CI audit checks these immutable hashes and the loader.c patch itself.
This is narrower and stronger evidence than simply finding selector strings
in compiled ELF files, but does not prove execution decisions.

In the patched dlls/ntdll/unix/loader.c, the function
charoite_wine29_selected_path() demands all three Wine29 paths when one is
specified and rejects older Wine28/27/26 selectors in the same source cohort.
load_ntdll() constructs the initial ntdll.dll location from the Wine29 PE
selector; load_apiset_dll() constructs the initial apisetschema.dll
location using that same selector. Other DLL lookup uses the general Wine
WINEDLLPATH search roots and the ARM64 /aarch64-windows suffix. These are
source-level call-site observations, not actual runtime path traces. The
preserved v1 log already shows NTDLL and API-set initial loading succeeded,
so the next unknown is the **subsequent ordinary kernel32 DLL resolution,
transitive imports or PE/ARM64EC rejection**, not merely whether a Wine29
selector marker exists.

The v0.75 experimental package (versionCode 106, signed CI VERIFIED in
run 42318373542) preserves the old v1 read-only System diagnostic button, adding
bounded adjacent log context around the last kernel32 and c0000135 mentions,
plus precise find_dll_file, load_dll, import_dll and mapping marker
counts. Existing log byte caps, source-hash PE gates and environment-field
redaction remain. No new Wineboot/Wine execution, scratch creation, prefix
mutation or test-button proliferation is authorized.

**Avoid inference leap:** a log with no kernel32 PE mapping marker cannot
alone distinguish missing file, bad machine/ABI, missing transitive
dependency, incorrect search scope or incomplete debug logging. On-device
evidence is still needed. See CURRENT_HANDOFF.md.


**Verified build update:** [GitHub Actions run 42318373542](https://github.com/rgarn023/CharoitePortal/actions/runs/42318373542) COMPLETED SUCCESS at source commit 697a8921d6372709948ee4cb53c8e7cbb372d6c3. Native call-site gate passed all six checks and published [artifact 13550689928](https://github.com/rgarn023/CharoitePortal/actions/runs/42318373542/artifacts/13550689928). Signed experimental v0.75 APK [artifact 13552056677](https://github.com/rgarn023/CharoitePortal/actions/runs/42318373542/artifacts/13552056677) passed 138 stable and 157 Next tests, Gradle, identity and signing checks. No Wine29 bootstrap rerun, no device test and no proven kernel32 root-cause fix.


## November 6 phone v0.75 report and verified source-flow hypothesis

The owner-provided preserved-v1 report confirms source-SHA-verified kernel32,
kernelbase, NTDLL, API-set and Wineboot PE files (all raw COFF AA64).
Wineboot and NTDLL mapped; API-set loaded; kernel32 was never recorded
as mapped. The prefix contains system.reg and user.reg but no drive_c.
Explicit Wineboot --help failed with c0000135. Automatic --init had already
failed separately (new_process exit 1). The server's two NO_SUCH_FILE lines
refer to alternative Wineboot locations; the correct scratch Wineboot
subsequently mapped, so those lines do not explain kernel32.

**Corrected reading of the trace:** The source-matched Wine 10 ntdll
startup deliberately invokes load_dll(NULL, kernel32.dll, ...).
Thus the trace text "looking for kernel32.dll in (null)" is NORMAL
caller behavior, not evidence that WINEDLLPATH is null.

**Exact source proof:** [Source-only CI 42320572066](https://github.com/rgarn023/CharoitePortal/actions/runs/42320572066)
completed SUCCESS; all 11 checks passed. The [JSON artifact
13552314392](https://github.com/rgarn023/CharoitePortal/actions/runs/42320572066/artifacts/13552314392)
verifies three pinned original Wine source Git blob identities, the exact
Wine29 .0.7 source archive and native patch hash, and original v1 Java
environment construction. Pinned Wine sets WINEBOOTSTRAPMODE for its internal
auto --init and restores the original mode before executing the separate
--help process. The original v1 Java cleanEnv() sets WINEDLLPATH, but does
not explicitly set WINEBOOTSTRAPMODE. In this Wine build,
find_builtin_without_file() limits the built-in DLL fallback outside
bootstrap mode. That is a plausible mechanism for the LATER --help
kernel32 failure when drive_c is absent.

**Unresolved:** The EARLIER internal --init process receives bootstrap
mode yet exited 1. Its original failure is not explained by the later
mode restoration. No root cause for that exit or proof of working Wineboot
or prefix exists. No new Wine execution, user-data access or APK build
occurred in this CI source audit.


## November 6, 2026 — v2 +file trace isolates a search-directory mismatch

Owner-provided signed Next v0.76 v2 one-shot report: sealed 111 PE/NLS, 3 native ELFs, and 34 hybrid DLL preflight PASS. wineserver socket/lock PASS. Automatic internal Wineboot --init again FAILED with return code 1. The later explicit ARM64 Wineboot.exe --help mapped the EXE and PE NTDLL, but terminated on kernel32.dll c0000135 (process exit 53). No usable prefix demonstrated; v1 and v2 scratch must be preserved.

The previously masked detail is now concrete: the explicit EXE was launched from the `runtime/lib/wine/arm64-windows/` scratch directory and `+file` recorded an exact failed file open of `arm64-windows/kernel32.dll` with `c0000034`, even though verified kernel32 was staged in `runtime/lib/wine/aarch64-windows/`. Subsequent Windows C: prefix searches failed with `c000003a`; there is not yet a complete drive_c. Thus the v2 explicit `--help` attempt did not map kernel32, and at least one crucial path search was directed to a different directory from its sealed module location. This proves a failed lookup, NOT an overall successful or failed ABI test, and does NOT explain the earlier internal automatic --init exit 1.

For Wine 10's native ARM64 builtin lookup, source `get_pe_dir(IMAGE_FILE_MACHINE_ARM64)` points to `/aarch64-windows`. The experimental v2 code already places a verified second Wineboot.exe copy beside the 34 PE DLLs under aarch64-windows, but the launcher used the *other* standalone copy under arm64-windows. That observed image directory is a plausible reason the explicit child process attempted kernel32 from arm64-windows. The next isolated v3 experiment should change ONLY the explicit Wineboot executable argument to the existing hash-verified aarch64-windows/wineboot.exe copy and trace the exact DLL candidate and result. It must NOT globalize WINEBOOTSTRAPMODE or reuse/modify v1 or v2 scratch. No claim that such a test alone initializes prefix, fixes Wineboot automatic --init, or enables games.

New code (not yet a verified signed release when first authored): `next-generation/CharoiteWine29V3LayoutProbe.java`, `next-generation/tests/test_wine29_v3_layout_contract.py`, versionName 11.2-next.0.77/versionCode 108, explicit on-phone manual authorization only. Existing stable Portal and game data untouched.
