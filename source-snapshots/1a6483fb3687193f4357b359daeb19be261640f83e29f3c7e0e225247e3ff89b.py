#!/usr/bin/env python3
"""Preserve exact source objects referenced by experiment manifests."""
from __future__ import annotations
import hashlib
import ast
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


def supplemental_dependencies(sources, current):
    """Pin local imports omitted from the original manifest, without rewriting it."""
    supplemental = {}
    pending = list(sources.items())
    while pending:
        name, expected = pending.pop()
        if not name.startswith("Ghostext-paper/scripts/"):
            continue
        tree = ast.parse((CACHE / (expected + ".py")).read_bytes())
        modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.append(node.module.split(".")[0])
            elif isinstance(node, ast.Import):
                modules.extend(alias.name.split(".")[0] for alias in node.names)
        for module in modules:
            dependency = f"Ghostext-paper/scripts/{module}.py"
            if dependency in current and dependency not in sources and dependency not in supplemental:
                supplemental[dependency] = current[dependency]
                pending.append((dependency, current[dependency]))
    return supplemental


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
        supplemental = supplemental_dependencies(sources, current)
        data_inputs = {}
        input_aliases = {}
        for name, expected in manifest.get("inputs", {}).items():
            data_path = ROOT / name
            assert data_path.resolve().is_relative_to(ROOT.resolve())
            assert hashlib.sha256(data_path.read_bytes()).hexdigest() == expected
            data_inputs["Ghostext-paper/" + name] = expected
        if "study_plan_sha256" in manifest:
            expected = manifest["study_plan_sha256"]
            if "study_plan_path" in manifest:
                plan_path = ROOT / manifest["study_plan_path"]
                assert plan_path.resolve().is_relative_to(ROOT.resolve())
                assert hashlib.sha256(plan_path.read_bytes()).hexdigest() == expected
                data_inputs["Ghostext-paper/" + manifest["study_plan_path"]] = expected
            else:
                # The first two pilot versions precede an explicit plan path.
                name = f"Ghostext-paper/results/sp2027-accept-protocol/{expected}.md"
                assert hashlib.sha256((ROOT.parent / name).read_bytes()).hexdigest() == expected
                data_inputs[name] = expected
                input_aliases["Ghostext-paper/notes/sp2027-accept-study-plan.md"] = {
                    "source": name, "sha256": expected}
        if "selected_case_ids" in manifest and "input_sha256" in manifest:
            matches = [
                p for p in (ROOT / "results").glob("sp2027-*/pairs.jsonl")
                if hashlib.sha256(p.read_bytes()).hexdigest() == manifest["input_sha256"]
            ]
            if len(matches) != 1:
                raise ValueError(f"Cannot identify unique diagnostic input for {path}")
            for data_path in [matches[0], matches[0].with_name("manifest.json")]:
                data_inputs["Ghostext-paper/" + str(data_path.relative_to(ROOT))] = (
                    hashlib.sha256(data_path.read_bytes()).hexdigest())
        profiles[path.parent.name] = {
            "manifest": str(path.relative_to(ROOT)),
            "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "sources": sources, "supplemental_helpers": supplemental,
            "data_inputs": data_inputs,
            "input_aliases": input_aliases,
            "external_inputs": manifest.get("upstream"),
            "supplement_note": (
                "Local imported modules omitted from older manifests are explicitly pinned "
                "at artifact freeze. This supplements dependencies without retroactively "
                "claiming that their hashes were recorded by the original runs. The unchanged "
                "helper functions are checked in sp2027-validation/helper-compatibility.json."
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
