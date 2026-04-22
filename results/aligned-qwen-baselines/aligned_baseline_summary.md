# Aligned Qwen Baseline Comparison

Generated at `2026-04-21T13:48:52Z` with backend `Qwen/Qwen3.5-2B`.

| Method | n | Success | Encode median (s) | Decode median (s) | Plaintext bits/token | Payload bits/token | Payload bit entropy | One fraction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ghostext full | 6 | 6/6 | 31.85 | 31.24 | 0.975 | 2.452 | 1.000 | 0.499 |
| NLS-style AEAD packet | 6 | 4/6 | 46.21 | 46.24 | 0.655 | 1.747 | 1.000 | 0.491 |
| NLS-style UTF-8 | 6 | 5/6 | 8.50 | 8.53 | 2.487 | 2.487 | 0.991 | 0.488 |

## Failure Histograms

- `Ghostext full`: `{}`
- `NLS-style AEAD packet`: `{"stall_detected": 2}`
- `NLS-style UTF-8`: `{"stall_detected": 1}`
