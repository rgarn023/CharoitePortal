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
ANCHOR = '    asprintf( &env, "WINELOADER=%s", wineloader );'
MARKER = "CHAROITE_WINE29_V6_LOADER_EXEC"

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
    return original.replace(ANCHOR, ANDROID_SELECTOR + ANCHOR, 1)

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
    if target.is_symlink() or not target.is_file() or target.stat().st_size > 300000:
        raise ValueError("Unsafe source file")
    before = target.read_text(encoding="utf-8")
    after = patch_text(before)
    report = root / "charoite-wine29-v6-loader-patch.json"
    if report.exists() or report.is_symlink():
        raise ValueError("Refusing to overwrite v6 report")
    target.write_text(after, encoding="utf-8")
    try:
        git(["diff", "--check"], root)
    except Exception:
        target.write_text(before, encoding="utf-8")
        raise
    evidence = {
        "source_revision": PIN,
        "original_loader_git_blob": RAW_LOADER_BLOB,
        "modified_file": SOURCE,
        "candidate_native_loader": "libcharoite_wine29_v6_loader.so",
        "selector_env": MARKER,
        "mode": "SOURCE_PATCH_ONLY_FAIL_CLOSED",
        "source_patch_sha256": hashlib.sha256(after.encode()).hexdigest(),
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
