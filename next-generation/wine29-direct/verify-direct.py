#!/usr/bin/env python3
"""Static, source-coherent Wine29 propsys/wininet PE candidate verifier.

Only reads pinned CI artifacts and LLVM logs; never executes guest binaries.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
GENERATION = "wine10-arm64ec-dependencies.0.10-direct-candidate"
NAMES = ("propsys", "wininet")
OUTPUT = "wine29-07-two-direct-import-candidates.json"
FORBIDDEN = ("/data/data/", "/data/user/", "/storage/emulated/", "/sdcard/")


def load(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


static = load(ROOT/"wine29-imports/classify.py", "wine29_import_classify_source")
hybrid = load(ROOT/"wine29-deps/verify-wine29-deps.py", "wine29_arm64ec_hybrid")


def checked(path: Path, max_bytes=64*1024*1024) -> bytes:
    info=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= max_bytes:
        raise ValueError("Unsafe candidate file: " + str(path))
    data=path.read_bytes()
    if len(data)!=info.st_size:
        raise ValueError("Candidate changed during review")
    return data


def collect(archive: Path, six: Path, two: Path, new: Path, readobj: Path) -> dict:
    for p in (archive, six, two, new, readobj):
        if not p.is_absolute() or p.is_symlink() or any(v in str(p) for v in FORBIDDEN):
            raise ValueError("Require isolated absolute runner sources")
    if (not new.is_dir() or not readobj.is_file() or new.resolve() in {
        six.resolve(), two.resolve()}):
        raise ValueError("Refuse modified prior candidate source/output")
    old = static.analyze(archive, six, two)
    if (old["next_regular_import_candidates"] != ["propsys.dll", "wininet.dll"] or
        old["provider_dll_count"] != 31 or old["launch_ready"] is not False):
        raise ValueError("Pinned 31-DLL static gate not verified")
    providers = {name+".dll" for name in static.SIX_HASHES} | {
        name+".dll" for name in static.TWO_HASHES}
    import tarfile
    with tarfile.open(archive,"r:gz") as tar:
        manifest=json.load(tar.extractfile("manifest.json"))
    providers |= {
        name+".dll" for name, data in manifest["components"].items()
        if data["format"]=="PE" and name!="wineboot"
    }
    if len(providers)!=31:
        raise ValueError("Wrong original Wine29 provider set")
    providers |= {name+".dll" for name in NAMES}
    results={}
    for name in NAMES:
        file = new/(name+"-arm64ec.dll")
        content = checked(file)
        raw = hybrid.raw_coff_machine(content)
        h = checked(new/(name+"-pe-header.txt"))
        imp = checked(new/(name+"-pe-imports.txt"))
        fresh_h = subprocess.run([str(readobj),"--file-headers",str(file)],
                                 capture_output=True,check=True).stdout
        fresh_imp = subprocess.run([str(readobj),"--coff-imports",str(file)],
                                   capture_output=True,check=True).stdout
        if (fresh_h!=h or fresh_imp!=imp or
            b"Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)" not in h):
            raise ValueError("LLVM ARM64EC view/import replay differs: "+name)
        normal, delay = static.pe_imports(content)
        llvm = sorted(set(d.lower() for d in re.findall(
            rb"^\s*Name:\s*([A-Za-z0-9_.+-]+\.(?:dll|drv))\s*$", imp, re.M)))
        llvm = [b.decode("ascii") for b in llvm]
        results[name] = {
            "filename":file.name, "sha256":hashlib.sha256(content).hexdigest(),
            "size":len(content), "raw_carrier":f"0x{raw:04X}",
            "arm64ec_view":"0xA641",
            "header_sha256":hashlib.sha256(h).hexdigest(),
            "imports_sha256":hashlib.sha256(imp).hexdigest(),
            "llvm_imports":llvm,
            "regular_imports":sorted(set(normal)),
            "delay_load_imports":sorted(set(delay)),
            "regular_unbundled":sorted(set(normal)-providers),
            "delayed_unbundled":sorted(set(delay)-providers),
        }
    unresolved_regular=sorted(set(dep for r in results.values() for dep in r["regular_unbundled"]))
    unresolved_delay=sorted(set(dep for r in results.values() for dep in r["delayed_unbundled"]))
    return {
        "schema_version":1, "generation":GENERATION, "source_commit":SOURCE,
        "source_archive_sha256":static.BASE_SHA, "component_count":2,
        "providers_after_expansion":len(providers),
        "previous_31_dll_regular_unbundled":old["next_regular_import_candidates"],
        "components":results,
        "new_regular_import_names_not_in_33_providers":unresolved_regular,
        "new_delay_import_names_not_in_33_providers":unresolved_delay,
        "scope_note":"Candidate-only PE import data, not full loader/delay resolution or runtime",
        "portable_currency_equivalence_proven":False,
        "launch_ready":False,"wineboot_executed":False,
        "windows_exe_executed":False, "prefix_created":False,
        "device_tested":False,"installed":False,
    }


def run(mode: str, archive: Path, six: Path, two: Path, out: Path, readobj: Path) -> dict:
    if mode not in ("create","verify"):
        raise ValueError("Unsupported attestation mode")
    result=collect(archive,six,two,out,readobj)
    report=out/OUTPUT
    if mode=="create":
        if report.exists() or report.is_symlink():
            raise ValueError("Refuse overwrite of direct-import artifact")
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    else:
        if json.loads(checked(report))!=result:
            raise ValueError("PE source/candidate artifact bytes changed")
        allowed={OUTPUT}
        for name in NAMES:
            allowed.update({name+"-arm64ec.dll",name+"-pe-header.txt",name+"-pe-imports.txt"})
        if {x.name for x in out.iterdir()}!=allowed:
            raise ValueError("Unexpected candidate artifact entry")
    print("WINE29_07_TWO_SOURCE_ONLY_DIRECT_CANDIDATES_HASHES=PASS")
    print("WINE29_07_TWO_DIRECT_CANDIDATE_ARM64EC_ABI=PASS")
    print("WINE29_07_NEW_REGULAR_IMPORT_UNBUNDLED_COUNT="+str(
        len(result["new_regular_import_names_not_in_33_providers"])))
    print("WINE29_07_NO_APK_PHONE_WINEBOOT_WINDOWS_EXECUTION=PASS")
    return result


if __name__=="__main__":
    if len(sys.argv)!=7:
        raise SystemExit("Usage: verify-direct.py create|verify ABS_BASELINE_TAR ABS_SIX ABS_TWO ABS_NEW ABS_LLVM_READOBJ")
    run(sys.argv[1],*(Path(v) for v in sys.argv[2:]))
