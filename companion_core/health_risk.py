"""Multi-feature physiological screening. Not diagnosis.

Uses baseline deviation, trends, persistence, signal quality, and environment.
A compact exported tree may refine the score; missing model falls back to this engine.
"""

from companion_core.config import HEALTH
from companion_core.types import HealthFeatures, HealthResult, HealthStatus, Baseline


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def heuristic_risk(f: HealthFeatures, baseline: Baseline) -> tuple[float, str]:
    if f.signal_quality < HEALTH.signal_quality_min:
        return 0.0, "low_signal_quality_no_alert"
    if not f.valid:
        return 0.0, "insufficient_features"

    parts = []
    score = 0.0

    hr_dev = abs(f.hr_dev or 0.0)
    spo2_dev = max(0.0, f.spo2_dev or 0.0)
    temp_dev = abs(f.temp_dev or 0.0)
    hr_tr = abs(f.hr_trend or 0.0) / 4.0
    spo2_tr = max(0.0, -(f.spo2_trend or 0.0)) / 1.5
    temp_tr = abs(f.temperature_trend or 0.0) / 0.4

    score += 0.22 * _clip01((hr_dev - 0.8) / 2.0)
    score += 0.28 * _clip01((spo2_dev - 0.3) / 1.5)
    score += 0.18 * _clip01((temp_dev - 0.6) / 1.8)
    score += 0.08 * _clip01(hr_tr)
    score += 0.10 * _clip01(spo2_tr)
    score += 0.06 * _clip01(temp_tr)
    score += 0.08 * f.persistence

    # Environmental context only mildly scales physiological concern (heat/humidity/air).
    env = 1.0
    if f.ambient_temp is not None and f.ambient_temp >= 34:
        env += 0.05
    if f.humidity is not None and f.humidity >= 85:
        env += 0.03
    if f.mq135_relative is not None and f.mq135_relative >= 0.7:
        env += 0.04
    score *= env

    if hr_dev > 1.0:
        parts.append("hr_baseline_dev")
    if spo2_dev > 0.5:
        parts.append("spo2_baseline_dev")
    if temp_dev > 0.8:
        parts.append("temp_baseline_dev")
    if f.persistence > 0.4:
        parts.append("persistence")

    reason = ",".join(parts) if parts else "within_personal_pattern"
    return _clip01(score), reason


def status_from_score(score: float, f: HealthFeatures) -> HealthStatus:
    if f.signal_quality < HEALTH.signal_quality_min or not f.valid:
        return HealthStatus.INSUFFICIENT if not f.valid else HealthStatus.RECHECK
    if score >= HEALTH.risk_elevated:
        return HealthStatus.ELEVATED
    if score >= HEALTH.risk_recheck:
        return HealthStatus.RECHECK
    return HealthStatus.NORMAL


def combine_tree_score(heuristic: float, tree_score: float | None) -> float:
    if tree_score is None:
        return heuristic
    return 0.55 * heuristic + 0.45 * tree_score


def make_result(
    f: HealthFeatures,
    baseline: Baseline,
    score: float,
    reason: str,
    demo_mode: bool,
    used_tree: bool,
) -> HealthResult:
    st = status_from_score(score, f)
    return HealthResult(
        risk_score=round(score, 4),
        status=st,
        features=f,
        baseline=baseline,
        edge_ai=True,
        model_name=HEALTH.model_name if used_tree else "health_heuristic_v1",
        model_version=HEALTH.model_version if used_tree else "1.0.0",
        reason=reason,
        demo_mode=demo_mode,
    )


ALERT_COPY = {
    HealthStatus.NORMAL: "Status normal for this screening window.",
    HealthStatus.RECHECK: "Please recheck your readings.",
    HealthStatus.ELEVATED: (
        "Persistent abnormal pattern detected. "
        "Consider appropriate medical attention if symptoms are present or readings remain abnormal."
    ),
    HealthStatus.INSUFFICIENT: "Insufficient quality measurements. Please recheck placement and remain still.",
}
