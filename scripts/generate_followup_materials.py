#!/usr/bin/env python3
"""Render complete all-text results and independent endpoint-budget curves."""
from __future__ import annotations

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

MODELS = [("gpt2", "GPT-2"), ("qwen25", "Qwen2.5-0.5B")]
VARIANTS = [("unverified", "Unverified"), ("verified", "Verified"),
            ("fixed_endpoint", "Independent endpoint")]
MULTIPLIERS = ["1.00", "1.25", "1.50", "2.00"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inputs, outputs, evidence = {}, {}, {}
    def load(relative):
        path = ROOT / relative
        value = json.loads(path.read_text())
        inputs[relative] = sha(path)
        return value
    for model, _ in MODELS:
        upstream = load(f"results/sp2027-upstream-{model}/analysis.json")
        visible = load(f"results/sp2027-observable-{model}/analysis.json")
        budget = load(f"results/sp2027-budget-{model}/analysis.json")
        fidelity = load(f"results/sp2027-observable-fidelity/{model}.json")
        assert upstream["planned_secret_instances"] == upstream["observed_secret_instances"] == 160
        assert budget["planned_instances"] == budget["observed_instances"] == 160
        assert visible["arm_pairs"] == 480 and fidelity["counts"]["all_output_bindings"] == 960
        assert fidelity["all_checked_paths_match"]
        evidence[model] = {"upstream": upstream, "observable": visible, "budget": budget}
    certificate = load("results/sp2027-verified-certificate/summary.json")
    all_emitted = all(e["observable"]["all_planned_generations_complete"] for e in evidence.values())
    population = (
        "All planned generations complete, so every published string enters."
        if all_emitted else
        "The all-attempt population includes explicit no-output observations; "
        "separate emitted-string denominators are retained in the analyses.")
    table = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Public-score results on all planned upstream outputs. "
        + population +
        r" Each model/payload/arm has 40 development and 40 test observations per class, "
        r"with ten test prompt clusters. Intervals use 5000 prompt-cluster resamples; "
        r"TPR/FPR use the fixed development-quantile rule. Canonicality and receiver success do not filter rows.}",
        r"\label{tab:upstream-observable}", r"\begin{tabular}{lrlrrr}", r"\toprule",
        r"Model & $B$ & Arm & AUC [95\% cluster interval] & TPR & FPR \\",
        r"\midrule",
    ]
    for model, label in MODELS:
        for bits in ["128", "512"]:
            for variant, arm in VARIANTS:
                result = evidence[model]["observable"]["variants"][variant]["by_message_bits"][bits]["all_attempts"]
                assert result["development_pairs"] == result["test_pairs"] == 40
                assert len(result["test_prompt_ids"]) == 10
                low, high = result["auc_prompt_cluster_95"]
                table.append(
                    f"{label} & {bits} & {arm} & "
                    f"${result['auc']:.3f}\\;[{low:.3f},{high:.3f}]$ & "
                    f"${result['test_tpr']:.3f}$ & ${result['test_fpr']:.3f}$ \\\\")
        if model != MODELS[-1][0]:
            table.append(r"\midrule")
    table += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    path = ROOT / "paper/tables/upstream-observable-results.tex"
    path.write_text("\n".join(table) + "\n")
    outputs[str(path.relative_to(ROOT))] = sha(path)

    budget_table = [
        r"\begin{table*}[t]", r"\centering",
        r"\caption{Independent endpoint budgets. Each recovery cell gives ID/text "
        r"recoveries out of 80 planned instances, including generation and decoding failures. "
        r"Rates are payload bits per prescribed token budget, not successful-delivery throughput.}",
        r"\label{tab:upstream-budget}", r"\begin{tabular}{lrrrrrr}", r"\toprule",
        r"Model & $B$ & $N$ & $\lceil1.25N\rceil$ & $\lceil1.5N\rceil$ & $2N$ & Rate at $N$/$2N$ \\",
        r"\midrule",
    ]
    for model, label in MODELS:
        for bits in ["128", "512"]:
            result = evidence[model]["budget"]["by_message_bits"][bits]
            cells = []
            for multiplier in MULTIPLIERS:
                value = result[multiplier]
                assert value["planned_instances"] == 80 and value["prompt_clusters"] == 20
                cells.append(f"{value['id_recovery_successes']}/{value['text_recovery_successes']}")
            first = result["1.00"]["aggregate_bits_per_prescribed_token"]
            last = result["2.00"]["aggregate_bits_per_prescribed_token"]
            budget_table.append(
                f"{label} & {bits} & " + " & ".join(cells) + f" & {first:.3f}/{last:.3f} \\\\")
    budget_table += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
    path = ROOT / "paper/tables/upstream-budget-results.tex"
    path.write_text("\n".join(budget_table) + "\n")
    outputs[str(path.relative_to(ROOT))] = sha(path)

    plt.rcParams.update({
        "font.family": "DejaVu Serif", "font.size": 8, "axes.titlesize": 8,
        "axes.labelsize": 8, "legend.fontsize": 8, "xtick.labelsize": 7,
        "ytick.labelsize": 7, "lines.linewidth": 1.4, "pdf.fonttype": 42,
        "ps.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(7, 3.7), constrained_layout=True)
    x = np.array([float(m) for m in MULTIPLIERS])
    for column, (model, label) in enumerate(MODELS):
        for row, bits in enumerate(["128", "512"]):
            ax = axes[row, column]
            values = evidence[model]["budget"]["by_message_bits"][bits]
            for field, series_label, color, marker, linestyle in [
                    ("id", "Original token IDs", "#1f4e79", "o", "-"),
                    ("text", "Published text", "#b65f00", "s", "--")]:
                y = np.array([values[m][f"{field}_recovery_fraction"] for m in MULTIPLIERS])
                bounds = np.array([values[m][f"{field}_recovery_prompt_cluster_95"]
                                   for m in MULTIPLIERS])
                ax.plot(x, y, color=color, marker=marker, linestyle=linestyle,
                        markersize=3.5, label=series_label)
                ax.fill_between(x, bounds[:, 0], bounds[:, 1], color=color, alpha=.13, linewidth=0)
            ax.set(title=f"{label}, B={bits}", ylabel="Recovery fraction",
                   xlabel="Independent budget / N", ylim=(0, 1.03), xlim=(.97, 2.03))
            ax.set_xticks(x, ["1", "1.25", "1.5", "2"])
            ax.set_yticks([0, .25, .5, .75, 1])
            ax.grid(axis="y", color="#e3e3e3", linewidth=.5)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    path = ROOT / "paper/figures/upstream-budget-recovery.pdf"
    fig.savefig(path, bbox_inches="tight", pad_inches=.03,
                metadata={"Creator": "Matplotlib", "Author": "", "CreationDate": None, "ModDate": None})
    plt.close(fig)
    outputs[str(path.relative_to(ROOT))] = sha(path)

    directory = ROOT / "results/sp2027-followup-materials"
    directory.mkdir(parents=True, exist_ok=True)
    summary = {
        "all_planned_generations_complete": all_emitted,
        "models": {model: {
            "public_score_statuses": {
                variant: evidence[model]["observable"]["variants"][variant]["public_score_statuses"]
                for variant, _ in VARIANTS},
            "verified_all_text": {
                bits: evidence[model]["observable"]["variants"]["verified"]["by_message_bits"][bits]["all_attempts"]
                for bits in ["128", "512"]},
            "budget_counts": {
                bits: {m: {
                    key: evidence[model]["budget"]["by_message_bits"][bits][m][key]
                    for key in ["planned_instances", "id_recovery_successes", "text_recovery_successes",
                                "canonical_complete_outputs", "aggregate_bits_per_prescribed_token"]}
                    for m in MULTIPLIERS} for bits in ["128", "512"]},
        } for model, _ in MODELS},
        "finite_certificate_lower_bounds": {
            str(row["bits"]): row["tv_lower_decimal_rounded_down"]
            for row in certificate["certificates"]},
    }
    path = directory / "summary.json"
    path.write_text(json.dumps(summary, indent=2) + "\n")
    outputs[str(path.relative_to(ROOT))] = sha(path)
    (directory / "manifest.json").write_text(json.dumps({
        "source_script_sha256": sha(Path(__file__)), "inputs": inputs, "outputs": outputs,
        "scope": "Complete frozen analyses; generation/recovery failures retained in the stated populations.",
    }, indent=2) + "\n")
    print("Generated both-model observable table, recovery table/figure, and finite-certificate summary")


if __name__ == "__main__":
    main()
