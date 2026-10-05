# CareShield: Passive Medical Device Security Monitor

**Team:** 404 (group 6)
**Event:** ASTRA 2026, Cyber in Healthcare
**Selected Track:** Track 2, Medical Devices + Cyber-Physical Safety
**Challenge Number & Title:** Group 6, Track 2 challenge: Passive security monitoring for medical devices with human approved response

> All devices, patients and data in this project are **synthetic**. No real hospital, device or patient data is used, and no real systems are scanned or attacked.

## Problem Statement
Hospitals rely on devices like infusion pumps and ventilators. They often run old software, are hard to update, and sit on the hospital network. An attacker who sends unauthorized commands (for example, changing a dose or pushing fake firmware) could put a patient at risk.

## Proposed Solution
CareShield passively watches device activity, flags suspicious behavior, explains why, and asks a **human** to approve or reject any response. It never blocks or changes a device on its own, because interfering with a medical device could harm a patient.

**Flow:** Healthcare Problem -> Cyber Risk -> Detection -> Human Review -> Approved Action -> Patient Protected

```
Simulated devices -> Detector (rules + patient-risk score) -> Alert
                                                                |
                     Dashboard <- Risk score + reasons <--------+
                         |
                  Human: Approve / Reject -> Audit log
```

## Key Features
- Simulated hospital devices (2 infusion pumps, 1 ventilator) with synthetic patients
- Rule-based detection of: unknown senders, unsafe dose or rate, sudden rate jumps, unscheduled firmware updates
- **Patient-impact score:** the same threat scores higher when the patient is high-risk
- Every alert lists **why** it fired (explainable)
- **Human-in-the-loop:** Approve / Reject buttons for every alert
- **Audit log** of every human decision
- Live dashboard with built-in demo attack buttons (simulated devices only)
- Login with roles: only a **clinician** can approve or reject; an **observer** account is read-only
- "Are you sure?" confirmation (Cancel is the default) so an accidental click changes nothing
- Audit log records **who** made each decision

## Technology Stack
- Python 3, FastAPI, Uvicorn (backend)
- HTML, CSS and JavaScript (dashboard, no external libraries)
- No AI/ML model is used; detection is rule-based

## Setup / Installation
```bash
git clone <this-repo-url>
cd medguard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
uvicorn main:app --reload
```
Then open http://127.0.0.1:8000/login and sign in with a **demo account**:

| Role | Username | Password | Can do |
|---|---|---|---|
| Clinician | nurse1 | nurse-demo-123 | View, approve, reject, run demo controls |
| Observer | viewer1 | viewer-demo-123 | View only |

These are **fake demo credentials for the prototype only**, not real accounts. They can be overridden with the environment variables in `.env.example`.

Then open http://127.0.0.1:8000/ in your browser.

## Demo Instructions
0. Sign in as nurse1 (see Usage). Approve and Reject ask for confirmation before saving.
1. Watch normal traffic flow in the "Live device traffic" table.
2. Click **Authorized nurse changes rate**. No alert is raised (false-positive check).
3. Click **Dangerous dose jump**. An alert appears with a risk score and reasons.
4. Click **Approve response** (or **Reject**). The decision appears in the Audit log.
5. Try **Unknown sender** and **Firmware tampering** the same way.

## Testing / Evaluation Results
Run: `python3 tests/run_evaluation.py` (full output saved in `docs/test_results.txt`)

| Test | Result |
|---|---|
| Normal readings flagged | 0 / 50 |
| Harmless authorized changes flagged | 0 / 5 |
| Simulated attacks detected | 8 / 8 |

Screenshots: see the `docs/` folder.

## Limitations
- Devices are **simulated**; this has not been tested on real medical devices or real hospital networks.
- The test attacks were written by the team to match the rules, so 8/8 shows the system works as designed, not that it catches every real-world attack.
- Detection is rule-based with fixed thresholds, so it can miss unfamiliar attack patterns and can raise false alarms in unusual but legitimate situations.
- "Approve response" records the decision and recommended action; it does not control a real device.
- Data is held in memory and resets when the server restarts.
- This is a prototype, not a certified medical product.
- Login is a **demo**: hard-coded accounts, in-memory sessions, no HTTPS, no password hashing. A real deployment needs hospital single sign-on and multi-factor authentication.
- Sender identification uses IP addresses, which a skilled attacker can spoof. A real system needs device authentication (for example, certificates) and network segmentation.

## Future Scope
- Support real medical device protocols (for example, HL7, DICOM) via passive network monitoring
- Add anomaly-detection ML as a second opinion, with human review kept
- Persistent storage and user logins for clinicians
- Scale to many wards and hospital-wide deployment

## Team Members and Contributions
- Mehza : Backend, dashboard and server, and presentation
- Minha : Testing, detector and documentation

## Third-Party Components
- FastAPI (MIT), Uvicorn (BSD): open-source Python libraries
- No external datasets, APIs or AI models are used

## License
MIT License. See the `LICENSE` file.