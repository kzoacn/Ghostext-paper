#!/usr/bin/env python3
"""Preserve exact source objects referenced by experiment manifests."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "source-snapshots"


def store(data):
    key = hashlib.sha256(data).hexdigest()
    path = CACHE / (key + ".py")
    if not path.exists():
        path.write_bytes(data)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == key
    return key


def resolve(name, expected):
    parts = Path(name).parts
    if parts[0] not in {"Ghostext", "Ghostext-paper"} or ".." in parts or not name.endswith(".py"):
        raise ValueError(f"Unsupported source path: {name}")
    cached = CACHE / (expected + ".py")
    if cached.exists():
        assert hashlib.sha256(cached.read_bytes()).hexdigest() == expected
        return
    repo, relative = ROOT.parent / parts[0], str(Path(*parts[1:]))
    current = repo / relative
    if current.exists() and store(current.read_bytes()) == expected:
        return
    history = subprocess.check_output(
        ["git", "-C", str(repo), "log", "--all", "--format=%H", "--", relative], text=True).splitlines()
    for revision in history:
        result = subprocess.run(["git", "-C", str(repo), "show", f"{revision}:{relative}"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected:
            store(result.stdout)
            return
    raise ValueError(f"No exact source object found for {name} / {expected}")


def main():
    CACHE.mkdir(exist_ok=True)
    current = {}
    for directory in [ROOT / "scripts", ROOT.parent / "Ghostext/src/ghostext"]:
        for path in sorted(directory.glob("*.py")):
            current[str(path.relative_to(ROOT.parent))] = store(path.read_bytes())
    profiles = {}
    for path in sorted((ROOT / "results").glob("sp2027-*/manifest.json")):
        manifest = json.loads(path.read_text())
        sources = manifest.get("source_sha256")
        if not isinstance(sources, dict):
            continue
        for name, expected in sources.items():
            resolve(name, expected)
        # This helper was unchanged throughout the original research session.
        helper = "Ghostext-paper/scripts/artifact_utils.py"
        supplemental = {} if helper in sources else {helper: current[helper]}
        profiles[path.parent.name] = {
            "manifest": str(path.relative_to(ROOT)),
            "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sources": sources, "supplemental_helpers": supplemental,
            "supplement_note": (
                "Older manifests omitted artifact_utils.py. Its unchanged session source "
                "is supplied explicitly here; this does not rewrite the original manifest."
            ),
        }
    output = {
        "method": "Byte-exact SHA-256 source objects from the working tree, preserved intermediates, and repository history.",
        "profiles": profiles, "current_sources": current,
        "resume_rule": "Use the named frozen profile to resume an old cohort; current source may intentionally fail its manifest hash check.",
    }
    path = ROOT / "results/sp2027-source-map/index.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n")
    print("Resolved", len(profiles), "experiment profiles and", len(current), "current source files")


if __name__ == "__main__":
    main()
