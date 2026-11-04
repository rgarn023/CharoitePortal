#!/usr/bin/env python3
"""Create a distinct Wine29-native patched SOURCE generation, never a runtime.

Only run against a fresh, already source-validated isolated checkout produced
by prepare-source.sh. Old Wine28 and 27-component .0.6 artifacts are immutable.
All exact source anchors are checked before writing any of the four files.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
GENERATION = "wine10-arm64ec-bootstrap.0.7"
REQUIRED = (
    "CHAROITE_WINE29_NATIVE_DIR", "CHAROITE_WINE29_PE_DIR",
    "CHAROITE_WINE29_DATA_DIR", "Wine29/Wine28 selector conflict"
)
PATHS = ("loader/main.c", "dlls/ntdll/unix/loader.c", "server/unicode.c")


def exact(text: str, old: str, new: str, purpose: str) -> str:
    if text.count(old) != 1 or old == new:
        raise ValueError("Pinned Wine29 patch anchor mismatch: " + purpose)
    return text.replace(old, new, 1)


def transform(sources: dict[str, str]) -> dict[str, str]:
    if set(sources) != set(PATHS):
        raise ValueError("Wrong Wine29 source file selection")
    if any("CHAROITE_WINE29_NATIVE_DIR" in x for x in sources.values()):
        raise ValueError("Refusing an already-modified Wine29 source tree")
    out = dict(sources)

    # Source priority is before the older self/WINEDLLPATH search, so a missing
    # Wine29 library cannot silently fall back to another Wine generation.
    insert = r'''
#if defined(__ANDROID__) && defined(__aarch64__)
    /* Opt-in, source-matched Wine29 only. No Wine28/native fallback. */
    {
        const char *native29 = getenv( "CHAROITE_WINE29_NATIVE_DIR" );
        const char *pe29 = getenv( "CHAROITE_WINE29_PE_DIR" );
        const char *data29 = getenv( "CHAROITE_WINE29_DATA_DIR" );
        if (native29 || pe29 || data29)
        {
            char *canonical;
            if (!native29 || !pe29 || !data29 ||
                getenv( "CHAROITE_WINE28_NATIVE_DIR" ) ||
                getenv( "CHAROITE_WINE28_PE_DIR" ) ||
                getenv( "CHAROITE_WINE27_NATIVE_DIR" ) ||
                getenv( "CHAROITE_WINE26_DATA_DIR" ) ||
                native29[0] != '/' || strstr( native29, ".." ) ||
                strchr( native29, ':' ) || !(canonical = realpath( native29, NULL )))
            {
                fprintf( stderr, "Wine29/Wine28 selector conflict or invalid native directory\n" );
                return NULL;
            }
            handle = try_dlopen( canonical, "libcharoite_wine29_ntdll.so" );
            free( canonical );
            return handle;  /* fail closed, even if library is missing */
        }
    }
#endif
'''
    out["loader/main.c"] = exact(
        out["loader/main.c"],
        "    void *handle = NULL;\n\n    if (self &&",
        "    void *handle = NULL;\n" + insert + "\n    if (self &&",
        "native loader must select Wine29 before old cohorts",
    )

    # All Wine29 selectors must be present; every previous-generation
    # selector is forbidden. A canonical absolute path is mandatory.
    helper = r'''
#if defined(__ANDROID__) && defined(__aarch64__)
static char *charoite_wine29_selected_path( const char *selector )
{
    const char *native = getenv( "CHAROITE_WINE29_NATIVE_DIR" );
    const char *pe = getenv( "CHAROITE_WINE29_PE_DIR" );
    const char *data = getenv( "CHAROITE_WINE29_DATA_DIR" );
    const char *dir;
    char *canonical;
    if (!native && !pe && !data) return NULL;
    if (!native || !pe || !data ||
        getenv( "CHAROITE_WINE28_NATIVE_DIR" ) ||
        getenv( "CHAROITE_WINE28_PE_DIR" ) ||
        getenv( "CHAROITE_WINE27_NATIVE_DIR" ) ||
        getenv( "CHAROITE_WINE26_DATA_DIR" ))
        fatal_error( "Wine29/Wine28 selector conflict or incomplete source cohort\n" );
    if (!(dir = getenv( selector )) || dir[0] != '/' ||
        strstr( dir, ".." ) || strchr( dir, ':' ) ||
        !(canonical = realpath( dir, NULL )))
        fatal_error( "invalid isolated Wine29 source directory\n" );
    return canonical;
}
#endif

'''
    ntdll = out["dlls/ntdll/unix/loader.c"]
    ntdll = exact(ntdll,
        "static void init_paths( char *argv[] )\n",
        helper + "static void init_paths( char *argv[] )\n",
        "new isolated native NTDLL directory helper")
    ntdll = exact(ntdll,
        '        if (getenv( "CHAROITE_WINE26_DATA_DIR" ))\n',
        '''        if ((data_dir = charoite_wine29_selected_path( "CHAROITE_WINE29_DATA_DIR" )))
        {
            /* Source-verified Wine29 NLS tree; do not fall back to Wine26. */
        }
        else if (getenv( "CHAROITE_WINE26_DATA_DIR" ))
''',
        "Wine29 data path takes priority over old cohort")
    # Both initial Windows NTDLL and API-set schema loading require the exact
    # same isolated PE directory, not the APK's native /lib directory.
    # The API-set lookup occurs before the initial NTDLL image lookup in
    # pinned loader.c. Both have the same old Wine28 branch text. Split only
    # when exactly two distinct occurrences are present, never guess.
    branch = '    if (getenv( "CHAROITE_WINE28_PE_DIR" ))\n'
    parts = ntdll.split(branch)
    if (len(parts) != 3 or "load_apiset_dll(void)" not in parts[0] or
            "open_unix_file" not in parts[1] or "open_builtin_pe_file" not in parts[2]):
        raise ValueError("Pinned Wine28 API-set/NTDLL branch ordering changed")
    api29 = '''    if (getenv( "CHAROITE_WINE29_PE_DIR" ) ||
        getenv( "CHAROITE_WINE29_NATIVE_DIR" ) ||
        getenv( "CHAROITE_WINE29_DATA_DIR" ))
    {
        char *resolved = charoite_wine29_selected_path( "CHAROITE_WINE29_PE_DIR" );
        if (asprintf( &name, "%s/apisetschema.dll", resolved ) < 0)
            fatal_error( "cannot construct isolated Wine29 API-set path\\n" );
        free( resolved );
    }
    else if (getenv( "CHAROITE_WINE28_PE_DIR" ))
'''
    native29 = '''    if (getenv( "CHAROITE_WINE29_PE_DIR" ) ||
        getenv( "CHAROITE_WINE29_NATIVE_DIR" ) ||
        getenv( "CHAROITE_WINE29_DATA_DIR" ))
    {
        char *resolved = charoite_wine29_selected_path( "CHAROITE_WINE29_PE_DIR" );
        if (asprintf( &name, "%s/ntdll.dll", resolved ) < 0)
            fatal_error( "cannot construct isolated Wine29 NTDLL PE path\\n" );
        free( resolved );
    }
    else if (getenv( "CHAROITE_WINE28_PE_DIR" ))
'''
    ntdll = parts[0] + api29 + parts[1] + native29 + parts[2]
    ntdll = exact(ntdll,
        '    if (getenv( "CHAROITE_WINE28_PE_DIR" ) && status == STATUS_DLL_NOT_FOUND)\n',
        '''    if ((getenv( "CHAROITE_WINE29_PE_DIR" ) ||
         getenv( "CHAROITE_WINE29_NATIVE_DIR" ) ||
         getenv( "CHAROITE_WINE29_DATA_DIR" )) && status == STATUS_DLL_NOT_FOUND)
        fatal_error( "verified isolated Wine29 NTDLL PE was not found\\n" );
    if (getenv( "CHAROITE_WINE28_PE_DIR" ) && status == STATUS_DLL_NOT_FOUND)
''',
        "no legacy fallback on missing Wine29 NTDLL")
    ntdll = exact(ntdll,
        '    if (status && getenv( "CHAROITE_WINE28_PE_DIR" ))\n',
        '''    if (status && (getenv( "CHAROITE_WINE29_PE_DIR" ) ||
                   getenv( "CHAROITE_WINE29_NATIVE_DIR" ) ||
                   getenv( "CHAROITE_WINE29_DATA_DIR" )))
        fatal_error( "verified isolated Wine29 API-set PE is absent or unreadable: %x\\n", status );
    if (status && getenv( "CHAROITE_WINE28_PE_DIR" ))
''',
        "no legacy fallback on missing Wine29 API-set")
    out["dlls/ntdll/unix/loader.c"] = ntdll

    # Wine server must use the same exact NLS tree before trying global
    # Wine locations; after selecting Wine29, no fallback on failure.
    server = out["server/unicode.c"]
    server = exact(server,
        '    nls_dirs[0] = get_nls_dir();\n    for (i = 0; i < ARRAY_SIZE( nls_dirs ); i++)\n',
        r'''    nls_dirs[0] = get_nls_dir();
#if defined(__ANDROID__) && defined(__aarch64__)
    {
        const char *native29 = getenv( "CHAROITE_WINE29_NATIVE_DIR" );
        const char *pe29 = getenv( "CHAROITE_WINE29_PE_DIR" );
        const char *data29 = getenv( "CHAROITE_WINE29_DATA_DIR" );
        if (native29 || pe29 || data29)
        {
            char *canonical;
            if (!native29 || !pe29 || !data29 ||
                getenv( "CHAROITE_WINE28_NATIVE_DIR" ) ||
                getenv( "CHAROITE_WINE28_PE_DIR" ) ||
                getenv( "CHAROITE_WINE27_NATIVE_DIR" ) ||
                getenv( "CHAROITE_WINE26_DATA_DIR" ) ||
                data29[0] != '/' || strstr( data29, ".." ) ||
                strchr( data29, ':' ) || !(canonical = realpath( data29, NULL )))
                fatal_error( "Wine29/Wine28 selector conflict or invalid NLS directory\n" );
            if (asprintf( &path, "%s/nls/l_intl.nls", canonical ) < 0)
                fatal_error( "cannot construct Wine29 NLS path\n" );
            free( canonical );
            fd = open_fd( NULL, path, nt_name, O_RDONLY, &mode, FILE_READ_DATA,
                          FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                          FILE_NON_DIRECTORY_FILE | FILE_SYNCHRONOUS_IO_NONALERT );
            if (!fd) fatal_error( "source-verified Wine29 l_intl.nls absent\n" );
        }
    }
#endif
    if (!fd) for (i = 0; i < ARRAY_SIZE( nls_dirs ); i++)
''',
        "Wine29 wineserver NLS path must take priority")
    out["server/unicode.c"] = server

    for name, source in out.items():
        if source == sources[name]:
            raise ValueError("Unmodified required Wine29 source: " + name)
    if not all(any(marker in value for value in out.values()) for marker in REQUIRED):
        raise ValueError("Incomplete Wine29 source selector marker set")
    return out


def prepare(root: Path) -> dict:
    if not root.is_absolute() or root.is_symlink():
        raise ValueError("Require a fresh absolute non-symlink CI workspace")
    if any(part in str(root) for part in ("/data/data/", "/data/user/", "/storage/emulated/")):
        raise ValueError("Never modify Android app/user storage")
    if not (root / ".git").is_dir() or not (root / "charoite-source-validation.txt").is_file():
        raise ValueError("Must use separately validated pinned Wine source checkout")
    old_delta = root / "charoite-source-delta.patch"
    if not old_delta.is_file() or b"CHAROITE_WINE28_PE_DIR" not in old_delta.read_bytes():
        raise ValueError("Previous Wine28 API-set source patches not applied")
    record = root / "charoite-wine29-native-source-validation.json"
    delta_file = root / "charoite-wine29-native-source-delta.patch"
    if record.exists() or delta_file.exists():
        raise ValueError("Refusing already generated Wine29 source")
    # Source HEAD must still equal the pinned commit; no branch update.
    sha = subprocess.run(("git", "-C", str(root), "rev-parse", "HEAD"),
                         check=True, capture_output=True, text=True).stdout.strip()
    if sha != BASE:
        raise ValueError("Wine source commit changed")
    originals = {name: (root / name).read_text(encoding="utf-8") for name in PATHS}
    updated = transform(originals)  # all-or-nothing validation before writes
    for name, data in updated.items():
        (root / name).write_text(data, encoding="utf-8")
    subprocess.run(("git", "-C", str(root), "diff", "--check"), check=True)
    diff = subprocess.run(("git", "-C", str(root), "diff", "--binary"),
                          check=True, capture_output=True).stdout
    if any(x.encode() not in diff for x in REQUIRED):
        raise ValueError("Expected source marker absent from generated delta")
    info = {"generation": GENERATION, "source_commit": BASE, "package": "com.charoitx",
            "runtime_executable": False, "device_tested": False,
            "native_elf_installed": False,
            "patch_sources": {name: {"before_sha256": hashlib.sha256(originals[name].encode()).hexdigest(),
                                     "after_sha256": hashlib.sha256(updated[name].encode()).hexdigest()}
                              for name in PATHS},
            "delta_sha256": hashlib.sha256(diff).hexdigest(),
            "legacy_wine28_cohort_modified": False}
    delta_file.write_bytes(diff)
    record.write_text(json.dumps(info, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return info


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: prepare-wine29-native.py ABSOLUTE_FRESH_PREPARED_WINE_SOURCE")
    report = prepare(Path(sys.argv[1]))
    print("CHAROITE_WINE29_NATIVE_ISOLATED_SOURCE=PASS")
    print(json.dumps(report, sort_keys=True))
