"""Automation milestone contract. Existing Wine scratch remains read-only."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
AUTO = (ROOT/"CharoiteNextAutoReports.java").read_text()
PREP = (ROOT/"prepare_next.py").read_text()
WF = (ROOT.parent/".github/workflows/charoite-next.yml").read_text()
RUNTIME = (ROOT/"CharoiteNextRuntime.java").read_text()

class AutomatedDiagnosticReportingContract(unittest.TestCase):
    def test_deliberate_opt_in_and_device_bound_credential(self):
        for item in ('private static final String ENABLED', 'putBoolean(ENABLED, true)',
                     'getBoolean(ENABLED, false)', 'getSharedPreferences',
                     'AndroidKeyStore', 'AES/GCM/NoPadding', 'GCMParameterSpec',
                     'KeyProperties.PURPOSE_ENCRYPT', 'remove(TOKEN)', 'JobScheduler',
                     'setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)', 'setPeriodic(PERIOD_MS)',
                     'setPersisted(false)', 'if (!enabled(ctx)) return',
                     'Last result:', 'showSettings(Activity activity)'):
            self.assertIn(item, AUTO)
        self.assertNotIn('github_pat_', AUTO.replace('github_pat_[A-Za-z0-9_]{30,}', ''))
        self.assertNotIn('setInstanceFollowRedirects(true)', AUTO)
    def test_fixed_public_endpoint_allowlist_data_and_no_running_wine(self):
        for item in ('https://api.github.com/repos/rgarn023/CharoitePortal/issues',
                     'getNoBackupFilesDir()', 'v9-wine-pe-help.log',
                     'v9-foreground-wineserver.log', 'sanitizedReport(Context ctx)',
                     'get_new_process_info() = 0 { success=0, exit_code=1 }',
                     'pe_kernel32_missing', 'server_no_such_file',
                     'reportId', 'LAST_ACK', 'setConnectTimeout(12000)',
                     'setReadTimeout(12000)', 'setFixedLengthStreamingMode'):
            if item == 'reportId':
                self.assertIn('String reportId = id(report)', AUTO)
            else:
                self.assertIn(item, AUTO)
        for forbidden in ('ProcessBuilder(', 'Runtime.getRuntime()', '.exec(',
                          '.delete(', '.mkdir(', '.mkdirs(', 'FileOutputStream(',
                          'registry', 'getFilesDir()', 'com.touhoudr', 'readLine('):
            self.assertNotIn(forbidden, AUTO)
        self.assertIn('JSONObject issue = new JSONObject()', AUTO)
        self.assertIn('status != 201', AUTO)
        self.assertIn('connection', AUTO.lower().replace('httpurlconnection', 'connection'))
    def test_manifest_ui_version_and_attribution(self):
        for item in ('"CharoiteNextAutoReports.java"', 'CharoiteNextAutoReports.showSettings(this)',
                     'CharoiteNextAutoReports.schedule(this)', 'JobService',
                     'android.permission.BIND_JOB_SERVICE',
                     'Automatic phone diagnostics (GitHub opt-in)',
                     'versionCode 85', '11.2-next.0.54'):
            if item == 'JobService':
                self.assertIn('CharoiteNextAutoReports$UploadJob', PREP)
            else:
                self.assertIn(item, PREP)
        self.assertIn('0.54 (opt-in auto phone diagnostics', RUNTIME)
        self.assertIn("versionCode='85' versionName='11.2-next.0.54'", WF)
        self.assertIn('cp next-generation/CharoiteNextAutoReports.java legal-bundle/CharoiteNextAutoReports.java', WF)

if __name__=="__main__":
    unittest.main()
