"""Static source-only INF CopyFiles coverage analysis, no Wine/device actions."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "analysis/wine29_bootstrap/audit_inf_copyqueue.py"
SPEC = importlib.util.spec_from_file_location("charoite_copyqueue_audit", SCRIPT)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)

NLS = {"data/nls/c_%03d.nls" % i for i in range(74)}
NLS.add("data/nls/locale.nls")
NLS.add("data/nls/sortdefault.nls")
PE = {"data/pe/arm64ec/x%02d.dll" % i for i in range(34)}
SEALED = PE | NLS | {"data/pe/arm64/wineboot.exe"}
INF = """[DefaultInstall.ntarm64]
CopyFiles=ColorFiles,EtcFiles,InfFiles,NlsFiles,SortFiles
[DefaultInstall.ntarm64.Services]
AddService=RpcSs,0,RpcSsService
[ColorFiles]
srgb.icm,"@%11%\\mscms.dll,-1"
[EtcFiles]
hosts,"@%11%\\ws2_32.dll,-1"
[InfFiles]
input.inf,"@%12%\\hidclass.sys,-1"
[NlsFiles]
c_000.nls
c_001.nls
[SortFiles]
sortdefault.nls
"""

class CopyQueueAudit(unittest.TestCase):
    def test_source_copy_sections_and_coverage_only_not_runtime_result(self):
        report = A.audit(INF, SEALED)
        self.assertEqual(report["copyfile_rows"], 6)
        self.assertEqual(report["requested_nls_not_in_sealed"], [])
        self.assertEqual(report["resource_providers_not_in_sealed_pe"],
                         ["hidclass.sys", "mscms.dll", "ws2_32.dll"])
        self.assertTrue(report["rpcss_registration_declared"])
        self.assertFalse(report["wine_executed"])
        self.assertFalse(report["v28_reused"])
        self.assertIn("neither absence", report["interpretation"])

    def test_excludes_resource_provider_already_in_sealed_cohort(self):
        updated = set(SEALED)
        updated.remove("data/pe/arm64ec/x00.dll")
        updated.add("data/pe/arm64ec/ws2_32.dll")
        report = A.audit(INF, updated)
        self.assertEqual(report["resource_providers_in_sealed_pe"], ["ws2_32.dll"])
        self.assertNotIn("ws2_32.dll", report["resource_providers_not_in_sealed_pe"])

    def test_fails_closed_on_missing_sections_ambiguous_copies_or_bad_registry(self):
        for bad in (
            INF.replace("AddService=RpcSs", "AddService=Other"),
            INF.replace("CopyFiles=ColorFiles,EtcFiles,InfFiles,NlsFiles,SortFiles",
                        "CopyFiles=ColorFiles"),
            INF + "\n[ColorFiles]\nother\n",
            INF.replace("CopyFiles=ColorFiles,EtcFiles,InfFiles,NlsFiles,SortFiles",
                        "CopyFiles=ColorFiles,EtcFiles,InfFiles,NlsFiles,SortFiles\nCopyFiles=ColorFiles"),
            INF.replace("hosts,\"@%11%\\ws2_32.dll,-1\"", "hosts,unknown"),
        ):
            with self.subTest(bad=bad[:42]):
                with self.assertRaises(ValueError):
                    A.audit(bad, SEALED)

    def test_rejects_partial_or_expanded_staged_archive(self):
        with self.assertRaises(ValueError):
            A.audit(INF, set(list(SEALED)[:110]))

    def test_source_only_workflow_contract(self):
        workflow = (ROOT / ".github/workflows/wine29-v28-copyqueue-source-audit.yml").read_text()
        for required in (
            "workflow_dispatch:", "41947164001", "42552476223",
            "ada8bd980722deba16e89231652a25a27a7e197a7638abc9d38a61e0614e412e",
            "5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a",
            "audit_inf_copyqueue.py", "actions/upload-artifact@v4"
        ):
            self.assertIn(required, workflow)
        for forbidden in ("adb shell", "wineboot -i", "wineserver -p",
                          "openai/codex", "OPENAI_API_KEY", "assembleDebug",
                          "gh release create", "charoite-next-wine29-entry-v28"):
            self.assertNotIn(forbidden, workflow)

if __name__ == "__main__":
    unittest.main()
