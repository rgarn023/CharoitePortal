"""Fail-closed source contract for a future isolated Wine29 v6 native cohort."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "patch_v6_child_loader.py"
spec = importlib.util.spec_from_file_location("patch_v6_child_loader", MODULE)
patch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patch)

FIXTURE = '''
#include <sys/stat.h>
#include <stdlib.h>
static void init_paths( char *argv[] )
{
    wineloader = build_path( bin_dir, basename );
    asprintf( &env, "WINELOADER=%s", wineloader );
}
void __wine_main(void)
{
    if (!getenv( "WINELOADERNOEXEC" ))  /* first time around */
        return;
}
'''

class V6ChildLoaderSourceContract(unittest.TestCase):
    def test_one_source_anchor_and_android_only(self):
        out = patch.patch_text(FIXTURE)
        self.assertEqual(out.count(patch.MARKER), 1)
        self.assertEqual(out.count("#ifdef __ANDROID__"), 1)
        self.assertIn('wineloader = canonical;', out)
        self.assertIn('asprintf( &env, "WINELOADER=%s", wineloader );', out)
        self.assertIn("fatal_error(", out)
        self.assertEqual(out.replace(patch.ANDROID_SELECTOR, ""), FIXTURE)

    def test_no_fallback_to_wine_bindir_on_android(self):
        out = patch.patch_text(FIXTURE)
        selector = out.split("#ifdef __ANDROID__", 1)[1].split("#endif", 1)[0]
        self.assertNotIn("build_relative_path", selector)
        self.assertNotIn("build_path(", selector)
        self.assertNotIn("execv(", selector)
        self.assertIn('libcharoite_wine29_v6_loader.so', selector)
        self.assertIn('"/data/app/"', selector)
        self.assertIn('"/lib/arm64/"', selector)

    def test_requires_regular_executable_canonical_path(self):
        selector = patch.ANDROID_SELECTOR
        for required in ("lstat( candidate, &st )", "S_ISREG( st.st_mode )",
                         "S_IXUSR", "S_IXGRP", "S_IXOTH", "realpath( candidate, NULL )",
                         "strcmp( canonical, candidate )", "wineloader = canonical"):
            self.assertIn(required, selector)

    def test_missing_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            patch.patch_text(FIXTURE.replace(patch.ANCHOR, ""))

    def test_duplicate_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            patch.patch_text(FIXTURE + patch.ANCHOR)

    def test_missing_prerequisite_rejected(self):
        with self.assertRaisesRegex(ValueError, "prerequisite"):
            patch.patch_text(FIXTURE.replace('#include <sys/stat.h>', ""))

    def test_cannot_repatch_or_change_legacy_cohort(self):
        with self.assertRaisesRegex(ValueError, "repatch"):
            patch.patch_text(patch.patch_text(FIXTURE))
        self.assertNotIn("libcharoite_wine29_loader.so", patch.ANDROID_SELECTOR)
        self.assertNotIn("libcharoite_wine28_loader.so", patch.ANDROID_SELECTOR)
        self.assertIn("v6", patch.ANDROID_SELECTOR)

    def test_native_main_loads_only_own_v6_ntdll(self):
        main = '''
#include <stdlib.h>
static void *try_dlopen( const char *dir, const char *name ) { return 0; }
static void *load_ntdll( char *argv0 )
{
    void *handle = NULL;
    if (self && ((path = realpath_dirname( self ))))
        return NULL;
}
'''
        result = patch.patch_native_entry(main)
        self.assertEqual(result.count(patch.NTDLL_MARKER), 1)
        self.assertIn('libcharoite_wine29_v6_ntdll.so', result)
        selector = result.split('#if defined(__ANDROID__) && defined(__aarch64__)', 1)[1].split('#endif', 1)[0]
        self.assertIn('return handle;', selector)
        self.assertIn('exit(1)', selector)
        self.assertNotIn('libcharoite_wine29_ntdll.so', selector)
        self.assertNotIn('libcharoite_wine28_ntdll.so', selector)
        self.assertIn('lstat( native_dir, &st )', selector)
        self.assertIn('strcmp( canonical, native_dir )', selector)
        self.assertEqual(result.replace(patch.NATIVE_NTDLL_SELECTOR, ''), main)

    def test_main_native_selector_repatch_and_missing_anchor_fail(self):
        main = '''
#include <stdlib.h>
static void *try_dlopen( const char *dir, const char *name ) { return 0; }
static void *load_ntdll( char *argv0 )
{
    void *handle = NULL;
    if (self && ((path = realpath_dirname( self ))))
        return NULL;
}
'''
        with self.assertRaisesRegex(ValueError, 'repatch'):
            patch.patch_native_entry(patch.patch_native_entry(main))
        with self.assertRaisesRegex(ValueError, 'anchor'):
            patch.patch_native_entry(main.replace('static void *load_ntdll( char *argv0 )', ''))

    def test_v6_source_requires_own_pe_nls_namespace(self):
        self.assertIn('CHAROITE_WINE29_V6_PE_DIR', patch.stage.__code__.co_consts.__str__())
        self.assertIn('CHAROITE_WINE29_V6_DATA_DIR', patch.stage.__code__.co_consts.__str__())

    def test_git_blob_fails_on_tampering(self):
        self.assertNotEqual(patch.git_blob_sha(b"modified"), patch.RAW_LOADER_BLOB)
        self.assertEqual(len(patch.RAW_LOADER_BLOB), 40)

if __name__ == "__main__":
    unittest.main()
