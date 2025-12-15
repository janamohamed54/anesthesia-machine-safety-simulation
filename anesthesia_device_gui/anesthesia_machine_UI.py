import sys
from typing import Dict, List, Tuple
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox,
    QVBoxLayout, QHBoxLayout, QTextEdit, QGroupBox, QPushButton, QCheckBox
)
from PyQt5.QtCore import Qt


# =========================
# REALISTIC EVALUATION LOGIC
# =========================
def evaluate_anesthesia_realistic(
    patient_type: str,
    weight_kg: float,
    fio2: float,
    fresh_gas_flow_lpm: float,
    agent: str,
    agent_percent: float,
    airway_pressure_cmh2o: float,
    tidal_volume_ml: float,
    resp_rate_bpm: float,
    hypoxic_guard_enabled: bool
) -> Dict[str, any]:
    alarms: List[str] = []
    warnings: List[str] = []

    # ---- Validate basic numeric sanity (not "restrictions", but validity)
    if weight_kg <= 0:
        alarms.append("Invalid weight (must be > 0 kg).")
    if fio2 < 0 or fio2 > 100:
        alarms.append("Invalid FiO₂ (must be between 0 and 100%).")
    if fresh_gas_flow_lpm < 0:
        alarms.append("Invalid fresh gas flow (cannot be negative).")
    if agent_percent < 0:
        alarms.append("Invalid agent concentration (cannot be negative).")
    if resp_rate_bpm < 0:
        alarms.append("Invalid respiratory rate (cannot be negative).")
    if tidal_volume_ml < 0:
        alarms.append("Invalid tidal volume (cannot be negative).")

    # If invalids exist, stop further clinical reasoning
    if alarms:
        return {"status": "ALARM", "alarms": alarms, "warnings": warnings, "computed": {}}

    # ---- Oxygen safety
    if fio2 < 21:
        alarms.append("FiO₂ < 21% is not physiologically valid for delivered oxygen mixture.")
    elif fio2 < 30:
        alarms.append("HYPOXIC MIXTURE RISK: FiO₂ < 30% (high priority).")
    elif fio2 < 40:
        warnings.append("Low FiO₂ (30–39%): monitor oxygenation & clinical context.")

    if hypoxic_guard_enabled and fio2 < 25:
        alarms.append("Hypoxic Guard: FiO₂ below 25% → delivery should be inhibited.")

    # ---- Fresh Gas Flow (FGF) reasonableness
    if fresh_gas_flow_lpm == 0 and agent_percent > 0:
        alarms.append("Agent set > 0% but FGF = 0 → inconsistent delivery (check settings).")
    elif fresh_gas_flow_lpm <= 0.3 and agent_percent > 0:
        alarms.append("FGF very low with volatile agent → inadequate wash-in / unstable concentration.")

    if fresh_gas_flow_lpm < 0.5:
        warnings.append("Very low FGF (<0.5 L/min): risk of slow wash-in & CO₂ absorber dependence.")
    if fresh_gas_flow_lpm > 10:
        warnings.append("High FGF (>10 L/min): wasteful, drying, heat loss risk.")

    # ---- Agent limits (simplified realistic)
    agent_alarm_max = {"Sevoflurane": 4.0, "Isoflurane": 3.0, "Desflurane": 10.0}
    agent_warn_high = {"Sevoflurane": 3.0, "Isoflurane": 2.5, "Desflurane": 8.0}

    if agent_percent > agent_alarm_max.get(agent, 5.0):
        alarms.append(f"{agent} concentration too high (>{agent_alarm_max.get(agent)}%).")
    elif agent_percent > agent_warn_high.get(agent, 3.0):
        warnings.append(f"{agent} concentration high (>{agent_warn_high.get(agent)}%): consider reducing.")

    # ---- Ventilation computations
    mv_lpm = (tidal_volume_ml * resp_rate_bpm) / 1000.0  # L/min
    vt_ml_per_kg = tidal_volume_ml / weight_kg if weight_kg > 0 else 0

    # VT ranges based on patient type
    if patient_type == "adult":
        vt_rec_low, vt_rec_high = 6.0, 8.0
        mv_alarm_low, mv_warn_low = 3.0, 4.0
    else:
        vt_rec_low, vt_rec_high = 5.0, 8.0
        mv_alarm_low, mv_warn_low = 0.8, 1.2

    # VT alarms/warnings (mL/kg)
    if vt_ml_per_kg < 4.0:
        alarms.append(f"VT too low: {vt_ml_per_kg:.1f} mL/kg (<4).")
    elif vt_ml_per_kg < vt_rec_low:
        warnings.append(f"VT below recommended: {vt_ml_per_kg:.1f} mL/kg (target {vt_rec_low}-{vt_rec_high}).")

    if vt_ml_per_kg > 10.0:
        alarms.append(f"VT too high: {vt_ml_per_kg:.1f} mL/kg (>10).")
    elif vt_ml_per_kg > vt_rec_high:
        warnings.append(f"VT above recommended: {vt_ml_per_kg:.1f} mL/kg (target {vt_rec_low}-{vt_rec_high}).")

    # RR safety
    if resp_rate_bpm < 6:
        alarms.append("APNEA / severe bradypnea: RR < 6 bpm.")
    elif resp_rate_bpm < 8:
        warnings.append("Low RR (6–7 bpm): monitor ventilation adequacy.")
    elif resp_rate_bpm > 35:
        warnings.append("High RR (>35 bpm): possible distress or overventilation.")

    # Minute ventilation adequacy
    if mv_lpm < mv_alarm_low:
        alarms.append(f"Low minute ventilation: MV {mv_lpm:.1f} L/min (too low).")
    elif mv_lpm < mv_warn_low:
        warnings.append(f"Borderline MV: {mv_lpm:.1f} L/min (consider increasing VT/RR).")

    # Airway pressure
    if airway_pressure_cmh2o > 40:
        alarms.append("HIGH AIRWAY PRESSURE > 40 cmH₂O (barotrauma risk).")
    elif airway_pressure_cmh2o > 30:
        warnings.append("Elevated airway pressure (30–40 cmH₂O).")

    # Disconnection/leak suspicion: low pressure + low MV
    if airway_pressure_cmh2o < 5 and mv_lpm < mv_warn_low:
        alarms.append("Possible DISCONNECTION/LEAK: low pressure AND low ventilation.")

    status = "ALARM" if alarms else ("WARNING" if warnings else "RUNNING")

    computed = {
        "MV_Lmin": round(mv_lpm, 2),
        "VT_mLkg": round(vt_ml_per_kg, 2),
        "VT_target_mLkg": f"{vt_rec_low}-{vt_rec_high}"
    }

    return {"status": status, "alarms": alarms, "warnings": warnings, "computed": computed}


# =========================
# GUI – START MODE (type then press START)
# =========================
class AnesthesiaStartRealistic(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Anesthesia Workstation – Start Mode (Realistic)")
        self.setGeometry(280, 90, 980, 690)
        self.setStyleSheet("background-color:#0b0f14; color:#e6e6e6;")

        main = QVBoxLayout()
        self.setLayout(main)

        # Big banner
        self.banner = QLabel("IDLE – Enter parameters and press START")
        self.banner.setAlignment(Qt.AlignCenter)
        self.banner.setStyleSheet(self.banner_style("#4a4e69"))
        main.addWidget(self.banner)

        # Inputs
        input_box = QGroupBox("SETUP PARAMETERS")
        input_box.setStyleSheet("QGroupBox { font-size:16px; font-weight:bold; }")
        il = QVBoxLayout()
        input_box.setLayout(il)

        self.patient_type = QComboBox()
        self.patient_type.addItems(["adult", "pediatric"])
        il.addWidget(QLabel("Patient Type"))
        il.addWidget(self.patient_type)

        self.weight = self.add_input(il, "Weight (kg)", "70")
        self.fio2 = self.add_input(il, "FiO₂ (%)", "50")
        self.fgf = self.add_input(il, "Fresh Gas Flow (L/min)", "4")

        self.agent = QComboBox()
        self.agent.addItems(["Sevoflurane", "Isoflurane", "Desflurane"])
        il.addWidget(QLabel("Volatile Agent"))
        il.addWidget(self.agent)

        self.agent_pct = self.add_input(il, "Agent Concentration (%)", "2")
        self.pressure = self.add_input(il, "Airway Pressure (cmH₂O)", "18")
        self.vt = self.add_input(il, "Tidal Volume (mL)", "500")
        self.rr = self.add_input(il, "Respiratory Rate (bpm)", "12")

        self.hypoxic_guard = QCheckBox("Enable Hypoxic Guard (FiO₂ must be ≥ 25%)")
        self.hypoxic_guard.setChecked(True)
        il.addWidget(self.hypoxic_guard)

        main.addWidget(input_box)

        # Buttons
        btns = QHBoxLayout()
        self.start_btn = QPushButton("▶ START")
        self.start_btn.setStyleSheet(self.btn_style("#1faa59"))
        self.start_btn.clicked.connect(self.on_start)

        self.defaults_btn = QPushButton("Load Defaults")
        self.defaults_btn.setStyleSheet(self.btn_style("#264653"))
        self.defaults_btn.clicked.connect(self.load_defaults)

        self.reset_btn = QPushButton("RESET")
        self.reset_btn.setStyleSheet(self.btn_style("#8d99ae"))
        self.reset_btn.clicked.connect(self.reset_fields)

        btns.addWidget(self.start_btn)
        btns.addWidget(self.defaults_btn)
        btns.addWidget(self.reset_btn)
        main.addLayout(btns)

        # Output
        out_box = QGroupBox("RESULTS (Alarms / Warnings / Calculations)")
        out_box.setStyleSheet("QGroupBox { font-size:16px; font-weight:bold; }")
        ol = QVBoxLayout()
        out_box.setLayout(ol)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background-color:#121822; font-size:14px; padding:10px;")
        ol.addWidget(self.output)

        main.addWidget(out_box)

        self.load_defaults()

    # -------- UI helpers
    def add_input(self, layout, label, default):
        layout.addWidget(QLabel(label))
        e = QLineEdit(default)
        e.setStyleSheet("font-size:15px; padding:6px;")
        layout.addWidget(e)
        return e

    def btn_style(self, bg):
        return f"""
            QPushButton {{
                background-color:{bg};
                color:white;
                font-size:17px;
                font-weight:bold;
                padding:12px;
                border-radius:8px;
            }}
        """

    def banner_style(self, bg):
        return f"""
            QLabel {{
                background-color:{bg};
                color:white;
                font-size:28px;
                font-weight:900;
                padding:16px;
                border-radius:10px;
            }}
        """

    # -------- Actions
    def on_start(self):
        self.output.clear()
        try:
            result = evaluate_anesthesia_realistic(
                patient_type=self.patient_type.currentText(),
                weight_kg=float(self.weight.text()),
                fio2=float(self.fio2.text()),
                fresh_gas_flow_lpm=float(self.fgf.text()),
                agent=self.agent.currentText(),
                agent_percent=float(self.agent_pct.text()),
                airway_pressure_cmh2o=float(self.pressure.text()),
                tidal_volume_ml=float(self.vt.text()),
                resp_rate_bpm=float(self.rr.text()),
                hypoxic_guard_enabled=self.hypoxic_guard.isChecked()
            )
        except ValueError:
            self.banner.setText("ALARM – Invalid numeric input")
            self.banner.setStyleSheet(self.banner_style("#e63946"))
            self.output.setText("⛔ Please enter valid numbers in all fields.")
            return

        # Banner based on status
        if result["status"] == "RUNNING":
            self.banner.setText("RUNNING – Parameters accepted")
            self.banner.setStyleSheet(self.banner_style("#1faa59"))
        elif result["status"] == "WARNING":
            self.banner.setText("WARNING – Review recommended")
            self.banner.setStyleSheet(self.banner_style("#f4a261"))
        else:
            self.banner.setText("⛔ HIGH PRIORITY ALARM – Correct now")
            self.banner.setStyleSheet(self.banner_style("#e63946"))

        # Print computed values
        comp = result.get("computed", {})
        if comp:
            self.output.append("CALCULATED")
            self.output.append(f"- Minute Ventilation (MV): {comp['MV_Lmin']} L/min")
            self.output.append(f"- VT per kg: {comp['VT_mLkg']} mL/kg (target {comp['VT_target_mLkg']})")
            self.output.append("")

        # Print alarms/warnings
        if result["alarms"]:
            self.output.append("⛔ ALARMS")
            for a in result["alarms"]:
                self.output.append(f"- {a}")
            self.output.append("")

        if result["warnings"]:
            self.output.append("⚠ WARNINGS")
            for w in result["warnings"]:
                self.output.append(f"- {w}")
            self.output.append("")

        if not result["alarms"] and not result["warnings"]:
            self.output.append("✅ No issues detected. Minimum and clinical checks passed.")

    def load_defaults(self):
        self.patient_type.setCurrentIndex(0)  # adult
        self.weight.setText("70")
        self.fio2.setText("50")
        self.fgf.setText("4")
        self.agent.setCurrentIndex(0)  # sevo
        self.agent_pct.setText("2")
        self.pressure.setText("18")
        self.vt.setText("500")
        self.rr.setText("12")
        self.hypoxic_guard.setChecked(True)
        self.banner.setText("IDLE – Enter parameters and press START")
        self.banner.setStyleSheet(self.banner_style("#4a4e69"))
        self.output.clear()

    def reset_fields(self):
        for f in [self.weight, self.fio2, self.fgf, self.agent_pct, self.pressure, self.vt, self.rr]:
            f.setText("")
        self.output.clear()
        self.banner.setText("IDLE – Enter parameters and press START")
        self.banner.setStyleSheet(self.banner_style("#4a4e69"))


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = AnesthesiaStartRealistic()
    w.show()
    sys.exit(app.exec_())
