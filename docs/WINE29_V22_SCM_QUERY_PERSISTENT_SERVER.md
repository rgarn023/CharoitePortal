[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V22 — isolated persistent-server ARM64 sc.exe query RpcSs

**SIGNED V22 APK VERIFIED — OWNER PHONE V22 EXECUTION NOT ATTEMPTED.** Experimental `com.charoitx`, versionCode **145**, versionName **11.2-next.0.114**. [**Successful GitHub Actions run 42546439374**](https://github.com/rgarn023/CharoitePortal/actions/runs/42546439374), exact signed-APK [**source commit 9cc720d**](https://github.com/rgarn023/CharoitePortal/commit/9cc720d4219b04d37d18df9dff8208c84cbd283f), [**direct signed APK artifact 13644080090**](https://github.com/rgarn023/CharoitePortal/actions/runs/42546439374/artifacts/13644080090) (461,557,742 ZIP bytes, SHA-256 `c27f5aa7f57a3ac0b50298cd7b2d27b20c6afa4d54cf56d3319c53b75f83e9af`, expires 2027-02-07T01:36:20Z); [**source and LGPL artifact 13643591787**](https://github.com/rgarn023/CharoitePortal/actions/runs/42546439374/artifacts/13643591787). Gradle build, **273 Next tests**, V22 one-shot/consent source gate, package metadata and original experimental APK signer continuity **PASS**. CI did not run Wine on phone.

## V21 evidence motivating V22

On November 8, 2026 the owner reported one source-verified direct Wineboot `-i` **exit 0**, followed by **one independent Wineboot `--help` exit 0 with nonempty output**, while the persistent private wineserver remained alive. No observed `c0000135`, missing builtin, or child exec errno marker. After intentionally stopping V21's private server, registry file-size metadata were **1,981 / 1,858 / 123 bytes**; contents and completeness are UNVERIFIED. V21 is PERMANENTLY CONSUMED. Do not rerun, read without separate scope, delete, clean, or repurpose its scratch or logs. No SCM ran in V21.

## Exact V22 one-shot on-device scope

1. After separate explicit **one-shot consent**, verify the pinned 34 hybrid DLL imports, 111 PE/NLS assets, source-built ARM64 Wineboot/services/sc and ARM64X userenv, and three original APK-native V6 ELF hashes BEFORE creating scratch. Refuse if the V22 scratch directory already exists.
2. Create **only new V22** private scratch under experimental `com.charoitx` no-backup storage, new private C: symlink and HOME/TMP, stage verified files, launch private `wineserver -f -d -p` and confirm socket+lock. Never access Wine29 V1–V21, Wine28, stable Portal, games, saves, user prefixes, original rootfs or network.
3. Execute exactly one direct ARM64 Wineboot `-i` (45 s, 2 MiB), with Wine's own internal services allowed. Only if exit 0, correct C: mapping and Wine-created Windows folders, no observed child-creation failure and server alive, invoke **one independent source-verified ARM64 `sc.exe query RpcSs`** (20 s, 2 MiB). Never run separate Wineboot --help, other sc.exe/SCM commands, service mutation, installers or games.
4. Report completion, exact native exit, bounded output presence, recognizable RpcSs service name and state, errors 1060/1722, DLL-load/exec markers and before/after server liveness. Exit 0 alone is insufficient evidence of a successful service status query. Keep raw logs and paths private.
5. Intentionally finalize only V22-owned processes. Record registry file presence before finalization and name/size metadata after; never read contents. Keep V22 scratch/logs FOREVER, including on errors, without retry, reset, deletion or cleanup.

**Interpretation:** A recognizable RpcSs service status and persistent server establish at most a narrow independent SCM query, NOT general service readiness, registry completeness, Windows app support or gaming. Any failure requires a separately scoped read-only V22 postmortem.

## System action — paired warnings and controls

Download the [**verified v0.114 signed APK artifact 13644080090**](https://github.com/rgarn023/CharoitePortal/actions/runs/42546439374/artifacts/13644080090), extract APK from ZIP, and install **in place** over experimental `com.charoitx` (never uninstall or clear storage). Under **System → CURRENT WINE29 ACTION — V22 INDEPENDENT SC.EXE RPCSS QUERY**, warnings accompany **Test Wine29 v22 SCM query (one-shot)** and **Open current project handoff**. Tap Test and separately choose **Authorize ONE fresh v22 test** or **Cancel — do not execute**. Afterwards select **Copy short report**; paste COMPLETE text beginning **Handoff** and ending **END OF SHORT V22 SCM QUERY REPORT**.

**Charoite 1.0 readiness: ~30% complete / ~70% remaining**, unchanged until phone SCM and later app/game milestones.
