"""V28 one-shot permanently consumed: scoped, bounded historical classification only."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
C=(ROOT/"CharoiteWine29V28ScopedTriage.java").read_text()
R=(ROOT/"CharoiteWine29V28PreservedReadOnly.java").read_text()
P=(ROOT/"prepare_next.py").read_text()
W=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
J=(ROOT/"tests/CharoiteWine29V28ScopedTriageHarness.java").read_text()

class ScopedTriageOnly(unittest.TestCase):
    def test_no_new_evidence_scope_or_execution(self):
        for required in (
            "CharoiteWine29V28ScopedTriage.appendMarkers(b,scm,helper);",
            "readIfSafe(scratch,LOGS[i],LIMITS[i],b)",
            'readIfSafe(prefix,"system.reg",1048576,b)',
            "Os.lstat(", "OsConstants.S_ISREG", "Ask", # replaced below
        ):
            if required=="Ask":continue
            self.assertIn(required,R)
        self.assertIn("Authorize bounded READ ONLY",R)
        self.assertIn("Cancel — no file access",R)
        self.assertIn("262144, 2097152, 4194304, 2097152",R)
        for unsafe in ("ProcessBuilder(", ".exec(", "FileOutputStream(",
                       ".mkdir(", ".mkdirs(", ".delete(", ".renameTo(",
                       "Runtime.getRuntime()", "HttpURLConnection",
                       "getSharedPreferences(", "getAssets().open("):
            self.assertNotIn(unsafe,R)
            self.assertNotIn(unsafe,C)
        for old in ("charoite-next-wine29-entry-v27",
                    "charoite-next-wine29-entry-v25"):
            self.assertNotIn(old,R)
            self.assertNotIn(old,C)

    def test_precise_scm_state_and_allowlisted_setupapi(self):
        for required in (
            "Pattern.compile(", "service_name", "Matcher state=STATE.matcher(line)",
            "headers==1 && rows==1 && validLabel",
            '"STOPPED", "START_PENDING", "STOP_PENDING", "RUNNING"',
            'classifyScm(out,scm)', 'classifySetupApi(out,helper)',
            '"err:setupapi:"', "unclassified error line count",
            "historical", # code writes HISTORICAL uppercase, check below
        ):
            if required=="historical":continue
            self.assertIn(required,C)
        self.assertIn("HISTORICAL, never a live-service check",C)
        self.assertIn("appendRegistryStart(StringBuilder out, String registry)",C)
        self.assertIn("WIN32_EXIT_CODE class",C)
        self.assertIn("failed to query value",C)
        self.assertIn("failed to set value",C)
        self.assertIn("could not create key",C)
        self.assertIn("CharoiteWine29V28ScopedTriage.appendRegistryStart(b,registry)",R)
        self.assertIn("RpcSs registry Start mode: DEMAND_START",J)
        self.assertIn("WIN32_EXIT_CODE class: SERVICE_NEVER_STARTED",J)
        self.assertNotIn("out.append(line)",C)
        self.assertNotIn("out.append(helper)",C)
        self.assertNotIn("out.append(scm)",C)
        self.assertNotIn("file.getAbsolutePath()",C)
        self.assertIn("scoped STATE: RUNNING",J)
        self.assertIn("scoped STATE: STOPPED",J)
        self.assertIn("scoped STATE: UNKNOWN / AMBIGUOUS",J)
        self.assertIn("secret.txt",J)
        self.assertIn('lacks(running,"secret.txt")',J)
        self.assertIn("V28_SCOPED_SCM_STATE_AND_SETUPAPI_SYNTHETIC_JAVA_GATE=PASS",J)

    def test_generated_ui_consent_string_literals_are_closed(self):
        self.assertIn('+ "contents are shared; no games, older "',P)
        self.assertIn('+"values, paths or identifiers. No Wine, no other generation, "',R)

    def test_ci_and_app_identity_stay_isolated(self):
        for value in (
            "versionCode 157", "11.2-next.0.126",
            '"CharoiteWine29V28ScopedTriage.java"',
            "Review V28 SCM state + SetupAPI (READ ONLY)",
            "showArchivedWine29V28Execution = false"
        ):self.assertIn(value,P)
        for value in (
            "charoite-next-vc157",
            "versionCode='157' versionName='11.2-next.0.126'",
            "CharoiteWine29V28ScopedTriage.java legal-bundle/",
            "CharoiteWine29V28ScopedTriageHarness.java",
            "V28_SCOPED_HISTORICAL_SERVICE_STATE_AND_SETUPAPI_SOURCE_GATE=PASS",
            "NEXT_STABLE_PORTAL_RELEASE_UNCHANGED=PASS"
        ):self.assertIn(value,W)

if __name__=="__main__":unittest.main()
