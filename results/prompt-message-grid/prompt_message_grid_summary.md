# Prompt-Message Grid Summary

Generated at `2026-04-22T19:24:02Z`.

## Overall

| Metric | Value |
|---|---|
| Decode success rate | 100/100=1.000 (Wilson 95% CI: [0.963, 1.000]) |
| Failure histogram | `{}` |
| Encode latency (s) | mean 50.56, median 37.74, p90 74.69, p99 196.55 |
| Decode latency (s) | mean 38.02, median 34.47, p90 58.07, p99 72.22 |
| End-to-end latency (s) | mean 88.58, median 74.95 |
| Encode bits/token | mean 2.619, median 2.677, min 1.099, max 3.213 |
| Packet length (bytes) | mean 167.1, median 159.0, min 119.0, max 235.0 |
| Attempts used | mean 1.40, median 1.00, max 6 |

## By Prompt Language

| Language | Trials | Success | Encode median (s) | Decode median (s) | Mean bits/token | Attempts mean |
|---|---:|---:|---:|---:|---:|---:|
| en | 50 | 50/50 | 35.04 | 34.21 | 2.686 | 1.18 |
| zh | 50 | 50/50 | 38.90 | 37.09 | 2.552 | 1.62 |

## By Message Length

| Length | Trials | Success | Encode median (s) | Decode median (s) | Mean bits/token | Mean packet bytes |
|---|---:|---:|---:|---:|---:|---:|
| long | 20 | 20/20 | 60.22 | 58.11 | 2.615 | 231.0 |
| medium | 40 | 40/40 | 42.31 | 37.43 | 2.594 | 170.0 |
| short | 40 | 40/40 | 27.90 | 26.45 | 2.645 | 132.2 |

## Runtime and Provenance

| Field | Value |
|---|---|
| Ghostext git head | `42321c805caf10dac232650dab7de84826bfa51e` |
| Paper git head | `222c331bb4df76b6894ed8b13cb01805689ff896` |
| Host | `kzoacn-PC` |
| Platform | `Linux-6.6.87.2-microsoft-standard-WSL2-x86_64-with-glibc2.39` |
| Python | `3.12.12` |
| CPU model | `AMD Ryzen 7 7800X3D 8-Core Processor` |
| RAM (GiB) | `30.92` |
| llama-cpp-python version | `0.3.20` |
| llama.cpp build commit | `f49e917` |
| ggml build commit | `f49e917-dirty` |
| Model id | `Qwen/Qwen3.5-2B` |
| Canonical GGUF name | `Qwen3.5 2B` |
| Backend id | `llama-cpp-qwen3` |
| Tokenizer hash | `0fa174fde298ae08d4f75613b3d06c9c027f382133c93e41b3bcf8e134dd8b75` |

