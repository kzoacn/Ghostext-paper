from __future__ import annotations

import hashlib
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any, Callable, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
PAPER_ROOT = SCRIPT_DIR.parent
GHOSTEXT_ROOT = PAPER_ROOT.parent / "Ghostext"
GHOSTEXT_SRC = GHOSTEXT_ROOT / "src"

if str(GHOSTEXT_SRC) not in sys.path:
    sys.path.insert(0, str(GHOSTEXT_SRC))

FIXED_DEMO_PASSPHRASE_POLICY = (
    "fixed local demo passphrase reused across released baseline and aligned comparison "
    "for reproducibility"
)
FULL_COVER_TEXT_POLICY = (
    "per-run JSONL releases full cover text; summary bundles retain hashes and aggregate metrics"
)


def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sh(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except Exception:
        return "unknown"
    return out.strip() or "unknown"


def quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def sha256_hex(data: bytes | str) -> str:
    payload = data.encode("utf-8") if isinstance(data, str) else data
    return hashlib.sha256(payload).hexdigest()


def deterministic_seed(*parts: object) -> int:
    payload = json.dumps(parts, ensure_ascii=False, sort_keys=False).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big", signed=False)


def parse_cmake_set_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    pattern = re.compile(r"""^\s*set\(([A-Za-z0-9_]+)\s+(?:"([^"]*)"|([^\s\)]+))\)\s*$""")
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.match(line)
        if match is None:
            continue
        values[match.group(1)] = match.group(2) or match.group(3) or ""
    return values


def read_llama_cpp_build_info() -> dict[str, Any]:
    info: dict[str, Any] = {
        "llama_cpp_python_version": "unknown",
        "llama_cpp_commit_sha": "unknown",
        "llama_cpp_build_number": "unknown",
        "ggml_build_commit": "unknown",
        "ggml_build_number": "unknown",
        "ggml_version": "unknown",
        "llama_system_info": "unknown",
    }
    try:
        import llama_cpp
    except Exception:
        return info

    try:
        info["llama_cpp_python_version"] = importlib.metadata.version("llama-cpp-python")
    except importlib.metadata.PackageNotFoundError:
        pass

    package_root = Path(inspect.getfile(llama_cpp)).resolve().parent.parent
    llama_cmake = package_root / "lib" / "cmake" / "llama" / "llama-config.cmake"
    ggml_cmake = package_root / "lib" / "cmake" / "ggml" / "ggml-config.cmake"
    llama_vars = parse_cmake_set_file(llama_cmake)
    ggml_vars = parse_cmake_set_file(ggml_cmake)
    info["llama_cpp_commit_sha"] = llama_vars.get("LLAMA_BUILD_COMMIT", info["llama_cpp_commit_sha"])
    info["llama_cpp_build_number"] = llama_vars.get("LLAMA_BUILD_NUMBER", info["llama_cpp_build_number"])
    info["ggml_build_commit"] = ggml_vars.get("GGML_BUILD_COMMIT", info["ggml_build_commit"])
    info["ggml_build_number"] = ggml_vars.get("GGML_BUILD_NUMBER", info["ggml_build_number"])
    info["ggml_version"] = ggml_vars.get("GGML_VERSION", info["ggml_version"])

    try:
        system_info = llama_cpp.llama_cpp.llama_print_system_info()
        if isinstance(system_info, bytes):
            info["llama_system_info"] = system_info.decode("utf-8", errors="replace").strip()
        else:
            info["llama_system_info"] = str(system_info).strip()
    except Exception:
        pass
    return info


def read_cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        for line in cpuinfo.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.lower().startswith("model name"):
                _, value = line.split(":", 1)
                return value.strip()
    output = sh(["lscpu"])
    for line in output.splitlines():
        if line.startswith("Model name:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def read_total_ram_gib() -> float:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return 0.0
    for line in meminfo.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.startswith("MemTotal:"):
            continue
        parts = line.split()
        if len(parts) < 2:
            break
        kib = float(parts[1])
        return kib / (1024.0 * 1024.0)
    return 0.0


def build_runtime_info() -> dict[str, Any]:
    llama_info = read_llama_cpp_build_info()
    return {
        "timestamp_utc": utc_timestamp(),
        "host": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_model": read_cpu_model(),
        "cpu_count_logical": os.cpu_count(),
        "ram_total_gib": round(read_total_ram_gib(), 2),
        "ghostext_git_head": sh(["git", "-C", str(GHOSTEXT_ROOT), "rev-parse", "HEAD"]),
        "paper_git_head": sh(["git", "-C", str(PAPER_ROOT), "rev-parse", "HEAD"]),
        **llama_info,
    }


def extract_model_provenance(
    *,
    model_path: Path,
    resolved_model_source: str,
    backend_metadata: dict[str, Any],
    llama_metadata: dict[str, Any],
) -> dict[str, Any]:
    base_models: list[dict[str, Any]] = []
    raw_count = llama_metadata.get("general.base_model.count", 0)
    try:
        base_model_count = int(raw_count)
    except Exception:
        base_model_count = 0
    for index in range(base_model_count):
        prefix = f"general.base_model.{index}."
        item = {
            "name": llama_metadata.get(prefix + "name"),
            "organization": llama_metadata.get(prefix + "organization"),
            "repo_url": llama_metadata.get(prefix + "repo_url"),
        }
        if any(value not in (None, "") for value in item.values()):
            base_models.append(item)

    return {
        "resolved_model_path": str(model_path),
        "resolved_model_source": resolved_model_source,
        "file_size_bytes": model_path.stat().st_size,
        "backend_metadata": backend_metadata,
        "gguf_metadata": {
            "general.architecture": llama_metadata.get("general.architecture"),
            "general.name": llama_metadata.get("general.name"),
            "general.basename": llama_metadata.get("general.basename"),
            "general.size_label": llama_metadata.get("general.size_label"),
            "general.license": llama_metadata.get("general.license"),
            "general.file_type": llama_metadata.get("general.file_type"),
            "tokenizer.ggml.model": llama_metadata.get("tokenizer.ggml.model"),
            "tokenizer.ggml.pre": llama_metadata.get("tokenizer.ggml.pre"),
        },
        "upstream_provenance": {
            "canonical_model_label": llama_metadata.get("general.name"),
            "base_models": base_models,
        },
    }


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    margin = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z * z) / (4.0 * total * total)))
    return (max(0.0, center - margin), min(1.0, center + margin))


def bootstrap_ci(
    values: list[float],
    statistic: Callable[[list[float]], float],
    *,
    iterations: int = 10000,
    confidence: float = 0.95,
    seed: int = 7,
) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    if len(values) == 1:
        return (values[0], values[0])
    rng = __import__("random").Random(seed)
    estimates: list[float] = []
    for _ in range(iterations):
        sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
        estimates.append(statistic(sample))
    estimates.sort()
    alpha = (1.0 - confidence) / 2.0
    lo = estimates[int(alpha * (len(estimates) - 1))]
    hi = estimates[int((1.0 - alpha) * (len(estimates) - 1))]
    return (lo, hi)


def roc_auc_score(labels: Iterable[int], scores: Iterable[float]) -> float:
    pairs = sorted(zip(scores, labels, strict=True), key=lambda item: item[0])
    n = len(pairs)
    if n == 0:
        return 0.0
    positives = sum(label for _, label in pairs)
    negatives = n - positives
    if positives == 0 or negatives == 0:
        return 0.0

    rank_sum = 0.0
    index = 0
    while index < n:
        tie_end = index + 1
        while tie_end < n and pairs[tie_end][0] == pairs[index][0]:
            tie_end += 1
        average_rank = (index + 1 + tie_end) / 2.0
        positive_in_tie = sum(label for _, label in pairs[index:tie_end])
        rank_sum += positive_in_tie * average_rank
        index = tie_end

    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def pearson_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0.0 or den_y == 0.0:
        return 0.0
    return num / (den_x * den_y)


def spearman_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    return pearson_correlation(_average_ranks(xs), _average_ranks(ys))


def _average_ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        average_rank = (cursor + 1 + end) / 2.0
        for index in order[cursor:end]:
            ranks[index] = average_rank
        cursor = end
    return ranks
