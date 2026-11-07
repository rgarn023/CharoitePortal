# Wine29 v3: source-verified matched PE directory test

State: Diagnostic source only until CI passes; **NO phone v3 execution has been authorized or performed**.

## Evidence from v2 (preserve as-is)
- v2 had fresh sealed PE/NLS/native hashes PASS and a running foreground wineserver.
- Initial Wine auto --init returned **exit 1**; exact earlier cause unknown.
- Explicit ARM64 Wineboot.exe --help mapped but failed loading kernel32.dll with **c0000135 / exit 53**.
- The v2 +file trace shows NtCreateFile attempting `.../runtime/lib/wine/arm64-windows/kernel32.dll` and returning **c0000034**, while the sealed kernel32 image is under `.../runtime/lib/wine/aarch64-windows/kernel32.dll`.
- C: fallback lookups returned c000003a in the incomplete prefix.
- v2's exact verified Windows PE machine COFF AA64 and module files being present do not establish module load compatibility.
- Separate failing --init and --help code paths must remain separate unknowns.

## Deliberately narrow v3 change
- Preserve v2 original source and scratch untouched; create a **brand new** `charoite-next-wine29-pe-dir-v3` only after explicit one-shot user consent in experimental `com.charoitx`.
- Use the identical sealed cohort: 34 PE DLLs, one source-verified ARM64 Wineboot.exe, 76 NLS, and three immutable APK native ELF checks. All preflights run before scratch creation.
- Copy the **exact same** source-hash-verified ARM64 Wineboot.exe to both scratch paths, as v2 did.
- Change **only the explicitly launched EXE path** from `arm64-windows/wineboot.exe` to `aarch64-windows/wineboot.exe`, colocated with source-verified `kernel32.dll`. Check canonical parents match.
- Preserve `WINEDLLPATH` as the private `runtime/lib/wine` root; DO NOT force `WINEBOOTSTRAPMODE` in the environment. Wine may still run internal --init in its new prefix.
- Collect bounded `+file,+module,+loaddll,+process,+seh,+server` traces; redact environment lines, scratch path, and long lines from copied output. Keep scratch and logs for offline read-only inspection.
- Do not auto-run the one-shot command; require the owner to consent separately inside System. Stop only processes spawned for the v3 test.
- No Wine prefix migration, Windows game launch, FEX, Proton, anti-cheat or graphics activation.

## Distinguish outcomes
1. **kernel32 from aarch64-windows is actually attempted:** confirms the explicit EXE location affected the candidate search. If still c0000135, use adjacent trace to distinguish path, loader rejection, or dependency.
2. **kernel32 maps and --help prints Usage:** explicit help-path progressed, **not** proof of valid automatic --init or working prefix.
3. **internal --init exits 1 again:** investigate separately; record missing drive_c and registry state only via explicitly scoped future read-only tools. Never assume the --help fix also repairs --init.
4. **no candidate marker:** inconclusive due to truncation/trace levels; do not guess.

The v1 and v2 original private scratch and stable Charoite Portal must remain untouched. A prior signed APK is not replaced by source changes until a new GitHub Actions APK and signature are verified.
