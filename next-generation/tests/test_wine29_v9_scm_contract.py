"""Source-built ARM64 sc.exe v9 must only run once in a NEW private prefix."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STAGE=(ROOT/"stage_wine29_v9_sc.py").read_text()
JAVA=(ROOT/"CharoiteWine29V9ScmProbe.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class Wine29V9Scm(unittest.TestCase):
    def test_source_pinned_and_deps_closed(self):
        for token in ("42426173638","311a141fa255886020c5e2adab643db0e954a07a",
            "13595845868","f8ac4ddbdca513a07ee15b29101b78203d07cd9094e65357e50b9709887e6c54",
            "wine29-v9-sc", "sc-arm64.exe.bin", "ordinary_imports", "unbundled_imports",
            "WINE29_V9_SC_SOURCE_PINNED_ASSET_SHA256=PASS",
            "prior_v8_userenv_unchanged"):
            with self.subTest(token=token):self.assertIn(token,STAGE)
        for denied in ("new ProcessBuilder","Runtime.getRuntime","/data/user/0/"):
            with self.subTest(denied=denied):self.assertNotIn(denied,STAGE)
    def test_new_scratch_and_explicit_native_query(self):
        for token in ("charoite-next-wine29-scm-v9","verifyV6Native(context);",
            "verifyV7Services(context);","verifyV8Userenv(context);","verifyV9Sc(context);",
            'scBuiltin=child(lib,"sc.exe")', "v9-sc-query.log",
            'scBuiltin.getAbsolutePath(),"query"', "serverProc.isAlive()",
            "source-built sc.exe query attempted", "V9 scratch retained",
            "END OF SHORT V9 SCM REPORT", "v9 server remains alive",
            "SCM functional readiness: NOT ESTABLISHED BY EXIT 0 ALONE"):
            with self.subTest(token=token):self.assertIn(token,JAVA)
        self.assertLess(JAVA.index("verifyV9Sc(context);"),JAVA.index("scratch = child(privateBase, SCRATCH);"))
        for denied in ("charoite-next-wine29-userenv-v8\";", "clearApplicationUserData(",
            ".delete(", "renameTo(", "Runtime.getRuntime("):
            with self.subTest(denied=denied):self.assertNotIn(denied,JAVA)
    def test_consent_ui_and_ci(self):
        for token in ("CharoiteWine29V9ScmProbe.java","showArchivedWine29V8ReadOnly = false;",
            "Test Wine29 v9 Service Manager query (one-shot)",
            "Authorize ONE v9 query","Cancel — do not execute",
            "CharoiteWine29V9ScmProbe.run(this)","nextCoreCard.addView(wine29V9Scm);",
            "versionCode 140","11.2-next.0.109"):
            with self.subTest(token=token):self.assertIn(token,UI)
        for token in ("stage_wine29_v9_sc.py", "test_wine29_v9_scm_contract.py",
            "WINE29_V9_SC_SOURCE_PINNED_APK_STAGE=PASS","WINE29_V9_SIGNED_APK_ARM64_SC_SOURCE_SHA256=PASS",
            "versionCode='140' versionName='11.2-next.0.109'"):
            with self.subTest(token=token):self.assertIn(token,WF)

if __name__=="__main__":unittest.main()
