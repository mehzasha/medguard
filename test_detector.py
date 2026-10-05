from detector import check_event

print("--- TEST 1: Normal reading ---")
print(check_event({"device": "pump-01", "source_ip": "10.0.0.5",
                   "action": "telemetry", "rate": 75}))

print("\n--- TEST 2: Nurse changes rate from an allowed computer (should be SAFE) ---")
print(check_event({"device": "pump-01", "source_ip": "10.0.0.5",
                   "action": "set_rate", "rate": 80}))

print("\n--- TEST 3: ATTACK! Unknown computer sets a huge rate ---")
print(check_event({"device": "pump-01", "source_ip": "10.9.9.9",
                   "action": "set_rate", "rate": 400}))