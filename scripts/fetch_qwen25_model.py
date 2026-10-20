#!/usr/bin/env python3
"""Fetch a fixed official Qwen2.5 base-model revision and verify its objects."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "Qwen/Qwen2.5-0.5B"
REVISION = "060db6499f32faf8b98477b0a26969ef7d8b9987"
WEIGHT_SHA256 = "88c142557820ccad55bb59756bfcfcf891de9cc6202816bd346445188a0ed342"
WEIGHT_SIZE = 988097824
# Git blob identifiers from the official repository API, before generation.
SMALL_OBJECTS = {
    "LICENSE": "6634c8cc3133b3848ec74b9f275acaaa1ea618ab",
    "README.md": "2d22b523f8968e42fc6b805e656133fa83f771ab",
    "config.json": "141506237b9022c4ab3e01734cfafb9310b57d2d",
    "generation_config.json": "cbbb3133034e192527e5321b4c679154e4819ab8",
    "merges.txt": "20024bfe7c83998e9aeaf98a0cd6a2ce6306c2f0",
    "tokenizer.json": "443909a61d429dff23010e5bddd28ff530edda00",
    "tokenizer_config.json": "ba7e4c5637b9732dadcd66286ce48334e8b31e9e",
    "vocab.json": "4783fe10ac3adce15ac8f358ef5462739852c569",
}


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def verify(path):
    if path.name == "model.safetensors":
        if path.stat().st_size != WEIGHT_SIZE or digest(path) != WEIGHT_SHA256:
            raise ValueError(f"Weight hash or size mismatch: {path}")
    else:
        data = path.read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if blob != SMALL_OBJECTS[path.name]:
            raise ValueError(f"Pinned Git blob mismatch: {path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--destination", type=Path, default=ROOT.parent / "models/qwen25-0.5b")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--record", type=Path,
                    default=ROOT / "results/sp2027-environment/qwen25-download.json")
    args = ap.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    for name in [*SMALL_OBJECTS, "model.safetensors"]:
        target = args.destination / name
        if not target.exists():
            if args.verify_only:
                raise FileNotFoundError(target)
            temporary = target.with_suffix(target.suffix + ".partial")
            url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}"
            request = urllib.request.Request(url, headers={"User-Agent": "research-reproduction"})
            print("Fetching pinned", name, flush=True)
            with urllib.request.urlopen(request, timeout=60) as source, temporary.open("wb") as sink:
                shutil.copyfileobj(source, sink, length=1024 * 1024)
            # Check before publishing a complete file.
            if name == "model.safetensors":
                if temporary.stat().st_size != WEIGHT_SIZE or digest(temporary) != WEIGHT_SHA256:
                    raise ValueError("Downloaded model failed hash verification")
            else:
                data = temporary.read_bytes()
                actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
                if actual != SMALL_OBJECTS[name]:
                    raise ValueError("Downloaded file failed pinned-object verification")
            temporary.replace(target)
        verify(target)
        print(name, "verified", flush=True)
    revision = args.destination / "revision.txt"
    if revision.exists():
        if revision.read_text() != REVISION + "\n":
            raise ValueError("Existing model revision marker differs")
    else:
        revision.write_text(REVISION + "\n")
    record = {
        "repository": REPOSITORY, "revision": REVISION,
        "official_model_page": f"https://huggingface.co/{REPOSITORY}/tree/{REVISION}",
        "weight_size_bytes": WEIGHT_SIZE, "small_git_objects": SMALL_OBJECTS,
        "files": {name: digest(args.destination / name)
                  for name in [*SMALL_OBJECTS, "model.safetensors", "revision.txt"]},
        "scope": "Official pinned base model; distinct from the earlier Qwen3.5 GGUF source.",
    }
    args.record.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(record, indent=2) + "\n"
    if args.record.exists() and args.record.read_text() != encoded:
        raise ValueError("Refusing to replace an existing model provenance record")
    args.record.write_text(encoded)


if __name__ == "__main__":
    main()
