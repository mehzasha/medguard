import random
from datetime import datetime

# ALL DATA HERE IS FAKE (synthetic). No real patients, no real devices.

DEVICES = {
    "pump-01": {
        "name": "Infusion Pump (Ward A, Bed 1)",
        "patient_id": "PT-001",
        "patient_risk": "high",
        "allowed_ips": ["10.0.0.5", "10.0.0.6"],
        "normal_rate": 75,
        "max_safe_rate": 120,
        "unit": "ml/h",
    },
    "pump-02": {
        "name": "Infusion Pump (Ward A, Bed 2)",
        "patient_id": "PT-002",
        "patient_risk": "medium",
        "allowed_ips": ["10.0.0.5", "10.0.0.7"],
        "normal_rate": 40,
        "max_safe_rate": 80,
        "unit": "ml/h",
    },
    "vent-01": {
        "name": "Ventilator (ICU, Bed 3)",
        "patient_id": "PT-003",
        "patient_risk": "high",
        "allowed_ips": ["10.0.0.8"],
        "normal_rate": 14,
        "max_safe_rate": 25,
        "unit": "breaths/min",
    },
}


def make_normal_event(device_id):
    """Makes one normal, harmless reading from a device."""
    d = DEVICES[device_id]
    return {
        "device": device_id,
        "source_ip": random.choice(d["allowed_ips"]),
        "action": "telemetry",
        "rate": d["normal_rate"] + random.randint(-2, 2),
        "time": datetime.now().strftime("%H:%M:%S"),
    }


if __name__ == "__main__":
    print(make_normal_event("pump-01"))