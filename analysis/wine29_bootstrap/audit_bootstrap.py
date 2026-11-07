#!/usr/bin/env python3
"""Read-only, immutable-source Wine29 prefix bootstrap audit. No Wine execution."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

PIN = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
BLOBS = {
    "dlls/ntdll/loader.c": "bc71fe04c94a8ed8d5f6fc9122b9dc1fde883528",
    "dlls/ntdll/unix/env.c": "1add6fdc872d92da2fd49597f79037d9774efd80",
    "dlls/ntdll/unix/loader.c": "2f978520af6c216586baa081caa4c1db38207fd4",
}
ARCHIVE = "66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
PATCH = "f8122ad18663a0bedb5dde7983f6ebb690963ac1c87016fe3d4a1cdbc3061428"
MEMBER = "source/charoite-wine29-native-source-delta.patch"


def source_text(path, expected):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 400000:
        raise ValueError("Unsafe Wine source input")
    body = path.read_bytes()
    sha = hashlib.sha1(b"blob " + str(len(body)).encode() + b"\0" + body).hexdigest()
    if sha != expected:
        raise ValueError("Pinned Git blob SHA1 mismatch")
    return body.decode("utf-8")


def require(source, expected):
    missing = [label for label, snippet in expected.items() if snippet not in source]
    if missing:
        raise ValueError("Pinned Wine source contract failed: " + ", ".join(missing))
    return dict.fromkeys(expected, True)


def inspect(root, archive, java_path):
    sources = {name: source_text(root / name, sha) for name, sha in BLOBS.items()}
    if archive.is_symlink() or not archive.is_file() or not 0 < archive.stat().st_size <= 128*1024*1024:
        raise ValueError("Unsafe source-matched archive")
    if hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE:
        raise ValueError("Wine29 archive mismatch")
    with tarfile.open(archive, "r:gz") as tar:
        member = tar.getmember(MEMBER)
        if not member.isfile() or not 0 < member.size < 1024*1024:
            raise ValueError("Unsafe source-matched delta")
        patch = tar.extractfile(member).read()
    if hashlib.sha256(patch).hexdigest() != PATCH:
        raise ValueError("Wine29 source delta mismatch")
    if any(x in patch for x in (b"WINEBOOTSTRAPMODE", b"is_prefix_bootstrap", b"WINEDLLDIR%u")):
        raise ValueError("Source patch changed bootstrap control flow; stop")
    win = sources["dlls/ntdll/loader.c"]
    env = sources["dlls/ntdll/unix/env.c"]
    unix = sources["dlls/ntdll/unix/loader.c"]
    checks = {}
    checks.update(require(win, {
        "native_bootstrap_is_winebootstrapmode": 'RtlQueryEnvironmentVariable_U( NULL, &bootstrap_mode_str, &val_str ) != STATUS_VARIABLE_NOT_FOUND;',
        "builtin_fallback_requires_bootstrap": 'if (!is_prefix_bootstrap)',
        "fallback_uses_winedlldir": 'swprintf( dllpath, ARRAY_SIZE(dllpath), L"WINEDLLDIR%u", i );',
        "startup_null_dll_loadpath_normal": 'load_dll( NULL, L"kernel32.dll", 0, &kernel32, FALSE )',
        "builtin_fallback_invoked_after_search": 'status = find_builtin_without_file( libname, nt_name, pwm, mapping, image_info, id );',
    }))
    checks.update(require(env, {
        "automatic_init_sets_bootstrap_mode": 'set_env_var( &env, &env_pos, &env_size, bootstrapW, ARRAY_SIZE(bootstrapW), valueW );',
        "automatic_init_runs_wineboot": 'run_wineboot( env, env_pos );',
        "automatic_init_restores_mode": 'set_env_var( &env, &env_pos, &env_size, bootstrapW, ARRAY_SIZE(bootstrapW), bootstrap );',
        "native_roots_are_exported_to_windows": 'snprintf( str, sizeof(str), "WINEDLLDIR%u", i );',
    }))
    checks.update(require(unix, {
        "native_loader_reads_winedllpath": 'getenv( "WINEDLLPATH" )',
        "native_loader_includes_image_root": 'dll_paths[count++] = dll_dir;',
    }))
    if java_path.is_symlink() or not java_path.is_file() or java_path.stat().st_size > 100000:
        raise ValueError("No bounded original v1 Java")
    java = java_path.read_text()
    sections = java.split("private static Map<String,String> cleanEnv(", 1)
    if len(sections) != 2:
        raise ValueError("Missing original v1 environment")
    env_method = sections[1].split("private static String boundedLog(", 1)[0]
    if 'env.clear();' not in env_method or 'env.put("WINEDLLPATH",' not in env_method:
        raise ValueError("Original v1 environment changed")
    if 'env.put("WINEBOOTSTRAPMODE",' in env_method:
        raise ValueError("Original v1 explicitly enables bootstrap; reassess")
    return {
        "schema_version": 1, "source_commit": PIN, "source_blob_sha1": BLOBS,
        "source_archive_sha256_verified": True, "native_source_delta_sha256_verified": True,
        "source_flow_checks": checks,
        "v1_clean_environment_explicit_bootstrap_mode": False,
        "supported_inference": (
            "Wine auto --init temporarily sets WINEBOOTSTRAPMODE, then restores "
            "the prior value. V1 cleanEnv never specifies it, so subsequent "
            "--help startup can skip built-in DLL fallback when the prefix is incomplete. "
            "load_dll kernel32 in (null) is ordinary source behavior."
        ),
        "unresolved": (
            "Why the earlier bootstrap-mode internal wineboot --init exited 1 "
            "is still unknown; no kernel32 resolution or initialized prefix proven."
        ),
        "wine_execution": "NONE", "phone_data_access": "NONE",
        "new_v2_execution_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_root", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument("v1_java", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    result = inspect(a.source_root, a.archive, a.v1_java)
    a.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("WINE29_BOOTSTRAP_SOURCE_FLOW=PASS_READ_ONLY")
    print("WINE29_ORIGINAL_AUTO_INIT_FAILURE=UNRESOLVED")
    print("WINE29_NEW_WINE_EXECUTION=NOT_AUTHORIZED")


if __name__ == "__main__":
    main()
