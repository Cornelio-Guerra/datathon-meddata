"""Servidor local para el tablero de decisión sobre diabetes.

No requiere dependencias nuevas: sirve la interfaz y expone una API JSON que
calcula los indicadores a partir del CSV disponible en ``data/``. Prioriza el
archivo BRFSS 2015 cuando esté presente y usa Pima solo como respaldo para que
el tablero siga siendo demostrable durante la sincronización del dataset.
"""

from __future__ import annotations

import csv
import json
import math
import mimetypes
import os
from collections import Counter, defaultdict
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
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


def pima_age(value: Any) -> str:
    number = as_number(value)
    if number is None:
        return "Sin dato"
    if number < 35:
        return "Menos de 35"
    if number < 50:
        return "35–49"
    return "50 o más"


def pima_bmi(value: Any) -> str:
    number = as_number(value)
    if number is None or number == 0:
        return "Sin dato"
    if number < 25:
        return "< 25"
    if number < 30:
        return "25–29,9"
    return "≥ 30"


def pima_glucose(value: Any) -> str:
    number = as_number(value)
    if number is None or number == 0:
        return "Sin dato"
    if number < 100:
        return "< 100"
    if number < 126:
        return "100–125"
    return "≥ 126"


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
    return pima_bmi(value)


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
    """Encuentra el CSV de diabetes más apropiado, sin asumir una ruta fija."""
    candidates = list(DATA_DIR.glob("*.csv"))
    if not candidates:
        raise FileNotFoundError("No se encontró ningún CSV dentro de data/.")

    def score(path: Path) -> tuple[int, str]:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                header = next(csv.reader(stream), [])
        except (OSError, UnicodeDecodeError):
            return (-1, path.name)
        fields = set(header)
        name = path.name.lower()
        result = 0
        if "Diabetes_012" in fields:
            result += 100
        if "brfss" in name:
            result += 20
        if "diabetes" in name:
            result += 8
        if "Outcome" in fields and {"Glucose", "BMI", "Age"}.issubset(fields):
            result += 40
        return (result, path.name)

    return max(candidates, key=score)


def schema_for(headers: list[str], source: Path) -> dict[str, Any]:
    if "Diabetes_012" in headers:
        return {
            "kind": "brfss",
            "name": "BRFSS 2015 — Indicadores de salud y diabetes",
            "source": source.name,
            "target": "Diabetes_012",
            "target_name": "diabetes diagnosticada",
            "positive": lambda row: (as_number(row.get("Diabetes_012")) or 0) >= 2,
            "target_classes": {
                "0": "Sin diabetes", "1": "Prediabetes", "2": "Diabetes",
            },
            "age_group": lambda row: brfss_age(row.get("Age")),
            "bmi_group": lambda row: brfss_bmi(row.get("BMI")),
            "factor_specs": [
                ("HighBP", "Presión arterial alta", lambda value: binary_label(value, "Sí", "No")),
                ("HighChol", "Colesterol alto", lambda value: binary_label(value, "Sí", "No")),
                ("BMI", "IMC", brfss_bmi),
                ("PhysActivity", "Actividad física", lambda value: binary_label(value, "Sí", "No")),
                ("DiffWalk", "Dificultad para caminar", lambda value: binary_label(value, "Sí", "No")),
                ("GenHlth", "Salud general percibida", general_health),
                ("Smoker", "Fumador/a actual o previo", lambda value: binary_label(value, "Sí", "No")),
                ("Age", "Grupo de edad", brfss_age),
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
                ("activity", "Actividad física", lambda row: binary_label(row.get("PhysActivity"), "Sí", "No")),
            ],
            "quality_rules": [],
        }
    if "Outcome" in headers and {"Glucose", "BMI", "Age"}.issubset(headers):
        return {
            "kind": "pima",
            "name": "Pima Indians Diabetes Database",
            "source": source.name,
            "target": "Outcome",
            "target_name": "resultado positivo de diabetes",
            "positive": lambda row: (as_number(row.get("Outcome")) or 0) == 1,
            "target_classes": {"0": "Sin resultado positivo", "1": "Resultado positivo"},
            "age_group": lambda row: pima_age(row.get("Age")),
            "bmi_group": lambda row: pima_bmi(row.get("BMI")),
            "factor_specs": [
                ("Glucose", "Glucosa", pima_glucose),
                ("BMI", "IMC", pima_bmi),
                ("Age", "Grupo de edad", pima_age),
                ("BloodPressure", "Presión arterial", lambda value: "0 (revisar)" if as_number(value) == 0 else "Con dato"),
                ("Pregnancies", "Embarazos", lambda value: "0" if as_number(value) == 0 else "1–2" if (as_number(value) or 0) <= 2 else "3 o más"),
                ("DiabetesPedigreeFunction", "Antecedente familiar (DPF)", lambda value: "Bajo" if (as_number(value) or 0) < 0.5 else "Medio" if (as_number(value) or 0) < 1 else "Alto"),
            ],
            "model_fields": [
                "Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin",
                "BMI", "DiabetesPedigreeFunction", "Age",
            ],
            "field_labels": {
                "Pregnancies": "Embarazos", "Glucose": "Glucosa", "BloodPressure": "Presión arterial",
                "SkinThickness": "Grosor de piel", "Insulin": "Insulina", "BMI": "IMC",
                "DiabetesPedigreeFunction": "Antecedente familiar (DPF)", "Age": "Edad",
            },
            "filter_specs": [
                ("age", "Grupo de edad", lambda row: pima_age(row.get("Age"))),
                ("bmi", "IMC", lambda row: pima_bmi(row.get("BMI"))),
                ("glucose", "Glucosa", lambda row: pima_glucose(row.get("Glucose"))),
            ],
            "quality_rules": [
                ("Glucose", "Glucosa", "0 es clínicamente improbable"),
                ("BloodPressure", "Presión arterial", "0 es clínicamente improbable"),
                ("SkinThickness", "Grosor de piel", "0 es clínicamente improbable"),
                ("Insulin", "Insulina", "0 es clínicamente improbable"),
                ("BMI", "IMC", "0 es clínicamente improbable"),
            ],
        }
    raise ValueError(
        "El CSV encontrado no tiene una estructura compatible. Se espera BRFSS "
        "(Diabetes_012) o Pima (Outcome, Glucose, BMI y Age)."
    )


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
    minimum = 100 if schema["kind"] == "brfss" else 15
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
        # BRFSS suele venir como 0.0/1.0/2.0, mientras Pima usa 0/1.
        # Comparar como número evita que el resumen cambie por ese detalle de CSV.
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
    special = []
    for field, label, note in schema["quality_rules"]:
        count = sum(1 for row in rows if as_number(row.get(field)) == 0)
        if count:
            special.append({"field": label, "count": count, "rate": percentage(count, len(rows)), "note": note})
    return {
        "missing": sorted(missing + special, key=lambda item: item["count"], reverse=True)[:8],
        "rows": len(rows),
        "columns": len(headers),
        "has_pii": False,
    }


def protocol_for(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str]) -> dict[str, Any]:
    """Traduce la estructura de protocolo a lo que sí permite el dataset disponible."""
    target = schema["target"]
    eligible_target = sum(1 for row in rows if as_number(row.get(target)) is not None)
    core_fields = [field for field in schema["model_fields"] if field in headers]
    usable_core = 0
    for row in rows:
        values = [as_number(row.get(field)) for field in core_fields]
        if as_number(row.get(target)) is not None and any(value is not None for value in values):
            usable_core += 1

    if schema["kind"] == "brfss":
        question = (
            "¿Qué capacidad tienen los indicadores sociodemográficos y de salud disponibles "
            "para discriminar la diabetes diagnosticada dentro de esta muestra?"
        )
        design = "Observacional, analítico, retrospectivo y de desarrollo tecnológico con datos secundarios."
        outcome_definition = "Diabetes_012 = 2 (diabetes); 0 y 1 se consideran no diabetes diagnosticada para el modelo exploratorio."
        variables = [
            ("Diabetes diagnosticada", "Diabetes_012", "Desenlace", "Cualitativa nominal", outcome_definition),
            ("IMC", "BMI", "Predictor", "Cuantitativa continua", "Valor de índice de masa corporal reportado."),
            ("Presión arterial alta", "HighBP", "Predictor", "Cualitativa dicotómica", "Indicador 0/1 del archivo."),
            ("Colesterol alto", "HighChol", "Predictor", "Cualitativa dicotómica", "Indicador 0/1 del archivo."),
            ("Actividad física", "PhysActivity", "Predictor", "Cualitativa dicotómica", "Indicador 0/1 del archivo."),
            ("Edad", "Age", "Predictor", "Ordinal", "Categoría de edad codificada en la fuente."),
            ("Sexo", "Sex", "Predictor", "Cualitativa dicotómica", "Categoría codificada en la fuente."),
        ]
    else:
        question = (
            "¿Qué capacidad tienen las variables clínicas disponibles para discriminar un resultado "
            "positivo de diabetes dentro de la muestra Pima?"
        )
        design = "Observacional, analítico, retrospectivo y de desarrollo tecnológico con datos secundarios."
        outcome_definition = "Outcome = 1 (resultado positivo) y Outcome = 0 (sin resultado positivo)."
        variables = [
            ("Resultado positivo de diabetes", "Outcome", "Desenlace", "Cualitativa dicotómica", outcome_definition),
            ("Glucosa", "Glucose", "Predictor", "Cuantitativa continua", "Concentración de glucosa registrada; 0 se trata como dato clínicamente improbable."),
            ("IMC", "BMI", "Predictor", "Cuantitativa continua", "Índice de masa corporal registrado; 0 se trata como dato clínicamente improbable."),
            ("Edad", "Age", "Predictor", "Cuantitativa continua", "Edad en años."),
            ("Presión arterial", "BloodPressure", "Predictor", "Cuantitativa continua", "Valor registrado; 0 se revisa como dato clínicamente improbable."),
            ("Antecedente familiar", "DiabetesPedigreeFunction", "Predictor", "Cuantitativa continua", "Diabetes Pedigree Function de la fuente."),
        ]

    return {
        "title": "Protocolo analítico de diabetes y apoyo a decisiones",
        "question": question,
        "objective": "Caracterizar los indicadores disponibles y evaluar un modelo exploratorio de clasificación para apoyar la priorización poblacional.",
        "objectives": [
            "Describir la frecuencia del desenlace y el perfil de la población incluida.",
            "Operacionalizar los predictores clínicos y conductuales disponibles en la fuente.",
            "Evaluar asociaciones descriptivas por subgrupo, sin atribuir causalidad.",
            "Validar modelos de clasificación con un conjunto de prueba separado.",
            "Traducir resultados agregados en acciones de prevención, tamizaje y seguimiento.",
        ],
        "design": design,
        "unit": "Cada fila del archivo representa una observación; el tablero no identifica ni perfila personas individuales.",
        "eligibility": {
            "included": f"Registros con desenlace {target} válido y al menos un predictor disponible.",
            "excluded": "Registros sin desenlace, valores clínicamente improbables tratados como faltantes y campos no disponibles para una comparación específica.",
            "all": len(rows), "valid_target": eligible_target, "usable": usable_core,
        },
        "variables": [
            {"name": name, "field": field, "role": role, "type": kind, "definition": definition}
            for name, field, role, kind, definition in variables if field in headers
        ],
        "ethics": [
            "Mostrar únicamente resultados agregados; no inferir riesgo clínico individual desde este tablero.",
            "No incorporar identificadores directos ni combinar fuentes sin base legal, aprobación ética y controles de acceso.",
            "Antes de uso operativo, validar sesgos, desempeño por subgrupo y pertinencia clínica con profesionales de salud.",
        ],
    }


def model_report(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str]) -> dict[str, Any]:
    """Entrena una comparación reproducible, conservando el conjunto de prueba separado."""
    cache_key = f"{schema['source']}:{len(rows)}:{','.join(headers)}"
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
            raise ValueError("No hay predictores suficientes para entrenar el modelo.")
        frame = pd.DataFrame([{field: as_number(row.get(field)) for field in fields} for row in rows])
        target = np.array([int(schema["positive"](row)) for row in rows])
        if schema["kind"] == "pima":
            for field in ("Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"):
                if field in frame:
                    frame.loc[frame[field] == 0, field] = np.nan
        if len(np.unique(target)) < 2:
            raise ValueError("El desenlace solo tiene una clase; no es posible validar un clasificador.")
        x_train, x_test, y_train, y_test = train_test_split(
            frame, target, test_size=0.20, random_state=42, stratify=target
        )
        models = {
            "Regresión logística": Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1500, class_weight="balanced", random_state=42)),
            ]),
            "Random Forest": Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("model", RandomForestClassifier(
                    n_estimators=160 if len(rows) > 10_000 else 300,
                    max_depth=12 if len(rows) > 10_000 else None,
                    min_samples_leaf=3 if len(rows) > 10_000 else 1,
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
                "accuracy": round(accuracy_score(y_test, prediction), 3),
                "precision": round(precision_score(y_test, prediction, zero_division=0), 3),
                "recall": round(recall_score(y_test, prediction, zero_division=0), 3),
                "f1": round(f1_score(y_test, prediction, zero_division=0), 3),
                "auc": round(roc_auc_score(y_test, probability), 3),
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
            "note": "Resultados exploratorios en un conjunto de prueba separado (20%). No se deben usar como diagnóstico ni decisión clínica individual.",
        }
    except Exception as error:  # Permite que el tablero descriptivo siga disponible.
        result = {"status": "unavailable", "message": f"No fue posible calcular la validación: {error}"}
    MODEL_CACHE[cache_key] = result
    return result


def data_health(rows: list[dict[str, str]], schema: dict[str, Any], headers: list[str], filters: dict[str, str]) -> dict[str, Any]:
    selected = filtered_rows(rows, schema, filters)
    positives = sum(1 for row in selected if schema["positive"](row))
    baseline = percentage(positives, len(selected))
    factors = factor_summary(selected, schema, baseline)
    age_rates = group_rates(selected, schema["age_group"], schema["positive"], 20 if schema["kind"] == "brfss" else 10)
    bmi_rates = group_rates(selected, schema["bmi_group"], schema["positive"], 20 if schema["kind"] == "brfss" else 10)
    segment_rows = []
    segment_buckets: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for row in selected:
        age = schema["age_group"](row)
        bmi = schema["bmi_group"](row)
        if "Sin dato" not in {age, bmi}:
            key = f"{age} · IMC {bmi}"
            segment_buckets[key][0] += 1
            segment_buckets[key][1] += int(schema["positive"](row))
    for label, values in segment_buckets.items():
        if values[0] >= (100 if schema["kind"] == "brfss" else 10):
            segment_rows.append({"label": label, "n": values[0], "rate": percentage(values[1], values[0])})
    segments = sorted(segment_rows, key=lambda item: item["rate"], reverse=True)[:6]

    numeric_means = {}
    for field in ("BMI", "Glucose", "Age"):
        values = [as_number(row.get(field)) for row in selected]
        values = [value for value in values if value is not None and not (schema["kind"] == "pima" and field in {"BMI", "Glucose"} and value == 0)]
        if values:
            numeric_means[field] = round(sum(values) / len(values), 1)

    top = factors[0] if factors else None
    if not selected:
        recommendation = {
            "problem": "El filtro no devuelve registros.",
            "finding": "No hay base suficiente para comparar este segmento.",
            "action": "Amplía uno o más filtros antes de priorizar una acción.",
            "follow_up": "Revisar el tamaño muestral antes de interpretar tasas.",
        }
    elif top:
        recommendation = {
            "problem": f"La proporción de {schema['target_name']} es {baseline:.1f}% en la población filtrada.",
            "finding": f"La mayor tasa observada fue {top['rate']:.1f}% en «{top['factor']}: {top['group']}» (n={pretty_number(top['n'])}).",
            "action": f"Priorizar una intervención preventiva y de detección para ese segmento; validar factibilidad con el equipo clínico.",
            "follow_up": "Medir cobertura, tamizajes completados y variación de la tasa por segmento en el próximo corte.",
        }
    else:
        recommendation = {
            "problem": "No hay suficientes grupos comparables para priorizar factores.",
            "finding": "La selección actual limita la lectura de asociaciones.",
            "action": "Usar un filtro más amplio o revisar la calidad de los campos.",
            "follow_up": "Confirmar tamaño muestral y completitud antes de tomar decisiones.",
        }

    available_filters = []
    for filter_id, label, getter in schema["filter_specs"]:
        options = sorted({getter(row) for row in rows if getter(row) != "Sin dato"})
        available_filters.append({"id": filter_id, "label": label, "options": ["Todos", *options]})

    return {
        "dataset": {
            "name": schema["name"], "source": schema["source"], "kind": schema["kind"],
            "target": schema["target_name"], "fallback": schema["kind"] == "pima",
        },
        "filters": available_filters,
        "selection": {"n": len(selected), "positive": positives, "prevalence": baseline},
        "kpis": [
            {"label": "Registros analizados", "value": pretty_number(len(selected)), "context": f"de {pretty_number(len(rows))} registros"},
            {"label": schema["target_name"].capitalize(), "value": f"{baseline:.1f}%", "context": f"{pretty_number(positives)} resultados positivos"},
            {"label": "IMC promedio", "value": f"{numeric_means.get('BMI', 0):.1f}", "context": "excluye valores 0 clínicamente improbables" if schema["kind"] == "pima" else "en el segmento actual"},
            {"label": "Glucosa promedio", "value": f"{numeric_means.get('Glucose', 0):.1f}" if "Glucose" in numeric_means else "—", "context": "solo disponible en Pima" if schema["kind"] == "pima" else "no incluida en BRFSS"},
        ],
        "distribution": target_distribution(selected, schema),
        "factors": factors[:6],
        "age_rates": sorted(age_rates, key=lambda item: item["rate"], reverse=True),
        "bmi_rates": sorted(bmi_rates, key=lambda item: item["rate"], reverse=True),
        "segments": segments,
        "quality": quality_report(rows, schema, headers),
        "protocol": protocol_for(rows, schema, headers),
        # La validación se calcula sobre la fuente completa y no cambia al filtrar;
        # así se evita presentar el mismo segmento como entrenamiento y prueba.
        "model": model_report(rows, schema, headers),
        "recommendation": recommendation,
        "method": [
            ["1. Plantear", "Formula la pregunta, el desenlace y el uso previsto del resultado."],
            ["2. Operacionalizar", "Define población, criterios, variables y reglas de calidad antes de analizar."],
            ["3. Describir", "Resume frecuencias, dispersión y asociaciones por segmento; no confundas asociación con causa."],
            ["4. Validar", "Evalúa el modelo en datos separados con recall, precisión, F1 y ROC-AUC."],
            ["5. Decidir y seguir", "Prioriza acciones poblacionales, asigna responsables y monitorea indicadores de cobertura y resultados."],
        ],
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    """Entrega frontend estático y solamente las rutas API necesarias."""

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

    def do_GET(self) -> None:  # noqa: N802 - API de la librería estándar
        parsed = urlparse(self.path)
        if parsed.path in {"/api/dashboard", "/api/health"}:
            try:
                rows, schema, headers = load_dataset()
                if parsed.path == "/api/health":
                    return self.send_json({"status": "ok", "dataset": schema["source"], "rows": len(rows)})
                filters = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
                return self.send_json(data_health(rows, schema, headers, filters))
            except (FileNotFoundError, ValueError, OSError) as error:
                return self.send_json({"error": str(error)}, HTTPStatus.SERVICE_UNAVAILABLE)
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:
        # Mantiene la terminal legible, sin eliminar los errores reales del servidor.
        print(f"[meddata] {self.address_string()} - {format % args}")


def main() -> None:
    mimetypes.add_type("application/javascript", ".js")
    server = ThreadingHTTPServer(("127.0.0.1", PORT), DashboardHandler)
    print(f"Tablero listo en http://127.0.0.1:{PORT}")
    print("Presiona Ctrl+C para detenerlo.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
