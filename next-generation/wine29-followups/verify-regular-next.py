#!/usr/bin/env python3
"""Independent sealed Wine29 wininet/propsys 27+6+2+2 PE imports.

CI-only: reads immutable source archive and source-built candidate PE files.
Explicitly classifies regular versus delay imports without executing Windows PE.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
GENERATION="wine10-arm64ec-dependencies.0.10-regular-candidate"
SOURCE="c74acb09d51b447f5d5ac56c87608d3ec565a767"
BASELINE="66068032bd2203c8e53fddc92ce46b84086eb293306b2bd12bb741bf9a5e035e"
MODULES=("wininet","propsys")
FORBIDDEN=("/data/data/","/data/user/","/storage/emulated/","/sdcard/")
OUTPUT="wine29-07-ten-candidate-regular-delay-import-review.json"


def load(module_path:Path, name:str):
    spec=importlib.util.spec_from_file_location(name,module_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


sixlib=load(ROOT/"wine29-deps/verify-wine29-deps.py","wine29_next_six")
twolib=load(ROOT/"wine29-followups/verify-followups.py","wine29_next_two")
bundlelib=load(ROOT/"charoite-wine/verify-bootstrap-bundle.py","wine29_next_base")
peclass=load(ROOT/"wine29-imports/classify.py","wine29_next_pe_parser")


def safe_bytes(path:Path, max_bytes:int=48*1024*1024)->bytes:
    info=path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or not 0<info.st_size<=max_bytes:
        raise ValueError("Unsafe source-only PE artifact: "+str(path))
    data=path.read_bytes()
    if len(data)!=info.st_size:
        raise ValueError("Artifact changed while reading")
    return data


def summarize(image_data:dict[str,bytes])->dict:
    provided={name for name in image_data if name.endswith(".dll")}
    regular,delay={},{}
    for label,blob in image_data.items():
        r,d=peclass.pe_imports(blob)
        regular[label]=sorted(set(r))
        delay[label]=sorted(set(d))
    def missing_owners(mapping):
        names={name for values in mapping.values() for name in values}
        return {name:sorted(owner for owner,values in mapping.items() if name in values)
                for name in sorted(names-provided)}
    return {
        "pe_images":len(image_data),
        "provided_dlls":len(provided),
        "regular_descriptor_count":sum(len(values) for values in regular.values()),
        "regular_distinct_count":len({d for ds in regular.values() for d in ds}),
        "unbundled_regular_owners":missing_owners(regular),
        "delay_descriptor_count":sum(len(values) for values in delay.values()),
        "unbundled_delay_owners":missing_owners(delay),
        "regular_imports_by_module":regular,
        "delay_imports_by_module":delay,
    }


def inspect(archive:Path,six:Path,two:Path,output:Path,readobj:Path)->dict:
    for folder in (archive,six,two,output,readobj):
        if not folder.is_absolute() or folder.is_symlink() or any(
            x in str(folder) for x in FORBIDDEN):
            raise ValueError("Require source-only absolute pinned CI paths")
    if (not six.is_dir() or not two.is_dir() or not output.is_dir() or
        not readobj.is_file() or len({str(six.resolve()),str(two.resolve()),
                                     str(output.resolve())})!=3):
        raise ValueError("Do not merge original or new PE candidate directories")
    if hashlib.sha256(safe_bytes(archive,128*1024*1024)).hexdigest()!=BASELINE:
        raise ValueError("Source pinned Wine29 archive SHA mismatch")
    base_manifest,_=bundlelib.verify(archive)
    six_proof=sixlib.run("verify",six,readobj)
    two_proof=twolib.run("verify",archive,six,two,readobj)
    if (base_manifest.get("source_commit")!=SOURCE or
        base_manifest.get("version")!="wine10-arm64ec-bootstrap.0.7" or
        six_proof.get("source_commit")!=SOURCE or
        two_proof.get("source_commit")!=SOURCE or
        two_proof.get("component_count")!=2 or
        six_proof.get("component_count")!=6 or
        two_proof.get("launch_ready") is not False or
        six_proof.get("launch_ready") is not False):
        raise ValueError("Wine29 PE component/cohort source mismatch")
    new={name:sixlib.info_for(output,name,readobj) for name in MODULES}
    images={}
    with tarfile.open(archive,"r:gz") as bundle:
        for name,item in base_manifest["components"].items():
            if item["format"]!="PE":continue
            member=bundle.getmember(item["path"])
            if not member.isfile() or member.size>48*1024*1024:
                raise ValueError("Unexpected original source-verified PE archive member")
            stream=bundle.extractfile(member)
            if stream is None:raise ValueError("Missing pinned Wine29 PE archive stream")
            images["wineboot.exe" if name=="wineboot" else name+".dll"]=stream.read()
    if len(images)!=24:
        raise ValueError("Incomplete verified 23-DLL plus ARM64 wineboot source")
    original=summarize(images)
    for folder,expected in ((six,sixlib.MODULES),(two,twolib.EXTRA)):
        for name in expected:
            images[name+".dll"]=safe_bytes(folder/(name+"-arm64ec.dll"))
    before=summarize(images)
    for name in MODULES:
        images[name+".dll"]=safe_bytes(output/(name+"-arm64ec.dll"))
    after=summarize(images)

    if (original["regular_descriptor_count"]!=111 or
        original["regular_distinct_count"]!=21 or
        set(original["unbundled_regular_owners"])!={
            "coml2.dll","imm32.dll","oleacc.dll","oleaut32.dll","shcore.dll"} or
        before["pe_images"]!=32 or before["provided_dlls"]!=31 or
        set(before["unbundled_regular_owners"])!={"wininet.dll","propsys.dll"} or
        after["pe_images"]!=34 or after["provided_dlls"]!=33 or
        set(new)!={"wininet","propsys"}):
        raise ValueError("Wine29 regular/delay import cohort or phone baseline mismatch")
    return {
        "schema_version":1,
        "generation":GENERATION,
        "source_commit":SOURCE,
        "original_archive_sha256":BASELINE,
        "source_only":True,
        "original_23_plus_wineboot":original,
        "previous_31_dll_sources":before,
        "expanded_33_dll_sources":after,
        "new_candidate_count":2,
        "new_candidate_modules":new,
        "six_source_currency_proof_sha256":six_proof["portability_patch_proof_sha256"],
        "regular_dependency_closure_proven_at_runtime":False,
        "delay_imports_are_not_proven_startup_required":True,
        "currency_rounding_equivalence_not_proven":True,
        "launch_ready":False,
        "wineboot_executed":False,
        "windows_exe_executed":False,
        "phone_staged":False,
        "prefix_created":False,
    }


def run(mode:str,archive:Path,six:Path,two:Path,out:Path,readobj:Path)->dict:
    if mode not in ("create","verify"):
        raise ValueError("Unexpected Wine29 static audit mode")
    result=inspect(archive,six,two,out,readobj)
    report=out/OUTPUT
    if mode=="create":
        if report.exists() or report.is_symlink():
            raise ValueError("Refusing replacement of source-only audit report")
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    else:
        prior=json.loads(safe_bytes(report).decode("utf-8"))
        if prior!=result:
            raise ValueError("PE bytes, SHA, imports or graph changed after source sealing")
        allow={OUTPUT}
        for name in MODULES:
            allow.update((name+"-arm64ec.dll",name+"-pe-header.txt",name+"-pe-imports.txt"))
        if {f.name for f in out.iterdir()}!=allow:
            raise ValueError("Unexpected source files in new sealed 2-module cohort")
    print("WINE29_07_WININET_PROPSYS_SOURCE_ABI_AND_HASHES=PASS")
    print("WINE29_07_PHONE_111_IMPORTS_BASELINE_MATCH=PASS")
    print("WINE29_07_REGULAR_IMPORTS_BEFORE_31="+",".join(
        result["previous_31_dll_sources"]["unbundled_regular_owners"]))
    print("WINE29_07_REGULAR_IMPORTS_AFTER_33="+",".join(
        result["expanded_33_dll_sources"]["unbundled_regular_owners"]))
    print("WINE29_07_DELAY_IMPORTS_AFTER_33="+",".join(
        result["expanded_33_dll_sources"]["unbundled_delay_owners"]))
    print("WINE29_07_SOURCE_ONLY_NO_WINEBOOT_PE_OR_PHONE_EXECUTION=PASS")
    return result


if __name__=="__main__":
    if len(sys.argv)!=7:
        raise SystemExit("Usage: verify-regular-next.py create|verify ABS_SOURCE_ARCHIVE ABS_SIX ABS_TWO ABS_NEW_TWO ABS_LLVM")
    run(sys.argv[1],*(Path(x) for x in sys.argv[2:]))
