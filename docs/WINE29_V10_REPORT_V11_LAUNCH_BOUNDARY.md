# Charoite Next — V10 phone audit findings and V11 native-command gate design

Date: 2026-11-07. **Design and documentation only.** No V11 scratch, signed V11 APK, on-device process execution, Wine/SCM query, registry-content access, retry, or phone mutation is authorized by this note. The currently verified install remains signed Next **v0.94**, code 125 (`com.charoitx`). Do not uninstall or clear its storage.

## Evidence: owner's short preserved V10 audit

The owner supplied `END OF SHORT V10 READ-ONLY REPORT`. The audit read only four named V10 log paths and explicitly named metadata, preserving the prior V10 scratch. **Never rerun V10 execution.**

- Existing V10 prefix `dosdevices/c:` points via the expected relative symlink to preseeded `drive_c`, neither followed nor entered; Wine-created-looking Windows/system32/users/xuser/AppData folders are present but registry contents were not read.
- After shutdown, `system.reg` = **1,981 B**, `user.reg` = **1,858 B**, `userdef.reg` = **123 B**, all nonempty. These are metadata observations, **not** registry integrity or SCM readiness.
- PE trace **604,395 B / 3,936 lines**: Wineboot PIDs `0x0024` and `0x002c`, services PID `0x0034`. Services and userenv mapped in PID `0x0034`; no observed module errors/DLL_NOT_FOUND; six PE exit events all **0**. Traces establish PE bootstrap progress, **not** an operational SCM.
- Server trace **488,028 B / 5,145 lines**: one server start, two process requests and replies; no DLL_NOT_FOUND marker.
- V10 `v10-native-version.log` was **empty (0 B)**, and the earlier bounded `wine --version` subprocess returned **127**. The V10 `sc.exe` entry log is absent: **not attempted**.

## Newly identified source-level command gate mismatch

The archived `next-generation/CharoiteWine29V10EntryProbe.java` method `cleanEnv` unconditionally sets:

```java
env.put("WINELOADERNOEXEC", "1");
```

That same `cleanEnv` is applied to the separate `ProcessBuilder(loader.getAbsolutePath(), "--version")` request. Wine 10's `dlls/ntdll/unix/loader.c` is documented with a command-line condition equivalent to:

```c
if (!getenv("WINELOADERNOEXEC") || argc <= 1)
    check_command_line(argc, argv);
```

For `wine --version`, `argc == 2`; with `WINELOADERNOEXEC=1`, the ordinary command-line handler can therefore be skipped. This is a **source-supported hypothesis** for why V10's version gate did not print a version. It **does not** independently prove the mechanism of exit 127; exact pinned/patched v6 loader behaviour and Android runtime still require separate verification.

Relevant source references: [V10 ProcessBuilder and cleanEnv](../next-generation/CharoiteWine29V10EntryProbe.java); [Wine 10 NTDLL Unix loader source](https://fossies.org/linux/wine/dlls/ntdll/unix/loader.c); [upstream Wine pre-exec/command-line history](https://www.winehq.org/pipermail/wine-cvs/2020-May/144654.html).

## Recommended V11 — future separately authorized fresh-scratch diagnostic

**Phase A: source-only preparation and CI gates; safe now.**

1. Review the *exact pinned source and applied v6 patch*, including Wine `check_command_line`, `WINELOADERNOEXEC`, and any loader-reexec behaviour. Treat upstream snippets as supporting context, not exact patched-source proof.
2. Implement a **separate V11 class**, never call or change the consumed V10 runner. Verify the same sealed 34 DLL, 111 PE/NLS, native three ELF hashes, source-built services/userenv/sc bytes **before creating any V11 scratch**. Do not read scratch V1–V10.
3. Give native *version-only* probes a deliberately distinct environment: one control `--version` with the inherited NOEXEC switch, one `--version` with it **unset**, both bounded and independently logged. Do not silently strip it from PE execution, Wineboot or child-loader paths.
4. If separately authorized later, start exactly one new `charoite-next-wine29-...-v11` private wineserver/prefix and source-verified Wineboot `-i`. When the foreground server and Wineboot gates succeed, try **only** source-matched ARM64 `sc.exe` with **no arguments** for a PE-entry/usage handshake. **Do not gate that independent PE-entry attempt solely on `wine --version`**; the V10 gate was a suspect test artefact. No `query`, `start`, `stop`, `create`, SCM mutation, Windows installers, games or other apps.
5. Bound each invocation's time and byte output; retain separately named V11 logs on the device, correlate PE mapping/usage output/exit and server observations. A nonzero Windows usage exit is not itself a failure if PE mapping and expected usage are proven. No process exit code alone proves PE entry.
6. Hard-fail if the V11 scratch already exists; never delete, retry or clean it. No automatic execution on installation, boot, or update. A new System button must require a separate clear **one-shot consent dialog** and archive all older Wine29 active actions. Preserve stable Portal `com.charoite`, Wine28 and Wine29 v1–v10, rootfs, existing user prefixes, games, and saves.

**Phase B: only after CI and signing are verified.** Publish a new uniquely versioned signed `com.charoitx` APK artifact with exact Actions run, artifact, source SHA, signing fingerprint and passing tests; install **in place**; authorize one V11 phone test. A GitHub source commit or source-only CI run must not be described as a build-ready APK.

## Current conclusion

The V10 PE bootstrap is materially ahead of earlier kernel32/userenv failures. The immediate next question is **native command-line handling and independently reaching `sc.exe` PE entry**. SCM, full Wine prefix correctness, graphics and gaming remain **unproven**. Exit 127/zero bytes is not a root-cause diagnosis.

**END OF V10 EVIDENCE / V11 DESIGN NOTE**
