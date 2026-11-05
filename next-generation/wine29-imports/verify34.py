#!/usr/bin/env python3
"""Independent 34-DLL Wine29 ordinary-vs-delay PE import closure, CI only.

Verifies pinned source evidence, candidate manifests and exact PE SHA-256s.
Does not execute any Wine/PE program or access Android/device data.
"""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import stat
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
prior=load(ROOT/"wine29-imports/classify.py","wine29_34_prior")
hybrid=load(ROOT/"wine29-deps/verify-wine29-deps.py","wine29_34_pe_machine")


def audited_file(folder: Path, name: str, manifest: dict) -> bytes:
    entry=manifest["components"][name]
    data=prior.safe_bytes(folder/(name+"-arm64ec.dll"))
    if (prior.sha(data)!=entry["sha256"] or len(data)!=entry["size"] or
        hybrid.raw_coff_machine(data) not in (0xAA64,0xA641)):
        raise ValueError("Source artifact PE SHA/size/header mismatch: "+name)
    return data


def inspect(archive: Path, six: Path, two: Path, direct: Path, mpr: Path) -> dict:
    for file in (archive,six,two,direct,mpr):
        if not file.is_absolute() or file.is_symlink() or any(x in str(file) for x in prior.FORBIDDEN):
            raise ValueError("Require isolated absolute CI source artifacts")
    if len({str(x.resolve()) for x in (six,two,direct,mpr)})!=4:
        raise ValueError("Distinct immutable source cohorts required")
    source=prior.analyze(archive,six,two)
    if source["next_regular_import_candidates"]!=["propsys.dll","wininet.dll"]:
        raise ValueError("Original 31 provider PE classification changed")
    direct_report=json.loads(prior.safe_bytes(direct/"wine29-07-two-direct-import-candidates.json"))
    mpr_report=json.loads(prior.safe_bytes(mpr/"wine29-07-mpr-direct-followup.json"))
    if (direct_report.get("generation")!="wine10-arm64ec-dependencies.0.10-direct-candidate" or
        direct_report.get("source_commit")!=prior.SOURCE_SHA or
        direct_report.get("source_archive_sha256")!=prior.BASE_SHA or
        set(direct_report.get("components",{}))!={"propsys","wininet"} or
        direct_report.get("providers_after_expansion")!=33 or
        direct_report.get("launch_ready") is not False or
        mpr_report.get("generation")!="wine10-arm64ec-dependencies.0.11-mpr-candidate" or
        mpr_report.get("source_commit")!=prior.SOURCE_SHA or
        mpr_report.get("source_archive_sha256")!=prior.BASE_SHA or
        mpr_report.get("provider_count_after_new_mpr")!=34 or
        mpr_report.get("first_33_regular_gap")!=["mpr.dll"] or
        mpr_report.get("launch_ready") is not False):
        raise ValueError("Source generation/chain mismatch")
    with tarfile.open(archive,"r:gz") as t:
        m=json.load(t.extractfile("manifest.json"))
        images={("wineboot.exe" if n=="wineboot" else n+".dll"):t.extractfile(v["path"]).read()
                for n,v in m["components"].items() if v["format"]=="PE"}
    six_report=json.loads(prior.safe_bytes(six/"wine29-07-six-candidates.json"))
    two_report=json.loads(prior.safe_bytes(two/"wine29-07-eight-candidate-import-review.json"))
    for folder,names,manifest in (
        (six,tuple(prior.SIX_HASHES),six_report),
        (two,tuple(prior.TWO_HASHES),two_report),
        (direct,("propsys","wininet"),direct_report),
    ):
        for name in names:
            images[name+".dll"]=audited_file(folder,name,manifest)
    mpr_bin=prior.safe_bytes(mpr/"mpr-arm64ec.dll")
    if (prior.sha(mpr_bin)!=mpr_report["component"]["sha256"] or
        len(mpr_bin)!=mpr_report["component"]["size"] or
        hybrid.raw_coff_machine(mpr_bin) not in (0xAA64,0xA641)):
        raise ValueError("MPR binary hash, size or machine mismatch")
    images["mpr.dll"]=mpr_bin
    providers=set(images)-{"wineboot.exe"}
    if len(providers)!=34 or len(images)!=35:
        raise ValueError("Expected original 23 + 6 + 2 + 2 + 1 DLL providers")
    regular,delayed={},{}
    for name,content in images.items():
        reg,delay=prior.pe_imports(content)
        regular[name]=reg;delayed[name]=delay
    def owners(imports):
        names={dep for ds in imports.values() for dep in ds}
        return {dep:sorted(name for name,ds in imports.items() if dep in ds)
                for dep in sorted(names-providers)}
    r_owners=owners(regular);d_owners=owners(delayed)
    if (r_owners or
        "winspool.drv" not in d_owners or
        "cryptui.dll" not in d_owners or
        "dhcpcsvc.dll" not in d_owners or
        sum(map(len,regular.values())) < 181):
        raise ValueError("Incomplete or unexpected source 34-DLL PE import graph")
    return {
        "schema_version":1,
        "source_commit":prior.SOURCE_SHA,
        "source_archive_sha256":prior.BASE_SHA,
        "regular_pe_import_graph_verified":True,
        "regular_unbundled_import_names":[],
        "ordinary_import_descriptors":sum(len(x) for x in regular.values()),
        "distinct_regular_import_names":len({x for ds in regular.values() for x in ds}),
        "ordinary_import_owners_outside_cohort":r_owners,
        "delayed_import_descriptors":sum(len(x) for x in delayed.values()),
        "delayed_import_owners_outside_cohort":d_owners,
        "provided_dlls":sorted(providers),
        "provider_count":34,
        "pe_image_count":35,
        "source_only":True,
        "delay_imports_not_proven_at_startup":True,
        "runtime_loader_closure_proven":False,
        "wineboot_executed":False,"windows_exe_executed":False,
        "device_tested":False,"prefix_created":False,"installed":False,
        "launch_ready":False,
    }


def main(args):
    if len(args)!=6:raise SystemExit(
        "Usage: verify34.py ABS_BASELINE_TARGZ ABS_SIX ABS_TWO ABS_DIRECT ABS_MPR ABS_FRESH_JSON")
    *source,output=(Path(a) for a in args)
    if (not output.is_absolute() or output.exists() or output.is_symlink() or
        not output.parent.is_dir() or any(x in str(output) for x in prior.FORBIDDEN)):
        raise ValueError("Refusing output overwrite/unsafe storage")
    report=inspect(*source)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print("WINE29_07_34_DLL_PE_REGULAR_IMPORT_GRAPH_ZERO_UNBUNDLED=PASS")
    print("WINE29_07_34_DLL_DELAY_IMPORTS_TRACKED_SEPARATELY=PASS")
    print("WINE29_07_PE_LOADER_AND_PREFIX_EXECUTION=NOT_ATTEMPTED")


if __name__=="__main__":
    main(sys.argv[1:])
