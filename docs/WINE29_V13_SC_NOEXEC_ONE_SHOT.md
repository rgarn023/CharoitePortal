# Charoite Next — Wine29 V13 scoped noexec sc.exe entry

## New evidence: November 8, 2026 V12 read-only postmortem
Owner's V12 read-only report (signed v0.98) documents PE trace **606,645 bytes / 3,954 lines**, server trace **488,277 bytes / 5,143 lines**. Wineboot mapped in PIDs 0024 and 002c, services.exe and userenv.dll mapped in PID 0034, six PE exit events all zero, and no observed DLL-not-found or module failures. Three post-shutdown registries exist: system.reg 1,981 bytes; user.reg 1,858; userdef.reg 123 (metadata only; integrity unverified). The sc.exe entry log has **zero bytes**; no sc.exe process request or PE mapping appears in the bounded PE/server traces. V12's source report records one no-argument sc.exe attempt **exit 127** while foreground server stayed alive before and after. These are owner-supplied observations; raw logs remain on phone. **sc.exe entry and SCM readiness are NOT verified.**

## Targeted V13 hypothesis
V12 passed `WINELOADERNOEXEC=1` to both Wineboot and a separate direct native loader invocation for `sc.exe`. Earlier V11's **native --version** comparison reported exit 127 with this variable and exit 0 when unset. That contrast suggests an exact experiment but does not diagnose the V12 failure (version-only is not a PE launch).

V13 changes precisely one launch variable: the final no-argument sc.exe `ProcessBuilder` **removes `WINELOADERNOEXEC`**, while Wineboot and foreground wineserver keep the prior setting. The existing source-built ARM64 sc.exe, services.exe, userenv.dll and 34 verified hybrid DLLs, 111 staged PE/NLS entries and three APK-native ELF hashes remain unchanged. Do not add more DLLs, new Wine code, or version probes to this comparison.

## Isolation, consent, success criteria
- Separate `com.charoitx` scratch `charoite-next-wine29-entry-v13`, **new private prefix only**. Refuse any existing V13 scratch and retain first-attempt data; never retry, delete, clean, overwrite or access V12 and older Wine29/Wine28 scratch.
- Source/hash preflight before creating a scratch. Bounded private server (socket + lock), Wineboot `-i` with possible internal Windows helpers, at most **one no-argument** ARM64 sc.exe PE-entry attempt when server remains live.
- **Explicit affirmative on-device authorization**, with Cancel; nothing starts at boot, installation, page visit or CI. No SCM query/start/stop, services operations, native version checks, games, installers, Steam, Battle.net or graphics.
- Only successful sc.exe PE mapping plus observable entrypoint evidence can clear the PE-entry gate; exit 0 alone, usage text alone, or module presence alone is not proof of SCM. Exit 127 again means investigate preserved V13 native/PE/server traces read-only; no retry.
- Stable Portal `com.charoite`, user prefixes, rootfs, games and saves untouched. Install any future verified APK **in place** only, never uninstall or clear app data.

## Verified signed v0.99 release — November 8, 2026

[GitHub Actions 42453554339](https://github.com/rgarn023/CharoitePortal/actions/runs/42453554339) completed **SUCCESS** at exact signed source `17223608ea0ea542f8aacebb1bdaad6ebd56b2e1`. **138 stable + 226 Next tests PASS**, V13 consent/NOEXEC isolation gate PASS, Gradle BUILD SUCCESSFUL. AAPT `com.charoitx`, versionCode **130**, versionName **11.2-next.0.99**; original Next signing fingerprint `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` **MATCH**.

- [Signed v0.99 APK Actions artifact 13607130952](https://github.com/rgarn023/CharoitePortal/actions/runs/42453554339/artifacts/13607130952): ZIP **461,560,825 bytes**, `sha256:fa5dd82de0b4a92b7eaca84bce552a6f979f10e01155275d305dbca528681f0c`; expires 2027-02-06T06:09:06Z.
- [Source/LGPL attribution artifact 13606562754](https://github.com/rgarn023/CharoitePortal/actions/runs/42453554339/artifacts/13606562754): ZIP 498,365 bytes, SHA-256 `710cc584cfe5ca5140335c3a1f627597c657006a36dace47c793b1aec088e83a`.
- **CI did not run Wine or Windows PE on phone**. Windows sc.exe mapping and SCM readiness remain UNVERIFIED.

Install **in place** over existing signed experimental `com.charoitx`; NEVER uninstall/clear storage or touch stable `com.charoite`. The System action **Test Wine29 v13 sc.exe loader handoff (one-shot)** is executable only after explicit affirmative consent; it is **not** a read-only audit. Copy complete bounded report through `END OF SHORT V13 ENTRY REPORT`. Never rerun if V13 scratch exists. Later forensic analysis should be read-only before any new-generation experiment.
