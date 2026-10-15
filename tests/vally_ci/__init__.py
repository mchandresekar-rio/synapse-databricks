"""Deterministic, repository-local helpers for Vally CI."""

from .artifacts import redact_result_tree
from .coverage import build_coverage_report
from .normalize import (
    MalformedResultError,
    NoResultsError,
    NormalizationError,
    normalize_results,
)
from .reporting import build_summary, classify_failure, redact
from .roi import compute_roi_verdict
from .selection import (
    CoverageError,
    detect_changed_skills,
    enforce_coverage,
    select_specs,
)
from .sharding import aggregate_shard_results, plan_weighted_shards

__all__ = [
    "CoverageError",
    "MalformedResultError",
    "NoResultsError",
    "NormalizationError",
    "aggregate_shard_results",
    "build_coverage_report",
    "build_summary",
    "classify_failure",
    "compute_roi_verdict",
    "detect_changed_skills",
    "enforce_coverage",
    "normalize_results",
    "plan_weighted_shards",
    "redact",
    "redact_result_tree",
    "select_specs",
]
