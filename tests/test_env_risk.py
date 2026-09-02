from companion_core.env_risk import predict, classify, heat_index_approx
from companion_core.flood_features import FloodFeatures


def test_heat_wave_high():
    f = FloodFeatures(rain_1h=0, rain_24h=2, rain_72h=10, intensity=0, trend=0)
    r = predict(ambient_temp=42.0, humidity=78.0, mq135_relative=1.3, flood=f)
    assert r["status"] in ("WATCH", "HIGH")
    assert r["heat_index"] > 35


def test_normal_low():
    f = FloodFeatures()
    r = predict(ambient_temp=29.0, humidity=60.0, mq135_relative=1.0, flood=f)
    assert r["status"] == "LOW"
