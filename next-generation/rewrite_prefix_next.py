#!/usr/bin/env python3
"""Rebase pinned Winlator native assets to the separate Charoite Next Android UID.

The stable Portal uses com.charoite; Next uses com.charoitx. Both are 12-byte
package IDs, matching com.winlator in fixed-size native ELF loader strings.
Reuse the audited archive walker without changing its stable-edition target.
"""
from pathlib import Path
import importlib.util
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: rewrite_prefix_next.py PINNED_UPSTREAM")

script = Path(__file__).resolve().parents[1] / "runtime-preview" / "rewrite_prefix.py"
spec = importlib.util.spec_from_file_location("charoite_stable_rewriter", script)
if spec is None or spec.loader is None:
    raise RuntimeError("Missing stable archive rewriting implementation")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.ORIGINAL == b"com.winlator"
assert module.TARGET == b"com.charoite"
module.TARGET = b"com.charoitx"
assert len(module.ORIGINAL) == len(module.TARGET) == 12
module.main(Path(sys.argv[1]).resolve())
