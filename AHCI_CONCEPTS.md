# Applied Human-Computer Interaction (AHCI) Concepts

This document outlines the core AHCI principles implemented in the **Hospital Triage Assistant** to ensure efficiency, reduce cognitive load, and prevent errors in high-pressure medical environments.

---

## 1. Fitts' Law
**Definition:** The time to acquire a target is a function of the distance to and size of the target.
- **Implementation:** 
    - The "Add New Patient" button in the sidebar is significantly larger than other navigation elements, as it is the most frequent action.
    - Submit buttons in the registration form are full-width and tall to maximize clickable area.
    - Action buttons (View Detail, Discharge) are placed with sufficient padding and size to ensure rapid selection without precision errors.

## 2. Hick-Hyman Law
**Definition:** The time it takes to make a decision increases with the number and complexity of choices.
- **Implementation:** 
    - Instead of a long dropdown menu for priority levels, the registration form uses **3 large, distinct buttons** (Critical, Urgent, Stable). This allows the user to process and click the desired option in a single cognitive step.

## 3. Miller's Law (The Magical Number 7±2)
**Definition:** The average person can only keep 7±2 items in their working memory.
- **Implementation:** 
    - The active patient queue is visually constrained to show approximately 7 rows at a time without scrolling.
    - Patient data in the "Detail View" is **chunked** into three logical groups: Personal Info, Vitals, and History/Notes, preventing information overload.

## 4. Preattentive Attributes
**Definition:** Visual properties that the brain processes automatically before conscious attention.
- **Implementation:** 
    - **Color Coding:** Critical patients are marked with red (`#C0392B`), Urgent with Amber (`#D4870A`), and Stable with Green (`#1E8449`).
    - **Motion/Flashing:** Overdue patients trigger a flashing "⚠ OVERDUE" label, using movement/oscillation to demand immediate attention from the user.

## 5. Gulf of Evaluation
**Definition:** The difficulty of assessing the state of the system and whether goals have been met.
- **Implementation:** 
    - **Live Timers:** Wait times update every second, giving the nurse an immediate sense of the queue's "pressure."
    - **Real-time Preview:** As the user fills out the registration form, a "Live Preview" card updates on the right, allowing them to evaluate the record before committing it.

## 6. Gulf of Execution
**Definition:** The gap between a user's goal and the means to achieve it.
- **Implementation:** 
    - **Field Validation:** Required fields are highlighted in red if missed, providing immediate feedback on how to fix the error.
    - **Clear Affordances:** Buttons use hover effects and cursor changes to signal "clickability."
    - **Confirm Dialogs:** Critical actions like "Discharge" or "Register" show a summary confirmation, ensuring the user's intent matches the system action.

## 7. Gestalt Principle: Proximity
**Definition:** Objects that are close to each other are perceived as a group.
- **Implementation:** 
    - Related information (BP, HR, SpO2) is grouped within specific "LabelFrame" borders in the Detail View, helping the eye navigate the medical data faster.

## 8. Situational Awareness (SA)
**Definition:** Perceiving, comprehending, and projecting the state of the environment.
- **Implementation:** 
    - **Auto-Sorting:** The queue is always sorted by Priority then Wait Time, ensuring the nurse is always aware of the most "dangerous" situations first.
    - **Persistent Stats:** A "Queue Overview" panel in the sidebar provides a high-level summary of all active patient counts.
