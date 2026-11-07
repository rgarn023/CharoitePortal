#!/usr/bin/env python3
"""Stage an isolated, fail-closed Android child-loader selector in pinned Wine29 source.

CI source preparation only. This never executes Wine or edits an installed APK,
user prefix, game, scratch, or existing Wine29 v1-v5 native cohort.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PIN = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
RAW_LOADER_BLOB = "2f978520af6c216586baa081caa4c1db38207fd4"
SOURCE = "dlls/ntdll/unix/loader.c"
NATIVE_ENTRY_SOURCE = "loader/main.c"
ANCHOR = '    asprintf( &env, "WINELOADER=%s", wineloader );'
MARKER = "CHAROITE_WINE29_V6_LOADER_EXEC"
NTDLL_MARKER = "CHAROITE_WINE29_V6_NATIVE_DIR"

# All checks occur before Wine's existing WINELOADER export. Native Android
# runtime can receive ONLY the full canonical, APK-extracted, owner-verified
# loader pathname. In particular, the calculated Wine bindir is not fallback.
ANDROID_SELECTOR = r'''
#ifdef __ANDROID__
    {
        const char *candidate = getenv( "CHAROITE_WINE29_V6_LOADER_EXEC" );
        const char *name;
        struct stat st;
        char *canonical;

        if (!candidate || strncmp( candidate, "/data/app/", 10 ) ||
            !(name = strrchr( candidate, '/' )) ||
            strcmp( name + 1, "libcharoite_wine29_v6_loader.so" ) ||
            !strstr( candidate, "/lib/arm64/" ))
            fatal_error( "Wine29 v6: APK-owned native child loader path missing or invalid\n" );

        if (lstat( candidate, &st ) || !S_ISREG( st.st_mode ) ||
            !(st.st_mode & (S_IXUSR | S_IXGRP | S_IXOTH)))
            fatal_error( "Wine29 v6: native child loader not an executable regular file\n" );

        canonical = realpath( candidate, NULL );
        if (!canonical || strcmp( canonical, candidate ))
            fatal_error( "Wine29 v6: native child loader path is not canonical\n" );

        /* Java must check the native APK ELF SHA-256 before invoking Wine.
         * This native selector rejects the legacy bindir-derived path.
         * A verified three-ELF cohort and matching PE/NLS are mandatory
         * before exposing any on-device test or releasing an APK. */
        wineloader = canonical;
    }
#endif

'''


# Android-only Wine loader must dlopen its OWN v6 NTDLL, never the legacy
# Wine28/Wine29 ntdll or the regular WINEDLLPATH fallback chain.
NATIVE_NTDLL_SELECTOR = r'''
#if defined(__ANDROID__) && defined(__aarch64__)
    {
        const char *native_dir = getenv( "CHAROITE_WINE29_V6_NATIVE_DIR" );
        const char *suffix = "/lib/arm64";
        struct stat st;
        char *canonical;
        size_t len;

        if (!native_dir || strncmp( native_dir, "/data/app/", 10 ) ||
            (len = strlen( native_dir )) < strlen( suffix ) ||
            strcmp( native_dir + len - strlen( suffix ), suffix ) ||
            strstr( native_dir, ".." ) || strchr( native_dir, ':' ) ||
            lstat( native_dir, &st ) || !S_ISDIR( st.st_mode ))
        {
            fprintf( stderr, "wine: Wine29 v6 APK native NTDLL directory invalid\n" );
            exit(1);
        }
        canonical = realpath( native_dir, NULL );
        if (!canonical || strcmp( canonical, native_dir ))
        {
            fprintf( stderr, "wine: Wine29 v6 APK native NTDLL directory noncanonical\n" );
            exit(1);
        }
        free( canonical );
        handle = try_dlopen( native_dir, "libcharoite_wine29_v6_ntdll.so" );
        if (!handle)
        {
            fprintf( stderr, "wine: Wine29 v6 matched native NTDLL cannot load: %s\n", dlerror() );
            exit(1);
        }
        return handle; /* Intentional: no legacy Wine or WINEDLLPATH fallback. */
    }
#endif

'''

def patch_native_entry(original):
    """Pin the v6 executable to a new v6 native NTDLL before any Wine fallback."""
    signature = "static void *load_ntdll( char *argv0 )"
    anchor = '    if (self && ((path = realpath_dirname( self ))))'
    if original.count(signature) != 1 or original.count(anchor) != 1:
        raise ValueError("Pinned native Wine main loader anchor missing or ambiguous")
    if NTDLL_MARKER in original:
        raise ValueError("Refusing to repatch matched v6 native NTDLL selector")
    if original.index(signature) > original.index(anchor):
        raise ValueError("Wine main loader startup order changed")
    for required in ("void *handle = NULL;", "static void *try_dlopen(", "#include <stdlib.h>"):
        if required not in original:
            raise ValueError("Pinned native Wine main prerequisite missing: " + required)
    return original.replace(anchor, NATIVE_NTDLL_SELECTOR + anchor, 1)

def git(args, root):
    completed = subprocess.run(["git", "-C", str(root), *args],
                               check=True, capture_output=True)
    return completed.stdout

def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def patch_text(original):
    """Keep source exact except the single fail-closed Android selector."""
    if original.count(ANCHOR) != 1:
        raise ValueError("Ambiguous Wine10 WINELOADER export anchor")
    if MARKER in original:
        raise ValueError("Refusing to repatch a native child loader")
    for required in ("#include <sys/stat.h>", "#include <stdlib.h>",
                     "wineloader = build_path( bin_dir, basename );",
                     'if (!getenv( "WINELOADERNOEXEC" ))'):
        if original.count(required) != 1:
            raise ValueError("Pinned Wine loader prerequisite missing: " + required)
    if not (original.index("wineloader = build_path( bin_dir, basename );") <
            original.index(ANCHOR) <
            original.index('if (!getenv( "WINELOADERNOEXEC" ))')):
        raise ValueError("Unexpected Wine loader initialization order")
    patched = original.replace(ANCHOR, ANDROID_SELECTOR + ANCHOR, 1)
    # Capture execv errno on v6 only; do not infer that NTSTATUS 0x1 proves execv failed.
    # The pathname is not emitted, only bounded numeric errno and fixed selector id.
    exec_anchor = '    execv( argv[1], argv + 1 );'
    if patched.count(exec_anchor) != 1:
        raise ValueError("Pinned Android child execv anchor missing/ambiguous")
    patched = patched.replace(exec_anchor, exec_anchor + """
#ifdef __ANDROID__
    fprintf( stderr, "CHAROITE_WINE29_V6_CHILD_EXECV_FAILURE errno=%d\\n", errno );
#endif
""", 1)
    return patched

def stage(root: Path):
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("A fresh absolute prepared Wine source directory is required")
    if git(["rev-parse", "HEAD"], root).decode().strip() != PIN:
        raise ValueError("Wine source checkout is not the exact pinned revision")
    baseline = git(["show", "HEAD:" + SOURCE], root)
    if git_blob_sha(baseline) != RAW_LOADER_BLOB:
        raise ValueError("Upstream native Wine loader Git blob hash mismatch")
    if not (root / "charoite-source-validation.txt").is_file():
        raise ValueError("The 11 existing Charoite Android patches must be verified first")
    target = root / SOURCE
    entry_target = root / NATIVE_ENTRY_SOURCE
    server_target = root / "server/unicode.c"
    for item in (target, entry_target, server_target):
        if item.is_symlink() or not item.is_file() or not 0 < item.stat().st_size < 300000:
            raise ValueError("Unsafe pinned Wine source file: " + str(item.name))
    before = target.read_text(encoding="utf-8")
    entry_before = entry_target.read_text(encoding="utf-8")
    server_before = server_target.read_text(encoding="utf-8")
    if git(["show", "HEAD:" + NATIVE_ENTRY_SOURCE], root).decode("utf-8").count(
            "static void *load_ntdll( char *argv0 )") != 1:
        raise ValueError("Pinned Wine native main source differs from expected")
    after = patch_text(before)
    entry_after = patch_native_entry(entry_before)
    # The v6 native generation must bind its own PE/NLS selectors rather
    # than inherit Wine28 and Wine26 symbolic environment names. These
    # replacements apply only in this freshly prepared source tree.
    for old_name, new_name in (
        ("CHAROITE_WINE28_PE_DIR", "CHAROITE_WINE29_V6_PE_DIR"),
        ("CHAROITE_WINE26_DATA_DIR", "CHAROITE_WINE29_V6_DATA_DIR"),
    ):
        if old_name not in after:
            raise ValueError("Missing source-matched v6 selector rebasing anchor " + old_name)
        after = after.replace(old_name, new_name)
    if "CHAROITE_WINE26_DATA_DIR" not in server_before:
        raise ValueError("Missing native Wine NLS server selector rebase")
    server_after = server_before.replace("CHAROITE_WINE26_DATA_DIR",
                                         "CHAROITE_WINE29_V6_DATA_DIR")
    report = root / "charoite-wine29-v6-loader-patch.json"
    if report.exists() or report.is_symlink():
        raise ValueError("Refusing to overwrite v6 report")
    target.write_text(after, encoding="utf-8")
    entry_target.write_text(entry_after, encoding="utf-8")
    server_target.write_text(server_after, encoding="utf-8")
    try:
        git(["diff", "--check"], root)
    except Exception:
        target.write_text(before, encoding="utf-8")
        entry_target.write_text(entry_before, encoding="utf-8")
        server_target.write_text(server_before, encoding="utf-8")
        raise
    evidence = {
        "source_revision": PIN,
        "original_loader_git_blob": RAW_LOADER_BLOB,
        "modified_files": [SOURCE, NATIVE_ENTRY_SOURCE, "server/unicode.c"],
        "candidate_native_loader": "libcharoite_wine29_v6_loader.so",
        "selector_env": MARKER,
        "matched_native_ntdll_env": NTDLL_MARKER,
        "isolated_pe_selector": "CHAROITE_WINE29_V6_PE_DIR",
        "isolated_nls_selector": "CHAROITE_WINE29_V6_DATA_DIR",
        "matched_native_ntdll": "libcharoite_wine29_v6_ntdll.so",
        "mode": "SOURCE_PATCH_ONLY_FAIL_CLOSED",
        "source_patch_sha256": hashlib.sha256(after.encode()).hexdigest(),
        "main_loader_patch_sha256": hashlib.sha256(entry_after.encode()).hexdigest(),
        "nls_server_patch_sha256": hashlib.sha256(server_after.encode()).hexdigest(),
        "three_elf_cohort_built": False,
        "pe_nls_cohort_validated": False,
        "android_apk_built": False,
        "phone_wine_executed": False,
        "one_shot_enabled": False,
    }
    report.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    return evidence

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fresh_prepared_source_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.fresh_prepared_source_root), sort_keys=True))

if __name__ == "__main__":
    main()
