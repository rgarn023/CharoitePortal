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

## Build gate
Source candidate `com.charoitx` **versionCode 130**, **11.2-next.0.99**; CI must PASS stable + Next tests, Android Gradle, AAPT identity, original experimental signing certificate SHA-256 `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175`, and verifiable Actions artifact. No v0.99 signed APK claimed until those checks complete. Latest verified signed v0.98 is [Actions 42452319230](https://github.com/rgarn023/CharoitePortal/actions/runs/42452319230), [artifact 13605744619](https://github.com/rgarn023/CharoitePortal/actions/runs/42452319230/artifacts/13605744619).
