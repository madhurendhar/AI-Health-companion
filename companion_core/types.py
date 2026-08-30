from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class SensorState(str, Enum):
    OK = "OK"
    SENSOR_ERROR = "SENSOR_ERROR"
    NO_SIGNAL = "NO_SIGNAL"
    INVALID_READING = "INVALID_READING"
    WARMING_UP = "WARMING_UP"
    STALE_DATA = "STALE_DATA"
    NO_FINGER = "NO_FINGER"


class HealthStatus(str, Enum):
    NORMAL = "NORMAL"
    RECHECK = "RECHECK"
    ELEVATED = "ELEVATED"
    INSUFFICIENT = "INSUFFICIENT"


class AirStatus(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    WARMING_UP = "WARMING_UP"


class FloodStatus(str, Enum):
    LOW = "LOW"
    WATCH = "WATCH"
    HIGH = "HIGH"


class NetworkState(str, Enum):
    ONLINE = "ONLINE"
    NETWORK_ERROR = "NETWORK_ERROR"
    STALE_DATA = "STALE_DATA"
    OFFLINE = "OFFLINE"


@dataclass
class SensorReading:
    timestamp_s: float
    hr_bpm: Optional[float] = None
    spo2_pct: Optional[float] = None
    object_temp_c: Optional[float] = None
    mlx_ambient_c: Optional[float] = None
    dht_temp_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    mq135_raw: Optional[float] = None
    mq135_relative: Optional[float] = None
    ppg_quality: float = 0.0
    max30102_state: SensorState = SensorState.NO_SIGNAL
    mlx_state: SensorState = SensorState.NO_SIGNAL
    dht_state: SensorState = SensorState.NO_SIGNAL
    mq_state: SensorState = SensorState.WARMING_UP
    demo_mode: bool = False


@dataclass
class HealthFeatures:
    hr: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    hr_trend: Optional[float] = None
    spo2_trend: Optional[float] = None
    temperature_trend: Optional[float] = None
    signal_quality: float = 0.0
    hr_dev: Optional[float] = None
    spo2_dev: Optional[float] = None
    temp_dev: Optional[float] = None
    persistence: float = 0.0
    ambient_temp: Optional[float] = None
    humidity: Optional[float] = None
    mq135_relative: Optional[float] = None
    valid: bool = False


@dataclass
class Baseline:
    resting_hr: float = 72.0
    hr_range: float = 12.0
    typical_spo2: float = 97.5
    typical_temp: float = 36.4
    ambient_temp: float = 27.0
    humidity: float = 60.0
    samples: int = 0
    ready: bool = False


@dataclass
class HealthResult:
    risk_score: float
    status: HealthStatus
    features: HealthFeatures
    baseline: Baseline
    edge_ai: bool
    model_name: str
    model_version: str
    reason: str
    demo_mode: bool = False


@dataclass
class FloodFeatures:
    rain_1h: float = 0.0
    rain_3h: float = 0.0
    rain_6h: float = 0.0
    rain_12h: float = 0.0
    rain_24h: float = 0.0
    rain_48h: float = 0.0
    rain_72h: float = 0.0
    intensity: float = 0.0
    trend: float = 0.0
    location: str = ""


@dataclass
class FloodResult:
    risk_score: float
    status: FloodStatus
    features: FloodFeatures
    last_update_s: float
    stale: bool
    network: NetworkState
    model_name: str
    model_version: str
    demo_mode: bool = False
    reason: str = ""
