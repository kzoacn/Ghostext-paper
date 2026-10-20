#!/usr/bin/env python3
"""Render manuscript tables from complete, validated analysis files."""
from __future__ import annotations
import argparse
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fixed(value):
    return format(Decimal(str(value)).quantize(Decimal(".001"), rounding=ROUND_HALF_UP), "f")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require-all", action="store_true")
    args = ap.parse_args()
    paths, blocks = [], []
    for policy, suffix in [("Strict", ""), ("Expanded", "-expanded")]:
        for backend, label in [("gpt2", "GPT-2"), ("qwen", "Qwen3.5-2B")]:
            path = ROOT / f"results/sp2027-stopping-{backend}{suffix}/analysis.json"
            if not path.exists():
                if args.require_all:
                    raise FileNotFoundError(path)
                continue
            data = json.loads(path.read_text())
            assert data["observed_pairs"] == data["planned_pairs"]
            paths.append(path)
            blocks.append((policy, label, data))
    lines = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Stopping-score results on held-out topic families. Eligible pairs are complete, canonical, and exactly length matched. The denominator counts all planned pairs. AUC intervals resample five test topic families; TPR/FPR use the threshold fitted only to development controls.}",
        r"\label{tab:stopping-llm}", r"\begin{tabular}{llrrrrrr}", r"\toprule",
        r"Source & Model & $B$ & Eligible/planned & Dev./test & AUC [95\% cluster interval] & TPR & FPR \\",
        r"\midrule",
    ]
    completion_lines = []
    for policy, label, data in blocks:
        for bits, group in data["by_message_bits"].items():
            score = group["algorithm_completion_analysis"]
            assert score["estimable"]
            lo, hi = score["auc_topic_cluster_95"]
            lines.append(
                f"{policy} & {label} & {bits} & {group['complete_pairs']}/{group['planned_pairs']} & "
                f"{score['development_pairs']}/{score['test_pairs']} & "
                f"{fixed(score['auc'])} [{fixed(lo)},{fixed(hi)}] & "
                f"{fixed(score['test_tpr'])} & {fixed(score['test_fpr'])}" + r" \\")
        ns = data["stego_statuses"].get("complete", 0)
        nn = data["natural_statuses"].get("complete", 0)
        attempted = data["planned_pairs"]
        failed_s, failed_n = attempted - ns, attempted - nn
        reverse = data["completed_but_reverse_recovery_failed"]
        completion_lines.append(
            f"{policy} & {label} & {attempted} & {ns} & {nn} & {failed_s}/{failed_n} & {reverse}" + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table*}"])
    tables = ROOT / "paper/tables"
    tables.mkdir(exist_ok=True)
    (tables / "stopping-results.tex").write_text("\n".join(lines) + "\n")
    status = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{All attempted stopping-study pairs. Failure counts are stego/control; failed prefixes remain in the artifact. Reverse mismatches count completed stego outputs and are sender-side checks, not independent receiver trials.}",
        r"\label{tab:stopping-outcomes}", r"\begin{tabular}{llrrrrr}", r"\toprule",
        r"Source & Model & Planned pairs & Stego complete & Control complete & Failures (S/C) & Reverse mismatches \\",
        r"\midrule", *completion_lines, r"\bottomrule", r"\end{tabular}", r"\end{table*}",
    ]
    (tables / "stopping-outcomes.tex").write_text("\n".join(status) + "\n")
    repair_lines = []
    for backend, label in [("gpt2", "GPT-2"), ("qwen", "Qwen3.5-2B")]:
        path = ROOT / f"results/sp2027-repair-{backend}/analysis.json"
        if not path.exists():
            if args.require_all:
                raise FileNotFoundError(path)
            continue
        paths.append(path)
        data = json.loads(path.read_text())
        for guard, r in data["by_guard"].items():
            probe = r["probe_on_complete_matched_pairs"][guard]
            repair_lines.append(
                f"{label} & {guard} & {r['deliveries']}/{r['evaluable_trials']} & "
                f"{r['first_attempt_deliveries']}/{r['evaluable_trials']} & {r['attempts']} & "
                f"{fixed(r['mean_net_bpt_given_delivery'])} & {r['complete_matched_pairs']} & "
                f"{probe['stego'].get('admissible', 0)}/{probe['natural'].get('admissible', 0)}" + r" \\")
    repair = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Fresh authenticated delivery trials under strict candidates, with 16-byte plaintexts and no natural tail. The interrupted/resumed Qwen3.5-2B $g=128$ case is reported separately and excluded here, leaving 39 evaluable trials in that row. Net rate conditions on delivery; probe counts use complete matched controls only.}",
        r"\label{tab:repair-matrix}", r"\begin{tabular}{lrrrrrrr}", r"\toprule",
        r"Model & $g$ & Delivered/evaluable & First attempt & Attempts & Net bits/token & Matched pairs & Accepts (S/C) \\",
        r"\midrule", *repair_lines, r"\bottomrule", r"\end{tabular}", r"\end{table*}",
    ]
    (tables / "repair-results.tex").write_text("\n".join(repair) + "\n")
    output = {
        "source_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "complete_inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "tables": {
            str((tables / name).relative_to(ROOT)):
                hashlib.sha256((tables / name).read_bytes()).hexdigest()
            for name in ["repair-results.tex", "stopping-outcomes.tex", "stopping-results.tex"]},
    }
    target = ROOT / "results/sp2027-tables/manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2) + "\n")
    print("Rendered tables from", len(paths), "completed analysis files")


if __name__ == "__main__":
    main()
