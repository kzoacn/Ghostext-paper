#!/usr/bin/env python3
"""Generate the new upstream and endpoint tables/figure from complete analyses."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "tmp/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze_upstream_rrc import eligible


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream-only", action="store_true")
    args = ap.parse_args()
    upstream = ROOT / "results/sp2027-upstream-gpt2"
    summary_path = upstream / "analysis.json"
    summary = json.loads(summary_path.read_text())
    assert summary["planned_secret_instances"] == summary["observed_secret_instances"] == 160
    paths = sorted((upstream / "cases").glob("*.json"))
    assert {p.name: sha(p) for p in paths} == summary["case_sha256"]
    rows = [json.loads(p.read_text()) for p in paths]
    table = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Current upstream RRC on GPT-2: held-out visible-text results. "
        r"Every row conditions on complete, canonical, exactly length-matched pairs. "
        r"Intervals resample eligible test prompt clusters (5000 draws); thresholds use development controls. "
        r"Length-only AUC is exactly 0.5 throughout. Fixed-endpoint recovery failures are retained.}",
        r"\label{tab:upstream-results}",
        r"\begin{tabular}{lrrrrr}", r"\toprule",
        r"Arm & $B$ (bits) & Dev./test pairs & Test prompts & AUC [95\% cluster interval] & TPR/FPR \\",
        r"\midrule",
    ]
    for variant, label in [("unverified", "Unverified stop"), ("verified", "Verified stop"),
                           ("fixed_endpoint", "Fixed endpoint")]:
        for bits in ["128", "512"]:
            value = summary["variants"][variant]["by_message_bits"][bits]["primary"]
            low, high = value["auc_prompt_cluster_95"]
            table.append(
                f"{label} & {bits} & {value['development_pairs']}/{value['test_pairs']} & "
                f"{len(value['test_prompt_ids'])} & "
                f"${value['auc']:.3f}\\;[{low:.3f},{high:.3f}]$ & "
                f"${value['test_tpr']:.3f}/{value['test_fpr']:.3f}$ \\\\")
    table += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    table_path = ROOT / "paper/tables/upstream-results.tex"
    table_path.write_text("\n".join(table) + "\n")
    inputs = {str(summary_path.relative_to(ROOT)): sha(summary_path)}
    inputs.update({str(p.relative_to(ROOT)): sha(p) for p in paths})
    table_outputs = {str(table_path.relative_to(ROOT)): sha(table_path)}
    if not args.upstream_only:
        endpoint_table = [
            r"\begin{table}[t]", r"\centering",
            r"\caption{Post-hoc public endpoint replay of guarded no-tail deliveries. "
            r"Counts use the original eligible pair sets and known 16-byte plaintext length.}",
            r"\label{tab:endpoint-replay}", r"\begin{tabular}{lrrr}", r"\toprule",
            r"Model & Paired texts & Stego endpoint & Natural endpoint \\", r"\midrule"]
        for backend, directory in [("GPT-2", "sp2027-endpoint-gpt2-corrected"),
                                   ("Qwen", "sp2027-endpoint-qwen")]:
            path = ROOT / "results" / directory / "analysis.json"
            data = json.loads(path.read_text())
            assert data["source_replay_check_passed"]
            inputs[str(path.relative_to(ROOT))] = sha(path)
            n = data["pairs"]
            endpoint_table.append(
                f"{backend} & {n} & {data['rates']['stego']['hits']}/{n} & "
                f"{data['rates']['natural']['hits']}/{n} \\\\")
        endpoint_table += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
        path = ROOT / "paper/tables/endpoint-replay.tex"
        path.write_text("\n".join(endpoint_table) + "\n")
        table_outputs[str(path.relative_to(ROOT))] = sha(path)
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "font.size": 8, "axes.titlesize": 8,
        "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "lines.linewidth": 1.4, "pdf.fonttype": 42,
        "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(7., 3.7), constrained_layout=True)
    for i, variant in enumerate(["verified", "fixed_endpoint"]):
        for j, bits in enumerate([128, 512]):
            ax = axes[i, j]
            selected = [r for r in rows if r["split"] == "test"
                        and r["message_bits"] == bits and eligible(r, variant)]
            for collection, label, color in [
                    ("variants", "Generated arm", "#225ea8"),
                    ("natural_controls", "Independent natural control", "#d95f0e")]:
                gaps = np.sort([abs(r[collection][variant]["surprisal_bits"] - bits)
                                for r in selected])
                ax.step(np.r_[0, gaps], np.r_[0, np.arange(1, len(gaps) + 1) / len(gaps)],
                        where="post", label=label, color=color)
            arm = "Verified stop" if variant == "verified" else "Fixed endpoint"
            ax.set_title(f"{arm}, B={bits}; {len(selected)} held-out pairs")
            ax.set(xlabel=r"Absolute information gap $|I-B|$ (bits)",
                   ylabel="Empirical CDF", ylim=(0, 1.03))
            ax.set_xscale("symlog", linthresh=1)
            ax.set_xticks([0, 1, 10, 100, 1000], ["0", "1", "10", "100", "1000"])
            ax.set_xlim(left=0)
    handles, labels = axes[-1, -1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    figure_path = ROOT / "paper/figures/upstream-endpoint-control.pdf"
    fig.savefig(figure_path, bbox_inches="tight", pad_inches=.03,
                metadata={"Creator": "Matplotlib", "Author": "", "CreationDate": None, "ModDate": None})
    plt.close(fig)
    for name, outputs in [
            ("sp2027-accept-tables", table_outputs),
            ("sp2027-accept-figures", {str(figure_path.relative_to(ROOT)): sha(figure_path)})]:
        directory = ROOT / "results" / name
        directory.mkdir(parents=True, exist_ok=True)
        metadata = {
            "source_script_sha256": sha(Path(__file__)), "upstream_only": args.upstream_only,
            "inputs": inputs, "outputs": outputs}
        (directory / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Generated upstream materials" + ("" if args.upstream_only else " and endpoint table"))


if __name__ == "__main__":
    main()
