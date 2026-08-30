"""Location-specific flood early-risk. Not guaranteed flood detection."""

from companion_core.config import FLOOD
from companion_core.types import FloodFeatures, FloodStatus, NetworkState, FloodResult


def heuristic_flood_score(f: FloodFeatures) -> tuple[float, str]:
    # Reference thresholds (mm) for screening — not official warning criteria.
    s24 = f.rain_24h
    s72 = f.rain_72h
    intensity = f.intensity
    score = 0.0
    score += min(0.35, s24 / 120.0)
    score += min(0.30, s72 / 250.0)
    score += min(0.25, intensity / 40.0)
    if f.trend > 2:
        score += 0.1
    score = max(0.0, min(1.0, score))
    reason = f"rain24={s24:.1f} rain72={s72:.1f} intensity={intensity:.1f}"
    return score, reason


class FloodStateMachine:
    def __init__(self):
        self.status = FloodStatus.LOW
        self.last_change_s = 0.0

    def update(self, score: float, now_s: float) -> FloodStatus:
        h = FLOOD.hysteresis
        if now_s - self.last_change_s < FLOOD.cooldown_s and self.status != FloodStatus.LOW:
            # cooldown: only allow escalation
            if self.status == FloodStatus.WATCH and score >= FLOOD.high_score:
                self.status = FloodStatus.HIGH
                self.last_change_s = now_s
            return self.status

        nxt = self.status
        if self.status == FloodStatus.LOW:
            if score >= FLOOD.high_score:
                nxt = FloodStatus.HIGH
            elif score >= FLOOD.watch_score:
                nxt = FloodStatus.WATCH
        elif self.status == FloodStatus.WATCH:
            if score >= FLOOD.high_score:
                nxt = FloodStatus.HIGH
            elif score < FLOOD.watch_score - h:
                nxt = FloodStatus.LOW
        else:  # HIGH
            if score < FLOOD.high_score - h:
                nxt = FloodStatus.WATCH

        if nxt != self.status:
            self.status = nxt
            self.last_change_s = now_s
        return self.status


def poll_interval_s(status: FloodStatus) -> int:
    if status == FloodStatus.HIGH:
        return FLOOD.poll_high_s
    if status == FloodStatus.WATCH:
        return FLOOD.poll_watch_s
    return FLOOD.poll_normal_s


def make_flood_result(
    f: FloodFeatures,
    score: float,
    status: FloodStatus,
    now_s: float,
    last_update_s: float,
    network: NetworkState,
    demo: bool,
    reason: str,
    used_tree: bool,
) -> FloodResult:
    stale = (now_s - last_update_s) > FLOOD.stale_after_s if last_update_s else True
    net = network
    if stale and network == NetworkState.ONLINE:
        net = NetworkState.STALE_DATA
    return FloodResult(
        risk_score=round(score, 4),
        status=status,
        features=f,
        last_update_s=last_update_s,
        stale=stale,
        network=net,
        model_name=FLOOD.model_name if used_tree else "flood_heuristic_v1",
        model_version=FLOOD.model_version,
        demo_mode=demo,
        reason=reason,
    )
