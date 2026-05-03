"""
constants.py
Colour / style constants, priority data, and chief complaints list.
"""

# ─────────────────────────────────────────────
#  PRIORITY DATA
# ─────────────────────────────────────────────

PRIORITY_LEVELS = ["CRITICAL", "URGENT", "STABLE"]
PRIORITY_ORDER  = {"CRITICAL": 0, "URGENT": 1, "STABLE": 2}

PRIORITY_COLORS = {
    "CRITICAL": {"bg": "#C0392B", "fg": "#FFFFFF", "light": "#FADBD8", "badge": "#922B21"},
    "URGENT":   {"bg": "#D4870A", "fg": "#FFFFFF", "light": "#FDEBD0", "badge": "#9A6210"},
    "STABLE":   {"bg": "#1E8449", "fg": "#FFFFFF", "light": "#D5F5E3", "badge": "#145A32"},
}

CHIEF_COMPLAINTS = [
    "Chest pain", "Shortness of breath", "Severe abdominal pain",
    "Head trauma", "Altered consciousness", "Stroke symptoms",
    "Allergic reaction", "Fracture", "Laceration", "Fever",
    "Back pain", "Dizziness", "Palpitations", "Seizure",
]

# ─────────────────────────────────────────────
#  COLOUR / STYLE CONSTANTS
# ─────────────────────────────────────────────

BG_DARK    = "#0D1B2A"
BG_PANEL   = "#112233"
BG_CARD    = "#162840"
BG_INPUT   = "#1A3050"
ACCENT     = "#2980B9"
ACCENT2    = "#1ABC9C"
TEXT_PRI   = "#ECF0F1"
TEXT_SEC   = "#95A5A6"
TEXT_HINT  = "#5D7080"
BORDER     = "#1E3A5F"
HEADER_BG  = "#0A1628"
