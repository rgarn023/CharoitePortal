#!/usr/bin/env python3
"""Pinned Wine10 Wine29 child-loader path audit. Source-only: never run Wine."""
import argparse
import hashlib
import json
from pathlib import Path

PIN = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
BLOBS = {"dlls/ntdll/unix/loader.c": "2f978520af6c216586baa081caa4c1db38207fd4"}

def source_text(path: Path, expected: str) -> str:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 400000:
        raise ValueError("Unsafe pinned source input")
    data = path.read_bytes()
    got = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if got != expected:
        raise ValueError("Pinned Wine source Git blob hash changed")
    return data.decode("utf-8")

PROCESS_SHA = "01286e119067567d1a8c7d3c8d5d61407ab43750"
NATIVE_LOADER = "libcharoite_wine29_loader.so"

def required(source, names):
    for label, literal in names.items():
        if source.count(literal) != 1:
            raise ValueError("Pinned source callsite missing/ambiguous: " + label)

def inspect(source_dir: Path, java_path: Path):
    native = source_text(source_dir / "dlls/ntdll/unix/loader.c",
                         BLOBS["dlls/ntdll/unix/loader.c"])
    process = source_text(source_dir / "dlls/ntdll/unix/process.c", PROCESS_SHA)
    if java_path.is_symlink() or not java_path.is_file() or not (0 < java_path.stat().st_size < 100000):
        raise ValueError("Unsafe v5 Java reference")
    java = java_path.read_text(encoding="utf-8")
    required(native, {
        "android_does_not_use_proc_self_exe": '#if (defined(__linux__) && !defined(__ANDROID__))',
        "fallback_relative_bindir": 'if (!bin_dir) bin_dir = build_relative_path( dll_dir, LIBDIR "/wine", BINDIR );',
        "build_wineloader_from_basename": 'wineloader = build_path( bin_dir, basename );',
        "export_computed_wine_loader": 'asprintf( &env, "WINELOADER=%s", wineloader );',
        "exec_saved_native_wine_loader": 'execv( argv[1], argv + 1 );',
        "assign_computed_native_loader": 'argv[1] = strdup( wineloader );',
        "early_preexec_guard": 'if (!getenv( "WINELOADERNOEXEC" ))  /* first time around */',
        "child_loader_exec": 'return loader_exec( argv, machine );',
    })
    required(process, {
        "child_fork_calls_wine_loader": 'exec_wineloader( argv, socketfd, pe_info );',
        "parent_reads_child_startup": 'SERVER_START_REQ( get_new_process_info )',
        "parent_returns_failed_child_exit": 'status = reply->exit_code;',
    })
    # Ensure process-source callsites belong to a single child-exec path.
    start = process.index('static NTSTATUS spawn_process(')
    end = process.index('NTSTATUS WINAPI __wine_unix_spawnvp', start)
    child = process[start:end]
    if 'exec_wineloader( argv, socketfd, pe_info );\n            _exit(1);' not in child:
        raise ValueError("Unexpected pinned child native exec/fail path")
    if not (native.index('wineloader = build_path( bin_dir, basename );') <
            native.index('argv[1] = strdup( wineloader );') <
            native.index('if (!getenv( "WINELOADERNOEXEC" ))')):
        raise ValueError("Native loader callsite order changed")
    for label, literal in {
        "native_executable_name": 'private static final String NATIVE_LOADER = "' + NATIVE_LOADER + '";',
        "actual_native_library_directory": 'context.getApplicationInfo().nativeLibraryDir',
        "source_verified_native_loader": 'NATIVE_LOADER',
        "source_hash_preflight": 'CharoiteWine29Sealed012PePreflight.run(context)',
        "source_hash_data_stage": 'CharoiteWine29Sealed012Stage.verifyOnly(context)',
        "isolated_v5": 'charoite-next-wine29-c-drive-v5',
        "initial_noexec": 'env.put("WINELOADERNOEXEC", "1");',
    }.items():
        if literal not in java:
            raise ValueError("V5 Android native loader reference changed: " + label)
    for forbidden in ("CHAROITE_WINE29_LOADER_EXEC", 'env.put("WINELOADER",'):
        if forbidden in java:
            raise ValueError("Unexpected claimed native loader override in existing v5")
    return {
        "schema_version": 1,
        "source_revision": PIN,
        "source_git_blob_sha1": {
            "dlls/ntdll/unix/loader.c": BLOBS["dlls/ntdll/unix/loader.c"],
            "dlls/ntdll/unix/process.c": PROCESS_SHA,
        },
        "owner_v5_observed": {
            "private_c_link": "verified relative symlink",
            "wine_created_windows_and_users": "true, from owner report",
            "internal_auto_init_child_spawn": "failed status 0x1",
        },
        "source_facts": {
            "android_bin_dir_relative_to_native_ntdll": True,
            "computed_wineloader_from_bin_dir_and_argv_basename": True,
            "child_spawn_always_calls_exec_wineloader": True,
            "child_exec_failure_can_exit_one": True,
            "parent_can_surface_child_startup_exit_code": True,
            "WINELOADERNOEXEC_skips_only_early_preexec_branch": True,
            "existing_v5_uses_apk_native_loader_name": NATIVE_LOADER,
            "existing_v5_has_no_explicit_exec_path_patch": True,
        },
        "likely_problem": "Wine10 child process re-exec resolves the native loader using ntdll-derived bindir, which may differ from Android APK nativeLibraryDir. Exact on-phone exec path / errno NOT yet captured.",
        "not_proven": [
            "No evidence yet identifies exact failing execv path or errno",
            "Status 0x1 alone does not prove execv was the failure",
            "No initialized runtime, child PE or Windows gaming proven",
        ],
        "next_change": "Create a separately source-built, source-verified Wine native loader/NTDLL cohort with fail-closed APK-owned executable selector and on-device one-shot child smoke; never replace sealed Wine29 v0.80 cohorts.",
        "effect": "READ_ONLY_SOURCE_AUDIT",
        "wine_execution": "NONE",
        "phone_file_access": "NONE",
        "apk_build": "NOT_REQUESTED_BY_SOURCE_AUDIT",
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pinned_source_root", type=Path)
    ap.add_argument("v5_java", type=Path)
    args = ap.parse_args()
    print(json.dumps(inspect(args.pinned_source_root, args.v5_java), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
