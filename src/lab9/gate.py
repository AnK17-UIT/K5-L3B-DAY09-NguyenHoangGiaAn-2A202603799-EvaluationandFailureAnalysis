"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """Validate complete, aligned reports and enforce the same-version ratchet."""
    problems = []
    graded = {metric["id"] for metric in spec["metrics"]} & GRADERS.keys()
    graded.update(rule["metric"] for rule in spec.get("slices", []))
    coordinates = []
    for source, report in (("PR", pr), ("baseline", base)):
        manifest = report["manifest"]
        rows = report["rows"]
        seeds = set(manifest["seeds"])
        if len(rows) != manifest["items"] * len(manifest["seeds"]):
            problems.append(f"{source} row count differs from manifest items × seeds")
        pairs = {
            (row["item_id"], row["seed"]): frozenset(row.get("slices") or [])
            for row in rows
        }
        if len(pairs) != len(rows):
            problems.append(f"{source} contains duplicate (item_id, seed) rows")
        item_ids = {item for item, _ in pairs}
        if (len(item_ids) != manifest["items"] or len(seeds) != len(manifest["seeds"])
                or pairs.keys() != {(item, seed) for item in item_ids for seed in seeds}):
            problems.append(f"{source} rows do not cover the manifest item × seed grid")
        coordinates.append(pairs)

        if report.get("evaluator_failures"):
            problems.append(f"{source} contains evaluator failures")
        for metric, value in report["metrics"].items():
            if value is not None and not _finite_score(value):
                problems.append(f"{source} metric {metric} is not finite")
        for metric in sorted(graded):
            count = sum(not _finite_score(row.get(metric)) for row in rows)
            if count:
                problems.append(f"{source} metric {metric} has {count} missing or invalid row scores")

    current, reference = coordinates
    if current.keys() != reference.keys():
        problems.append("PR (item_id, seed) pairs differ from the baseline")
    elif current != reference:
        problems.append("PR slice tags differ from the baseline")

    if base_spec is not None and spec["eval_set_version"] == base_spec["eval_set_version"]:
        current_metrics = {metric["id"]: metric for metric in spec["metrics"]}
        for previous in base_spec["metrics"]:
            mid = previous["id"]
            rule = current_metrics.get(mid)
            if rule is None or _loosened(
                rule.get("threshold", {}), previous.get("threshold", {}),
                rule.get("blocking"), previous.get("blocking"),
            ):
                problems.append(f"ratchet: metric {mid} was removed or loosened")

        current_slices = {(rule["name"], rule["metric"]): rule for rule in spec.get("slices", [])}
        for previous in base_spec.get("slices", []):
            key = previous["name"], previous["metric"]
            rule = current_slices.get(key)
            if rule is None or _loosened(rule, previous, rule.get("blocking"), previous.get("blocking")):
                problems.append(f"ratchet: slice {key[0]}/{key[1]} was removed or loosened")
    return problems


def _finite_score(value) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def _loosened(current: dict, previous: dict, blocking: bool, was_blocking: bool) -> bool:
    if was_blocking and not blocking:
        return True
    if previous.get("no_significant_drop") and not current.get("no_significant_drop"):
        return True
    if "min" in previous and not current.get("min", -math.inf) >= previous["min"]:
        return True
    return any(
        limit in previous and not current.get(limit, math.inf) <= previous[limit]
        for limit in ("max", "max_increase")
    )


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for rule in spec.get("slices", []):
        name, metric = rule["name"], rule["metric"]
        key = f"slice:{name}/{metric}"
        current = per_item(pr, metric, slice_name=name)
        reference = per_item(base, metric, slice_name=name)
        if not current or current.keys() != reference.keys():
            failed = True
            detail = "missing or unmatched item scores"
        else:
            value = sum(current.values()) / len(current)
            floor = rule.get("min")
            failed = floor is not None and value < floor
            detail = f"{value:.4f}" if floor is None else f"{value:.4f} (min {floor:g})"
            if rule.get("no_significant_drop"):
                items = sorted(current)
                delta, low, high = stats.paired_bootstrap(
                    [current[item] for item in items],
                    [reference[item] for item in items],
                    n_resamples=bs.get("n_resamples", 1000),
                    rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95),
                )
                failed = failed or high < 0
                detail += f" Δ {delta:+.3f} CI [{low:+.3f}, {high:+.3f}]"
        verdict = "ok"
        if failed:
            verdict = "BLOCK" if rule.get("blocking") else "warn"
            if rule.get("blocking"):
                blocked.append(key)
        lines.append(f"  {key:<36} {detail} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
