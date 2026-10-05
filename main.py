import asyncio
import random
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from devices import DEVICES, make_normal_event
from detector import check_event

# ---------- Memory (everything is fake and lives only in RAM) ----------
events = []   # recent readings
alerts = []   # suspicious things found
audit = []    # every human decision
alert_counter = 0


def now():
    return datetime.now().strftime("%H:%M:%S")


def process(event):
    """Check one event. If it looks suspicious, create an alert."""
    global alert_counter
    event["time"] = now()
    result = check_event(event)

    events.append({**event, "suspicious": result["suspicious"]})
    del events[:-40]  # keep only the last 40

    if result["suspicious"]:
        alert_counter += 1
        d = DEVICES[event["device"]]
        alerts.append({
            "id": alert_counter,
            "time": event["time"],
            "device": event["device"],
            "device_name": d["name"],
            "patient_id": d["patient_id"],
            "source_ip": event["source_ip"],
            "action": event["action"],
            "rate": event.get("rate"),
            "reasons": result["reasons"],
            "risk_score": result["risk_score"],
            "patient_risk": result["patient_risk"],
            "recommended": "Revert to last safe setting and flag the sender for review",
            "status": "pending",
        })


async def simulator():
    """Sends a normal reading from a random fake device every second."""
    while True:
        process(make_normal_event(random.choice(list(DEVICES))))
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(simulator())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


# ---------- What the dashboard will ask for ----------
@app.get("/api/state")
def get_state():
    pending_devices = {a["device"] for a in alerts if a["status"] == "pending"}
    devices = [
        {
            "id": did,
            "name": d["name"],
            "patient_id": d["patient_id"],
            "patient_risk": d["patient_risk"],
            "status": "ALERT" if did in pending_devices else "OK",
        }
        for did, d in DEVICES.items()
    ]
    return {
        "devices": devices,
        "events": events[-15:][::-1],
        "alerts": alerts[::-1],
        "audit": audit[::-1],
    }


# ---------- Buttons that run the fake attacks (for the demo) ----------
@app.post("/api/attack/{kind}")
def run_attack(kind: str):
    if kind == "nurse_change":  # harmless, should NOT alarm
        process({"device": "pump-01", "source_ip": "10.0.0.5",
                 "action": "set_rate", "rate": 80})
    elif kind == "unknown_sender":
        process({"device": "pump-02", "source_ip": "10.9.9.9",
                 "action": "telemetry", "rate": 40})
    elif kind == "dose_jump":
        process({"device": "pump-01", "source_ip": "10.9.9.9",
                 "action": "set_rate", "rate": 400})
    elif kind == "firmware":
        process({"device": "vent-01", "source_ip": "10.7.7.7",
                 "action": "firmware_update"})
    else:
        return {"error": "unknown attack"}
    return {"ok": True, "ran": kind}


# ---------- Human decision: Approve or Reject ----------
@app.post("/api/decide/{alert_id}/{decision}")
def decide(alert_id: int, decision: str):
    for a in alerts:
        if a["id"] == alert_id and a["status"] == "pending":
            if decision == "approve":
                a["status"] = "approved"
                outcome = "Human APPROVED the response: " + a["recommended"]
            else:
                a["status"] = "rejected"
                outcome = "Human REJECTED: marked as false alarm, no action taken"
            audit.append({"time": now(), "alert_id": alert_id,
                          "device": a["device"], "decision": decision.upper(),
                          "note": outcome})
            return {"ok": True}
    return {"error": "alert not found or already decided"}

    # ---------- Show the dashboard page ----------
from fastapi.responses import FileResponse


@app.get("/")
def home():
    return FileResponse("public/index.html")