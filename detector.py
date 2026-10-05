from devices import DEVICES

# How much a patient's risk level boosts the alert score
RISK_MULTIPLIER = {"high": 1.5, "medium": 1.0, "low": 0.7}

# Remember the last rate we saw for each device
last_rate = {}


def check_event(event):
    """Looks at one event. Returns a list of reasons it looks suspicious."""
    device = DEVICES[event["device"]]
    reasons = []
    score = 0

    # Rule 1: Is the sender allowed to talk to this device?
    if event["source_ip"] not in device["allowed_ips"]:
        reasons.append(f"Unknown sender {event['source_ip']} (not on allowed list)")
        score += 40

    # Rule 2: Is someone changing the rate?
    if event["action"] == "set_rate":
        if event["rate"] > device["max_safe_rate"]:
            reasons.append(
                f"Rate {event['rate']} is above safe limit {device['max_safe_rate']} {device['unit']}"
            )
            score += 60

        previous = last_rate.get(event["device"], device["normal_rate"])
        if abs(event["rate"] - previous) / previous > 0.5:
            reasons.append(f"Sudden jump from {previous} to {event['rate']}")
            score += 30

    # Rule 3: Firmware updates are not expected during normal care
    if event["action"] == "firmware_update":
        reasons.append("Unscheduled firmware update attempt")
        score += 50

    # Remember this rate for next time
        if event["action"] in ("telemetry", "set_rate") and not reasons:
         last_rate[event["device"]] = event["rate"]

    # Boost the score if the patient is high risk
    final_score = round(score * RISK_MULTIPLIER[device["patient_risk"]])

    return {
        "suspicious": len(reasons) > 0,
        "reasons": reasons,
        "risk_score": min(final_score, 100),
        "patient_risk": device["patient_risk"],
    }