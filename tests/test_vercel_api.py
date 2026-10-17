"""Pruebas del despliegue en Vercel (parte A del issue #5).

Cubre:
- api/score/calculate.py: mismo JSON y mismos códigos que POST /api/score/calculate
  de dashboard/app.py, y el caso de prueba del issue (10 puntos, nivel Alto).
- Que importar la función no lea el CSV ni cargue pandas/numpy.
- api/snapshot.py y outputs/dashboard_snapshot.json: vistas correctas y cifras del README.
- vercel.json y los requirements de api/: rutas, exclusiones y cero dependencias.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import dashboard.app as app  # noqa: E402

ISSUE_CASE = {
    "BMI": 31, "Age": 9, "GenHlth": 4, "HighBP": 1, "HighChol": 1,
    "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
    "PhysActivity": 1, "HvyAlcoholConsump": 0,
}
SNAPSHOT_PATH = ROOT / "outputs" / "dashboard_snapshot.json"


def load_module(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


calculate_api = load_module("api/score/calculate.py", "vercel_api_score_calculate")
snapshot_api = load_module("api/snapshot.py", "vercel_api_snapshot")


def fake_handler(base: type, path: str, body: bytes = b"", content_length: str | None = None):
    """Instancia un handler sin socket, como hace tests/test_dashboard.py."""

    class Fake(base):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            self.path = path
            self.headers = {
                "Content-Length": str(len(body)) if content_length is None else content_length,
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

    return Fake()


def response_of(handler: Any) -> tuple[int, dict[str, str], Any]:
    return int(handler.status_code), handler.response_headers, json.loads(handler.wfile.getvalue().decode("utf-8"))


class TestVercelCalculate(unittest.TestCase):

    def post(self, base: type, body: bytes, content_length: str | None = None):
        handler = fake_handler(base, "/api/score/calculate", body, content_length)
        handler.do_POST()
        return response_of(handler)

    def test_01_issue_case(self) -> None:
        """El caso de prueba del issue #5 da 10 puntos, nivel Alto, 33.1 %."""
        status, headers, body = self.post(calculate_api.handler, json.dumps(ISSUE_CASE).encode("utf-8"))
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(body["total_score"], 10)
        self.assertEqual(body["risk_level"], "Alto")
        self.assertEqual(body["expected_prevalence_pct"], 33.1)
        self.assertTrue(body["derivation_recommended"])

    def test_02_same_responses_as_local_server(self) -> None:
        """Mismo código, cabeceras y JSON que DashboardHandler.do_POST para cada entrada."""
        valid_years = {**ISSUE_CASE, "Age": 60, "BMI": 31.2}
        cases: list[tuple[str, bytes, str | None]] = [
            ("caso del issue", json.dumps(ISSUE_CASE).encode("utf-8"), None),
            ("edad en años", json.dumps(valid_years).encode("utf-8"), None),
            ("campos faltantes", b'{"BMI": 25.0}', None),
            ("cuerpo vacío", b"", None),
            ("JSON malformado", b'{"BMI": ', None),
            ("lista en vez de objeto", b"[1, 2, 3]", None),
            ("cadena JSON", b'"hola"', None),
            ("IMC fuera de rango", json.dumps({**ISSUE_CASE, "BMI": 5}).encode("utf-8"), None),
            ("GenHlth inválido", json.dumps({**ISSUE_CASE, "GenHlth": 8}).encode("utf-8"), None),
            ("binario inválido", json.dumps({**ISSUE_CASE, "Stroke": 2}).encode("utf-8"), None),
            ("texto no numérico", json.dumps({**ISSUE_CASE, "BMI": "abc"}).encode("utf-8"), None),
            ("campo nulo", json.dumps({**ISSUE_CASE, "Age": None}).encode("utf-8"), None),
            ("bytes no UTF-8", b"\xff\xfe", None),
            ("Content-Length inválido", b"{}", "abc"),
        ]
        for label, body, content_length in cases:
            with self.subTest(label):
                local = self.post(app.DashboardHandler, body, content_length)
                vercel = self.post(calculate_api.handler, body, content_length)
                self.assertEqual(vercel, local)

    def test_03_get_is_rejected(self) -> None:
        handler = fake_handler(calculate_api.handler, "/api/score/calculate")
        handler.do_GET()
        status, _, body = response_of(handler)
        self.assertEqual(status, HTTPStatus.METHOD_NOT_ALLOWED)
        self.assertIn("error", body)

    def test_04_import_does_not_read_csv(self) -> None:
        """Importar y usar la función no ejecuta src/score_diabetes.py ni carga pandas."""
        script = f"""
import builtins, json, runpy, sys
from io import BytesIO

def forbidden(*args, **kwargs):
    raise AssertionError("runpy.run_path no debe ejecutarse")
runpy.run_path = forbidden

real_open = builtins.open
def guarded_open(file, *args, **kwargs):
    if str(file).endswith(".csv"):
        raise AssertionError(f"no se debe abrir el CSV: {{file}}")
    return real_open(file, *args, **kwargs)
builtins.open = guarded_open
import io
io.open = guarded_open  # pathlib abre archivos con io.open

import importlib.util
spec = importlib.util.spec_from_file_location("calc", {str(ROOT / "api" / "score" / "calculate.py")!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class Fake(module.handler):
    def __init__(self, body):
        self.headers = {{"Content-Length": str(len(body))}}
        self.rfile, self.wfile, self.code = BytesIO(body), BytesIO(), None
    def send_response(self, code, message=None): self.code = code
    def send_header(self, *args): pass
    def end_headers(self): pass

handler = Fake(json.dumps({ISSUE_CASE!r}).encode("utf-8"))
handler.do_POST()
result = json.loads(handler.wfile.getvalue())
heavy = sorted(name for name in ("pandas", "numpy", "sklearn") if name in sys.modules)
print(json.dumps({{"code": handler.code, "score": result["total_score"], "heavy": heavy}}))
"""
        completed = subprocess.run(
            [sys.executable, "-c", script], cwd=str(ROOT / "api"), capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        outcome = json.loads(completed.stdout.strip().splitlines()[-1])
        self.assertEqual(outcome, {"code": 200, "score": 10, "heavy": []})


class TestVercelSnapshot(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        def reject_constant(name: str) -> None:
            raise ValueError(f"el snapshot contiene {name}, que no es JSON válido")

        cls.snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"), parse_constant=reject_constant)

    def get(self, path: str):
        handler = fake_handler(snapshot_api.handler, path)
        handler.do_GET()
        return response_of(handler)

    def test_01_structure(self) -> None:
        self.assertEqual(set(self.snapshot), {"meta", "dashboard", "score_summary"})
        self.assertEqual(self.snapshot["meta"]["filters"], {})
        # Las respuestas guardadas son las del servidor local, que nunca envía "snapshot".
        self.assertNotIn("snapshot", self.snapshot["dashboard"])

    def test_02_views_by_path(self) -> None:
        """Elige la vista por ?view= o por la ruta original, según lo que entregue Vercel."""
        dashboard_paths = ["/api/dashboard", "/api/dashboard?", "/api/snapshot?view=dashboard", "/api/dashboard?age=60%E2%80%9364"]
        for path in dashboard_paths:
            with self.subTest(path):
                status, headers, body = self.get(path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
                self.assertEqual(body["snapshot"], self.snapshot["meta"])
                self.assertEqual({k: v for k, v in body.items() if k != "snapshot"}, self.snapshot["dashboard"])
        for path in ["/api/score/summary", "/api/snapshot?view=score_summary", "/api/score/summary/"]:
            with self.subTest(path):
                status, _, body = self.get(path)
                self.assertEqual(status, HTTPStatus.OK)
                self.assertEqual(body, self.snapshot["score_summary"])

    def test_03_readme_figures(self) -> None:
        """Las cifras publicadas son las del README."""
        summary = self.snapshot["score_summary"]
        metrics = summary["metrics"]
        self.assertEqual(metrics["sensitivity"], 85.5)
        self.assertEqual(metrics["specificity"], 58.5)
        self.assertEqual(metrics["npv"], 95.6)
        self.assertEqual(round(metrics["auc"], 3), 0.798)
        self.assertEqual(metrics["detected_diabetics"], 29_867)
        self.assertEqual(metrics["total_diabetics"], 34_926)
        self.assertEqual(summary["population_n"], 224_364)  # calibrados
        self.assertEqual(summary["derivation_cutoff"], 7)
        self.assertEqual(
            [(level["level"], level["prevalence"]) for level in summary["risk_distribution"]],
            [("Bajo", 4.4), ("Moderado", 17.9), ("Alto", 33.1), ("Muy alto", 49.2)],
        )
        dashboard = self.snapshot["dashboard"]
        self.assertEqual(dashboard["score"], summary)
        self.assertEqual(dashboard["selection"]["n"], 228_976)  # depurados
        self.assertEqual(self.snapshot["meta"]["population_n"], 228_976)
        kpis = {kpi["label"]: kpi["value"] for kpi in dashboard["kpis"]}
        self.assertEqual(kpis["Sensibilidad del Score"], "85.5%")
        self.assertEqual(kpis["AUC del Score"], "0.798")
        self.assertEqual(kpis["Prevalencia de diabetes"], "15.3%")

    def test_04_matches_score_engine(self) -> None:
        """El snapshot no quedó desactualizado respecto a src/score_diabetes.py."""
        import dashboard.score_adapter as sa

        self.assertEqual(self.snapshot["score_summary"], sa.get_score_summary())


class TestVercelConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))

    def test_01_static_output(self) -> None:
        output = ROOT / self.config["outputDirectory"]
        self.assertTrue((output / "index.html").is_file())
        self.assertTrue((output / "app.js").is_file())

    def test_02_rewrites(self) -> None:
        rewrites = {rule["source"]: rule["destination"] for rule in self.config["rewrites"]}
        self.assertEqual(rewrites["/api/dashboard"], "/api/snapshot?view=dashboard")
        self.assertEqual(rewrites["/api/score/summary"], "/api/snapshot?view=score_summary")

    def test_03_bundle_exclusions(self) -> None:
        """excludeFiles es un solo glob (Vercel no acepta listas) y deja fuera lo pesado."""
        pattern = self.config["functions"]["api/**/*.py"]["excludeFiles"]
        self.assertIsInstance(pattern, str)
        self.assertLessEqual(len(pattern), 256)
        match = re.fullmatch(r"\{([^{}]+)\}/\*\*", pattern)
        self.assertIsNotNone(match, f"formato inesperado: {pattern}")
        excluded = set(match.group(1).split(","))
        self.assertLessEqual({"data", "notebooks", "tests", "capturas", "docs", ".venv"}, excluded)
        # La función del snapshot lee outputs/ y la calculadora importa dashboard/.
        self.assertNotIn("outputs", excluded)
        self.assertNotIn("dashboard", excluded)

    def test_04_functions_have_no_dependencies(self) -> None:
        for path in sorted((ROOT / "api").rglob("requirements.txt")):
            with self.subTest(str(path.relative_to(ROOT))):
                lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
                self.assertEqual([line for line in lines if line and not line.startswith("#")], [])
        for entrypoint in sorted((ROOT / "api").rglob("*.py")):
            with self.subTest(str(entrypoint.relative_to(ROOT))):
                self.assertTrue((entrypoint.parent / "requirements.txt").is_file())


if __name__ == "__main__":
    unittest.main()
