"""Pruebas automatizadas para el dashboard de apoyo a decisiones sobre diabetes.

Cubre:
- Carga y estructura del dataset BRFSS 2015.
- Cálculo del score de Sullivan y consistencia matemática.
- Estratificación de riesgo y puntos de corte.
- Validación de entradas y respuestas de la calculadora individual.
- Endpoints HTTP /api/health, /api/dashboard y /api/score/calculate.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from http import HTTPStatus
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard.app as app
import dashboard.score_adapter as sa


class TestDiabetesDashboard(unittest.TestCase):

    def test_01_load_dataset(self) -> None:
        """Verifica la carga adecuada del dataset BRFSS."""
        rows, schema, headers = app.load_dataset()
        self.assertGreater(len(rows), 200_000)
        self.assertEqual(schema["kind"], "brfss")
        self.assertIn("Diabetes_012", headers)
        self.assertIn("BMI", headers)
        self.assertIn("Age", headers)
        self.assertIn("HighBP", headers)
        self.assertIn("HighChol", headers)

    def test_02_score_summary_metrics(self) -> None:
        """Verifica que el score adapter extraiga correctamente las métricas de Cornelio."""
        summary = sa.get_score_summary()
        self.assertEqual(summary["status"], "ok")
        self.assertEqual(summary["score_min"], -2)
        self.assertEqual(summary["score_max"], 18)
        self.assertEqual(summary["derivation_cutoff"], 7)
        self.assertEqual(summary["cutoffs"], [6, 9, 12])
        self.assertAlmostEqual(summary["metrics"]["sensitivity"], 85.5, delta=0.5)
        self.assertAlmostEqual(summary["metrics"]["specificity"], 58.5, delta=0.5)
        self.assertAlmostEqual(summary["metrics"]["auc"], 0.798, delta=0.01)
        self.assertEqual(len(summary["risk_distribution"]), 4)

    def test_03_score_risk_classification(self) -> None:
        """Verifica la clasificación de estratos de riesgo según puntos."""
        # Caso 1: Paciente bajo riesgo (joven, IMC normal, activo, sin comorbilidades)
        p_bajo = {
            "BMI": 22.0, "Age": 25, "GenHlth": 1, "HighBP": 0, "HighChol": 0,
            "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
            "PhysActivity": 1, "HvyAlcoholConsump": 0,
        }
        res_bajo = sa.calculate_patient_score(p_bajo)
        self.assertLessEqual(res_bajo["total_score"], 6)
        self.assertEqual(res_bajo["risk_level"], "Bajo")
        self.assertFalse(res_bajo["derivation_recommended"])
        self.assertEqual(res_bajo["expected_prevalence_pct"], 4.4)

        # Caso 2: Paciente moderado (corte de derivación >= 7)
        p_mod = {
            "BMI": 28.0, "Age": 50, "GenHlth": 3, "HighBP": 1, "HighChol": 1,
            "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
            "PhysActivity": 1, "HvyAlcoholConsump": 0,
        }
        res_mod = sa.calculate_patient_score(p_mod)
        self.assertIn(res_mod["total_score"], [7, 8, 9])
        self.assertEqual(res_mod["risk_level"], "Moderado")
        self.assertTrue(res_mod["derivation_recommended"])
        self.assertEqual(res_mod["expected_prevalence_pct"], 17.9)

        # Caso 3: Paciente muy alto riesgo
        p_alto = {
            "BMI": 38.0, "Age": 70, "GenHlth": 5, "HighBP": 1, "HighChol": 1,
            "DiffWalk": 1, "HeartDiseaseorAttack": 1, "Stroke": 1,
            "PhysActivity": 0, "HvyAlcoholConsump": 0,
        }
        res_alto = sa.calculate_patient_score(p_alto)
        self.assertGreaterEqual(res_alto["total_score"], 13)
        self.assertEqual(res_alto["risk_level"], "Muy alto")
        self.assertTrue(res_alto["derivation_recommended"])
        self.assertEqual(res_alto["expected_prevalence_pct"], 49.2)

    def test_04_calculator_validation_errors(self) -> None:
        """Verifica el rechazo estricto de entradas inválidas o incompletas."""
        # Falta campo obligatorio
        with self.assertRaises(ValueError):
            sa.calculate_patient_score({"BMI": 25.0, "Age": 45})

        # IMC fuera de rango
        with self.assertRaises(ValueError):
            sa.calculate_patient_score({
                "BMI": 5.0, "Age": 45, "GenHlth": 2, "HighBP": 0, "HighChol": 0,
                "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
                "PhysActivity": 1, "HvyAlcoholConsump": 0,
            })

        # GenHlth fuera de 1..5
        with self.assertRaises(ValueError):
            sa.calculate_patient_score({
                "BMI": 25.0, "Age": 45, "GenHlth": 8, "HighBP": 0, "HighChol": 0,
                "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
                "PhysActivity": 1, "HvyAlcoholConsump": 0,
            })

    def test_05_data_health_structure(self) -> None:
        """Verifica la respuesta completa de data_health y componentes del dashboard."""
        rows, schema, headers = app.load_dataset()
        data = app.data_health(rows, schema, headers, {})
        self.assertIn("kpis", data)
        self.assertIn("score", data)
        self.assertIn("model_comparison", data)
        self.assertIn("factors", data)
        self.assertIn("quality", data)
        self.assertIn("protocol", data)
        self.assertIn("disclaimer", data)
        self.assertGreater(len(data["model_comparison"]), 1)


class DummyHandler(app.DashboardHandler):
    """Handler simulado para pruebas de endpoints HTTP sin socket de red."""

    def __init__(self, path: str, method: str = "GET", body: bytes = b"") -> None:
        self.path = path
        self.command = method
        self.headers = {
            "Content-Length": str(len(body)),
            "Content-Type": "application/json",
        }
        self.rfile = BytesIO(body)
        self.wfile = BytesIO()
        self.status_code = HTTPStatus.OK
        self.response_headers: dict[str, str] = {}

    def send_response(self, code: int, message: str | None = None) -> None:
        self.status_code = code

    def send_header(self, keyword: str, value: str) -> None:
        self.response_headers[keyword] = value

    def end_headers(self) -> None:
        pass


class TestHttpEndpoints(unittest.TestCase):

    def test_01_api_health_endpoint(self) -> None:
        """Prueba GET /api/health."""
        handler = DummyHandler("/api/health")
        handler.do_GET()
        self.assertEqual(handler.status_code, HTTPStatus.OK)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(body.get("status"), "ok")
        self.assertEqual(body.get("score_engine"), "ready")
        self.assertGreater(body.get("rows", 0), 200_000)

    def test_02_api_dashboard_endpoint(self) -> None:
        """Prueba GET /api/dashboard."""
        handler = DummyHandler("/api/dashboard")
        handler.do_GET()
        self.assertEqual(handler.status_code, HTTPStatus.OK)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("kpis", body)
        self.assertIn("score", body)
        self.assertIn("model_comparison", body)

    def test_03_api_score_calculate_success(self) -> None:
        """Prueba POST /api/score/calculate con payload válido."""
        payload = json.dumps({
            "BMI": 31.2, "Age": 62, "GenHlth": 4, "HighBP": 1, "HighChol": 1,
            "DiffWalk": 1, "HeartDiseaseorAttack": 0, "Stroke": 0,
            "PhysActivity": 0, "HvyAlcoholConsump": 0,
        }).encode("utf-8")
        handler = DummyHandler("/api/score/calculate", method="POST", body=payload)
        handler.do_POST()
        self.assertEqual(handler.status_code, HTTPStatus.OK)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertEqual(body["status"], "ok")
        self.assertGreaterEqual(body["total_score"], 7)
        self.assertTrue(body["derivation_recommended"])

    def test_04_api_score_calculate_invalid(self) -> None:
        """Prueba POST /api/score/calculate con campos faltantes o inválidos."""
        payload = json.dumps({"BMI": 25.0}).encode("utf-8")
        handler = DummyHandler("/api/score/calculate", method="POST", body=payload)
        handler.do_POST()
        self.assertEqual(handler.status_code, HTTPStatus.BAD_REQUEST)
        body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()

