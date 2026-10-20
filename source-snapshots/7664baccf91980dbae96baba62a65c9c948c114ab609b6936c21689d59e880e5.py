#!/usr/bin/env python3
"""Map each frozen experiment profile to its command and stopping policy."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source_map = json.loads((ROOT / "results/sp2027-source-map/index.json").read_text())
    output = {}
    for name, profile in source_map["profiles"].items():
        path = ROOT / profile["manifest"]
        manifest = json.loads(path.read_text())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == profile["manifest_sha256"]
        backend = manifest.get("backend", "qwen")
        model = "<QWEN_GGUF>" if backend == "qwen" else "<GPT2_DIRECTORY>"
        schema = manifest.get("schema")
        entry, arguments = None, []
        details = {}
        if schema == "stopping-llm-v1":
            p = manifest["parameters"]
            entry = "run_stopping_llm.py"
            arguments = ["--backend", backend, "--model-path", model,
                         "--out-dir", "<NEW_OUTPUT_DIRECTORY>", "--threads", str(p["threads"]),
                         "--repeats", str(p["repeats"]), "--bits", *map(str, p["bits"]),
                         "--seed", str(p["seed"])]
            if p["verify_before_stop"]:
                arguments.append("--verify-before-stop")
            if p.get("empty_candidate_search", 0):
                arguments += ["--empty-candidate-search", str(p["empty_candidate_search"])]
            complete_size = len(manifest["prompts"]) * p["repeats"] * len(p["bits"])
            if len(manifest["tasks"]) < complete_size:
                arguments += ["--limit", str(len(manifest["tasks"]))]
            source = ROOT / "source-snapshots" / (
                profile["sources"]["Ghostext-paper/scripts/stopping_experiment.py"] + ".py")
            assert "max_tokens = 2 * bits" in source.read_text()
            details = {
                "generation_horizon": "2 * message_bits",
                "ideal_theorem_horizon": "uncapped",
                "control": "independent Q draws at the observed stego length",
                "randomness": "public deterministic experimental PRNG tapes; not a cryptographic secrecy test",
                "scope": "capped published-rule adapter" if not p["verify_before_stop"]
                         else "separate mechanical verification-before-stop ablation",
            }
        elif schema == "repair-matrix-v1":
            p = manifest["parameters"]
            repeats = max(t["repeat"] for t in manifest["tasks"]) + 1
            guards = sorted({t["guard_bits"] for t in manifest["tasks"]})
            entry = "run_repair_matrix.py"
            arguments = ["--backend", backend, "--model-path", model,
                         "--out-dir", "<NEW_OUTPUT_DIRECTORY>", "--threads", str(p["threads"]),
                         "--repeats", str(repeats), "--guards", *map(str, guards)]
            complete_size = (20 if backend == "qwen" else 10) * repeats * len(guards)
            if len(manifest["tasks"]) < complete_size:
                arguments += ["--limit", str(len(manifest["tasks"]))]
            details = {
                "header_token_cap": 2048, "body_token_cap": 4096,
                "max_attempts": 10, "tail_tokens": 0,
                "randomness": "OS packet/guard randomness; statistically rerunnable, saved text exactly replayable on the compatible stack",
            }
        elif schema == "keyless-bootstrap-v1":
            entry = "run_keyless_attack.py"
            arguments = ["--model-path", model, "--threads", str(manifest["threads"]),
                         "--out-dir", "<NEW_OUTPUT_DIRECTORY>", "--include-grid"]
            details = {"public_bootstrap_bytes": 60, "probe_horizon": 2048, "guards": [0, 128],
                       "historical_control": "floating probabilities plus three raw-argmax fallbacks"}
        elif schema == "upstream-rrc-v1":
            entry = "run_upstream_rrc.py"
            arguments = ["--model-path", model, "--out-dir", "<NEW_OUTPUT_DIRECTORY>"]
            if manifest["pilot"]:
                arguments.append("--pilot")
            details = {
                **manifest["parameters"], "upstream": manifest["upstream"],
                "study_plan_sha256": manifest["study_plan_sha256"],
                "scope": "Excluded harness pilot" if manifest["pilot"]
                         else "Frozen current-upstream confirmatory cohort",
                "external_fetch": "Immutable RRC inputs are fetched and hash checked by the entry point.",
            }
        elif schema == "public-endpoint-replay-v1":
            entry = "run_public_endpoint_replay.py"
            arguments = ["--backend", backend, "--model-path", model,
                         "--threads", str(manifest["parameters"]["threads"]),
                         "--out-dir", "<NEW_OUTPUT_DIRECTORY>"]
            details = {**manifest["parameters"], "scope": manifest["scope"]}
            if name == "sp2027-endpoint-gpt2":
                details["interpretation"] = (
                    "Retained one-thread runtime-mismatch diagnostic, excluded from the same-source result.")
        elif schema == "upstream-public-replay-v1":
            entry = "replay_upstream_public_features.py"
            arguments = ["--model-path", model, "--out-dir", "<NEW_OUTPUT_DIRECTORY>"]
            details = {"selection": manifest["selection"], "scope": manifest["scope"],
                       "upstream": manifest["upstream"]}
        elif "selected_case_ids" in manifest:
            entry = "replay_reverse_failures.py"
            original = f"Ghostext-paper/results/sp2027-stopping-{backend}"
            # These targeted manifests predate a backend field; filenames identify their model.
            if "gpt2" in name:
                model, original = "<GPT2_DIRECTORY>", "Ghostext-paper/results/sp2027-stopping-gpt2"
            arguments = [original, "--model-path", model, "--out-dir", "<NEW_OUTPUT_DIRECTORY>"]
            details = {"selection": "all completed reverse-failure cases; a targeted diagnostic"}
        elif "test_passphrase" in manifest and "tasks" in manifest:
            entry = "run_expanded_policy_pilot.py"
            repeats = max(t["repeat"] for t in manifest["tasks"]) + 1
            arguments = ["--backend", backend, "--model-path", model,
                         "--out-dir", "<NEW_OUTPUT_DIRECTORY>", "--threads", str(manifest["threads"]),
                         "--repeats", str(repeats)]
            details = {"scope": "post-hoc development-case delivery pilot", "empty_candidate_search": 4096}
        if entry is None:
            raise ValueError(f"No command map for {name}")
        output[name] = {
            "source_profile": name, "entry_point": f"Ghostext-paper/scripts/{entry}",
            "working_directory": "root of the materialized profile",
            "arguments": arguments, "policy": details,
            "staged_input_files": profile.get("data_inputs", {}),
            "staged_input_aliases": profile.get("input_aliases", {}),
            "recorded_cpu_affinity": manifest.get("parameters", {}).get("cpu_affinity"),
            "package_environment": "results/sp2027-environment/python-packages.json",
        }
    target = ROOT / "results/sp2027-source-map/protocols.json"
    target.write_text(json.dumps(output, indent=2) + "\n")
    print("Mapped", len(output), "frozen profiles to commands and protocol parameters")


if __name__ == "__main__":
    main()
