[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V18 preserved idle-server postmortem — V19 strict read-only inspector

**Source candidate only until signed CI and artifact are verified.** Experimental \`com.charoitx\` candidate versionCode 142, versionName \`11.2-next.0.111\`. No phone Wine, PE, SCM or games execute in CI.

## Preserved V18 owner observation

V18 original pinned source/module preflight PASS; private wineserver socket/lock observed; direct Wineboot \`-i\` native exit 0, private C: mapping preseeded, Windows/users folders created by Wine. Registry checks immediately after \`-i\` were false; retained metadata after finalization shows \`system.reg\` 1,981 bytes, \`user.reg\` 1,858 bytes, \`userdef.reg\` 123 bytes; registry contents, consistency and completeness unverified. The foreground wineserver was alive at idle +0 ms but absent by the nominal +1,000 ms checkpoint; process exit code 1 and the actual idle interval reported was about 200 ms. The Java \`waitFor(timeout)\` can return early when the process exits; the nominal checkpoint is **not evidence of surviving 1,000 ms**. Cause of exit remains unknown. No independent Wineboot --help, sc.exe, SCM or games attempted.

V18 is permanently consumed. No retry, deletion, cleanup or modification, even if a read-only inspection fails.

## Exact V19 read-only inspector scope

Only the existing private \`charoite-next-wine29-entry-v18\` scratch; fail closed when absent. Open **only two named logs** for bounded text inspection: \`v18-wine-direct-init.log\` and \`v18-foreground-wineserver.log\`. At most 8 MiB each, 100,000 lines, 16,384-character line handling and 9,000-character short report. Collect only process-ID and module-name sanitized event counts, PE exit markers, services/userenv/module failure/registry-save counts, server process/request/shutdown markers. Never paste raw paths, full log lines or private contents. Named path existence/type and registry **size only** are allowed; inspect \`dosdevices/c:\` via lstat/readlink without following it, and reject symlinked or escaped metadata paths. Never parse registry contents.

**No ProcessBuilder, Wineboot, Wine, sc.exe, services.exe, wineserver, native processes, scratch creation, writes, cleanup, deletion, network, independent PE startup, SCM or games.** No previous generation V1–V17, Wine28, stable Portal, original rootfs, game/user prefixes, or saves may be accessed.

In **System → CURRENT WINE29 ACTION — V18 PRESERVED READ-ONLY**, keep these instructions adjacent to **Inspect Wine29 v18 idle server (read-only)** and **Open current project handoff**. Tap Inspect and **Copy short report**; paste the complete report, starting with Handoff and ending with **END OF SHORT V18 READ-ONLY REPORT**, into a new conversation. Archive/hide the V18 one-shot execution button permanently.

Build/sign only in GitHub Actions, verify package \`com.charoitx\`, versionCode 142, versionName \`11.2-next.0.111\`, original experimental signing certificate and direct Actions artifact before installing **in place**. Never uninstall or clear experimental app data. The stable Portal remains untouched.

**Charoite 1.0: approximately 30% complete / 70% remaining.** Do not count the read-only inspector as independent Windows PE entry, SCM, gameplay, graphics/audio/input or Portal/Core integration.
