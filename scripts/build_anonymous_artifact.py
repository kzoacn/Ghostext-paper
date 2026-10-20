#!/usr/bin/env python3
"""Export an anonymous review bundle while preserving scientific observations."""
from __future__ import annotations
import argparse
import getpass
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FULL_COHORTS = [
    ("sp2027-stopping-gpt2", "pairs.jsonl"), ("sp2027-stopping-qwen", "pairs.jsonl"),
    ("sp2027-stopping-gpt2-expanded", "pairs.jsonl"),
    ("sp2027-stopping-qwen-expanded", "pairs.jsonl"),
    ("sp2027-repair-gpt2", "runs.jsonl"), ("sp2027-repair-qwen", "runs.jsonl"),
]
CASE_COHORTS = [
    "sp2027-upstream-gpt2", "sp2027-upstream-gpt2-pilot", "sp2027-upstream-gpt2-pilot-v2",
    "sp2027-endpoint-gpt2", "sp2027-endpoint-gpt2-corrected", "sp2027-endpoint-qwen",
    "sp2027-upstream-qwen25-pilot", "sp2027-upstream-qwen25",
    "sp2027-observable-gpt2", "sp2027-observable-qwen25",
    "sp2027-budget-gpt2", "sp2027-budget-qwen25",
]
RENDER_PROFILES = [
    "sp2027-figures", "sp2027-tables", "sp2027-accept-figures", "sp2027-accept-tables",
    "sp2027-followup-materials",
]
EXCLUDED_SCRIPTS = {"merge_aligned_baselines.py", "merge_real_backend_baseline.py",
                    "run_aligned_baselines.py", "run_hmin_sweep.py"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity_tokens():
    values = {getpass.getuser(), Path.home().name, platform.node()}
    result = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    remote = result.stdout.strip() if result.returncode == 0 else ""
    match = re.search(r"github\.com[:/]([^/]+)/", remote)
    if match:
        values.add(match.group(1))
    generic = {"root", "user", "runner", "codex", "anonymous"}
    return sorted((v for v in values if len(v) >= 4 and v.lower() not in generic),
                  key=len, reverse=True)


def sanitize(value, tokens, key=""):
    if key in {"host", "hostname", "ghostext_git_head", "paper_git_head"}:
        return "redacted-for-anonymous-review"
    if isinstance(value, dict):
        return {k: sanitize(v, tokens, k) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v, tokens, key) for v in value]
    if isinstance(value, str):
        # Observations are immutable. Identity checks below still inspect them.
        if key in {"cover_text", "prefix_text", "prompt", "message", "text"}:
            return value
        value = re.sub(r"/home/[^/\s]+", "<HOME>", value)
        value = re.sub(r"[A-Za-z]:[/\\]Users[/\\][^/\\\s]+", "<HOME>", value)
        value = value.replace(str(ROOT.parent), "<WORKSPACE>")
        for token in tokens:
            value = re.sub(re.escape(token), "<ANONYMOUS>", value, flags=re.IGNORECASE)
    return value


def transform_json(data, transform, jsonl=False):
    if jsonl:
        old = [json.loads(line) for line in data.decode().splitlines()]
        new = [transform(row) for row in old]
        if new == old:
            return data
        return ("\n".join(json.dumps(row, ensure_ascii=False) for row in new) + "\n").encode()
    old = json.loads(data)
    new = transform(old)
    return data if new == old else (json.dumps(new, ensure_ascii=False, indent=2) + "\n").encode()


def replace_hashes(value, replacements):
    if isinstance(value, dict):
        return {key: replace_hashes(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [replace_hashes(item, replacements) for item in value]
    return replacements.get(value, value) if isinstance(value, str) else value


def scientific_fields(value):
    """Extract observation fields whose values must survive the export exactly."""
    keys = {"cover_text", "prefix_text", "prompt", "message", "text", "token_ids",
            "chosen_probabilities", "surprisal_bits", "status", "recovery_match",
            "attempts_used", "elapsed_seconds", "net_bpt", "gross_bpt",
            "interval_observations", "cdf_low", "cdf_high", "probability_decimal",
            "visible_token_ids", "visible_continuation_token_ids", "context_token_ids",
            "trace", "segment_endpoints", "packet_sha256", "text_sha256",
            "score", "natural_band_upper", "verified_survival_upper", "early_stop_upper",
            "tv_lower", "unclipped_tv_lower", "event_lower_numerator",
            "missing_mass_numerator", "event_upper_numerator"}
    if isinstance(value, dict):
        return {k: v if k in keys or isinstance(v, (int, float, bool)) else scientific_fields(v)
                for k, v in value.items()
                if k in keys or isinstance(v, (dict, list, int, float, bool))}
    if isinstance(value, list):
        return [scientific_fields(v) for v in value]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--draft", action="store_true", help="Allow incomplete cohorts; never label this a final artifact")
    args = ap.parse_args()
    for name, filename in FULL_COHORTS:
        directory = ROOT / "results" / name
        manifest = json.loads((directory / "manifest.json").read_text())
        rows = [json.loads(l) for l in (directory / filename).read_text().splitlines()]
        complete = len(rows) == len(manifest["tasks"]) and \
            {r["case_id"] for r in rows} == {r["case_id"] for r in manifest["tasks"]}
        if not args.draft and (not complete or not (directory / "analysis.json").exists()):
            raise ValueError(f"Incomplete/unanalysed cohort: {name}")
    for name in CASE_COHORTS:
        directory = ROOT / "results" / name
        if args.draft and not (directory / "manifest.json").exists():
            continue
        manifest = json.loads((directory / "manifest.json").read_text())
        rows = [json.loads(p.read_text()) for p in (directory / "cases").glob("*.json")]
        complete = (len(rows) == len(manifest["tasks"]) and
                    {r["case_id"] for r in rows} == {r["case_id"] for r in manifest["tasks"]})
        if not args.draft and (not complete or not (directory / "analysis.json").exists()):
            raise ValueError(f"Incomplete/unanalysed case cohort: {name}")
    if not args.draft:
        public_replay = json.loads(
            (ROOT / "results/sp2027-upstream-public-features/summary.json").read_text())
        assert public_replay["all_public_features_match"] and public_replay["pairs"] == 6
        observable_audit = json.loads(
            (ROOT / "results/sp2027-observable-audit/summary.json").read_text())
        assert observable_audit["all_passed"] and all(observable_audit["checks"].values())
        certificate = json.loads(
            (ROOT / "results/sp2027-verified-certificate/summary.json").read_text())
        assert {row["bits"] for row in certificate["certificates"]} == {128, 512, 2048}
        for model in ["gpt2", "qwen25"]:
            fidelity = json.loads(
                (ROOT / "results/sp2027-observable-fidelity" / (model + ".json")).read_text())
            assert fidelity["all_checked_paths_match"]
            assert fidelity["counts"]["all_output_bindings"] == len(fidelity["records"]) == 960
    tokens = identity_tokens()
    source_files = {}
    paper_files = {ROOT / "paper/main.tex", ROOT / "paper/refs.bib", ROOT / "paper/main.pdf"}
    paper_files.update((ROOT / "paper").glob("*.sty"))
    paper_files.update([ROOT / "paper/IEEEtran.cls", ROOT / "paper/IEEEtran.bst"])
    pending = [ROOT / "paper/main.tex"]
    pattern = re.compile(r"\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}")
    while pending:
        current = pending.pop()
        for match in pattern.finditer(current.read_text()):
            path = ROOT / "paper" / match.group(1)
            if not path.suffix:
                path = path.with_suffix(".tex")
            if path not in paper_files:
                paper_files.add(path)
                if path.suffix == ".tex":
                    pending.append(path)
    for path in paper_files:
        source_files["Ghostext-paper/" + str(path.relative_to(ROOT))] = path
    # Retain generated supporting figures even when a shorter manuscript
    # no longer includes them; their provenance manifests still reference them.
    for name in RENDER_PROFILES:
        manifest_path = ROOT / "results" / name / "manifest.json"
        if not manifest_path.exists():
            continue
        render_manifest = json.loads(manifest_path.read_text())
        for category in ["outputs", "tables"]:
            for relative, expected in render_manifest.get(category, {}).items():
                source = ROOT / relative
                assert source.resolve().is_relative_to(ROOT.resolve())
                assert sha(source.read_bytes()) == expected
                source_files["Ghostext-paper/" + relative] = source
    for path in (ROOT / "scripts").glob("*.py"):
        if path.name not in EXCLUDED_SCRIPTS:
            source_files["Ghostext-paper/scripts/" + path.name] = path
    for path in (ROOT / "source-snapshots").glob("*"):
        if path.is_file():
            source_files["Ghostext-paper/source-snapshots/" + path.name] = path
    for path in (ROOT / "results").glob("sp2027-*"):
        for file in path.rglob("*"):
            if file.is_file() and file.suffix in {".json", ".jsonl", ".npz"}:
                source_files["Ghostext-paper/" + str(file.relative_to(ROOT))] = file
    for relative in ["results/prompt-message-grid/prompt_message_grid_runs.jsonl",
                     "results/real-backend-baseline-runs-merged.jsonl",
                     "results/detector-block/matched_natural_covers.jsonl",
                     "results/sp2027-validation/core-pytest.txt",
                     "REPRODUCIBILITY.md", "requirements-analysis.txt", "requirements-revision.txt"]:
        source_files["Ghostext-paper/" + relative] = ROOT / relative
    source_map = json.loads((ROOT / "results/sp2027-source-map/index.json").read_text())
    for profile in source_map["profiles"].values():
        for relative, expected in profile.get("data_inputs", {}).items():
            source = ROOT.parent / relative
            assert source.resolve().is_relative_to(ROOT.parent.resolve())
            assert sha(source.read_bytes()) == expected
            source_files[relative] = source
    source_files["Ghostext-paper/notes/sp2027-accept-study-plan.md"] = (
        ROOT / "notes/sp2027-accept-study-plan.md")
    for directory in ["src", "tests"]:
        for path in (ROOT.parent / "Ghostext" / directory).rglob("*.py"):
            source_files["Ghostext/" + str(path.relative_to(ROOT.parent / "Ghostext"))] = path
    for name in ["spec.md", "pyproject.toml"]:
        source_files["Ghostext/" + name] = ROOT.parent / "Ghostext" / name

    original = {name: path.read_bytes() for name, path in source_files.items()}
    if not args.draft:
        checked = json.loads((ROOT / "results/sp2027-format/validation.json").read_text())
        assert sha(original["Ghostext-paper/paper/main.pdf"]) == checked["pdf_sha256"]
        for name, expected in checked["paper_sources_sha256"].items():
            assert sha(original["Ghostext-paper/" + name]) == expected
        visual = json.loads((ROOT / "results/sp2027-format/visual-review.json").read_text())
        assert visual["pdf_sha256"] == checked["pdf_sha256"] and visual["all_pages_inspected"]
        assert len(visual["pages"]) == checked["total_pages"]
        tests = json.loads((ROOT / "results/sp2027-validation/core-tests.json").read_text())
        assert tests["returncode"] == 0
        for name, expected in tests["source_sha256"].items():
            assert sha(original[name]) == expected
    released = {}
    for name, data in original.items():
        suffix = Path(name).suffix
        if suffix in {".json", ".jsonl"}:
            data = transform_json(data, lambda v: sanitize(v, tokens), suffix == ".jsonl")
        released[name] = data
    # Reconnect derived hashes to exported inputs. This dependency graph is acyclic.
    versions = {name: {sha(data)} for name, data in original.items()}
    for _ in range(12):
        replacements = {}
        for name, data in released.items():
            versions[name].add(sha(data))
            replacements.update({old_hash: sha(data) for old_hash in versions[name]})
        updated = {}
        for name, data in released.items():
            if Path(name).suffix in {".json", ".jsonl"}:
                data = transform_json(data, lambda v: replace_hashes(v, replacements),
                                      Path(name).suffix == ".jsonl")
            updated[name] = data
        if updated == released:
            break
        released = updated
    else:
        raise ValueError("Exported hash references did not converge")
    for name, data in released.items():
        if Path(name).suffix in {".json", ".jsonl"}:
            parse = (lambda b: [json.loads(l) for l in b.decode().splitlines()]) \
                if name.endswith(".jsonl") else json.loads
            assert scientific_fields(parse(data)) == scientific_fields(parse(original[name])), name
        if Path(name).suffix in {".py", ".md", ".txt", ".toml", ".tex", ".bib", ".json", ".jsonl"}:
            text = data.decode()
            for token in tokens:
                if re.search(re.escape(token), text, re.IGNORECASE):
                    raise ValueError(f"Identity string remains in {name}; do not publish")
        if name.startswith("Ghostext-paper/source-snapshots/") and name.endswith(".py"):
            assert sha(data) == Path(name).stem

    base = ROOT / "output/artifact"
    name = "ghostext-sp2027-draft" if args.draft else "ghostext-sp2027"
    destination = base / name
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for path, data in released.items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (destination / "Ghostext/README.md").write_text(
        "# Review implementation\n\nSee ../Ghostext-paper/REPRODUCIBILITY.md for setup and commands.\n")
    (destination / "README.md").write_text(
        "# Ghostext S&P 2027 review artifact\n\n"
        + ("This is an incomplete draft export.\n\n" if args.draft else "")
        + "Start with Ghostext-paper/REPRODUCIBILITY.md. The manuscript is "
          "Ghostext-paper/paper/main.pdf. Model weights are fetched separately using pinned revisions.\n\n"
          "FILE-INDEX.json maps original file hashes to exported hashes. Only metadata identities "
          "and references to changed file hashes are transformed; observations remain unchanged.\n")
    index = {
        "status": "draft-incomplete" if args.draft else "frozen-review-artifact",
        "redactions": ["local host/account identifiers", "personal paths", "author repository commit identifiers"],
        "observation_integrity": "Cover text, prompts, payloads, token/probability sequences, statuses, and measurement fields preserved.",
        "files": {path: {"original_sha256": sha(original[path]), "exported_sha256": sha(data),
                         "transformed": data != original[path]}
                  for path, data in sorted(released.items())},
    }
    for extra in ["README.md", "Ghostext/README.md"]:
        index["files"][extra] = {"exported_sha256": sha((destination / extra).read_bytes()),
                                "generated_for_export": True}
    (destination / "FILE-INDEX.json").write_text(json.dumps(index, indent=2) + "\n")
    source_index = json.loads((destination / "Ghostext-paper/results/sp2027-source-map/index.json").read_text())
    for profile in source_index["profiles"].values():
        manifest = destination / "Ghostext-paper" / profile["manifest"]
        assert sha(manifest.read_bytes()) == profile["manifest_sha256"]
        for source_hash in [*profile["sources"].values(), *profile["supplemental_helpers"].values()]:
            obj = destination / "Ghostext-paper/source-snapshots" / (source_hash + ".py")
            assert sha(obj.read_bytes()) == source_hash
    from pypdf import PdfReader
    pdf = PdfReader(destination / "Ghostext-paper/paper/main.pdf")
    pdf_strings = json.dumps(dict(pdf.metadata or {})) + "\n".join(page.extract_text() for page in pdf.pages)
    for token in tokens:
        assert not re.search(re.escape(token), pdf_strings, re.IGNORECASE), "Identity remains in PDF"
    assert sha((ROOT / "paper/main.pdf").read_bytes()) == sha(original["Ghostext-paper/paper/main.pdf"]), \
        "PDF changed during export; finish the build before exporting"
    archive = ROOT / "output" / (name + "-artifact.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(destination.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(str(Path(name) / path.relative_to(destination)), (2000, 1, 1, 0, 0, 0))
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, path.read_bytes())
    print(destination)
    print(archive)
    print("Files:", len(index["files"]), "ZIP SHA-256:", sha(archive.read_bytes()))


if __name__ == "__main__":
    main()
