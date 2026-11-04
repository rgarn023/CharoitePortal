"""Source-only tests for isolated Wine29 selectors. Never executes Wine."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "prepare-wine29-native.py"
spec = importlib.util.spec_from_file_location("wine29_source_prep", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def synthetic_pinned_sources():
    # Minimal representative source anchors after the frozen Wine28 patches.
    main = '''static void *load_ntdll( char *argv0 )
{
    const char *self = get_self_exe( argv0 );
    char *path, *p;
    void *handle = NULL;

    if (self && ((path = realpath_dirname( self ))))
        handle = try_dlopen( path, "ntdll.so" );
}
'''
    loader = '''static void init_paths( char *argv[] )
{
        if (getenv( "CHAROITE_WINE26_DATA_DIR" ))
        {
        }
}
static void load_apiset_dll(void)
{
    if (getenv( "CHAROITE_WINE28_PE_DIR" ))
    {
        status = open_unix_file( &handle, name );
    }
    if (status && getenv( "CHAROITE_WINE28_PE_DIR" ))
        fatal_error( "old apiset" );
}
static void load_ntdll_pe(void)
{
    if (getenv( "CHAROITE_WINE28_PE_DIR" ))
    {
        status = open_builtin_pe_file( name );
    }
    if (getenv( "CHAROITE_WINE28_PE_DIR" ) && status == STATUS_DLL_NOT_FOUND)
        fatal_error( "old ntdll" );
}
'''
    unicode = '''struct fd *load_intl_file(void)
{
    nls_dirs[0] = get_nls_dir();
    for (i = 0; i < ARRAY_SIZE( nls_dirs ); i++)
    {
    }
}
'''
    return {"loader/main.c": main,
            "dlls/ntdll/unix/loader.c": loader,
            "server/unicode.c": unicode}


class Wine29SourceIsolation(unittest.TestCase):
    def test_separate_generation_is_source_only(self):
        code = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('GENERATION = "wine10-arm64ec-bootstrap.0.7"', code)
        self.assertIn('charoite-wine29-native-source-delta.patch', code)
        self.assertIn("charoite-source-validation.txt", code)
        self.assertIn("git", code)
        for forbidden in ("wineboot -i", "subprocess.Popen", "shutil.rmtree", "rm -rf",
                          "os.system(", "ProcessBuilder(", ".unlink("):
            self.assertNotIn(forbidden, code)

    def test_three_separate_native_cohort_lookups(self):
        original = synthetic_pinned_sources()
        patched = M.transform(original)
        self.assertEqual(set(original), set(patched))
        self.assertNotEqual(original["loader/main.c"], patched["loader/main.c"])
        for code in patched.values():
            self.assertIn("CHAROITE_WINE29_NATIVE_DIR", code)
            self.assertIn("CHAROITE_WINE29_PE_DIR", code)
            self.assertIn("CHAROITE_WINE29_DATA_DIR", code)
            self.assertIn("Wine29/Wine28 selector conflict", code)
            self.assertIn('getenv( "CHAROITE_WINE28_PE_DIR" )', code)
        main = patched["loader/main.c"]
        self.assertLess(main.index("libcharoite_wine29_ntdll.so"),
                        main.index("if (self &&"))
        self.assertIn("return handle;  /* fail closed", main)
        loader = patched["dlls/ntdll/unix/loader.c"]
        self.assertEqual(loader.count('"%s/apisetschema.dll"'), 1)
        self.assertEqual(loader.count('"%s/ntdll.dll"'), 1)
        self.assertIn("verified isolated Wine29 API-set PE is absent", loader)
        self.assertIn("verified isolated Wine29 NTDLL PE was not found", loader)
        server = patched["server/unicode.c"]
        self.assertIn("if (!fd) for", server)
        self.assertIn("source-verified Wine29 l_intl.nls absent", server)
        self.assertEqual(original, synthetic_pinned_sources())

    def test_refuse_missing_old_patch_or_double_application(self):
        original = synthetic_pinned_sources()
        with self.assertRaisesRegex(ValueError, "anchor mismatch"):
            M.transform({**original,
                         "server/unicode.c": original["server/unicode.c"].replace(
                             "nls_dirs[0] = get_nls_dir();", "nls_dirs[0] = NULL;")})
        with self.assertRaisesRegex(ValueError, "already-modified"):
            M.transform(M.transform(original))

    def test_refuse_misordered_apiset_and_ntdll(self):
        original = synthetic_pinned_sources()
        loader = original["dlls/ntdll/unix/loader.c"]
        loader = loader.replace("        status = open_builtin_pe_file( name );",
                                "        status = something_else( name );")
        with self.assertRaisesRegex(ValueError, "ordering changed"):
            M.transform({**original, "dlls/ntdll/unix/loader.c": loader})


if __name__ == "__main__":
    unittest.main()
