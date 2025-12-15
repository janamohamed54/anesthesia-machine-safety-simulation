# Anesthesia Machine Safety Simulation  
**Based on ISO 80601-2-13**

## 📌 Project Overview
This project is a **software-based simulation of an anesthesia workstation**, developed to demonstrate how **medical device safety standards** are applied in practice.

The application allows users to:
- Manually enter anesthesia parameters
- Start the system explicitly (start-based workflow)
- Detect unsafe operating conditions
- Display clear **warnings and high-priority alarms**
- Reset and recover without restarting the software

The simulation focuses on **clinical realism**, **human–machine interaction**, and **standards compliance**.

---

## 🏥 Simulated Medical Device
**Anesthesia Machine (Anesthetic Workstation)**

The simulation covers:
- Oxygen delivery (FiO₂)
- Fresh gas flow (FGF)
- Volatile anesthetic agent concentration
- Mechanical ventilation parameters
- Patient-dependent safety checks
- Alarm prioritization and escalation

---

## 📜 Applied Standards

### ✅ ISO 80601-2-13  
*Medical electrical equipment – Particular requirements for the basic safety and essential performance of an anaesthetic workstation*

This standard was selected because it specifically governs:
- Minimum oxygen concentration requirements
- Hypoxic mixture prevention
- Volatile anesthetic agent delivery safety
- Ventilation and airway pressure safety
- Alarm visibility, priority, and behavior
- Human–machine interface requirements

### Related Standards
- **IEC 60601-1** – General medical electrical safety  
- **IEC 60601-1-8** – Alarm systems  
- **ISO 14971** – Medical device risk management  

---

## ⚙️ Features
- Manual parameter entry (no automatic restriction)
- Start-based validation (realistic device workflow)
- Patient-specific ventilation logic (adult / pediatric)
- Realistic clinical constraints and thresholds
- Color-coded system states:
  - 🟢 RUNNING
  - 🟡 WARNING
  - 🔴 ALARM
- High-visibility alarm banner
- Reset and default recovery buttons
- PyQt-based graphical user interface (desktop application)

---

## 🧠 Safety Logic Highlights
The system evaluates:
- Hypoxic gas mixtures (FiO₂ limits)
- Hypoxic guard behavior
- Minute ventilation adequacy
- Tidal volume relative to patient weight (mL/kg)
- Apnea and hypoventilation
- High airway pressure (barotrauma risk)
- Volatile anesthetic agent overdose
- Gas delivery inconsistencies

Alarm severity is escalated based on clinical risk.

---

## 🖥️ User Interface
The GUI is designed according to **human factors principles**:
- Clear separation between setup and operation
- Explicit START button
- Large, color-coded alarm banner
- Dedicated alarm output panel
- Reset without restarting the program

Screenshots of:
- Normal operation
- Warning condition
- Alarm condition  
can be found in the project report.

---

## ▶️ How to Run

### 1️⃣ Install requirements
```bash
pip install pyqt5
