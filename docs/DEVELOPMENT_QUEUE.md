# Charoite Portal — Development Queue

**Scope:** experimental Wine29 source-only provider work on `main`. Updated 2026-11-12. Queue entries are priorities, not claims of completed tests.

| Priority | Task | State | Exit evidence / next action |
| --- | --- | --- | --- |
| P0 | Verify latest five-module workflow run(s) and `batch-import-closure.json` | **WAITING FOR EVIDENCE** | Retrieve actual run ID, job conclusion, artifact manifests and import table; investigate failures with logs; do not assume pass |
| P0 | Resolve candidate PE import dependencies | **IN PROGRESS** | Track `mouhid.sys`, `hidclass.sys`, `hidparse.sys`, `winehid.sys`, `winexinput.sys`; compare external imports to verified sealed module set; distinguish unresolved imports |
| P1 | Build `mscms.dll` with pinned LCMS2 dependencies | **NOT STARTED** | Pin dependency, verify license/build, ARM64 PE header and imports in source-only CI |
| P1 | Build `winebth.sys`, `winebus.sys`, `wineusb.sys` | **NOT STARTED** | Confirm Android/Bionic Unix companion availability and build closure; PE-only output is insufficient |
| P1 | Build bounded, automated provider-closure report | **IN PROGRESS** | Report per-module source hashes, PE machine, ordinary/delay imports, missing providers, native companions, provenance and explicit unverified runtime |
| P2 | Integrate fully verified modules into isolated NEW Wine29 scratch | **BLOCKED** | Requires full dependency closure and owner approval for new runtime/phone test |
| P2 | Validate Wine29 prefix bootstrap, RpcSs, and installer functionality | **BLOCKED** | Requires opt-in, fresh scratch only, controlled logs and non-destructive tests |
| P3 | Portal/Next integration, UX and gameplay regression | **BLOCKED** | Requires working runtime and owner-authorized device test |

## Known evidence (do not overstate)
- [Three-module CI run #43247190822](https://github.com/rgarn023/CharoitePortal/actions/runs/43247190822) **SUCCESS**; `mouhid.sys`, `hidclass.sys` and supporting `hidparse.sys` built/inspected as ARM64 PE. Two of eight original missing provider modules source-built; **0/8 full closure verified**.
- Five-module expansion [commit 1c33328](https://github.com/rgarn023/CharoitePortal/commit/1c333282a0b32acb0f1fc3cc937b7057ef590a44). Owner screenshot suggested workflow #13 success, but run/job/artifact evidence was not independently inspected.
- [Batch import report commit 6e07661](https://github.com/rgarn023/CharoitePortal/commit/6e076612d9d40f58d2848ab7644bb2a1e3f23ab9) and [Actions summary fix 7e131c2](https://github.com/rgarn023/CharoitePortal/commit/7e131c2001e2454d531792e3557a825698bc6096) **committed, not yet run-verified**.
- [Issue #7](https://github.com/rgarn023/CharoitePortal/issues/7) enumerates original eight: `mscms.dll`, `hidclass.sys`, `mouhid.sys`, `winebth.sys`, `winebus.sys`, `winehid.sys`, `wineusb.sys`, `winexinput.sys`. `hidparse.sys` is supporting dependency.

## Session discipline
- Work through multiple safe tasks per active ChatGPT session, then update this queue and [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md).
- No routine owner notifications; only ask for permission, access, APK installation, or testing when truly necessary.
- Avoid repeated source-only workflow commits merely to trigger a run. Diagnose failed runs before modifying CI.
- Never modify or access stable app data, user games/saves, consumed Wine29 generations or historical scratch.
