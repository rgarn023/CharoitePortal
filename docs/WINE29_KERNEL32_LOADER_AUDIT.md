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

**Next read-only CI step (not yet implemented):** inspect the exact
source-hash-verified Wine29 .0.7 loader, Unix ntdll and wineserver ELF
string tables for the effective Wine29/28 selector names and compare
against the isolated v1 environment before proposing a native-loader fix.
Do not change or rerun an existing phone scratch on this hypothesis.

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
