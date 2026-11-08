[**Current Charoite project handoff**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V17 preserved independent-control postmortem — strict read-only

V17 owner evidence: isolated Wineboot -i finished with native exit 0; folders were Wine-created after preseeded drive_c; early registry checks were false but post-shutdown registry file sizes were system.reg 1,981 B, user.reg 1,858 B, userdef.reg 123 B (metadata only). Foreground wineserver was alive before independent Wineboot --help. That verified native-loader ProcessBuilder.start returned a process, which exited 127 with **zero output** in approximately 202 ms. The foreground server was no longer alive after the control. The deliberate IllegalStateException guard then **skipped independent sc.exe**. No SCM, independent Wineboot PE mapping, server-death cause, or game support established.

## Precisely bounded audit

Only consumed private \`charoite-next-wine29-entry-v17\`, read only; fail if scratch absent. Four fixed V17 log files: \`v17-wine-direct-init.log\`, \`v17-independent-wineboot-help.log\`, \`v17-sc-entry.log\` (expected absent), and \`v17-foreground-wineserver.log\`. Maximum 8 MiB per log, 100,000 lines, 16,384 characters/line and 9,000 characters total output. Only explicitly named scratch-local path metadata are inspected. Relative C: mapping checked through lstat/readlink only; no symlink traversal, no registry file contents or parsing. No raw process log lines or paths copied to the short report.

**No Wine/Wineboot/sc.exe/services.exe/wineserver execution, ProcessBuilder, process creation, scratch creation, modifications, cleanup, retries, games, installers, SCM or other app access.** Wine29 V1–V16 scratch, Wine28, stable com.charoite, original rootfs, game/user prefixes and saves are outside scope. V17 is permanently consumed, even if inspection fails.

Under **System → CURRENT WINE29 ACTION — V17 PRESERVED READ-ONLY**, instructions sit alongside **Inspect Wine29 v17 control + server (read-only)** and **Open current project handoff**. Tap Inspect, then **Copy short report** and paste every line starting with Handoff through **END OF SHORT V17 READ-ONLY REPORT** into a new chat. This audit does not require execution consent. Previous V17 one-shot execution control is archived.

Experimental \`com.charoitx\` candidate versionCode **140**, versionName **11.2-next.0.109**. GitHub Actions tests, signing identity and a fresh signed artifact must be independently verified **before** installing the replacement APK in place. Never uninstall or clear storage. Readiness remains **~30% complete / 70% remaining** pending verified independent Windows PE startup, SCM, gameplay/graphics/audio/input and Portal/Core integration.
