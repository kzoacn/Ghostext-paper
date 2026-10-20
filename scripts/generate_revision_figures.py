#!/usr/bin/env python3
"""Create publication figures directly from retained experiment records."""
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

OUT = ROOT / "paper/figures"
SOURCES = []


def read(relative):
    path = ROOT / relative
    SOURCES.append(path)
    return json.loads(path.read_text())


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", pad_inches=.03,
                metadata={"Creator": "Matplotlib", "Author": "", "CreationDate": None,
                          "ModDate": None})
    plt.close(fig)


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Serif", "font.size": 8,
        "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "lines.linewidth": 1.4,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.spines.top": False, "axes.spines.right": False,
    })
    codec = read("results/sp2027-codec-audit/summary.json")["results"]
    dp = read("results/sp2027-stopping-dp/summary.json")["results"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0), constrained_layout=True)
    ax = axes[0]
    colors = ["#225ea8", "#d95f0e", "#756bb1"]
    for case, label, color, marker in [
        ("skew3", "Skewed 3-token source", colors[0], "o"),
        ("context_dependent", "Context-dependent source", colors[1], "s"),
    ]:
        rows = [r for r in codec if r["case"] == case]
        assert rows
        ax.semilogy([r["guard_bits"] for r in rows],
                    [r["transcript_tv"] for r in rows], marker=marker,
                    color=color, markersize=3.5, label=label)
    guards = np.linspace(0, 128, 129)
    ax.semilogy(guards, np.minimum(1., 32 * 4 / np.exp2(guards + 1)),
                "--", color="#555555", label=r"Bound ($N=4,T=32$)")
    ax.set(xlabel="Guard bits g", ylabel="Complete-transcript TV",
           xlim=(-2, 130), ylim=(1e-40, 2))
    ax.set_xticks([0, 32, 64, 96, 128])
    ax.set_yticks([1, 1e-10, 1e-20, 1e-30, 1e-40])
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.28), frameon=False)
    ax.set_title("(a) Rounding repair; stopping-matched reference", pad=7)
    ax = axes[1]
    rows = [r for r in dp if r["p_A"] == .75]
    bits = [r["message_bits"] for r in rows]
    for key, label, color, marker in [
        ("stego_band_probability", "Stopped source: in band", colors[0], "o"),
        ("control_band_probability", "Independent control: in band", colors[1], "s"),
        ("count_and_length_tv", "Count-and-length TV", colors[2], "^"),
    ]:
        ax.plot(bits, [r[key] for r in rows], marker=marker, markersize=3.5,
                color=color, label=label)
    ax.plot(bits, [0.] * len(bits), ":", color="#555555", label="Uniform-source TV control")
    ax.set_xscale("log", base=2)
    ax.set_xticks([8, 32, 128, 512, 2048], ["8", "32", "128", "512", "2048"])
    ax.set(xlabel="Message bits B", ylabel="Probability or TV", ylim=(-.035, 1.06))
    ax.set_title("(b) Stopping leakage; identical length marginals", pad=7)
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.28), frameon=False)
    save(fig, "finite-message-effects.pdf")

    # Only a completed analyzed cohort is eligible for a paper figure.
    cohorts = []
    for backend in ["gpt2", "qwen"]:
        directory = ROOT / f"results/sp2027-stopping-{backend}"
        if not (directory / "analysis.json").exists():
            continue
        summary = read(str((directory / "analysis.json").relative_to(ROOT)))
        if summary["observed_pairs"] != summary["planned_pairs"]:
            raise ValueError("Incomplete cohort")
        path = directory / "pairs.jsonl"
        SOURCES.append(path)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        cohorts.append((backend, rows))
    if cohorts:
        fig, axes = plt.subplots(len(cohorts), 2, figsize=(7.0, 2.05 * len(cohorts) + .2),
                                 squeeze=False, constrained_layout=True)
        for row_index, (backend, rows) in enumerate(cohorts):
            for column, bits in enumerate([128, 512]):
                ax = axes[row_index, column]
                selected = [r for r in rows if r["split"] == "test"
                            and r["message_bits"] == bits
                            and r["stego"]["status"] == r["natural"]["status"] == "complete"
                            and r["stego"]["canonical_text_roundtrip"]
                            and r["natural"]["canonical_text_roundtrip"]
                            and r["stego"]["tokens"] == r["natural"]["tokens"]]
                for label, legend, color in [
                    ("stego", "Stopped source", colors[0]),
                    ("natural", "Independent control", colors[1]),
                ]:
                    gaps = np.sort([abs(r[label]["surprisal_bits"] - bits) for r in selected])
                    ax.step(np.r_[0, gaps], np.r_[0, np.arange(1, len(gaps) + 1) / len(gaps)],
                            where="post", label=legend, color=color)
                ax.set(xlabel=r"Absolute surprisal gap $|S-B|$ (bits)",
                       ylabel="Empirical CDF", ylim=(0, 1.03))
                ax.set_xscale("symlog", linthresh=1)
                ax.set_xticks([0, 1, 10, 100, 1000], ["0", "1", "10", "100", "1000"])
                ax.set_xlim(left=0)
                ax.set_title(f'{"GPT-2" if backend == "gpt2" else "Qwen3.5-2B"}, '
                             f'B={bits}; {len(selected)} held-out pairs')
        handles, labels = axes[-1, -1].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
        save(fig, "stopping-llm-gap.pdf")
    generated = [OUT / "finite-message-effects.pdf"]
    if cohorts:
        generated.append(OUT / "stopping-llm-gap.pdf")
    metadata = {
        "source_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in SOURCES},
        "outputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in generated},
    }
    destination = ROOT / "results/sp2027-figures/manifest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(metadata, indent=2) + "\n")
    print("\n".join(str(p.relative_to(ROOT)) for p in generated))


if __name__ == "__main__":
    main()
