# Merged Real-Backend Baseline Summary

Generated at `2026-04-22T06:42:06Z` from released baseline artifacts.

Merged inputs:
- `/mnt/d/work/Ghostext-paper/results/real-backend-baseline-r1`
- `/mnt/d/work/Ghostext-paper/results/real-backend-baseline-r2`

Baseline policy: `top_p=0.995`, `max_candidates=64`, `min_entropy_bits=0.0`, `total_frequency=4096`.

## Runtime and Provenance

| Field | Value |
|---|---|
| Ghostext git head | `b1eb84c74b6dcf2cfccf7909883d1bc05911b41d` |
| Paper git head | `ac8a422dd76df4409d8488241447e040a75f564b` |
| Host | `KZ-ThinkBook` |
| Platform | `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39` |
| Python | `3.12.3` |
| CPU model | `AMD Ryzen 7 8845H w/ Radeon 780M Graphics` |
| RAM (GiB) | `13.55` |
| llama-cpp-python version | `0.3.20` |
| llama.cpp build commit | `f49e917` |
| ggml build commit | `f49e917-dirty` |
| Model id | `Qwen/Qwen3.5-2B` |
| Canonical GGUF name | `Qwen3.5 2B` |
| Backend id | `llama-cpp-qwen3` |
| Tokenizer hash | `0fa174fde298ae08d4f75613b3d06c9c027f382133c93e41b3bcf8e134dd8b75` |

## Overall

| Metric | Value |
|---|---|
| Decode success rate | 18/18=1.000 (Wilson 95% CI: [0.824, 1.000]) |
| Failure histogram | `{}` |
| Encode latency (s) | median 58.18, p90 108.16, p99 153.39; bootstrap 95% CI [34.73, 73.60] |
| Decode latency (s) | median 35.73, p90 65.94, p99 69.72; bootstrap 95% CI [31.26, 58.92] |
| Encode bits/token | mean 2.448 (median 2.405, min 1.705, max 3.144); bootstrap 95% CI [2.286, 2.616] |
| Attempts used | mean 1.778, max 4, histogram `{"1": 11, "2": 2, "3": 3, "4": 2}` |
| Approx. single-attempt encode time (s) | 35.28 |
| Bhat TV total | mean 24.499, median 24.267 |

## By Language

| Lang | Trials | Encode median (s) | Decode median (s) | Mean bits/token | Attempts histogram |
|---|---:|---:|---:|---:|---|
| en | 9 | 35.80 | 33.02 | 2.662 | `{"1": 7, "2": 1, "3": 1}` |
| zh | 9 | 65.87 | 39.34 | 2.234 | `{"1": 4, "2": 1, "3": 2, "4": 2}` |

