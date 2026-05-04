# Hospital Triage Assistant

The **Hospital Triage Assistant** is a desktop application designed to optimize the emergency department triage process. By applying core **Applied Human-Computer Interaction (AHCI)** principles, the application reduces cognitive load for medical staff, speeds up patient processing, and enhances situational awareness in high-stress environments.

---

## 🎨 Key Features & AHCI Principles

This project is a practical implementation of several design laws:
- **Prioritized Queue:** Automatically sorts patients based on severity and wait time (**Situational Awareness**).
- **Color-Coded Triage:** Instant recognition of patient status through preattentive attributes.
- **Error-Resistant Forms:** Real-time validation and "Gulf of Evaluation" live previews.
- **Optimized Interaction:** High-frequency actions are larger and more accessible (**Fitts' Law**).

For a detailed breakdown of AHCI concepts, see [AHCI_CONCEPTS.md](./AHCI_CONCEPTS.md).

---

## 🛠️ Installation & Setup

All dependencies are restricted to a local virtual environment (`.venv`).

### 1. Prerequisites
- **Python 3.8+**
- **Tkinter Library:** 
  - *Linux:* `sudo apt-get install python3-tk`
  - *macOS/Windows:* Usually bundled with Python.

### 2. Environment Setup
Clone the repository and run the following commands:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip and install (minimal) dependencies
pip install --upgrade pip
# Currently, the project uses Python Standard Libraries. 
# If external libraries are added, run:
# pip install -r requirements.txt
```

### 3. Running the App
Ensure your virtual environment is active, then run:

```bash
python main.py
```

---

## 📂 Project Structure

- `main.py`: Entry point for the application.
- `app.py`: Main UI logic and event handlers.
- `models.py`: Patient data structures and state management.
- `constants.py`: Styling, theme colors, and triage configuration.
- `AHCI_CONCEPTS.md`: Detailed mapping of design principles.

---

## 🏥 Usage Guide

1. **Dashboard:** View the active patient queue, sorted by criticality.
2. **Register:** Use the "Add New Patient" sidebar button. Enter patient details and select a priority.
3. **Monitor:** Watch for flashing "OVERDUE" alerts if a patient exceeds their priority-specific wait time.
4. **Action:** Click "View" on any patient row to see detailed history, add notes, or change priority.
5. **Discharge:** Once a patient is treated, use the "Discharge" button to remove them from the active queue while keeping their record in the global log.

---

## 📜 License
MIT License - See [LICENSE](./LICENSE) for details.
