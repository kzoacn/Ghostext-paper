#!/usr/bin/env python3
"""Fetch immutable upstream RRC inputs and fail on any byte mismatch."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "dae326259e4fca8bc4fcf460dafdbc0e88a0a71a"
FILES = {
    "rrc_core.py": "e45a4df5eebc86881d606f2fd6c3cbab5729252dce96e5ae1a7ba424be02ec4a",
    "0.Prompts.tsv": "bb703742046ce990ad9d717e5edac77d2e8255cbacff42a349a8fd3e0041d9b7",
    "RRC_embed.py": "ebe7950eb6a89f659c163b67c5be7fb1ffc6afc850c0553afcbe633d068527d0",
    "RRC_extract.py": "1477225e71a78b03a66d6b3b89a690810d2e52c61111bf75fb6a4a4fc55c82fc",
    "CHANGELOG.md": "82467e1949d72ba388e2a421b77a1a4838a19a31bc1cab67788e44026c3776e5",
}
DEFAULT_DESTINATION = ROOT / "tmp/primary-source/rrc" / COMMIT


def fetch(destination=DEFAULT_DESTINATION):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, expected in FILES.items():
        path = destination / name
        url = f"https://raw.githubusercontent.com/ryehr/RRC_steganography/{COMMIT}/{name}"
        data = path.read_bytes() if path.exists() else urllib.request.urlopen(url).read()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"Unexpected upstream bytes: {name}: {actual}")
        if not path.exists():
            path.write_bytes(data)
        records[name] = {"sha256": actual, "bytes": len(data), "url": url}
    return destination, {
        "repository": "https://github.com/ryehr/RRC_steganography",
        "commit": COMMIT, "commit_date": "2026-09-04T11:58:49Z", "files": records,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    destination, manifest = fetch(args.destination)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Verified", len(manifest["files"]), "upstream files at", destination)


if __name__ == "__main__":
    main()
