# Merged Real-Backend Baseline Summary

Generated at `2026-04-21T10:50:13Z` from released baseline artifacts.

Merged inputs:
- `/mnt/d/work/Ghostext-paper/results/real-backend-baseline-r1`
- `/mnt/d/work/Ghostext-paper/results/real-backend-baseline-r2`

Baseline policy: `top_p=0.995`, `max_candidates=64`, `min_entropy_bits=0.0`, `total_frequency=4096`.

## Runtime and Provenance

| Field | Value |
|---|---|
| Ghostext git head | `b1eb84c74b6dcf2cfccf7909883d1bc05911b41d` |
| Host | `kzoacn-PC` |
| Platform | `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39` |
| Python | `3.12.12` |
| Model id | `Qwen/Qwen3.5-2B` |
| Backend id | `llama-cpp-qwen3` |
| Tokenizer hash | `0fa174fde298ae08d4f75613b3d06c9c027f382133c93e41b3bcf8e134dd8b75` |
| llama.cpp commit SHA | not captured in released source summaries |

## Overall

| Metric | Value |
|---|---|
| Decode success rate | 18/18=1.000 |
| Failure histogram | {} |
| Encode latency (s) | median 50.56, p90 88.75, p99 215.40 |
| Decode latency (s) | median 34.87, p90 54.13, p99 63.92 |
| Encode bits/token | mean 2.478 (median 2.586, min 1.894, max 3.071) |
| Attempts used | mean 1.944, max 5 |
| Approx. single-attempt encode time (s) | 30.57 |

## By Language

| Lang | Trials | Encode median (s) | Decode median (s) | Mean bits/token |
|---|---:|---:|---:|---:|
| en | 9 | 38.62 | 27.27 | 2.586 |
| zh | 9 | 55.57 | 36.96 | 2.370 |

