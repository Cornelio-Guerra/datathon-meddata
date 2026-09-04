"""Servidor local para el tablero de decisión sobre diabetes.

Sirve la interfaz web y expone una API JSON para análisis poblacional,
integración del score estadístico de Sullivan y calculadora individual de riesgo.
"""

from __future__ import annotations

import csv
import json
import math
import mimetypes
import os
import sys
from collections import defaultdict
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    from dashboard.score_adapter import calculate_patient_score, get_score_summary
except ImportError:
    from score_adapter import calculate_patient_score, get_score_summary

DATA_DIR = ROOT / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"
PORT = int(os.environ.get("MEDDATA_PORT", "8000"))
MODEL_CACHE: dict[str, dict[str, Any]] = {}


def as_number(value: Any) -> float | None:
    """Devuelve un número finito o None, sin convertir silenciosamente errores."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def percentage(numerator: int | float, denominator: int | float) -> float:
    return round((100 * numerator / denominator), 1) if denominator else 0.0


def pretty_number(value: int | float) -> str:
    return f"{int(value):,}".replace(",", ".")


BRFSS_AGE_LABELS = {
    "1": "18–24", "2": "25–29", "3": "30–34", "4": "35–39",
    "5": "40–44", "6": "45–49", "7": "50–54", "8": "55–59",
    "9": "60–64", "10": "65–69", "11": "70–74", "12": "75–79",
    "13": "80 o más",
}


def brfss_age(value: Any) -> str:
    number = as_number(value)
    if number is None:
        return "Sin dato"
    return BRFSS_AGE_LABELS.get(str(int(number)), "Sin dato")


def brfss_bmi(value: Any) -> str:
    number = as_number(value)
    if number is None or number == 0:
        return "Sin dato"
    if number <= 25:
        return "< 25 (Normal)"
    if number <= 30:
        return "25–30 (Sobrepeso)"
    if number <= 35:
        return "30–35 (Obesidad I)"
    return "> 35 (Obesidad II/III)"


def binary_label(value: Any, yes: str, no: str) -> str:
    number = as_number(value)
    if number is None:
        return "Sin dato"
    return yes if number == 1 else no


def general_health(value: Any) -> str:
    labels = {1: "Excelente", 2: "Muy buena", 3: "Buena", 4: "Regular", 5: "Mala"}
    number = as_number(value)
    return labels.get(int(number), "Sin dato") if number is not None else "Sin dato"


def find_dataset() -> Path:
    """Encuentra el CSV de BRFSS para diabetes en data/."""
    candidates = list(DATA_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("No se encontró ningún CSV dentro de data/.")

    for p in candidates:
        if "brfss" in p.name.lower() or "diabetes_012" in p.name.lower():
            return p
    return candidates[0]


def schema_for(headers: list[str], source: Path) -> dict[str, Any]:
    return {
        "kind": "brfss",
        "name": "BRFSS 2015 — Indicadores de Salud y Diabetes",
        "source": source.name,
        "target": "Diabetes_012",
        "target_name": "diabetes confirmada (clase 2)",
        "positive": lambda row: (as_number(row.get("Diabetes_012")) or 0) >= 2,
        "target_classes": {
            "0": "Sin diabetes", "1": "Prediabetes", "2": "Diabetes confirmada",
        },
        "age_group": lambda row: brfss_age(row.get("Age")),
        "bmi_group": lambda row: brfss_bmi(row.get("BMI")),
        "factor_specs": [
            ("HighBP", "Presión arterial alta", lambda value: binary_label(value, "Sí", "No")),
            ("HighChol", "Colesterol alto", lambda value: binary_label(value, "Sí", "No")),
            ("GenHlth", "Salud general percibida", general_health),
            ("BMI", "IMC", brfss_bmi),
            ("DiffWalk", "Dificultad para caminar", lambda value: binary_label(value, "Sí", "No")),
            ("HeartDiseaseorAttack", "Enfermedad cardíaca", lambda value: binary_label(value, "Sí", "No")),
            ("Age", "Grupo de edad", brfss_age),
            ("PhysActivity", "Actividad física", lambda value: binary_label(value, "Sí", "No")),
            ("Smoker", "Fumador/a actual o previo", lambda value: binary_label(value, "Sí", "No")),
            ("Stroke", "Antecedente de ACV", lambda value: binary_label(value, "Sí", "No")),
            ("HvyAlcoholConsump", "Consumo alto de alcohol", lambda value: binary_label(value, "Sí", "No")),
        ],
        "model_fields": [
            "HighBP", "HighChol", "CholCheck", "BMI", "Smoker", "Stroke",
            "HeartDiseaseorAttack", "PhysActivity", "Fruits", "Veggies",
            "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost", "GenHlth",
            "MentHlth", "PhysHlth", "DiffWalk", "Sex", "Age", "Education", "Income",
        ],
        "field_labels": {
            "HighBP": "Presión arterial alta", "HighChol": "Colesterol alto",
            "CholCheck": "Control de colesterol", "BMI": "IMC", "Smoker": "Tabaquismo",
            "Stroke": "Antecedente de ACV", "HeartDiseaseorAttack": "Enfermedad cardíaca",
            "PhysActivity": "Actividad física", "Fruits": "Consumo de frutas",
            "Veggies": "Consumo de vegetales", "HvyAlcoholConsump": "Alcohol de alto riesgo",
            "AnyHealthcare": "Cobertura de salud", "NoDocbcCost": "Barreras económicas de atención",
            "GenHlth": "Salud general percibida", "MentHlth": "Días de salud mental no buena",
            "PhysHlth": "Días de salud física no buena", "DiffWalk": "Dificultad para caminar",
            "Sex": "Sexo", "Age": "Grupo de edad", "Education": "Educación", "Income": "Ingreso",
        },
        "filter_specs": [
            ("age", "Grupo de edad", lambda row: brfss_age(row.get("Age"))),
            ("bmi", "IMC", lambda row: brfss_bmi(row.get("BMI"))),
            ("highBP", "Presión arterial alta", lambda row: binary_label(row.get("HighBP"), "Sí", "No")),
            ("highChol", "Colesterol alto", lambda row: binary_label(row.get("HighChol"), "Sí", "No")),
            ("genHlth", "Salud general", lambda row: general_health(row.get("GenHlth"))),
            ("activity", "Actividad física", lambda row: binary_label(row.get("PhysActivity"), "Sí", "No")),
        ],
        "quality_rules": [],
    }


@lru_cache(maxsize=1)
def load_dataset() -> tuple[list[dict[str, str]], dict[str, Any], list[str]]:
    path = find_dataset()
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = [{key.strip(): (value or "").strip() for key, value in row.items()} for row in reader]
        headers = [field.strip() for field in (reader.fieldnames or [])]
    if not rows:
        raise ValueError("El CSV está vacío.")
    return rows, schema_for(headers, path), headers


def filtered_rows(rows: list[dict[str, str]], schema: dict[str, Any], filters: dict[str, str]) -> list[dict[str, str]]:
    checks: list[Callable[[dict[str, str]], bool]] = []
    for filter_id, _, get_value in schema["filter_specs"]:
        selected = filters.get(filter_id, "")
        if selected and selected != "Todos":
            checks.append(lambda row, expected=selected, getter=get_value: getter(row) == expected)
    return [row for row in rows if all(check(row) for check in checks)]


def group_rates(
    rows: Iterable[dict[str, str]],
    label_for: Callable[[dict[str, str]], str],
    is_positive: Callable[[dict[str, str]], bool],
    minimum: int,
) -> list[dict[str, Any]]:
    buckets: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in rows:
        label = label_for(row)
        if label == "Sin dato":
            continue
        buckets[label][0] += 1
        buckets[label][1] += int(is_positive(row))
    return [
        {"label": label, "n": values[0], "positive": values[1], "rate": percentage(values[1], values[0])}
        for label, values in buckets.items()
        if values[0] >= minimum
    ]


def factor_summary(rows: list[dict[str, str]], schema: dict[str, Any], baseline: float) -> list[dict[str, Any]]:
    minimum = 100
    summaries: list[dict[str, Any]] = []
    for field, label, bucket in schema["factor_specs"]:
        rates = group_rates(rows, lambda row, fn=bucket, key=field: fn(row.get(key)), schema["positive"], minimum)
        if not rates:
            continue
        top = max(rates, key=lambda item: (item["rate"], item["n"]))
        summaries.append({
            "factor": label,
            "field": field,
            "group": top["label"],
            "rate": top["rate"],
            "n": top["n"],
            "delta": round(top["rate"] - baseline, 1),
            "groups": sorted(rates, key=lambda item: item["rate"], reverse=True)[:5],
        })
    return sorted(summaries, key=lambda item: (item["delta"], item["n"]), reverse=True)


def target_distribution(rows: list[dict[str, str]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    field = schema["target"]
    items = []
    for raw, label in schema["target_classes"].items():
        expected = as_number(raw)
        count = sum(1 for row in rows if as_number(row.get(field)) == expected)
        items.append({"label": label, "count": count, "rate": percentage(count, len(rows))})
    return items


def quality_report(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str]) -> dict[str, Any]:
    missing = []
    for header in headers:
        absent = sum(1 for row in rows if row.get(header, "") == "")
        if absent:
            missing.append({"field": header, "count": absent, "rate": percentage(absent, len(rows)), "note": "Vacío en el archivo"})
    return {
        "missing": missing,
        "rows": len(rows),
        "columns": len(headers),
        "has_pii": False,
    }


def protocol_for(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str]) -> dict[str, Any]:
    target = schema["target"]
    eligible_target = sum(1 for row in rows if as_number(row.get(target)) is not None)
    core_fields = [field for field in schema["model_fields"] if field in headers]
    usable_core = sum(1 for row in rows if as_number(row.get(target)) is not None and any(as_number(row.get(f)) is not None for f in core_fields))

    variables = [
        ("Diabetes confirmada", "Diabetes_012", "Desenlace", "Cualitativa policotómica", "0=Sin diabetes, 1=Prediabetes, 2=Diabetes confirmada. Para el score se excluye prediabetes."),
        ("IMC", "BMI", "Predictor", "Cuantitativa continua", "Índice de masa corporal (discretizado ≤25, 25-30, 30-35, >35)."),
        ("Edad", "Age", "Predictor", "Ordinal (13 categorías)", "Categorías etarias BRFSS 1-13 (18-24 hasta ≥80)."),
        ("Salud general percibida", "GenHlth", "Predictor", "Ordinal (1-5)", "1=Excelente a 5=Mala."),
        ("Presión arterial alta", "HighBP", "Predictor", "Cualitativa dicotómica", "1=Diagnosticado hipertenso, 0=No."),
        ("Colesterol alto", "HighChol", "Predictor", "Cualitativa dicotómica", "1=Diagnosticado colesterol alto, 0=No."),
        ("Dificultad para caminar", "DiffWalk", "Predictor", "Cualitativa dicotómica", "1=Dificultad seria para caminar o subir escaleras, 0=No."),
        ("Enfermedad cardíaca", "HeartDiseaseorAttack", "Predictor", "Cualitativa dicotómica", "1=Enfermedad coronaria o infarto, 0=No."),
        ("Derrame previo", "Stroke", "Predictor", "Cualitativa dicotómica", "1=Accidente cerebrovascular previo, 0=No."),
        ("Actividad física", "PhysActivity", "Predictor", "Cualitativa dicotómica", "1=Actividad física en los últimos 30 días, 0=No."),
        ("Consumo alto de alcohol", "HvyAlcoholConsump", "Predictor", "Cualitativa dicotómica", "1=Consumo elevado (hombres >14 tragos/sem, mujeres >7), 0=No."),
    ]

    return {
        "title": "Protocolo analítico de diabetes y apoyo a decisiones",
        "question": "¿Qué capacidad discriminatoria tienen los factores clínicos y de estilo de vida para identificar diabetes confirmada mediante un sistema de puntuación transparente frente a modelos de ML?",
        "objective": "Desarrollar y validar un score estadístico interpretable (Sullivan/Framingham) y compararlo con modelos supervisados para priorizar tamizaje poblacional de diabetes.",
        "objectives": [
            "Caracterizar la prevalencia de diabetes según indicadores sociodemográficos y clínicos en BRFSS 2015.",
            "Construir un score de puntuación entero basado en odds ratios ajustados sin cajas negras.",
            "Estratificar a la población en niveles de riesgo clínico (Bajo, Moderado, Alto, Muy alto) con punto de corte de derivación.",
            "Validar la sensibilidad (85.5%), especificidad (58.5%) y AUC (0.798) del score y contrastarlo con Regresión Logística y Random Forest.",
            "Proveer una herramienta clínica interactiva que asigne puntos y oriente la derivación oportuna.",
        ],
        "design": "Observacional, analítico, transversal de base poblacional con datos secundarios del BRFSS 2015.",
        "unit": "Cada registro corresponde a un adulto encuestado; datos anonimizados sin identificación individual.",
        "eligibility": {
            "included": "Adultos con registro completo de Diabetes_012 y factores de riesgo clave.",
            "excluded": "Duplicados exactos (23,899) y registros con IMC fisiológicamente inverosímil (<12 o >60, n=805). En el ajuste del score se excluye prediabetes (clase 1, 1.8%).",
            "all": len(rows), "valid_target": eligible_target, "usable": usable_core,
        },
        "variables": [
            {"name": name, "field": field, "role": role, "type": kind, "definition": definition}
            for name, field, role, kind, definition in variables if field in headers
        ],
        "ethics": [
            "Mostrar únicamente resultados agregados; no inferir diagnósticos médicos automáticos.",
            "Todos los análisis y calculadoras incluyen avisos de descargo de responsabilidad no diagnóstica.",
            "Preservar privacidad: sin almacenamiento de información de salud protegida (PII/PHI).",
        ],
    }


def model_report(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str]) -> dict[str, Any]:
    """Entrena y evalúa modelos ML en split estratificado 80/20 con caché."""
    cache_key = f"{schema['source']}:{len(rows)}"
    if cache_key in MODEL_CACHE:
        return MODEL_CACHE[cache_key]
    try:
        import numpy as np
        import pandas as pd
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        fields = [field for field in schema["model_fields"] if field in headers]
        if len(fields) < 2:
            raise ValueError("No hay predictores suficientes para entrenar.")

        frame = pd.DataFrame([{field: as_number(row.get(field)) for field in fields} for row in rows])
        target = np.array([int(schema["positive"](row)) for row in rows])

        if len(np.unique(target)) < 2:
            raise ValueError("Desenlace con una sola clase.")

        x_train, x_test, y_train, y_test = train_test_split(
            frame, target, test_size=0.20, random_state=42, stratify=target
        )

        models = {
            "Regresión Logística": Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42)),
            ]),
            "Random Forest": Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestClassifier(
                    n_estimators=100, max_depth=12, min_samples_leaf=4,
                    class_weight="balanced", random_state=42, n_jobs=-1,
                )),
            ]),
        }

        evaluations: list[dict[str, Any]] = []
        fitted: dict[str, Any] = {}
        for name, model in models.items():
            model.fit(x_train, y_train)
            prediction = model.predict(x_test)
            probability = model.predict_proba(x_test)[:, 1]
            evaluation = {
                "name": name,
                "accuracy": round(float(accuracy_score(y_test, prediction)), 3),
                "precision": round(float(precision_score(y_test, prediction, zero_division=0)), 3),
                "recall": round(float(recall_score(y_test, prediction, zero_division=0)), 3),
                "f1": round(float(f1_score(y_test, prediction, zero_division=0)), 3),
                "auc": round(float(roc_auc_score(y_test, probability)), 3),
            }
            evaluations.append(evaluation)
            fitted[name] = (model, probability)

        best = max(evaluations, key=lambda item: (item["auc"], item["recall"]))
        selected, probability = fitted[best["name"]]
        estimator = selected.named_steps["model"]
        importance = getattr(estimator, "feature_importances_", None)
        if importance is None:
            importance = np.abs(estimator.coef_[0])

        features = sorted(
            [{"label": schema["field_labels"].get(field, field), "value": round(float(value), 4)} for field, value in zip(fields, importance)],
            key=lambda item: item["value"], reverse=True,
        )[:8]

        risk_buckets: dict[str, list[float]] = defaultdict(list)
        observed_buckets: dict[str, list[int]] = defaultdict(list)
        for score, actual in zip(probability, y_test):
            label = "Bajo (<25%)" if score < .25 else "Moderado (25–49%)" if score < .5 else "Elevado (50–74%)" if score < .75 else "Alto (≥75%)"
            risk_buckets[label].append(float(score))
            observed_buckets[label].append(int(actual))
        risk_order = ["Bajo (<25%)", "Moderado (25–49%)", "Elevado (50–74%)", "Alto (≥75%)"]
        risk_bands = [
            {
                "label": label, "n": len(risk_buckets[label]),
                "predicted": round(100 * sum(risk_buckets[label]) / len(risk_buckets[label]), 1),
                "observed": percentage(sum(observed_buckets[label]), len(observed_buckets[label])),
            }
            for label in risk_order if risk_buckets[label]
        ]

        result = {
            "status": "ok", "train_n": len(x_train), "test_n": len(x_test),
            "positive_rate": percentage(int(target.sum()), len(target)), "models": evaluations,
            "selected": best["name"], "features": features, "risk_bands": risk_bands,
            "note": "Evaluación en conjunto de prueba separado (20%). Enfoque comparativo frente al score estadístico.",
        }
    except Exception as error:
        result = {"status": "unavailable", "message": f"No fue posible calcular validación ML: {error}"}
    MODEL_CACHE[cache_key] = result
    return result


def data_health(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str], filters: dict[str, str]) -> dict[str, Any]:
    selected = filtered_rows(rows, schema, filters)
    positives = sum(1 for row in selected if schema["positive"](row))
    baseline = percentage(positives, len(selected))
    factors = factor_summary(selected, schema, baseline)
    age_rates = group_rates(selected, schema["age_group"], schema["positive"], 20)
    bmi_rates = group_rates(selected, schema["bmi_group"], schema["positive"], 20)

    # Score estadístico
    score_data = get_score_summary()

    # Modelos ML
    ml_report = model_report(rows, schema, headers)

    # Comparación unificada de enfoques
    comparison_table = [
        {
            "approach": "Score Estadístico (Sullivan / Framingham)",
            "type": "Estadístico Interpretable",
            "sensitivity": f"{score_data['metrics']['sensitivity']:.1f}%",
            "specificity": f"{score_data['metrics']['specificity']:.1f}%",
            "ppv": f"{score_data['metrics']['ppv']:.1f}%",
            "npv": f"{score_data['metrics']['npv']:.1f}%",
            "auc": f"{score_data['metrics']['auc']:.3f}",
            "interpretability": "Máxima (reglas aditivas directas y auditables)",
            "use_case": "Tamizaje en atención primaria sin infraestructura digital compleja",
        }
    ]
    if ml_report.get("status") == "ok":
        for m in ml_report.get("models", []):
            comparison_table.append({
                "approach": m["name"],
                "type": "Machine Learning",
                "sensitivity": f"{m['recall']*100:.1f}%",
                "specificity": "—",
                "ppv": f"{m['precision']*100:.1f}%",
                "npv": "—",
                "auc": f"{m['auc']:.3f}",
                "interpretability": "Moderada a baja (coeficientes / ensamble de árboles)",
                "use_case": "Análisis multivariado y benchmarking técnico",
            })

    top = factors[0] if factors else None
    if not selected:
        recommendation = {
            "problem": "El filtro seleccionado no devuelve registros.",
            "finding": "No hay base suficiente para comparar este segmento.",
            "action": "Amplía los filtros para ver el perfil poblacional.",
            "follow_up": "Revisar el tamaño muestral antes de interpretar tasas.",
        }
    elif top:
        recommendation = {
            "problem": f"La proporción de diabetes confirmada es {baseline:.1f}% en la selección actual.",
            "finding": f"Mayor tasa observada: {top['rate']:.1f}% en «{top['factor']}: {top['group']}» (n={pretty_number(top['n'])}).",
            "action": f"Priorizar tamizaje preventivo y derivación con corte score ≥ {score_data['derivation_cutoff']} para evaluación confirmatoria.",
            "follow_up": "Monitorear cobertura de pruebas HbA1c y porcentaje de casos confirmados derivados a control.",
        }
    else:
        recommendation = {
            "problem": "No hay suficientes grupos comparables para priorizar factores.",
            "finding": "La selección actual limita la lectura de asociaciones.",
            "action": "Usar un filtro más amplio o revisar la calidad de los campos.",
            "follow_up": "Confirmar tamaño muestral antes de tomar decisiones.",
        }

    available_filters = []
    for filter_id, label, getter in schema["filter_specs"]:
        options = sorted({getter(row) for row in rows if getter(row) != "Sin dato"})
        available_filters.append({"id": filter_id, "label": label, "options": ["Todos", *options]})

    return {
        "dataset": {
            "name": schema["name"],
            "source": schema["source"],
            "kind": schema["kind"],
            "target": schema["target_name"],
        },
        "filters": available_filters,
        "selection": {"n": len(selected), "positive": positives, "prevalence": baseline},
        "kpis": [
            {"label": "Registros analizados", "value": pretty_number(len(selected)), "context": f"de {pretty_number(len(rows))} en BRFSS 2015"},
            {"label": "Prevalencia de diabetes", "value": f"{baseline:.1f}%", "context": f"{pretty_number(positives)} casos confirmados"},
            {"label": "Sensibilidad del Score", "value": f"{score_data['metrics']['sensitivity']:.1f}%", "context": f"Detecta {pretty_number(score_data['metrics']['detected_diabetics'])} de {pretty_number(score_data['metrics']['total_diabetics'])} diabéticos (corte ≥7)"},
            {"label": "AUC del Score", "value": f"{score_data['metrics']['auc']:.3f}", "context": "Discriminación Mann-Whitney sin sobreajuste"},
            {"label": "Rango de Score", "value": f"{score_data['score_min']} a {score_data['score_max']}", "context": f"Promedio poblacional: {score_data['score_mean']}"},
            {"label": "Población a derivar", "value": f"{score_data['derived_pct']:.1f}%", "context": f"Score ≥ {score_data['derivation_cutoff']} (Riesgo Moderado a Muy Alto)"},
        ],
        "distribution": target_distribution(selected, schema),
        "factors": factors[:8],
        "age_rates": sorted(age_rates, key=lambda item: item["rate"], reverse=True),
        "bmi_rates": sorted(bmi_rates, key=lambda item: item["rate"], reverse=True),
        "score": score_data,
        "model_comparison": comparison_table,
        "model": ml_report,
        "quality": quality_report(rows, schema, headers),
        "protocol": protocol_for(rows, schema, headers),
        "recommendation": recommendation,
        "disclaimer": score_data["disclaimer"],
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    """Maneja frontend estático y endpoints de la API JSON."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def send_json(self, content: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/api/dashboard", "/api/health", "/api/score/summary"}:
            try:
                if parsed.path == "/api/health":
                    rows, schema, _ = load_dataset()
                    return self.send_json({
                        "status": "ok",
                        "dataset": schema["source"],
                        "rows": len(rows),
                        "score_engine": "ready",
                    })
                if parsed.path == "/api/score/summary":
                    return self.send_json(get_score_summary())

                rows, schema, headers = load_dataset()
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                return self.send_json(data_health(rows, schema, headers, filters))
            except (FileNotFoundError, ValueError, OSError) as error:
                return self.send_json({"error": str(error)}, HTTPStatus.SERVICE_UNAVAILABLE)

        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/score/calculate":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length <= 0:
                    return self.send_json({"error": "Cuerpo de solicitud vacío"}, HTTPStatus.BAD_REQUEST)
                body = self.rfile.read(content_length).decode("utf-8")
                patient_data = json.loads(body)
                if not isinstance(patient_data, dict):
                    return self.send_json({"error": "El payload debe ser un objeto JSON"}, HTTPStatus.BAD_REQUEST)

                result = calculate_patient_score(patient_data)
                return self.send_json(result, HTTPStatus.OK)
            except json.JSONDecodeError as err:
                return self.send_json({"error": f"JSON malformado: {err}"}, HTTPStatus.BAD_REQUEST)
            except ValueError as err:
                return self.send_json({"error": str(err)}, HTTPStatus.BAD_REQUEST)
            except Exception as err:
                return self.send_json({"error": f"Error interno: {err}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

        return self.send_json({"error": "Ruta no encontrada"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[meddata] {self.address_string()} - {format % args}")


def main() -> None:
    mimetypes.add_type("application/javascript", ".js")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    print(f"Tablero MedData listo en http://127.0.0.1:{PORT}")
    print("Presiona Ctrl+C para detenerlo.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
