#!/usr/bin/env python3
"""Fetch or verify the exact public weight revisions used in the experiments."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backend", choices=["both", "qwen", "gpt2"], default="both")
    ap.add_argument("--destination", type=Path, default=ROOT.parent / "models")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--qwen-path", type=Path)
    ap.add_argument("--gpt2-path", type=Path)
    args = ap.parse_args()
    pins = json.loads((ROOT / "results/sp2027-environment/model-downloads.json").read_text())
    for name in (["qwen", "gpt2"] if args.backend == "both" else [args.backend]):
        pin = pins[name]
        if name == "qwen":
            directory = args.destination / "qwen"
            targets = {pin["filename"]: args.qwen_path or directory / pin["filename"]}
            hashes = {pin["filename"]: pin["sha256"]}
        else:
            directory = args.gpt2_path or args.destination / "gpt2"
            hashes = pin.get("all_local_files_sha256", pin["files"])
            targets = {filename: directory / filename for filename in hashes}
        for filename, path in targets.items():
            if not path.exists():
                if args.verify_only:
                    raise FileNotFoundError(path)
                path.parent.mkdir(parents=True, exist_ok=True)
                if filename == "revision.txt":
                    path.write_text(pin["revision"] + "\n")
                else:
                    from huggingface_hub import hf_hub_download
                    downloaded = Path(hf_hub_download(
                        repo_id=pin["repository"], revision=pin["revision"], filename=filename,
                        local_dir=str(path.parent), cache_dir=str(ROOT / "tmp/hf-cache"), token=False))
                    if downloaded != path:
                        raise ValueError(f"Unexpected download location: {downloaded}")
            actual = digest(path)
            if actual != hashes[filename]:
                raise ValueError(f"Model hash mismatch for {path}; do not substitute the latest revision")
            print(name, filename, "SHA-256 verified")


if __name__ == "__main__":
    main()
