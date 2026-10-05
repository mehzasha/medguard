import os
import random
import sys

# Let this file find devices.py and detector.py in the main folder
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import detector
from devices import DEVICES, make_normal_event


def flagged(event):
    detector.last_rate.clear()  # start each test fresh
    return detector.check_event(event)["suspicious"]


# 1) Normal readings (should NOT be flagged)
normal_flagged = 0
for _ in range(50):
    ev = make_normal_event(random.choice(list(DEVICES)))
    if detector.check_event(ev)["suspicious"]:
        normal_flagged += 1

# 2) Harmless changes by authorized staff (should NOT be flagged)
benign = [
    ("Nurse sets pump-01 to 80", {"device": "pump-01", "source_ip": "10.0.0.5", "action": "set_rate", "rate": 80}),
    ("Nurse sets pump-01 to 70", {"device": "pump-01", "source_ip": "10.0.0.6", "action": "set_rate", "rate": 70}),
    ("Nurse sets pump-02 to 45", {"device": "pump-02", "source_ip": "10.0.0.7", "action": "set_rate", "rate": 45}),
    ("Nurse sets pump-02 to 35", {"device": "pump-02", "source_ip": "10.0.0.5", "action": "set_rate", "rate": 35}),
    ("Nurse sets vent-01 to 16", {"device": "vent-01", "source_ip": "10.0.0.8", "action": "set_rate", "rate": 16}),
]

# 3) Simulated attacks (SHOULD be flagged)
attacks = [
    ("Unknown sender to pump-02", {"device": "pump-02", "source_ip": "10.9.9.9", "action": "telemetry", "rate": 40}),
    ("Unknown sender to vent-01", {"device": "vent-01", "source_ip": "10.9.9.9", "action": "telemetry", "rate": 14}),
    ("Dose jump to 400 from unknown sender", {"device": "pump-01", "source_ip": "10.9.9.9", "action": "set_rate", "rate": 400}),
    ("Unsafe dose 300 from an allowed IP", {"device": "pump-01", "source_ip": "10.0.0.5", "action": "set_rate", "rate": 300}),
    ("Sudden jump 40 to 70 from an allowed IP", {"device": "pump-02", "source_ip": "10.0.0.5", "action": "set_rate", "rate": 70}),
    ("Firmware update on pump-01", {"device": "pump-01", "source_ip": "10.0.0.5", "action": "firmware_update"}),
    ("Firmware update on vent-01 from unknown IP", {"device": "vent-01", "source_ip": "10.7.7.7", "action": "firmware_update"}),
    ("Ventilator rate 40 (above safe limit)", {"device": "vent-01", "source_ip": "10.0.0.8", "action": "set_rate", "rate": 40}),
]

lines = []
lines.append("CARESHIELD TEST RESULTS (all data synthetic, simulated devices only)")
lines.append("=" * 62)

benign_flagged = 0
lines.append("\nHarmless changes (expected: NOT flagged)")
for name, ev in benign:
    f = flagged(ev)
    benign_flagged += f
    lines.append(f"  {'FALSE ALARM' if f else 'ok':12} {name}")

attacks_caught = 0
lines.append("\nSimulated attacks (expected: flagged)")
for name, ev in attacks:
    f = flagged(ev)
    attacks_caught += f
    lines.append(f"  {'CAUGHT' if f else 'MISSED':12} {name}")

lines.append("\nSUMMARY")
lines.append(f"  Normal readings flagged:    {normal_flagged} / 50")
lines.append(f"  Harmless changes flagged:   {benign_flagged} / {len(benign)}")
lines.append(f"  Attacks detected:           {attacks_caught} / {len(attacks)}")

report = "\n".join(lines)
print(report)

os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
with open(os.path.join(ROOT, "docs", "test_results.txt"), "w") as f:
    f.write(report + "\n")