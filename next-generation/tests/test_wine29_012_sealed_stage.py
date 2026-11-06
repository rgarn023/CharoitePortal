"""Source-only safety regression for separate Wine29 .0.12 111-file phone stage."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "CharoiteWine29Sealed012Stage.java"
PACK = ROOT / "stage_wine29_sealed012.py"
PREPARE = ROOT / "prepare_next.py"
PRIOR = ROOT / "CharoiteWine29Native07Stage.java"

class Wine29Sealed012Contracts(unittest.TestCase):
    def test_isolated_staging_opt_in_only(self):
        stage = STAGE.read_text()
        prepare = PREPARE.read_text()
        self.assertIn('private static final String ROOT = "charoite-next-wine29-012-sealed-pe-nls";', stage)
        self.assertIn('private static final String FINAL = "wine10-arm64ec-dependencies-0.12-sealed-pe-nls";', stage)
        self.assertIn('private static final long SOURCE_RUN = 41947164001L;', stage)
        self.assertIn('private static final long SOURCE_ARTIFACT = 13378882549L;', stage)
        for expected in ('index.getInt("module_count") != 111',
                         'index.getInt("pe_count") != 35',
                         'index.getInt("nls_count") != 76',
                         'index.getBoolean("native_elf_in_sealed_data")',
                         'verifyAssets(context, entries);',
                         'verifyClosedInventory(slot, entries);',
                         'verifyRootContents(root);',
                         'new FileOutputStream(target)',
                         'if (!pending.renameTo(complete))'):
            self.assertIn(expected, stage)
        self.assertIn('new android.app.AlertDialog.Builder(this)', prepare)
        self.assertIn('setPositiveButton("Stage new DATA only"', prepare)
        self.assertIn('CharoiteWine29Sealed012Stage.run(this)', prepare)
        self.assertIn('CharoiteWine29Sealed012Stage.verifyOnly(this)', prepare)
        self.assertIn('versionName "11.2-next.0.71"', prepare)
        self.assertIn('versionCode 102', prepare)
        for forbidden in ("ProcessBuilder", "Runtime.getRuntime", ".delete(", "rm -rf", "getFilesDir()", "WINEPREFIX="):
            self.assertNotIn(forbidden, stage)
        self.assertNotIn("CharoiteWine29Sealed012Stage", PRIOR.read_text())

    def test_static_pinning_and_no_unsafe_writes(self):
        script = PACK.read_text()
        for token in (
            'ARCHIVE_SHA = "ada8bd980722deba16e89231652a25a27a7e197a7638abc9d38a61e0614e412e"',
            'SOURCE_RUN = 41947164001',
            'SOURCE_ARTIFACT = 13378882549',
            'len(expected) != 111',
            'len(allnames) != 112',
            'source_archive_sha256',
            'native_elf_files_in_bundle',
            'regular_unbundled_import_names',
            'asset_folder',
        ):
            if token == "asset_folder": continue
            self.assertIn(token, script)
        for forbidden in ("subprocess.", "os.system(", "Popen(", "unlink(", "rmtree(", "rm -rf", "adb install"):
            self.assertNotIn(forbidden, script)

    def test_source_generation_present(self):
        spec=importlib.util.spec_from_file_location("wine29_sealed012_stage", PACK)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ROOT, "charoite-next/wine29-sealed012")
        self.assertEqual(module.MAX_TOTAL, 128 * 1024 * 1024)
        with self.assertRaises((ValueError, FileNotFoundError)):
            module.validate_archive(Path("/file/that/does/not/exist.tar.gz"))

if __name__ == "__main__":
    unittest.main()
