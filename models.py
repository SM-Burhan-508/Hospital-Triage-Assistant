"""
models.py
Data model and patient store.

Data Architecture:
  - GLOBAL_PATIENTS  : dict[int, Patient]  — every patient ever registered
  - CURRENT_PATIENTS : dict[int, Patient]  — only non-discharged patients
  Adding a patient  → inserts into BOTH dicts
  Discharging       → removes from CURRENT_PATIENTS, stays in GLOBAL_PATIENTS
"""

from dataclasses import dataclass, field
from datetime import datetime

# ─────────────────────────────────────────────
#  GLOBAL PATIENT DICTIONARIES
# ─────────────────────────────────────────────

# All patients ever registered (including discharged)
GLOBAL_PATIENTS: dict = {}

# Only currently active (non-discharged) patients
CURRENT_PATIENTS: dict = {}

_id_counter = 0


def _next_id() -> int:
    global _id_counter
    _id_counter += 1
    return _id_counter


def register_patient(patient) -> None:
    """Add a new patient to both dictionaries."""
    GLOBAL_PATIENTS[patient.id]  = patient
    CURRENT_PATIENTS[patient.id] = patient


def discharge_patient(patient) -> None:
    """Mark discharged: remove from CURRENT, keep in GLOBAL."""
    patient.discharged = True
    if patient.id in CURRENT_PATIENTS:
        del CURRENT_PATIENTS[patient.id]
    # GLOBAL_PATIENTS keeps the record


# ─────────────────────────────────────────────
#  DATA MODEL
# ─────────────────────────────────────────────

@dataclass
class Patient:
    id: int
    name: str
    age: int
    gender: str
    chief_complaint: str
    priority: str
    arrived_at: datetime = field(default_factory=datetime.now)
    notes: list = field(default_factory=list)
    discharged: bool = False
    bp: str = ""
    hr: str = ""
    spo2: str = ""

    def wait_seconds(self) -> int:
        return int((datetime.now() - self.arrived_at).total_seconds())

    def wait_str(self) -> str:
        s = self.wait_seconds()
        m, sec = divmod(s, 60)
        h, m   = divmod(m, 60)
        if h:
            return f"{h}h {m:02d}m"
        return f"{m}m {sec:02d}s"

    def is_overdue(self) -> bool:
        s = self.wait_seconds()
        if self.priority == "CRITICAL": return s > 300    # 5 min
        if self.priority == "URGENT":   return s > 1800   # 30 min
        return False

    def add_note(self, text: str, author: str = "Nurse"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.notes.append(f"[{ts}] {author}: {text}")
