#!/usr/bin/env python3
"""Guard code proposed by an automated agent before crossing trust boundaries.

Only small source changes in scoped Wine files or matching regression tests.
No GitHub workflow edits, install scripts, arbitrary filesystem operations,
binary assets, symlinks, deletes, renamed files or direct main-branch changes.
"""
import re
import subprocess
import sys
from pathlib import Path

ALLOW = re.compile(
    r"next-generation/(?:"
    r"CharoiteWine(?:26|27|28)[A-Za-z0-9_]*\.java"
    r"|charoite-wine/patches/[0-9]{4}-[A-Za-z0-9_.-]+\.patch"
    r"|tests/test_wine(?:26|27|28)[a-z0-9_]*\.py"
    r")\Z"
)
MAX_FILES = 10
MAX_PATCH_BYTES = 128 * 1024


def git(*args):
    p = subprocess.run(("git",) + args, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=True)
    return p.stdout


def permitted_paths(name_status):
    fields = name_status.split(b"\x00")
    if fields[-1] != b"":
        raise ValueError("Unexpected Git status encoding")
    fields.pop()
    if len(fields) % 2:
        raise ValueError("Unexpected Git status fields")
    paths = []
    for status, name in zip(fields[::2], fields[1::2]):
        path = name.decode("utf-8")
        if status not in (b"A", b"M") or not ALLOW.fullmatch(path):
            raise ValueError("Unapproved agent edit: " + path)
        if path in paths:
            raise ValueError("Repeated path")
        paths.append(path)
    if not paths or len(paths) > MAX_FILES:
        raise ValueError("Invalid changed-file count")
    return paths


def validate_candidate(status_bytes, patch_bytes, summary, symlinks=()):
    paths = permitted_paths(status_bytes)
    if len(patch_bytes) > MAX_PATCH_BYTES or not patch_bytes:
        raise ValueError("Invalid candidate patch size")
    for entry in summary.splitlines():
        if entry and not re.fullmatch(r"create mode 100644 .+", entry.strip()):
            raise ValueError("Unapproved mode, delete, rename or symlink")
    if symlinks:
        raise ValueError("Symlink is not allowed")
    return paths


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("export", "inspect"):
        raise SystemExit("usage: guard_patch.py export|inspect PATH")
    command, filename = sys.argv[1:]
    staged = command == "inspect"
    args = ("--cached",) if staged else ("HEAD",)
    # Source job runs git add -N before export, exposing newly created files
    # in the diff without staging the content.
    status = git("diff", *args, "--name-status", "-z")
    patch = git("diff", *args, "--binary")
    summary = git("diff", *args, "--summary").decode("utf-8")
    git("diff", *args, "--check")
    path_list = permitted_paths(status)
    links = [p for p in path_list if Path(p).is_symlink()]
    validated = validate_candidate(status, patch, summary, links)
    # Independently reject staged symlink entries, regardless of file contents.
    if staged:
        entries = git("ls-files", "--stage", "--", *validated).decode()
        if any(line.split(maxsplit=1)[0] != "100644"
               for line in entries.splitlines()):
            raise ValueError("Unsupported Git object file mode")
        if Path(filename).read_bytes() != patch:
            raise ValueError("Patch changed after independent revalidation")
    else:
        Path(filename).write_bytes(patch)
    print("CHAROITE_AGENT_PATCH_GUARD=PASS; scoped files: "
          + ", ".join(validated))


if __name__ == "__main__":
    main()
