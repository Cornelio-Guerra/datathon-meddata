"""Adaptador del score estadístico de diabetes para el dashboard.

Conecta con src/score_diabetes.py sin modificarlo ni duplicar lógica,
extrayendo métricas poblacionales y proveyendo cálculo individual para pacientes.
"""

from __future__ import annotations

import functools
from pathlib import Path
import runpy
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCORE_SCRIPT = ROOT / "src" / "score_diabetes.py"


@functools.lru_cache(maxsize=1)
def load_score_module() -> dict[str, Any]:
    """Ejecuta y cachea el módulo de score estadístico de Cornelio en memoria."""
    if not SCORE_SCRIPT.exists():
        raise FileNotFoundError(f"No se encontró el motor de score en {SCORE_SCRIPT}")
    return runpy.run_path(str(SCORE_SCRIPT))


def get_score_summary() -> dict[str, Any]:
    """Extrae las métricas poblacionales y tablas del score estadístico."""
    ns = load_score_module()
    df = ns["df"]
    t_df = ns["T"]
    grupos_df = ns["grupos"]
    corte_derivacion = int(ns["CORTE_DERIVACION"])
    cortes = [int(c) for c in ns["cortes"]]

    total_pop = len(df)
    score_min = int(df["SCORE"].min())
    score_max = int(df["SCORE"].max())
    score_mean = round(float(df["SCORE"].mean()), 2)
    derived_count = int(df["DERIVAR"].sum())
    derived_pct = round(100.0 * derived_count / total_pop, 1) if total_pop else 0.0

    # Distribución por riesgo
    risk_distribution = []
    order = ["Bajo", "Moderado", "Alto", "Muy alto"]
    prev_map = {
        "Bajo": "≤6 pts",
        "Moderado": "7–9 pts",
        "Alto": "10–12 pts",
        "Muy alto": "≥13 pts",
    }
    for r in order:
        if r in grupos_df.index:
            row = grupos_df.loc[r]
            n_patients = int(row["n"])
            cases = int(row["casos"])
            prev = float(row["prev_%"])
            pct_pop = round(100.0 * n_patients / total_pop, 1) if total_pop else 0.0
            risk_distribution.append({
                "level": r,
                "range": prev_map.get(r, ""),
                "n": n_patients,
                "cases": cases,
                "prevalence": prev,
                "population_pct": pct_pop,
            })

    # Tabla de puntuación por factores
    score_table = []
    for _, row in t_df.iterrows():
        score_table.append({
            "factor": str(row["factor"]),
            "nombre": str(row["nombre"]),
            "nivel": int(row["nivel"]) if str(row["nivel"]).isdigit() else row["nivel"],
            "n": int(row["n"]),
            "prev_pct": float(row["prev_%"]),
            "or": float(row["OR"]),
            "puntos": int(row["puntos"]),
        })

    vp = int(ns["VP"])
    fn = int(ns["FN"])
    fp = int(ns["FP"])
    vn = int(ns["VN"])

    return {
        "status": "ok",
        "method": "Sullivan et al. (Framework Framingham basado en Odds Ratios)",
        "population_n": total_pop,
        "score_min": score_min,
        "score_max": score_max,
        "score_mean": score_mean,
        "derivation_cutoff": corte_derivacion,
        "cutoffs": cortes,
        "derived_patients": derived_count,
        "derived_pct": derived_pct,
        "metrics": {
            "sensitivity": round(float(ns["sens"]) * 100.0, 1),
            "specificity": round(float(ns["esp"]) * 100.0, 1),
            "ppv": round(float(ns["vpp"]) * 100.0, 1),
            "npv": round(float(ns["vpn"]) * 100.0, 1),
            "auc": round(float(ns["auc"]), 4),
            "detected_diabetics": vp,
            "total_diabetics": vp + fn,
            "false_positives": fp,
            "true_negatives": vn,
        },
        "risk_distribution": risk_distribution,
        "score_table": score_table,
        "calibration_constant_b": round(float(ns["B"]), 4),
        "disclaimer": (
            "Este resultado es una estimación estadística basada en indicadores poblacionales "
            "y NO constituye un diagnóstico médico. Consulte siempre a un profesional de la salud."
        ),
    }


def discretize_bmi(bmi_val: float) -> tuple[int, str, int]:
    """Mapea IMC continuo a nivel de Sullivan y puntos (idéntico a pd.cut con right=True)."""
    if bmi_val <= 25.0:
        return 0, "≤ 25.0 (Normal / Bajo)", 0
    elif bmi_val <= 30.0:
        return 1, "25.1 – 30.0 (Sobrepeso)", 1
    elif bmi_val <= 35.0:
        return 2, "30.1 – 35.0 (Obesidad I)", 2
    else:
        return 3, "> 35.0 (Obesidad II o III)", 2


def discretize_age(age_val: int | float) -> tuple[int, str, int]:
    """Mapea edad (en categoría BRFSS 1-13 o en años) a nivel y puntos."""
    val = float(age_val)
    # Si viene como categoría BRFSS (1..13)
    if 1 <= val <= 13 and float(val).is_integer():
        cat = int(val)
        if cat <= 4:      # 18-39
            return 0, "18–39 años (Cat. 1–4)", 0
        elif cat <= 7:    # 40-54
            return 1, "40–54 años (Cat. 5–7)", 2
        elif cat <= 9:    # 55-64
            return 2, "55–64 años (Cat. 8–9)", 2
        elif cat <= 11:   # 65-74
            return 3, "65–74 años (Cat. 10–11)", 3
        else:             # 75+
            return 4, "75 o más años (Cat. 12–13)", 3
    # Si viene como edad en años cumplidos
    if val < 40:
        return 0, "Menor de 40 años", 0
    elif val < 55:
        return 1, "40–54 años", 2
    elif val < 65:
        return 2, "55–64 años", 2
    elif val < 75:
        return 3, "65–74 años", 3
    else:
        return 4, "75 o más años", 3


def discretize_gen_health(gen_hlth: int | float) -> tuple[int, str, int]:
    """Mapea salud autopercibida (1=Excelente .. 5=Mala) a nivel y puntos."""
    val = int(gen_hlth)
    labels = {
        1: (0, "Excelente", 0),
        2: (1, "Muy buena", 1),
        3: (2, "Buena", 3),
        4: (3, "Regular", 3),
        5: (4, "Mala", 4),
    }
    return labels.get(val, (0, "Excelente", 0))


def calculate_patient_score(patient_data: dict[str, Any]) -> dict[str, Any]:
    """Calcula el score individual y riesgo de un paciente siguiendo las reglas exactas."""
    # Validación de campos obligatorios
    required = [
        "BMI", "Age", "GenHlth", "HighBP", "HighChol",
        "DiffWalk", "HeartDiseaseorAttack", "Stroke",
        "PhysActivity", "HvyAlcoholConsump"
    ]
    missing = [f for f in required if f not in patient_data or patient_data[f] is None]
    if missing:
        raise ValueError(f"Faltan campos obligatorios para el cálculo: {', '.join(missing)}")

    try:
        bmi = float(patient_data["BMI"])
        age = float(patient_data["Age"])
        gen_hlth = int(patient_data["GenHlth"])
        high_bp = int(patient_data["HighBP"])
        high_chol = int(patient_data["HighChol"])
        diff_walk = int(patient_data["DiffWalk"])
        heart_dis = int(patient_data["HeartDiseaseorAttack"])
        stroke = int(patient_data["Stroke"])
        phys_act = int(patient_data["PhysActivity"])
        alcohol = int(patient_data["HvyAlcoholConsump"])
    except (ValueError, TypeError) as e:
        raise ValueError(f"Formato numérico inválido en uno o más campos: {e}")

    # Validaciones de rango
    if not (10 <= bmi <= 80):
        raise ValueError(f"IMC fuera de rango válido (10–80): {bmi}")
    if not (1 <= age <= 120):
        raise ValueError(f"Edad fuera de rango válido (1–120 o cat. 1–13): {age}")
    if gen_hlth not in (1, 2, 3, 4, 5):
        raise ValueError(f"Salud autopercibida (GenHlth) debe estar entre 1 (Excelente) y 5 (Mala): {gen_hlth}")
    for k, v in [("HighBP", high_bp), ("HighChol", high_chol), ("DiffWalk", diff_walk),
                 ("HeartDiseaseorAttack", heart_dis), ("Stroke", stroke),
                 ("PhysActivity", phys_act), ("HvyAlcoholConsump", alcohol)]:
        if v not in (0, 1):
            raise ValueError(f"El campo binario {k} debe ser 0 o 1 (recibido: {v})")

    # Mapeo de factores a puntos según T (tabla de Sullivan)
    lvl_bmi, lbl_bmi, pts_bmi = discretize_bmi(bmi)
    lvl_age, lbl_age, pts_age = discretize_age(age)
    lvl_hlth, lbl_hlth, pts_hlth = discretize_gen_health(gen_hlth)

    pts_bp = 2 if high_bp == 1 else 0
    pts_chol = 2 if high_chol == 1 else 0
    pts_walk = 2 if diff_walk == 1 else 0
    pts_heart = 2 if heart_dis == 1 else 0
    pts_stroke = 1 if stroke == 1 else 0
    pts_act = -1 if phys_act == 1 else 0
    pts_alc = -1 if alcohol == 1 else 0

    breakdown = [
        {"factor": "IMC", "field": "BMI", "input_value": bmi, "category": lbl_bmi, "points": pts_bmi},
        {"factor": "Edad", "field": "Age", "input_value": age, "category": lbl_age, "points": pts_age},
        {"factor": "Salud autopercibida", "field": "GenHlth", "input_value": gen_hlth, "category": lbl_hlth, "points": pts_hlth},
        {"factor": "Presión arterial alta", "field": "HighBP", "input_value": high_bp, "category": "Sí" if high_bp else "No", "points": pts_bp},
        {"factor": "Colesterol alto", "field": "HighChol", "input_value": high_chol, "category": "Sí" if high_chol else "No", "points": pts_chol},
        {"factor": "Dificultad para caminar", "field": "DiffWalk", "input_value": diff_walk, "category": "Sí" if diff_walk else "No", "points": pts_walk},
        {"factor": "Enfermedad cardíaca", "field": "HeartDiseaseorAttack", "input_value": heart_dis, "category": "Sí" if heart_dis else "No", "points": pts_heart},
        {"factor": "Derrame previo (ACV)", "field": "Stroke", "input_value": stroke, "category": "Sí" if stroke else "No", "points": pts_stroke},
        {"factor": "Actividad física", "field": "PhysActivity", "input_value": phys_act, "category": "Sí (Protector)" if phys_act else "No", "points": pts_act},
        {"factor": "Consumo alto de alcohol", "field": "HvyAlcoholConsump", "input_value": alcohol, "category": "Sí" if alcohol else "No", "points": pts_alc},
    ]

    total_score = sum(item["points"] for item in breakdown)

    # Clasificación
    if total_score <= 6:
        risk_level = "Bajo"
        risk_color = "green"
        expected_prev = 4.4
        action_note = "Mantener estilos de vida saludables y control preventivo habitual."
    elif total_score <= 9:
        risk_level = "Moderado"
        risk_color = "amber"
        expected_prev = 17.9
        action_note = "Derivación recomendada: Tamizaje glucémico preventivo y asesoría en hábitos."
    elif total_score <= 12:
        risk_level = "Alto"
        risk_color = "orange"
        expected_prev = 33.1
        action_note = "Derivación prioritaria: Evaluación médica y pruebas de laboratorio (HbA1c/Glucosa en ayunas)."
    else:
        risk_level = "Muy alto"
        risk_color = "red"
        expected_prev = 49.2
        action_note = "Derivación urgente: Alta sospecha clínica; evaluación diagnóstica inmediata e intervención integral."

    derivar = total_score >= 7

    return {
        "status": "ok",
        "total_score": total_score,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "expected_prevalence_pct": expected_prev,
        "derivation_recommended": derivar,
        "derivation_cutoff": 7,
        "action_note": action_note,
        "factors_breakdown": breakdown,
        "disclaimer": (
            "Este resultado es una estimación estadística basada en indicadores poblacionales "
            "y NO constituye un diagnóstico médico. Consulte siempre a un profesional de la salud."
        ),
    }
