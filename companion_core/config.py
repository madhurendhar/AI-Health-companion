"""Shared configuration. No secrets. Tunable thresholds live here."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthConfig:
    sample_interval_ms: int = 40
    window_size: int = 50
    min_valid_in_window: int = 8
    hr_min: float = 35.0
    hr_max: float = 200.0
    spo2_min: float = 70.0
    spo2_max: float = 100.0
    object_temp_min_c: float = 20.0
    object_temp_max_c: float = 45.0
    ambient_temp_min_c: float = -10.0
    ambient_temp_max_c: float = 60.0
    humidity_min: float = 0.0
    humidity_max: float = 100.0
    ema_alpha: float = 0.25
    trend_window: int = 12
    baseline_adapt_rate: float = 0.02
    baseline_abnormal_skip: float = 0.55
    baseline_min_samples: int = 20
    persistence_windows: int = 4
    signal_quality_min: float = 0.45
    risk_recheck: float = 0.35
    risk_elevated: float = 0.65
    alert_cooldown_s: int = 90
    model_name: str = "health_tree_v1"
    model_version: str = "1.0.0"
    feature_schema_version: str = "health_features_v1"


@dataclass(frozen=True)
class FloodConfig:
    poll_normal_s: int = 1800
    poll_watch_s: int = 720
    poll_high_s: int = 300
    stale_after_s: int = 7200
    watch_score: float = 0.40
    high_score: float = 0.70
    hysteresis: float = 0.08
    cooldown_s: int = 600
    model_name: str = "flood_tree_v1"
    model_version: str = "1.0.0"
    feature_schema_version: str = "flood_features_v1"


@dataclass(frozen=True)
class StorageConfig:
    sd_write_interval_s: int = 30
    max_readings_rows: int = 20000
    max_events_rows: int = 4000


HEALTH = HealthConfig()
FLOOD = FloodConfig()
STORAGE = StorageConfig()
