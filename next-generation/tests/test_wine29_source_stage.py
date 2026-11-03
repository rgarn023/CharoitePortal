"""Wine29 27-source-cohort Android CI staging (DATA ONLY, no Wine execution)."""
from pathlib import Path
import importlib.util
import unittest
ROOT=Path(__file__).resolve().parents[1]
STAGE=(ROOT/"stage_wine29.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()
spec=importlib.util.spec_from_file_location("stage_wine29",ROOT/"stage_wine29.py")
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

class Wine29SourceStageContract(unittest.TestCase):
    def test_only_27_coherent_source_generation_and_existing_wine28_hashes(self):
        for item in ("41586391767","13208541305",
                     "wine10-arm64ec-bootstrap.0.6","wine-bootstrap-29.bundle",
                     "wine-bootstrap-28.bundle","ver.verify(archive)",
                     "ver.verify(old_archive)","source/charoite-source-delta.patch",
                     "verified isolated Wine28 API-set PE is absent or unreadable",
                     "api_set_namespace_version","api_set_sha256",
                     "module_count","native_elf_installed", "remaining_observed_pe_imports"):
            self.assertIn(item,STAGE)
        self.assertNotIn("ProcessBuilder(",STAGE)
        self.assertNotIn("subprocess.",STAGE)
        self.assertNotIn("Runtime.getRuntime(",STAGE)
        self.assertNotIn("rm -rf",STAGE)
        self.assertNotIn(".unlink(",STAGE)
        self.assertNotIn("shutil.rmtree(",STAGE)
        self.assertIn("Charoite-Wine-Coherent-Bootstrap-27-APISet-Experimental",WF)
        self.assertIn("stage_wine29.py",WF)

    def test_bad_cohort_or_forged_launch_readiness_refused(self):
        manifest={"version":"wine10-arm64ec-bootstrap.0.6",
                  "android_package":"com.charoitx","source_commit":M.SOURCE_SHA,
                  "component_count":27,"nls_count":76,
                  "launch_ready":True}
        previous={"version":"wine10-arm64ec-bootstrap.0.5","component_count":26}
        with self.assertRaisesRegex(ValueError,"source|runnable|verified"):
            M.index_for(manifest,{},b"source",previous,{"module_count":99})

if __name__=="__main__": unittest.main()
