#!/usr/bin/env python3
"""Create an isolated source tree for one recorded experiment configuration."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("profile")
    ap.add_argument("--destination", type=Path, required=True)
    args = ap.parse_args()
    index = json.loads((ROOT / "results/sp2027-source-map/index.json").read_text())
    profile = index["profiles"][args.profile]
    destination = args.destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Choose an empty destination; existing work will not be overwritten")
    destination.mkdir(parents=True, exist_ok=True)
    # Populate unchanged helpers as well as the manifest-listed source files.
    for source, target in [
        (ROOT / "scripts", destination / "Ghostext-paper/scripts"),
        (ROOT.parent / "Ghostext/src", destination / "Ghostext/src"),
    ]:
        shutil.copytree(source, target, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    objects = {**profile["supplemental_helpers"], **profile["sources"]}
    for name, expected in objects.items():
        source = ROOT / "source-snapshots" / (expected + ".py")
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        # Replay entry points can themselves materialize the original codec
        # from the generation manifest, so preserve these named objects too.
        cached_target = destination / "Ghostext-paper/source-snapshots" / (expected + ".py")
        cached_target.parent.mkdir(parents=True, exist_ok=True)
        cached_target.write_bytes(data)
    for name, expected in profile.get("data_inputs", {}).items():
        source = ROOT.parent / name
        assert source.resolve().is_relative_to(ROOT.parent.resolve())
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected
        target = destination / name
        assert target.resolve().is_relative_to(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for name, entry in profile.get("input_aliases", {}).items():
        source = destination / entry["source"]
        data = source.read_bytes()
        assert hashlib.sha256(data).hexdigest() == entry["sha256"]
        target = destination / name
        assert target.resolve().is_relative_to(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / "PROFILE.json").write_text(json.dumps(profile, indent=2) + "\n")
    print(destination)
    print("Run the recorded entry-point script from this tree with a new output directory.")
    print("Hash-checked required input records were staged; weights and dependencies remain separate.")


if __name__ == "__main__":
    main()
