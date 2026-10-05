import asyncio
import os
import random
import secrets
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel

from devices import DEVICES, make_normal_event
from detector import check_event

# ---------- Memory (everything is fake and lives only in RAM) ----------
events = []   # recent readings
alerts = []   # suspicious things found
audit = []    # every human decision
alert_counter = 0

# ---------- DEMO accounts (synthetic, for the prototype only) ----------
DEMO_USERS = {
    "nurse1": {
        "password": os.getenv("MEDGUARD_NURSE_PW", "nurse-demo-123"),
        "role": "clinician",
        "display": "Nurse (clinician)",
    },
    "viewer1": {
        "password": os.getenv("MEDGUARD_VIEWER_PW", "viewer-demo-123"),
        "role": "viewer",
        "display": "Observer (read-only)",
    },
}
sessions = {}  # login token -> user info


class LoginBody(BaseModel):
    username: str
    password: str


def current_user(request: Request):
    """Anyone logged in."""
    user = sessions.get(request.cookies.get("session"))
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


def clinician_only(user=Depends(current_user)):
    """Only clinicians may make decisions."""
    if user["role"] != "clinician":
        raise HTTPException(status_code=403, detail="Only clinicians can do this")
    return user


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


# ---------- Login / logout ----------
@app.post("/api/login")
def login(body: LoginBody, response: Response):
    u = DEMO_USERS.get(body.username)
    if not u or not secrets.compare_digest(
        u["password"].encode(), body.password.encode()
    ):
        raise HTTPException(status_code=401, detail="Wrong username or password")
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": body.username,
        "role": u["role"],
        "display": u["display"],
    }
    response.set_cookie("session", token, httponly=True, samesite="lax")
    return {"ok": True}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    sessions.pop(request.cookies.get("session"), None)
    response.delete_cookie("session")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


# ---------- What the dashboard will ask for (login required) ----------
@app.get("/api/state")
def get_state(user=Depends(current_user)):
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


# ---------- Demo attack buttons (clinician login required) ----------
@app.post("/api/attack/{kind}")
def run_attack(kind: str, user=Depends(clinician_only)):
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
        raise HTTPException(status_code=400, detail="unknown attack")
    return {"ok": True, "ran": kind}


# ---------- Human decision: Approve or Reject (clinician only) ----------
@app.post("/api/decide/{alert_id}/{decision}")
def decide(alert_id: int, decision: str, user=Depends(clinician_only)):
    if decision not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    for a in alerts:
        if a["id"] == alert_id and a["status"] == "pending":
            if decision == "approve":
                a["status"] = "approved"
                outcome = "Human APPROVED the response: " + a["recommended"]
            else:
                a["status"] = "rejected"
                outcome = "Human REJECTED: marked as false alarm, no action taken"
            audit.append({
                "time": now(),
                "alert_id": alert_id,
                "device": a["device"],
                "decision": decision.upper(),
                "user": user["username"],
                "note": outcome,
            })
            return {"ok": True}
    raise HTTPException(status_code=404, detail="alert not found or already decided")


# ---------- Pages ----------
@app.get("/login")
def login_page():
    return FileResponse("public/login.html")


@app.get("/")
def home():
    return FileResponse("public/index.html")