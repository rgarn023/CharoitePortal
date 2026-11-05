#!/usr/bin/env python3
"""CI-only MPR follow-on PE verification against source-built Wine29 first 33 DLLs."""
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
GENERATION="wine10-arm64ec-dependencies.0.11-mpr-candidate"
REPORT="wine29-07-mpr-direct-followup.json"


def load(path, name):
    s=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    return m

direct=load(ROOT/"wine29-direct/verify-direct.py","wine29_mpr_prior_direct")
static=load(ROOT/"wine29-imports/classify.py","wine29_mpr_prior_parser")
hybrid=load(ROOT/"wine29-deps/verify-wine29-deps.py","wine29_mpr_prior_hybrid")


def verify(mode, archive, six, two, direct_dir, new, readobj):
    if mode not in ("create","verify"):
        raise ValueError("Invalid MPR verification mode")
    for p in (archive,six,two,direct_dir,new,readobj):
        if not p.is_absolute() or p.is_symlink() or any(x in str(p) for x in static.FORBIDDEN):
            raise ValueError("Require isolated CI-only absolute paths")
    if new.resolve() in (six.resolve(),two.resolve(),direct_dir.resolve()) or not new.is_dir():
        raise ValueError("MPR output must be fresh separate cohort")
    prior=direct.run("verify",archive,six,two,direct_dir,readobj)
    if (prior["component_count"]!=2 or prior["providers_after_expansion"]!=33 or
        prior["new_regular_import_names_not_in_33_providers"]!=["mpr.dll"] or
        prior["launch_ready"] is not False):
        raise ValueError("MPR is not independently proven next direct-import gap")
    file=new/"mpr-arm64ec.dll"
    data=static.safe_bytes(file)
    machine=hybrid.raw_coff_machine(data)
    h=static.safe_bytes(new/"mpr-pe-header.txt")
    imp=static.safe_bytes(new/"mpr-pe-imports.txt")
    if (subprocess.run([str(readobj),"--file-headers",str(file)],
                       check=True,capture_output=True).stdout!=h or
        subprocess.run([str(readobj),"--coff-imports",str(file)],
                       check=True,capture_output=True).stdout!=imp or
        b"Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)" not in h):
        raise ValueError("Source-built MPR ARM64EC view/import proof mismatch")
    ordinary,delayed=static.pe_imports(data)
    providers={name+".dll" for name in static.SIX_HASHES}|{
        name+".dll" for name in static.TWO_HASHES}|{
        "mpr.dll","propsys.dll","wininet.dll"
    }
    import tarfile
    with tarfile.open(archive,"r:gz") as tar:
        manifest=json.load(tar.extractfile("manifest.json"))
    providers|={name+".dll" for name,item in manifest["components"].items()
                if item["format"]=="PE" and name!="wineboot"}
    if len(providers)!=34:raise ValueError("Unexpected source-matched provider count")
    result={
        "schema_version":1,"generation":GENERATION,
        "source_commit":static.SOURCE_SHA,
        "source_archive_sha256":static.BASE_SHA,
        "first_33_regular_gap":["mpr.dll"],
        "provider_count_after_new_mpr":34,
        "component":{
            "filename":file.name,"sha256":hashlib.sha256(data).hexdigest(),
            "size":len(data),"raw_carrier":f"0x{machine:04X}",
            "arm64ec_view":"0xA641",
            "pe_header_sha256":hashlib.sha256(h).hexdigest(),
            "llvm_imports_sha256":hashlib.sha256(imp).hexdigest(),
            "regular_imports":sorted(set(ordinary)),
            "delayed_imports":sorted(set(delayed)),
            "new_regular_unbundled":sorted(set(ordinary)-providers),
            "new_delayed_unbundled":sorted(set(delayed)-providers),
        },
        "not_full_loader_closure":True,
        "source_only":True,"launch_ready":False,
        "installed":False,"wineboot_executed":False,
        "windows_exe_executed":False,"prefix_created":False,
        "device_tested":False,
    }
    path=new/REPORT
    if mode=="create":
        if path.exists() or path.is_symlink():
            raise ValueError("Refusing MPR manifest overwrite")
        path.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    else:
        if json.loads(static.safe_bytes(path))!=result:
            raise ValueError("MPR verification differs from exact copied bytes")
        if {p.name for p in new.iterdir()}!={REPORT,"mpr-arm64ec.dll","mpr-pe-header.txt","mpr-pe-imports.txt"}:
            raise ValueError("Unexpected MPR artifact entry")
    print("WINE29_07_MPR_SOURCE_COHERENT_ARM64EC_PE_HASH=PASS")
    print("WINE29_07_MPR_NEW_REGULAR_IMPORT_GAP_COUNT="+str(
        len(result["component"]["new_regular_unbundled"])))
    print("WINE29_07_WINEBOOT_AND_PHONE_EXECUTION_NOT_ATTEMPTED=PASS")
    return result


if __name__=="__main__":
    if len(sys.argv)!=8:
        raise SystemExit("Usage: verify-mpr.py create|verify ABS_BASELINE_TAR ABS_SIX ABS_TWO ABS_DIRECT ABS_NEW_MPR ABS_READOBJ")
    verify(sys.argv[1],*(Path(x) for x in sys.argv[2:]))
