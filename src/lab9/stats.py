"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb
from numbers import Integral

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    counts = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for actual, predicted in zip(human, judge, strict=True):
        if actual not in ("PASS", POS) or predicted not in ("PASS", POS):
            raise ValueError("labels must be PASS or FAIL")
        prefix = "t" if actual == predicted else "f"
        suffix = "p" if predicted == POS else "n"
        counts[prefix + suffix] += 1
    return counts


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    counts = confusion(human, judge)
    tp = counts["tp"]
    predicted_fail = tp + counts["fp"]
    actual_fail = tp + counts["fn"]
    precision = tp / predicted_fail if predicted_fail else 0.0
    recall = tp / actual_fail if actual_fail else 0.0
    return precision, recall


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """Return Cohen's κ, or raise ValueError when chance agreement is 1."""
    counts = confusion(human, judge)
    n = sum(counts.values())
    actual_fail = counts["tp"] + counts["fn"]
    predicted_fail = counts["tp"] + counts["fp"]
    # Both agreement terms share n² as a denominator. Use counts to detect
    # undefined κ exactly, including the case of an empty sample.
    expected = actual_fail * predicted_fail + (n - actual_fail) * (n - predicted_fail)
    observed = (counts["tp"] + counts["tn"]) * n
    if expected == n * n:
        raise ValueError("Cohen's kappa is undefined for these labels")
    return (observed - expected) / (n * n - expected)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error and clip to [0, 1]."""
    denominator = sensitivity + specificity - 1
    if denominator == 0:
        raise ValueError("Rogan–Gladen is undefined when sensitivity + specificity is 1")
    corrected = (observed_rate + specificity - 1) / denominator
    return min(1.0, max(0.0, corrected))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy.stats import bootstrap

    if len(a) != len(b) or len(a) == 0:
        raise ValueError("paired bootstrap requires nonempty samples of equal length")
    differences = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    delta = float(np.mean(differences))
    if np.all(differences == differences[0]):
        return delta, delta, delta

    def mean_difference(pr, baseline, axis):
        return np.mean(pr - baseline, axis=axis)

    interval = bootstrap(
        (a, b), mean_difference, paired=True, method="percentile",
        n_resamples=n_resamples, rng=np.random.default_rng(rng),
        confidence_level=confidence,
    ).confidence_interval
    return delta, float(interval.low), float(interval.high)


def _validate_pass_counts(n: int, c: int, k: int) -> None:
    if any(isinstance(value, bool) or not isinstance(value, Integral) for value in (n, c, k)):
        raise ValueError("trial counts must be integers")
    if not (0 <= c <= n and 1 <= k <= n):
        raise ValueError("require 0 <= c <= n and 1 <= k <= n")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_pass_counts(n, c, k)
    total = comb(n, k)
    return (total - comb(n - c, k)) / total


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_pass_counts(n, c, k)
    return comb(c, k) / comb(n, k)
