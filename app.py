"""
app.py
Main application class — TriageApp.

AHCI Concepts Demonstrated:
  - Fitts' Law           : Large buttons for frequent/critical actions
  - Hick-Hyman Law       : 3 priority buttons instead of dropdown
  - Miller's Law (7±2)   : Max 7 patients visible; info chunked into 3 groups
  - Preattentive Attrs   : Colour-coded rows; flashing for overdue patients
  - Gulf of Evaluation   : Live wait timers; real-time form preview; notes log
  - Gulf of Execution    : Field validation; confirm dialogs; clear affordances
  - Gestalt: Proximity   : LabelFrame groups in detail view
  - Situation Awareness  : Auto-sorted queue; persistent alert system
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
from datetime import datetime
from typing import Optional

from constants import (
    PRIORITY_LEVELS, PRIORITY_ORDER, PRIORITY_COLORS, CHIEF_COMPLAINTS,
    BG_DARK, BG_PANEL, BG_CARD, BG_INPUT,
    ACCENT, ACCENT2, TEXT_PRI, TEXT_SEC, TEXT_HINT, BORDER, HEADER_BG,
)
from models import (
    Patient, GLOBAL_PATIENTS, CURRENT_PATIENTS,
    _next_id, register_patient, discharge_patient,
)


class TriageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hospital Triage Assistant")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(bg=BG_DARK)

        self._flash_state       = False
        self._detail_window: Optional[tk.Toplevel] = None
        self._row_widgets: list = []

        self._setup_fonts()
        self._setup_styles()
        self._seed_demo_patients()   # seed FIRST so queue renders with data
        self._build_ui()             # build UI (calls _refresh_queue internally)
        self._start_clock()
        self._start_flash_loop()

    # ── fonts & styles ─────────────────────
    def _setup_fonts(self):
        self.font_title  = tkfont.Font(family="Helvetica", size=18, weight="bold")
        self.font_h2     = tkfont.Font(family="Helvetica", size=13, weight="bold")
        self.font_h3     = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.font_body   = tkfont.Font(family="Helvetica", size=11)
        self.font_small  = tkfont.Font(family="Helvetica", size=9)
        self.font_mono   = tkfont.Font(family="Courier",   size=10)
        self.font_badge  = tkfont.Font(family="Helvetica", size=9,  weight="bold")
        self.font_timer  = tkfont.Font(family="Courier",   size=11, weight="bold")
        self.font_btn    = tkfont.Font(family="Helvetica", size=11, weight="bold")
        self.font_btn_lg = tkfont.Font(family="Helvetica", size=13, weight="bold")

    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Dark.TFrame",   background=BG_DARK)
        s.configure("Panel.TFrame",  background=BG_PANEL)
        s.configure("Card.TFrame",   background=BG_CARD)
        s.configure("Header.TFrame", background=HEADER_BG)

    # ── top-level layout ───────────────────
    def _build_ui(self):
        self._build_header()
        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill="both", expand=True)

        # Sidebar (fixed width)
        self.sidebar = tk.Frame(body, bg=BG_PANEL, width=310)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Separator
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # Main queue area
        self.main_area = tk.Frame(body, bg=BG_DARK)
        self.main_area.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_queue_area()

    # ── header ─────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=HEADER_BG, height=58)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=HEADER_BG)
        left.pack(side="left", padx=18, pady=0)

        cross = tk.Label(left, text=" + ", bg="#C0392B", fg="white",
                         font=tkfont.Font(family="Helvetica", size=15, weight="bold"))
        cross.pack(side="left", pady=14)

        tk.Label(left, text="  TriageAssist", bg=HEADER_BG, fg=TEXT_PRI,
                 font=tkfont.Font(family="Helvetica", size=15, weight="bold")).pack(side="left")
        tk.Label(left, text="   Emergency Department", bg=HEADER_BG, fg=TEXT_SEC,
                 font=self.font_body).pack(side="left")

        right = tk.Frame(hdr, bg=HEADER_BG)
        right.pack(side="right", padx=20)
        self.lbl_time = tk.Label(right, text="", bg=HEADER_BG, fg=TEXT_PRI,
                                 font=tkfont.Font(family="Courier", size=14, weight="bold"))
        self.lbl_time.pack(anchor="e")
        self.lbl_date = tk.Label(right, text="", bg=HEADER_BG, fg=TEXT_SEC,
                                 font=self.font_small)
        self.lbl_date.pack(anchor="e")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

    # ── sidebar ────────────────────────────
    def _build_sidebar(self):
        sb = self.sidebar
        pad = dict(padx=14)

        # ── Stats overview ──
        tk.Label(sb, text="QUEUE OVERVIEW", bg=BG_PANEL, fg=TEXT_HINT,
                 font=self.font_badge).pack(anchor="w", pady=(14, 6), **pad)

        self.stat_labels = {}
        for key, label, color in [
            ("CRITICAL", "Critical", PRIORITY_COLORS["CRITICAL"]["bg"]),
            ("URGENT",   "Urgent",   PRIORITY_COLORS["URGENT"]["bg"]),
            ("STABLE",   "Stable",   PRIORITY_COLORS["STABLE"]["bg"]),
            ("TOTAL",    "Active",   ACCENT),
            ("GLOBAL",   "All-time", TEXT_HINT),
        ]:
            row = tk.Frame(sb, bg=BG_PANEL)
            row.pack(fill="x", pady=2, **pad)
            dot = tk.Frame(row, bg=color, width=10, height=10)
            dot.pack(side="left", padx=(0, 8))
            dot.pack_propagate(False)
            tk.Label(row, text=label, bg=BG_PANEL, fg=TEXT_SEC,
                     font=self.font_body).pack(side="left")
            lbl = tk.Label(row, text="0", bg=BG_PANEL, fg=TEXT_PRI,
                           font=self.font_h2)
            lbl.pack(side="right")
            self.stat_labels[key] = lbl

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", pady=10, **pad)

        # ── ADD PATIENT BUTTON (Fitts' Law: largest, most prominent) ──
        tk.Label(sb, text="REGISTER PATIENT", bg=BG_PANEL, fg=TEXT_HINT,
                 font=self.font_badge).pack(anchor="w", pady=(0, 6), **pad)

        # The button is built as a tk.Button directly — no intermediate frame
        self.btn_add = tk.Button(
            sb,
            text="＋  Add New Patient",
            bg=ACCENT,
            fg="white",
            font=self.font_btn_lg,
            relief="flat",
            cursor="hand2",
            activebackground="#2471A3",
            activeforeground="white",
            pady=14,                      # tall button → Fitts' Law
            command=self._open_intake_form
        )
        self.btn_add.pack(fill="x", padx=14, pady=(0, 4))

        tk.Label(sb, text="Fitts' Law: largest button = most frequent action",
                 bg=BG_PANEL, fg=TEXT_HINT, font=self.font_small,
                 wraplength=270, justify="left").pack(anchor="w", **pad)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", pady=10, **pad)

        # ── View discharged log ──
        tk.Button(
            sb,
            text="View All-Time Patient Log",
            bg=BG_CARD,
            fg=TEXT_SEC,
            font=self.font_btn,
            relief="flat",
            cursor="hand2",
            pady=8,
            activebackground=BORDER,
            activeforeground=TEXT_PRI,
            command=self._open_global_log
        ).pack(fill="x", padx=14, pady=2)

        tk.Button(
            sb,
            text="Discharge All Stable",
            bg=BG_CARD,
            fg=TEXT_SEC,
            font=self.font_btn,
            relief="flat",
            cursor="hand2",
            pady=8,
            activebackground=BORDER,
            activeforeground=TEXT_PRI,
            command=self._discharge_all_stable
        ).pack(fill="x", padx=14, pady=2)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", pady=10, **pad)

        # ── AHCI legend ──
        tk.Label(sb, text="AHCI CONCEPTS ACTIVE", bg=BG_PANEL, fg=TEXT_HINT,
                 font=self.font_badge).pack(anchor="w", pady=(0, 6), **pad)

        for color, text in [
            (ACCENT2,   "Preattentive attrs — colour coding"),
            ("#E74C3C", "Flashing alert — overdue patients"),
            (ACCENT,    "Miller's Law — 7 rows max visible"),
            ("#F39C12", "Gulf of evaluation — live timers"),
            ("#9B59B6", "Situation awareness — auto-sort"),
        ]:
            row = tk.Frame(sb, bg=BG_PANEL)
            row.pack(fill="x", pady=1, **pad)
            tk.Frame(row, bg=color, width=8, height=8).pack(side="left", padx=(0, 6))
            tk.Label(row, text=text, bg=BG_PANEL, fg=TEXT_SEC,
                     font=self.font_small, wraplength=240,
                     justify="left").pack(side="left", anchor="w")

    # ── queue area (Screen 1) ───────────────
    def _build_queue_area(self):
        ma = self.main_area

        # Title row
        hdr = tk.Frame(ma, bg=BG_DARK)
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(hdr, text="Active Patient Queue", bg=BG_DARK, fg=TEXT_PRI,
                 font=self.font_title).pack(side="left")
        self.lbl_queue_count = tk.Label(hdr, text="", bg=BG_DARK, fg=TEXT_SEC,
                                        font=self.font_body)
        self.lbl_queue_count.pack(side="left", padx=10)
        tk.Label(hdr, text="Miller's Law: 7 rows visible  |  sorted priority → wait time",
                 bg=BG_DARK, fg=TEXT_HINT, font=self.font_small).pack(side="right")

        # ── Column header bar ──
        # COL_WIDTHS is the single source of truth: (header_text, pixel_width, anchor)
        # Both headers and data rows use the same widths so they are always aligned.
        self.COL_WIDTHS = [
            ("PRIORITY",        130, "w"),
            ("NAME / COMPLAINT", 260, "w"),
            ("AGE",              80, "center"),
            ("WAIT TIME",       120, "center"),
            ("NOTES",            90, "center"),
            ("",                100, "center"),   # View button column
        ]

        col_hdr = tk.Frame(ma, bg=BG_PANEL)
        col_hdr.pack(fill="x", padx=20, pady=(10, 0))

        # Left colour bar spacer to match the 6px bar in rows
        tk.Frame(col_hdr, bg=BG_PANEL, width=6).pack(side="left")

        for text, px, anchor in self.COL_WIDTHS:
            tk.Label(col_hdr, text=text, bg=BG_PANEL, fg=TEXT_HINT,
                     font=self.font_badge, width=px // 8,
                     anchor=anchor).pack(side="left", padx=4, pady=7)

        tk.Frame(ma, bg=BORDER, height=1).pack(fill="x", padx=20)

        # Scrollable canvas — Miller's Law: height limits visible rows to ~7
        self.q_canvas = tk.Canvas(ma, bg=BG_DARK, highlightthickness=0)
        vbar = tk.Scrollbar(ma, orient="vertical", command=self.q_canvas.yview)
        self.q_canvas.configure(yscrollcommand=vbar.set)

        vbar.pack(side="right", fill="y", padx=(0, 4))
        self.q_canvas.pack(fill="both", expand=True, padx=(20, 0), pady=(0, 8))

        self.q_frame = tk.Frame(self.q_canvas, bg=BG_DARK)
        self._q_win  = self.q_canvas.create_window((0, 0), window=self.q_frame, anchor="nw")

        self.q_frame.bind("<Configure>",
                          lambda e: self.q_canvas.configure(
                              scrollregion=self.q_canvas.bbox("all")))
        self.q_canvas.bind("<Configure>",
                           lambda e: self.q_canvas.itemconfig(self._q_win, width=e.width))
        self.q_canvas.bind_all("<MouseWheel>",
                               lambda e: self.q_canvas.yview_scroll(
                                   int(-1 * (e.delta / 120)), "units"))

        self._refresh_queue()

    # ── queue rendering ─────────────────────
    def _refresh_queue(self):
        for w in self._row_widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self._row_widgets.clear()

        # Situation Awareness: auto-sort by priority then longest wait first
        active = list(CURRENT_PATIENTS.values())
        active.sort(key=lambda p: (PRIORITY_ORDER[p.priority], -p.wait_seconds()))

        # Update sidebar stats
        for lvl in PRIORITY_LEVELS:
            self.stat_labels[lvl].config(
                text=str(sum(1 for p in active if p.priority == lvl)))
        self.stat_labels["TOTAL"].config(text=str(len(CURRENT_PATIENTS)))
        self.stat_labels["GLOBAL"].config(text=str(len(GLOBAL_PATIENTS)))
        self.lbl_queue_count.config(text=f"({len(active)} active)")

        if not active:
            empty = tk.Label(self.q_frame,
                             text="Queue is empty — register a patient to begin.",
                             bg=BG_DARK, fg=TEXT_HINT, font=self.font_h2)
            empty.pack(pady=60)
            self._row_widgets.append(empty)
            return

        for idx, patient in enumerate(active):
            self._build_row(patient, idx)

        # Force geometry recalculation so rows are visible immediately on launch
        self.q_frame.update_idletasks()
        self.q_canvas.configure(scrollregion=self.q_canvas.bbox("all"))

    def _build_row(self, patient: Patient, idx: int):
        pc      = PRIORITY_COLORS[patient.priority]
        row_bg  = BG_CARD if idx % 2 == 0 else BG_PANEL
        is_over = patient.is_overdue()

        outer = tk.Frame(self.q_frame, bg=row_bg, cursor="hand2")
        outer.pack(fill="x", pady=1)
        self._row_widgets.append(outer)

        # 6px coloured left bar (Preattentive attribute: priority colour)
        tk.Frame(outer, bg=pc["bg"], width=6).pack(side="left", fill="y")

        # Inner frame uses grid with fixed column minsize — matches header widths exactly
        inner = tk.Frame(outer, bg=row_bg)
        inner.pack(side="left", fill="both", expand=True)

        col_widths = [w for (_, w, _) in self.COL_WIDTHS]
        for col_i, w in enumerate(col_widths):
            inner.columnconfigure(col_i, minsize=w)

        # ── Col 0: Priority badge (+ overdue flash label) ──
        badge_frame = tk.Frame(inner, bg=row_bg)
        badge_frame.grid(row=0, column=0, sticky="w", padx=(6, 4), pady=8)

        tk.Label(badge_frame, text=patient.priority,
                 bg=pc["bg"], fg=pc["fg"],
                 font=self.font_badge, padx=8, pady=4).pack(anchor="w")

        if is_over:
            over_lbl = tk.Label(badge_frame, text="⚠ OVERDUE",
                                bg="#E74C3C", fg="white",
                                font=self.font_small, padx=4, pady=1)
            over_lbl.pack(anchor="w", pady=(2, 0))
            patient._flash_lbl = over_lbl
        else:
            patient._flash_lbl = None

        # ── Col 1: Name / complaint ──
        info = tk.Frame(inner, bg=row_bg)
        info.grid(row=0, column=1, sticky="w", padx=(0, 4), pady=8)
        tk.Label(info, text=patient.name, bg=row_bg, fg=TEXT_PRI,
                 font=self.font_h3).pack(anchor="w")
        tk.Label(info, text=patient.chief_complaint, bg=row_bg, fg=TEXT_SEC,
                 font=self.font_small).pack(anchor="w")

        # ── Col 2: Age ──
        tk.Label(inner, text=f"{patient.age}y {patient.gender[0]}",
                 bg=row_bg, fg=TEXT_SEC, font=self.font_body,
                 anchor="center").grid(row=0, column=2, sticky="ew", padx=4)

        # ── Col 3: Wait time (Gulf of Evaluation: always visible) ──
        wait_lbl = tk.Label(inner, text=patient.wait_str(),
                            bg=row_bg,
                            fg="#E74C3C" if is_over else ACCENT2,
                            font=self.font_timer, anchor="center")
        wait_lbl.grid(row=0, column=3, sticky="ew", padx=4)
        patient._wait_lbl = wait_lbl
        patient._row_bg   = row_bg

        # ── Col 4: Notes count ──
        nc = len(patient.notes)
        tk.Label(inner, text=f"{nc} note{'s' if nc != 1 else ''}",
                 bg=row_bg, fg=TEXT_HINT,
                 font=self.font_small, anchor="center").grid(
            row=0, column=4, sticky="ew", padx=4)

        # ── Col 5: View button (Fitts' Law) ──
        view_btn = tk.Button(
            inner,
            text="View →",
            bg=ACCENT, fg="white",
            font=self.font_btn,
            relief="flat", cursor="hand2",
            padx=10, pady=4,
            activebackground="#2471A3",
            activeforeground="white",
            command=lambda p=patient: self._open_detail(p)
        )
        view_btn.grid(row=0, column=5, padx=(4, 8), pady=6, sticky="e")

        # Entire row is clickable
        for w in [outer, inner, info]:
            w.bind("<Button-1>", lambda e, p=patient: self._open_detail(p))

    # ─────────────────────────────────────────────
    #  SCREEN 2 — INTAKE FORM
    # ─────────────────────────────────────────────

    def _open_intake_form(self):
        """
        AHCI concepts:
          Hick-Hyman  : 3 large priority buttons (not a dropdown)
          Gulf of Execution : clear step-by-step layout, field labels, tab order
          Gulf of Evaluation: live preview panel on the right
          Error prevention  : red highlight + message on empty required fields
          Fitts' Law        : large priority buttons, tall submit button
          Error recovery    : confirm dialog before commit
        """
        win = tk.Toplevel(self)
        win.title("Register New Patient")
        win.geometry("1020x780")
        win.minsize(900, 660)
        win.configure(bg=BG_DARK)
        win.grab_set()          # modal
        win.resizable(True, True)
        win.lift()
        win.focus_force()

        # ── Header (always at top) ──
        hdr = tk.Frame(win, bg=HEADER_BG, height=52)
        hdr.pack(side="top", fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  ＋  Register New Patient",
                 bg=HEADER_BG, fg=TEXT_PRI,
                 font=self.font_title).pack(side="left", padx=16, pady=10)
        tk.Frame(win, bg=BORDER, height=1).pack(side="top", fill="x")

        # ── Button row (packed BEFORE body so it is ALWAYS visible at bottom) ──
        # This is the key fix: pack the footer before the expanding body.
        btn_row = tk.Frame(win, bg=HEADER_BG)
        btn_row.pack(side="bottom", fill="x")
        tk.Frame(win, bg=BORDER, height=1).pack(side="bottom", fill="x")

        # ── Two-column body (fills remaining space) ──
        body = tk.Frame(win, bg=BG_DARK)
        body.pack(side="top", fill="both", expand=True)

        left  = tk.Frame(body, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=20, pady=14)

        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        right = tk.Frame(body, bg=BG_PANEL)
        right.pack(side="left", fill="y", ipadx=12)

        # ── StringVars ──
        sv_name      = tk.StringVar()
        sv_age       = tk.StringVar()
        sv_gender    = tk.StringVar(value="Male")
        sv_complaint = tk.StringVar()
        sv_bp        = tk.StringVar()
        sv_hr        = tk.StringVar()
        sv_spo2      = tk.StringVar()
        sv_priority  = tk.StringVar(value="")
        sv_note      = tk.StringVar()

        # Track entry widgets for validation highlighting
        entry_widgets = {}
        err_labels    = {}

        def make_field(parent, label, var, row_num,
                       is_combo=False, values=None, hint=""):
            tk.Label(parent, text=label, bg=BG_DARK, fg=TEXT_SEC,
                     font=self.font_h3).grid(
                row=row_num * 3, column=0, sticky="w", pady=(10, 2))

            if is_combo:
                w = ttk.Combobox(parent, textvariable=var, values=values,
                                 state="readonly", font=self.font_body, width=34)
            else:
                w = tk.Entry(parent, textvariable=var,
                             bg=BG_INPUT, fg=TEXT_PRI,
                             font=self.font_body, relief="flat",
                             insertbackground=TEXT_PRI, width=36)
                w.configure(highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=ACCENT)

            w.grid(row=row_num * 3 + 1, column=0, sticky="ew", ipady=7)

            if hint:
                tk.Label(parent, text=hint, bg=BG_DARK, fg=TEXT_HINT,
                         font=self.font_small).grid(
                    row=row_num * 3 + 1, column=1, sticky="w", padx=6)

            err = tk.Label(parent, text="", bg=BG_DARK,
                           fg="#E74C3C", font=self.font_small)
            err.grid(row=row_num * 3 + 2, column=0, sticky="w")

            entry_widgets[label] = w
            err_labels[label]    = err
            return w

        e_name      = make_field(left, "Patient Name *",    sv_name,      0)
        e_age       = make_field(left, "Age *",              sv_age,       1, hint="0–120")
        e_complaint = make_field(left, "Chief Complaint *",  sv_complaint, 2,
                                 is_combo=True, values=CHIEF_COMPLAINTS)
        e_gender    = make_field(left, "Gender",             sv_gender,    3,
                                 is_combo=True,
                                 values=["Male", "Female", "Other"])

        # Vitals (optional)
        tk.Label(left, text="Vitals (optional)", bg=BG_DARK, fg=TEXT_SEC,
                 font=self.font_h3).grid(row=12, column=0, sticky="w", pady=(12, 4))

        vitals_row = tk.Frame(left, bg=BG_DARK)
        vitals_row.grid(row=13, column=0, sticky="ew")

        def mini_entry(parent, label, var, width=9):
            tk.Label(parent, text=label, bg=BG_DARK,
                     fg=TEXT_HINT, font=self.font_small).pack(side="left")
            e = tk.Entry(parent, textvariable=var,
                         bg=BG_INPUT, fg=TEXT_PRI,
                         font=self.font_body, relief="flat",
                         width=width, insertbackground=TEXT_PRI)
            e.configure(highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
            e.pack(side="left", padx=(2, 12), ipady=4)

        mini_entry(vitals_row, "BP:",   sv_bp,   9)
        mini_entry(vitals_row, "HR:",   sv_hr,   6)
        mini_entry(vitals_row, "SpO₂:", sv_spo2, 6)

        left.columnconfigure(0, weight=1)

        # ── PRIORITY BUTTONS (Hick-Hyman Law) ──
        tk.Label(left, text="Priority Level *", bg=BG_DARK, fg=TEXT_SEC,
                 font=self.font_h3).grid(row=14, column=0, sticky="w", pady=(14, 2))
        tk.Label(left,
                 text="Hick–Hyman Law: 3 buttons (not dropdown) → faster decision",
                 bg=BG_DARK, fg=TEXT_HINT,
                 font=self.font_small).grid(row=15, column=0, sticky="w", pady=(0, 6))

        pri_frame = tk.Frame(left, bg=BG_DARK)
        pri_frame.grid(row=16, column=0, sticky="ew")
        pri_frame.columnconfigure((0, 1, 2), weight=1)

        priority_btn_refs = {}

        def select_priority(lvl):
            sv_priority.set(lvl)
            for lv, btn in priority_btn_refs.items():
                pc = PRIORITY_COLORS[lv]
                if lv == lvl:
                    btn.config(bg=pc["bg"], fg="white",
                               relief="solid", bd=2)
                else:
                    btn.config(bg=BG_CARD, fg=TEXT_SEC,
                               relief="flat", bd=0)
            _update_preview()

        desc_map = {
            "CRITICAL": "Life-threatening",
            "URGENT":   "Serious / urgent",
            "STABLE":   "Non-urgent",
        }
        for col, lvl in enumerate(PRIORITY_LEVELS):
            pc  = PRIORITY_COLORS[lvl]
            btn = tk.Button(
                pri_frame,
                text=f"{lvl}\n{desc_map[lvl]}",
                bg=BG_CARD, fg=TEXT_SEC,
                font=self.font_btn,
                relief="flat", cursor="hand2",
                width=14,
                pady=12,          # FITTS' LAW: tall, easy to click
                activebackground=pc["bg"],
                activeforeground="white",
                command=lambda l=lvl: select_priority(l)
            )
            btn.grid(row=0, column=col, padx=(0, 6), sticky="ew")
            priority_btn_refs[lvl] = btn

        err_priority = tk.Label(left, text="", bg=BG_DARK,
                                fg="#E74C3C", font=self.font_small)
        err_priority.grid(row=17, column=0, sticky="w", pady=(2, 0))

        # ── LIVE PREVIEW (Gulf of Evaluation) ──
        tk.Label(right, text="LIVE PREVIEW", bg=BG_PANEL, fg=TEXT_HINT,
                 font=self.font_badge).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(right, text="Gulf of Evaluation:\nsee record before committing",
                 bg=BG_PANEL, fg=TEXT_HINT, font=self.font_small,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 8))
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        card = tk.Frame(right, bg=BG_CARD, padx=14, pady=12)
        card.pack(fill="x", padx=14)

        prev_bar       = tk.Frame(card, bg=TEXT_HINT, height=4)
        prev_bar.pack(fill="x", pady=(0, 8))
        prev_name      = tk.Label(card, text="— name —",       bg=BG_CARD, fg=TEXT_HINT, font=self.font_h2)
        prev_name.pack(anchor="w")
        prev_complaint = tk.Label(card, text="Chief complaint", bg=BG_CARD, fg=TEXT_HINT, font=self.font_body)
        prev_complaint.pack(anchor="w")
        prev_age       = tk.Label(card, text="Age: —",          bg=BG_CARD, fg=TEXT_SEC,  font=self.font_body)
        prev_age.pack(anchor="w", pady=(6, 0))
        prev_priority  = tk.Label(card, text="Priority: —",     bg=BG_CARD, fg=TEXT_HINT, font=self.font_h3)
        prev_priority.pack(anchor="w")
        prev_vitals    = tk.Label(card, text="",                bg=BG_CARD, fg=TEXT_HINT, font=self.font_small)
        prev_vitals.pack(anchor="w", pady=(6, 0))

        def _update_preview(*_):
            n = sv_name.get().strip()
            prev_name.config(text=n or "— name —",
                             fg=TEXT_PRI if n else TEXT_HINT)
            c = sv_complaint.get()
            prev_complaint.config(text=c or "Chief complaint",
                                  fg=TEXT_SEC if c else TEXT_HINT)
            a = sv_age.get().strip()
            prev_age.config(text=f"Age: {a} — {sv_gender.get()}" if a else "Age: —")
            pri = sv_priority.get()
            if pri:
                pc = PRIORITY_COLORS[pri]
                prev_bar.config(bg=pc["bg"])
                prev_priority.config(text=f"Priority: {pri}", fg=pc["bg"])
            else:
                prev_bar.config(bg=TEXT_HINT)
                prev_priority.config(text="Priority: —", fg=TEXT_HINT)
            vp = []
            if sv_bp.get():   vp.append(f"BP {sv_bp.get()}")
            if sv_hr.get():   vp.append(f"HR {sv_hr.get()}")
            if sv_spo2.get(): vp.append(f"SpO₂ {sv_spo2.get()}")
            prev_vitals.config(text="  ".join(vp))

        for sv in [sv_name, sv_age, sv_gender, sv_complaint,
                   sv_bp, sv_hr, sv_spo2, sv_priority]:
            sv.trace_add("write", _update_preview)

        # ── Validation ──
        def _validate() -> bool:
            ok = True

            def check(var, key, test_fn, msg):
                nonlocal ok
                val = var.get().strip()
                err_labels[key].config(text="" if test_fn(val) else msg)
                w = entry_widgets[key]
                good = test_fn(val)
                if not good:
                    ok = False
                if not isinstance(w, ttk.Combobox):
                    w.configure(
                        highlightbackground=BORDER if good else "#E74C3C",
                        highlightcolor=ACCENT if good else "#E74C3C"
                    )

            check(sv_name,      "Patient Name *",
                  lambda v: len(v) >= 2,
                  "Name must be at least 2 characters")
            check(sv_age,       "Age *",
                  lambda v: v.isdigit() and 0 <= int(v) <= 120,
                  "Enter a valid age (0–120)")
            check(sv_complaint, "Chief Complaint *",
                  lambda v: len(v) >= 2,
                  "Please select a complaint")

            if not sv_priority.get():
                err_priority.config(text="Please select a priority level")
                ok = False
            else:
                err_priority.config(text="")

            return ok

        # ── Submit ──
        def _submit():
            if not _validate():
                return

            pri  = sv_priority.get()
            name = sv_name.get().strip()

            # Error recovery: confirm dialog (Gulf of Execution)
            confirmed = messagebox.askyesno(
                "Confirm Registration",
                f"Register patient?\n\n"
                f"  Name:       {name}\n"
                f"  Age:        {sv_age.get().strip()} — {sv_gender.get()}\n"
                f"  Complaint:  {sv_complaint.get()}\n"
                f"  Priority:   {pri}\n",
                parent=win,
                icon="warning" if pri == "CRITICAL" else "question"
            )
            if not confirmed:
                return

            pid = _next_id()
            p   = Patient(
                id=pid,
                name=name,
                age=int(sv_age.get().strip()),
                gender=sv_gender.get(),
                chief_complaint=sv_complaint.get(),
                priority=pri,
                bp=sv_bp.get().strip(),
                hr=sv_hr.get().strip(),
                spo2=sv_spo2.get().strip(),
            )
            p.add_note(f"Registered. Priority: {pri}.", "System")
            if sv_note.get().strip():
                p.add_note(sv_note.get().strip(), "Nurse")

            # ── ADD TO BOTH DICTIONARIES ──
            register_patient(p)   # → GLOBAL_PATIENTS + CURRENT_PATIENTS

            self._refresh_queue()
            win.destroy()

            if pri == "CRITICAL":
                messagebox.showwarning(
                    "Critical Patient Registered",
                    f"⚠  {name} added as CRITICAL.\nImmediate attention required.",
                    parent=self
                )

        # ── Populate the pre-packed btn_row (always visible at bottom) ──
        # Fitts' Law: full-width tall submit button = easiest possible target
        tk.Button(
            btn_row,
            text="✔  Register Patient",
            bg=ACCENT2, fg=BG_DARK,
            font=self.font_btn_lg,
            relief="flat", cursor="hand2",
            pady=14,
            activebackground="#17A589",
            activeforeground=BG_DARK,
            command=_submit
        ).pack(side="left", fill="x", expand=True, padx=(16, 8), pady=10)

        tk.Button(
            btn_row,
            text="Cancel",
            bg=BG_CARD, fg=TEXT_SEC,
            font=self.font_btn,
            relief="flat", cursor="hand2",
            padx=28, pady=14,
            activebackground=BORDER,
            activeforeground=TEXT_PRI,
            command=win.destroy
        ).pack(side="left", padx=(0, 16), pady=10)

        e_name.focus_set()

    # ─────────────────────────────────────────────
    #  SCREEN 3 — PATIENT DETAIL
    # ─────────────────────────────────────────────

    def _open_detail(self, patient: Patient):
        """
        AHCI concepts:
          Miller's Law   : 3 chunked info groups
          Gestalt Proximity: LabelFrame groups
          Gulf of Evaluation: timestamped notes log
          Fitts' Law     : large action buttons
          Situation Awareness: full history visible
          Error recovery : confirm before priority change / discharge
        """
        if self._detail_window and self._detail_window.winfo_exists():
            self._detail_window.destroy()

        win = tk.Toplevel(self)
        self._detail_window = win
        win.title(f"Patient — {patient.name}")
        win.geometry("720x700")
        win.configure(bg=BG_DARK)
        win.resizable(False, True)
        win.lift()

        pc = PRIORITY_COLORS[patient.priority]

        # Coloured header bar (Preattentive: priority visible immediately)
        top = tk.Frame(win, bg=pc["bg"], height=54)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text=f"  {patient.priority}",
                 bg=pc["bg"], fg="white",
                 font=self.font_title).pack(side="left", padx=14, pady=10)
        tk.Label(top,
                 text=f"ID #{patient.id:04d}  |  Arrived: {patient.arrived_at.strftime('%H:%M')}",
                 bg=pc["bg"], fg="white",
                 font=self.font_body).pack(side="right", padx=16)

        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(win, bg=BG_DARK)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        # Annotation
        tk.Label(body,
                 text="Miller's Law: 3 info chunks  |  Gestalt proximity: LabelFrame groups",
                 bg=BG_DARK, fg=TEXT_HINT, font=self.font_small).pack(anchor="w", pady=(0, 8))

        groups = tk.Frame(body, bg=BG_DARK)
        groups.pack(fill="x")

        def lf(parent, title, color):
            f = tk.LabelFrame(parent, text=f"  {title}  ",
                              bg=BG_PANEL, fg=color,
                              font=self.font_badge,
                              relief="solid", bd=1)
            return f

        def info_row(parent, label, value, vc=TEXT_PRI):
            r = tk.Frame(parent, bg=BG_PANEL)
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=label, bg=BG_PANEL, fg=TEXT_HINT,
                     font=self.font_small, width=14, anchor="w").pack(side="left")
            tk.Label(r, text=value or "—", bg=BG_PANEL,
                     fg=vc, font=self.font_body).pack(side="left")

        # Group 1: Personal
        g1 = lf(groups, "Personal", ACCENT)
        g1.pack(side="left", fill="both", expand=True, padx=(0, 6))
        info_row(g1, "Name",      patient.name)
        info_row(g1, "Age",       f"{patient.age} years")
        info_row(g1, "Gender",    patient.gender)
        info_row(g1, "Complaint", patient.chief_complaint)

        # Group 2: Vitals
        g2 = lf(groups, "Vitals", ACCENT2)
        g2.pack(side="left", fill="both", expand=True, padx=(0, 6))
        info_row(g2, "Blood Pressure", patient.bp   or "Not recorded")
        info_row(g2, "Heart Rate",     patient.hr   or "Not recorded")
        info_row(g2, "SpO₂",          patient.spo2 or "Not recorded")

        wait_lbl = tk.Label(g2, text="", bg=BG_PANEL, fg=ACCENT2,
                            font=self.font_timer)
        wait_lbl.pack(anchor="w", padx=10, pady=(4, 6))

        def _tick_wait():
            if win.winfo_exists():
                col = "#E74C3C" if patient.is_overdue() else ACCENT2
                wait_lbl.config(text=f"Wait: {patient.wait_str()}", fg=col)
                win.after(1000, _tick_wait)
        _tick_wait()

        # Group 3: Status
        g3 = lf(groups, "Status", pc["bg"])
        g3.pack(side="left", fill="both", expand=True)
        info_row(g3, "Priority",  patient.priority, vc=pc["bg"])
        info_row(g3, "Arrived",   patient.arrived_at.strftime("%H:%M:%S"))
        info_row(g3, "Notes",     f"{len(patient.notes)} entries")
        info_row(g3, "Overdue",   "YES" if patient.is_overdue() else "No",
                 vc="#E74C3C" if patient.is_overdue() else ACCENT2)

        # ── Action buttons (Fitts' Law) ──
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=10)
        tk.Label(body,
                 text="Fitts' Law: large buttons  |  Error recovery: confirm dialogs",
                 bg=BG_DARK, fg=TEXT_HINT,
                 font=self.font_small).pack(anchor="w", pady=(0, 8))

        act_row = tk.Frame(body, bg=BG_DARK)
        act_row.pack(fill="x")

        def upgrade():
            idx = PRIORITY_LEVELS.index(patient.priority)
            if idx == 0:
                messagebox.showinfo("Already Critical",
                                    "Patient is already CRITICAL.", parent=win)
                return
            new_p = PRIORITY_LEVELS[idx - 1]
            if messagebox.askyesno("Upgrade Priority",
                                   f"Upgrade {patient.name}:\n"
                                   f"{patient.priority} → {new_p}?",
                                   parent=win, icon="warning"):
                old = patient.priority
                patient.priority = new_p
                patient.add_note(f"Priority upgraded: {old} → {new_p}", "Nurse")
                self._refresh_queue()
                win.destroy()

        def downgrade():
            idx = PRIORITY_LEVELS.index(patient.priority)
            if idx == len(PRIORITY_LEVELS) - 1:
                messagebox.showinfo("Already Stable",
                                    "Patient is already STABLE.", parent=win)
                return
            new_p = PRIORITY_LEVELS[idx + 1]
            if messagebox.askyesno("Downgrade Priority",
                                   f"Downgrade {patient.name}:\n"
                                   f"{patient.priority} → {new_p}?",
                                   parent=win):
                old = patient.priority
                patient.priority = new_p
                patient.add_note(f"Priority downgraded: {old} → {new_p}", "Nurse")
                self._refresh_queue()
                win.destroy()

        def do_discharge():
            if messagebox.askyesno("Discharge Patient",
                                   f"Discharge {patient.name}?\n"
                                   f"They will be removed from the active queue\n"
                                   f"but kept in the all-time patient log.",
                                   parent=win):
                patient.add_note("Patient discharged.", "Nurse")
                discharge_patient(patient)   # removes from CURRENT, stays in GLOBAL
                self._refresh_queue()
                win.destroy()

        def do_edit():
            self._open_edit_form(patient, win)

        for text, bg, fn in [
            ("✎ Edit Patient",       "#5D6D7E",                              do_edit),
            ("▲ Upgrade Priority",   PRIORITY_COLORS["CRITICAL"]["bg"],      upgrade),
            ("▼ Downgrade Priority", PRIORITY_COLORS["URGENT"]["bg"],        downgrade),
            ("Discharge Patient",    PRIORITY_COLORS["STABLE"]["bg"],        do_discharge),
        ]:
            tk.Button(
                act_row,
                text=text, bg=bg, fg="white",
                font=self.font_btn,
                relief="flat", cursor="hand2",
                pady=10,
                activebackground=bg,
                activeforeground="white",
                command=fn
            ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        # ── Notes log (Gulf of Evaluation + Situation Awareness) ──
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=10)

        log_hdr = tk.Frame(body, bg=BG_DARK)
        log_hdr.pack(fill="x")
        tk.Label(log_hdr, text="Activity Log",
                 bg=BG_DARK, fg=TEXT_PRI,
                 font=self.font_h2).pack(side="left")
        tk.Label(log_hdr,
                 text="Gulf of Evaluation: full timestamped history",
                 bg=BG_DARK, fg=TEXT_HINT,
                 font=self.font_small).pack(side="right")

        log_frame = tk.Frame(body, bg=BG_PANEL)
        log_frame.pack(fill="both", expand=True, pady=(8, 0))

        log_txt = tk.Text(log_frame, bg=BG_PANEL, fg=TEXT_SEC,
                          font=self.font_mono, relief="flat",
                          state="disabled", wrap="word", height=8,
                          cursor="arrow")
        log_sb  = tk.Scrollbar(log_frame, command=log_txt.yview)
        log_txt.configure(yscrollcommand=log_sb.set)
        log_sb.pack(side="right", fill="y")
        log_txt.pack(fill="both", expand=True, padx=8, pady=6)

        def _refresh_log():
            log_txt.configure(state="normal")
            log_txt.delete("1.0", "end")
            for note in reversed(patient.notes):
                log_txt.insert("end", note + "\n")
            log_txt.configure(state="disabled")

        _refresh_log()

        # Add note
        note_row = tk.Frame(body, bg=BG_DARK)
        note_row.pack(fill="x", pady=(8, 0))
        note_var = tk.StringVar()
        note_e   = tk.Entry(note_row, textvariable=note_var,
                            bg=BG_INPUT, fg=TEXT_PRI,
                            font=self.font_body, relief="flat",
                            insertbackground=TEXT_PRI)
        note_e.configure(highlightthickness=1,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
        note_e.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        def _add_note():
            t = note_var.get().strip()
            if t:
                patient.add_note(t)
                note_var.set("")
                _refresh_log()
                self._refresh_queue()

        tk.Button(note_row, text="Add Note",
                  bg=ACCENT, fg="white",
                  font=self.font_btn, relief="flat", cursor="hand2",
                  padx=14, pady=6,
                  activebackground="#2471A3",
                  activeforeground="white",
                  command=_add_note).pack(side="left")

        note_e.bind("<Return>", lambda e: _add_note())

    # ─────────────────────────────────────────────
    #  EDIT PATIENT FORM
    # ─────────────────────────────────────────────

    def _open_edit_form(self, patient: Patient, detail_win: tk.Toplevel):
        """
        AHCI concepts:
          Gulf of Execution  : pre-filled fields — no need to re-enter known data
          Gulf of Evaluation : live preview updates as edits are made
          Error prevention   : validation before saving; confirm dialog on submit
          Fitts' Law         : large save button
          Hick-Hyman Law     : 3 priority buttons (not dropdown)
        """
        ewin = tk.Toplevel(self)
        ewin.title(f"Edit Patient — {patient.name}")
        ewin.geometry("1020x780")
        ewin.minsize(900, 660)
        ewin.configure(bg=BG_DARK)
        ewin.grab_set()
        ewin.resizable(True, True)
        ewin.lift()
        ewin.focus_force()

        pc = PRIORITY_COLORS[patient.priority]

        # ── Header ──
        hdr = tk.Frame(ewin, bg=HEADER_BG, height=52)
        hdr.pack(side="top", fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"  ✎  Edit Patient  —  #{patient.id:04d}",
                 bg=HEADER_BG, fg=TEXT_PRI,
                 font=self.font_title).pack(side="left", padx=16, pady=10)
        tk.Label(hdr, text="Pre-filled: Gulf of Execution",
                 bg=HEADER_BG, fg=TEXT_HINT,
                 font=self.font_small).pack(side="right", padx=16)
        tk.Frame(ewin, bg=BORDER, height=1).pack(side="top", fill="x")

        # ── Bottom button row (packed before body so always visible) ──
        btn_row = tk.Frame(ewin, bg=HEADER_BG)
        btn_row.pack(side="bottom", fill="x")
        tk.Frame(ewin, bg=BORDER, height=1).pack(side="bottom", fill="x")

        # ── Body ──
        body = tk.Frame(ewin, bg=BG_DARK)
        body.pack(side="top", fill="both", expand=True)

        left  = tk.Frame(body, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=20, pady=14)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")
        right = tk.Frame(body, bg=BG_PANEL)
        right.pack(side="left", fill="y", ipadx=12)

        # ── StringVars pre-filled with current patient data ──
        sv_name      = tk.StringVar(value=patient.name)
        sv_age       = tk.StringVar(value=str(patient.age))
        sv_gender    = tk.StringVar(value=patient.gender)
        sv_complaint = tk.StringVar(value=patient.chief_complaint)
        sv_bp        = tk.StringVar(value=patient.bp)
        sv_hr        = tk.StringVar(value=patient.hr)
        sv_spo2      = tk.StringVar(value=patient.spo2)
        sv_priority  = tk.StringVar(value=patient.priority)

        entry_widgets = {}
        err_labels    = {}

        def make_field(parent, label, var, row_num,
                       is_combo=False, values=None, hint=""):
            tk.Label(parent, text=label, bg=BG_DARK, fg=TEXT_SEC,
                     font=self.font_h3).grid(
                row=row_num * 3, column=0, sticky="w", pady=(10, 2))

            if is_combo:
                w = ttk.Combobox(parent, textvariable=var, values=values,
                                 state="readonly", font=self.font_body, width=34)
            else:
                w = tk.Entry(parent, textvariable=var,
                             bg=BG_INPUT, fg=TEXT_PRI,
                             font=self.font_body, relief="flat",
                             insertbackground=TEXT_PRI, width=36)
                w.configure(highlightthickness=1,
                            highlightbackground=BORDER,
                            highlightcolor=ACCENT)

            w.grid(row=row_num * 3 + 1, column=0, sticky="ew", ipady=7)

            if hint:
                tk.Label(parent, text=hint, bg=BG_DARK, fg=TEXT_HINT,
                         font=self.font_small).grid(
                    row=row_num * 3 + 1, column=1, sticky="w", padx=6)

            err = tk.Label(parent, text="", bg=BG_DARK,
                           fg="#E74C3C", font=self.font_small)
            err.grid(row=row_num * 3 + 2, column=0, sticky="w")

            entry_widgets[label] = w
            err_labels[label]    = err
            return w

        e_name      = make_field(left, "Patient Name *",   sv_name,      0)
        e_age       = make_field(left, "Age *",             sv_age,       1, hint="0–120")
        e_complaint = make_field(left, "Chief Complaint *", sv_complaint, 2,
                                 is_combo=True, values=CHIEF_COMPLAINTS)
        e_gender    = make_field(left, "Gender",            sv_gender,    3,
                                 is_combo=True, values=["Male", "Female", "Other"])

        # Vitals
        tk.Label(left, text="Vitals (optional)", bg=BG_DARK, fg=TEXT_SEC,
                 font=self.font_h3).grid(row=12, column=0, sticky="w", pady=(12, 4))
        vitals_row = tk.Frame(left, bg=BG_DARK)
        vitals_row.grid(row=13, column=0, sticky="ew")

        def mini_entry(parent, label, var, width=9):
            tk.Label(parent, text=label, bg=BG_DARK,
                     fg=TEXT_HINT, font=self.font_small).pack(side="left")
            e = tk.Entry(parent, textvariable=var,
                         bg=BG_INPUT, fg=TEXT_PRI,
                         font=self.font_body, relief="flat",
                         width=width, insertbackground=TEXT_PRI)
            e.configure(highlightthickness=1,
                        highlightbackground=BORDER,
                        highlightcolor=ACCENT)
            e.pack(side="left", padx=(2, 12), ipady=4)

        mini_entry(vitals_row, "BP:",   sv_bp,   9)
        mini_entry(vitals_row, "HR:",   sv_hr,   6)
        mini_entry(vitals_row, "SpO₂:", sv_spo2, 6)
        left.columnconfigure(0, weight=1)

        # ── Priority buttons (Hick-Hyman) ──
        tk.Label(left, text="Priority Level *", bg=BG_DARK, fg=TEXT_SEC,
                 font=self.font_h3).grid(row=14, column=0, sticky="w", pady=(14, 2))
        tk.Label(left,
                 text="Hick–Hyman Law: 3 buttons → faster decision",
                 bg=BG_DARK, fg=TEXT_HINT,
                 font=self.font_small).grid(row=15, column=0, sticky="w", pady=(0, 6))

        pri_frame = tk.Frame(left, bg=BG_DARK)
        pri_frame.grid(row=16, column=0, sticky="ew")
        pri_frame.columnconfigure((0, 1, 2), weight=1)

        priority_btn_refs = {}

        def select_priority(lvl):
            sv_priority.set(lvl)
            for lv, btn in priority_btn_refs.items():
                pcc = PRIORITY_COLORS[lv]
                if lv == lvl:
                    btn.config(bg=pcc["bg"], fg="white", relief="solid", bd=2)
                else:
                    btn.config(bg=BG_CARD, fg=TEXT_SEC, relief="flat", bd=0)
            _update_preview()

        desc_map = {"CRITICAL": "Life-threatening",
                    "URGENT":   "Serious / urgent",
                    "STABLE":   "Non-urgent"}

        for col_i, lvl in enumerate(PRIORITY_LEVELS):
            pcc = PRIORITY_COLORS[lvl]
            btn = tk.Button(
                pri_frame,
                text=f"{lvl}\n{desc_map[lvl]}",
                bg=pcc["bg"] if lvl == patient.priority else BG_CARD,
                fg="white" if lvl == patient.priority else TEXT_SEC,
                font=self.font_btn,
                relief="solid" if lvl == patient.priority else "flat",
                bd=2 if lvl == patient.priority else 0,
                cursor="hand2", width=14, pady=12,
                activebackground=pcc["bg"],
                activeforeground="white",
                command=lambda l=lvl: select_priority(l)
            )
            btn.grid(row=0, column=col_i, padx=(0, 6), sticky="ew")
            priority_btn_refs[lvl] = btn

        err_priority = tk.Label(left, text="", bg=BG_DARK,
                                fg="#E74C3C", font=self.font_small)
        err_priority.grid(row=17, column=0, sticky="w", pady=(2, 0))

        # ── Change summary (what's different) ──
        tk.Label(left, text="Change summary", bg=BG_DARK, fg=TEXT_SEC,
                 font=self.font_h3).grid(row=18, column=0, sticky="w", pady=(14, 4))
        changes_lbl = tk.Label(left, text="No changes yet.",
                               bg=BG_INPUT, fg=TEXT_HINT,
                               font=self.font_small, anchor="w",
                               justify="left", wraplength=380, padx=8, pady=6)
        changes_lbl.grid(row=19, column=0, sticky="ew")

        # ── Live preview (Gulf of Evaluation) ──
        tk.Label(right, text="LIVE PREVIEW", bg=BG_PANEL, fg=TEXT_HINT,
                 font=self.font_badge).pack(anchor="w", padx=16, pady=(16, 2))
        tk.Label(right, text="Gulf of Evaluation:\nverify edits before saving",
                 bg=BG_PANEL, fg=TEXT_HINT, font=self.font_small,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 8))
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=16, pady=(0, 10))

        card = tk.Frame(right, bg=BG_CARD, padx=14, pady=12)
        card.pack(fill="x", padx=14)

        prev_bar       = tk.Frame(card, bg=pc["bg"], height=4)
        prev_bar.pack(fill="x", pady=(0, 8))
        prev_name      = tk.Label(card, text=patient.name,    bg=BG_CARD, fg=TEXT_PRI, font=self.font_h2)
        prev_name.pack(anchor="w")
        prev_complaint = tk.Label(card, text=patient.chief_complaint, bg=BG_CARD, fg=TEXT_SEC, font=self.font_body)
        prev_complaint.pack(anchor="w")
        prev_age       = tk.Label(card, text=f"Age: {patient.age} — {patient.gender}", bg=BG_CARD, fg=TEXT_SEC, font=self.font_body)
        prev_age.pack(anchor="w", pady=(6, 0))
        prev_priority  = tk.Label(card, text=f"Priority: {patient.priority}", bg=BG_CARD, fg=pc["bg"], font=self.font_h3)
        prev_priority.pack(anchor="w")
        prev_vitals    = tk.Label(card, text="", bg=BG_CARD, fg=TEXT_HINT, font=self.font_small)
        prev_vitals.pack(anchor="w", pady=(6, 0))

        # Original snapshot for change detection
        original = {
            "name":      patient.name,
            "age":       str(patient.age),
            "gender":    patient.gender,
            "complaint": patient.chief_complaint,
            "bp":        patient.bp,
            "hr":        patient.hr,
            "spo2":      patient.spo2,
            "priority":  patient.priority,
        }

        def _update_preview(*_):
            n = sv_name.get().strip()
            prev_name.config(text=n or "— name —",
                             fg=TEXT_PRI if n else TEXT_HINT)
            c = sv_complaint.get()
            prev_complaint.config(text=c or "Chief complaint",
                                  fg=TEXT_SEC if c else TEXT_HINT)
            a = sv_age.get().strip()
            prev_age.config(
                text=f"Age: {a} — {sv_gender.get()}" if a else "Age: —")
            pri = sv_priority.get()
            if pri:
                pcc = PRIORITY_COLORS[pri]
                prev_bar.config(bg=pcc["bg"])
                prev_priority.config(text=f"Priority: {pri}", fg=pcc["bg"])
            else:
                prev_bar.config(bg=TEXT_HINT)
                prev_priority.config(text="Priority: —", fg=TEXT_HINT)
            vp = []
            if sv_bp.get():   vp.append(f"BP {sv_bp.get()}")
            if sv_hr.get():   vp.append(f"HR {sv_hr.get()}")
            if sv_spo2.get(): vp.append(f"SpO₂ {sv_spo2.get()}")
            prev_vitals.config(text="  ".join(vp))

            # Change summary
            current = {
                "name":      sv_name.get().strip(),
                "age":       sv_age.get().strip(),
                "gender":    sv_gender.get(),
                "complaint": sv_complaint.get(),
                "bp":        sv_bp.get().strip(),
                "hr":        sv_hr.get().strip(),
                "spo2":      sv_spo2.get().strip(),
                "priority":  sv_priority.get(),
            }
            diffs = []
            labels_map = {
                "name": "Name", "age": "Age", "gender": "Gender",
                "complaint": "Complaint", "bp": "BP", "hr": "HR",
                "spo2": "SpO₂", "priority": "Priority"
            }
            for k, lbl in labels_map.items():
                if current[k] != original[k]:
                    diffs.append(f"{lbl}: '{original[k]}' → '{current[k]}'")
            changes_lbl.config(
                text="\n".join(diffs) if diffs else "No changes yet.",
                fg=ACCENT2 if diffs else TEXT_HINT
            )

        for sv in [sv_name, sv_age, sv_gender, sv_complaint,
                   sv_bp, sv_hr, sv_spo2, sv_priority]:
            sv.trace_add("write", _update_preview)

        _update_preview()  # init preview with current values

        # ── Validation ──
        def _validate() -> bool:
            ok = True

            def check(var, key, test_fn, msg):
                nonlocal ok
                val = var.get().strip()
                good = test_fn(val)
                err_labels[key].config(text="" if good else msg)
                w = entry_widgets[key]
                if not isinstance(w, ttk.Combobox):
                    w.configure(
                        highlightbackground=BORDER if good else "#E74C3C",
                        highlightcolor=ACCENT if good else "#E74C3C"
                    )
                if not good:
                    ok = False

            check(sv_name,      "Patient Name *",
                  lambda v: len(v) >= 2,    "Name must be at least 2 characters")
            check(sv_age,       "Age *",
                  lambda v: v.isdigit() and 0 <= int(v) <= 120,
                  "Enter a valid age (0–120)")
            check(sv_complaint, "Chief Complaint *",
                  lambda v: len(v) >= 2,    "Please select a complaint")

            if not sv_priority.get():
                err_priority.config(text="Please select a priority level")
                ok = False
            else:
                err_priority.config(text="")
            return ok

        # ── Save ──
        def _save():
            if not _validate():
                return

            # Build change list for the confirm dialog and the audit log
            new_vals = {
                "name":      sv_name.get().strip(),
                "age":       sv_age.get().strip(),
                "gender":    sv_gender.get(),
                "complaint": sv_complaint.get(),
                "bp":        sv_bp.get().strip(),
                "hr":        sv_hr.get().strip(),
                "spo2":      sv_spo2.get().strip(),
                "priority":  sv_priority.get(),
            }
            changed_fields = {k: (original[k], new_vals[k])
                              for k in original if original[k] != new_vals[k]}

            if not changed_fields:
                messagebox.showinfo("No Changes",
                                    "No fields were modified.", parent=ewin)
                return

            summary = "\n".join(
                f"  {k.capitalize()}: '{v[0]}' → '{v[1]}'"
                for k, v in changed_fields.items()
            )
            if not messagebox.askyesno(
                "Confirm Changes",
                f"Save the following changes to {patient.name}?\n\n{summary}",
                parent=ewin
            ):
                return

            # Apply changes to Patient object
            patient.name            = new_vals["name"]
            patient.age             = int(new_vals["age"])
            patient.gender          = new_vals["gender"]
            patient.chief_complaint = new_vals["complaint"]
            patient.bp              = new_vals["bp"]
            patient.hr              = new_vals["hr"]
            patient.spo2            = new_vals["spo2"]
            patient.priority        = new_vals["priority"]

            # Audit log entry
            patient.add_note(
                "Record edited: " + "; ".join(
                    f"{k}={v[1]}" for k, v in changed_fields.items()
                ), "Nurse"
            )

            self._refresh_queue()
            ewin.destroy()
            detail_win.destroy()
            # Re-open detail so nurse sees updated info immediately
            self._open_detail(patient)

        # ── Populate button row ──
        tk.Button(
            btn_row,
            text="✔  Save Changes",
            bg=ACCENT2, fg=BG_DARK,
            font=self.font_btn_lg,
            relief="flat", cursor="hand2",
            pady=14,
            activebackground="#17A589",
            activeforeground=BG_DARK,
            command=_save
        ).pack(side="left", fill="x", expand=True, padx=(16, 8), pady=10)

        tk.Button(
            btn_row,
            text="Cancel",
            bg=BG_CARD, fg=TEXT_SEC,
            font=self.font_btn,
            relief="flat", cursor="hand2",
            padx=28, pady=14,
            activebackground=BORDER,
            activeforeground=TEXT_PRI,
            command=ewin.destroy
        ).pack(side="left", padx=(0, 16), pady=10)

        e_name.focus_set()

    # ─────────────────────────────────────────────
    #  ALL-TIME LOG WINDOW  (GLOBAL_PATIENTS)
    # ─────────────────────────────────────────────

    def _open_global_log(self):
        win = tk.Toplevel(self)
        win.title("All-Time Patient Log (GLOBAL_PATIENTS)")
        win.geometry("800x520")
        win.configure(bg=BG_DARK)
        win.lift()

        hdr = tk.Frame(win, bg=HEADER_BG, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  All-Time Patient Registry  (GLOBAL_PATIENTS dict)",
                 bg=HEADER_BG, fg=TEXT_PRI,
                 font=self.font_h2).pack(side="left", padx=16, pady=14)
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x")

        col_hdr = tk.Frame(win, bg=BG_PANEL)
        col_hdr.pack(fill="x", padx=16, pady=(8, 0))
        for text, w in [("ID", 5), ("NAME", 20), ("AGE", 5),
                        ("PRIORITY", 10), ("ARRIVED", 10),
                        ("STATUS", 12), ("NOTES", 6)]:
            tk.Label(col_hdr, text=text, bg=BG_PANEL, fg=TEXT_HINT,
                     font=self.font_badge, width=w, anchor="w").pack(
                side="left", padx=6, pady=6)
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16)

        canvas = tk.Canvas(win, bg=BG_DARK, highlightthickness=0)
        vsb    = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True, padx=16)

        inner = tk.Frame(canvas, bg=BG_DARK)
        cw    = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))

        all_patients = sorted(GLOBAL_PATIENTS.values(),
                              key=lambda p: p.id, reverse=True)

        if not all_patients:
            tk.Label(inner, text="No patients registered yet.",
                     bg=BG_DARK, fg=TEXT_HINT,
                     font=self.font_h2).pack(pady=40)
        else:
            for i, p in enumerate(all_patients):
                row_bg = BG_CARD if i % 2 == 0 else BG_PANEL
                row = tk.Frame(inner, bg=row_bg)
                row.pack(fill="x", pady=1)
                pc  = PRIORITY_COLORS[p.priority]
                tk.Frame(row, bg=pc["bg"], width=5).pack(side="left", fill="y")

                status = "Discharged" if p.discharged else "Active"
                s_col  = TEXT_HINT if p.discharged else ACCENT2

                for text, w, color in [
                    (f"#{p.id:04d}",                       5,  TEXT_HINT),
                    (p.name,                               20,  TEXT_PRI),
                    (str(p.age),                            5,  TEXT_SEC),
                    (p.priority,                           10,  pc["bg"]),
                    (p.arrived_at.strftime("%H:%M"),       10,  TEXT_SEC),
                    (status,                               12,  s_col),
                    (str(len(p.notes)),                     6,  TEXT_HINT),
                ]:
                    tk.Label(row, text=text, bg=row_bg,
                             fg=color, font=self.font_body,
                             width=w, anchor="w").pack(
                        side="left", padx=6, pady=4)

        tk.Label(win,
                 text=f"Total records in GLOBAL_PATIENTS: {len(GLOBAL_PATIENTS)}  "
                      f"|  Active in CURRENT_PATIENTS: {len(CURRENT_PATIENTS)}",
                 bg=BG_PANEL, fg=TEXT_SEC,
                 font=self.font_small).pack(fill="x", padx=16, pady=6)

    # ─────────────────────────────────────────────
    #  BACKGROUND LOOPS
    # ─────────────────────────────────────────────

    def _start_clock(self):
        def _tick():
            now = datetime.now()
            self.lbl_time.config(text=now.strftime("%H:%M:%S"))
            self.lbl_date.config(text=now.strftime("%A, %d %B %Y"))
            self._update_wait_labels()
            self.after(1000, _tick)
        _tick()

    def _update_wait_labels(self):
        """Gulf of Evaluation: wait times refresh every second."""
        for p in CURRENT_PATIENTS.values():
            lbl = getattr(p, "_wait_lbl", None)
            if lbl:
                try:
                    col = "#E74C3C" if p.is_overdue() else ACCENT2
                    lbl.config(text=p.wait_str(), fg=col)
                except tk.TclError:
                    pass

    def _start_flash_loop(self):
        """Preattentive motion cue for overdue CRITICAL patients."""
        def _flash():
            self._flash_state = not self._flash_state
            for p in CURRENT_PATIENTS.values():
                lbl = getattr(p, "_flash_lbl", None)
                if lbl:
                    try:
                        lbl.config(bg="#E74C3C" if self._flash_state else "#922B21")
                    except tk.TclError:
                        pass
            self.after(600, _flash)
        _flash()

    # ─────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────

    def _discharge_all_stable(self):
        stable = [p for p in CURRENT_PATIENTS.values()
                  if p.priority == "STABLE"]
        if not stable:
            messagebox.showinfo("None", "No stable patients to discharge.", parent=self)
            return
        if messagebox.askyesno("Discharge All Stable",
                               f"Discharge {len(stable)} stable patient(s)?",
                               parent=self):
            for p in stable:
                p.add_note("Batch discharge.", "System")
                discharge_patient(p)
            self._refresh_queue()

    def _seed_demo_patients(self):
        demo = [
            ("Ahmed Hassan",    42, "Male",   "Chest pain",            "CRITICAL", "130/85", "110", "94%",  420),
            ("Fatima Malik",    67, "Female", "Stroke symptoms",       "CRITICAL", "160/100","92",  "89%",  180),
            ("Sara Khan",       28, "Female", "Severe abdominal pain", "URGENT",   "118/76", "88",  "98%",  900),
            ("Omar Siddiqui",   55, "Male",   "Shortness of breath",   "URGENT",   "142/90", "104", "91%", 1200),
            ("Zainab Qureshi",  19, "Female", "Head trauma",           "URGENT",   "110/70", "78",  "99%",  600),
            ("Muhammad Ali",    73, "Male",   "Altered consciousness", "CRITICAL", "90/60",  "118", "87%",   60),
            ("Aisha Rehman",    34, "Female", "Allergic reaction",     "URGENT",   "105/68", "96",  "97%", 1500),
            ("Hassan Mirza",    45, "Male",   "Back pain",             "STABLE",   "125/82", "72",  "99%", 3600),
            ("Nadia Farooq",    22, "Female", "Fever",                 "STABLE",   "112/74", "82",  "98%", 2400),
        ]
        for (name, age, gender, complaint, priority,
             bp, hr, spo2, wait_sec) in demo:
            pid = _next_id()
            p   = Patient(
                id=pid, name=name, age=age, gender=gender,
                chief_complaint=complaint, priority=priority,
                bp=bp, hr=hr, spo2=spo2,
                arrived_at=datetime.fromtimestamp(
                    datetime.now().timestamp() - wait_sec)
            )
            p.add_note(f"Registered. Priority: {priority}.", "System")
            if priority == "CRITICAL":
                p.add_note("Attending physician notified.", "Charge Nurse")
            register_patient(p)   # → GLOBAL_PATIENTS + CURRENT_PATIENTS
