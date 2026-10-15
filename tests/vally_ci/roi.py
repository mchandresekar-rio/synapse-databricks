from __future__ import annotations


def _rate(metrics: dict) -> float:
    if "pass_rate" in metrics:
        return float(metrics["pass_rate"])
    total = int(metrics.get("case_count", 0))
    return float(metrics.get("passed_count", 0)) / total if total else 0.0


def _regression(baseline: float, skill: float) -> float:
    if baseline == 0:
        return 0.0 if skill == 0 else float("inf")
    return (skill - baseline) / baseline


def compute_roi_verdict(
    baseline: dict,
    skill: dict,
    *,
    min_pass_rate_gain: float = 0.0,
    min_score_gain: float = 0.0,
    max_cost_regression: float = 0.25,
) -> dict:
    """Compare without-skill and with-skill metrics using explicit quality/cost gates."""

    baseline_pass = _rate(baseline)
    skill_pass = _rate(skill)
    baseline_score = float(baseline.get("score") or 0)
    skill_score = float(skill.get("score") or 0)
    pass_gain = skill_pass - baseline_pass
    score_gain = skill_score - baseline_score
    duration_regression = _regression(
        float(baseline.get("duration_seconds") or 0),
        float(skill.get("duration_seconds") or 0),
    )
    token_regression = _regression(
        float(baseline.get("tokens") or 0),
        float(skill.get("tokens") or 0),
    )

    quality_ok = pass_gain >= min_pass_rate_gain and score_gain >= min_score_gain
    quality_improved = pass_gain > 0 or score_gain > 0
    cost_ok = (
        duration_regression <= max_cost_regression
        and token_regression <= max_cost_regression
    )
    if quality_ok and quality_improved and cost_ok:
        verdict = "positive"
    elif quality_ok and not quality_improved and cost_ok:
        verdict = "neutral"
    else:
        verdict = "negative"

    reasons = [
        f"pass-rate delta {pass_gain:+.3f}",
        f"score delta {score_gain:+.3f}",
        f"duration change {duration_regression:+.1%}",
        f"token change {token_regression:+.1%}",
    ]
    return {
        "schema_version": 1,
        "verdict": verdict,
        "quality_gate_passed": quality_ok,
        "cost_gate_passed": cost_ok,
        "deltas": {
            "pass_rate": pass_gain,
            "score": score_gain,
            "duration_ratio": duration_regression,
            "token_ratio": token_regression,
        },
        "reasons": reasons,
    }
