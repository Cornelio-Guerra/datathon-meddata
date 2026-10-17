"""Función de Vercel para POST /api/score/calculate.

Reproduce el endpoint del mismo nombre de dashboard/app.py: mismo JSON de
respuesta y mismos códigos de error. Reutiliza calculate_patient_score() de
dashboard/score_adapter.py, que trabaja con puntos fijos; por eso esta función
no lee el CSV ni ejecuta src/score_diabetes.py.
"""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importar el módulo no dispara la lectura del CSV: get_score_summary() y
# load_score_module() solo se ejecutan si alguien las llama, y aquí nadie lo hace.
from dashboard.score_adapter import calculate_patient_score  # noqa: E402


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel exige este nombre
    def send_json(self, content: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        # Mismo flujo y mismos mensajes que DashboardHandler.do_POST en dashboard/app.py.
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

    def do_GET(self) -> None:  # noqa: N802
        self.send_json({"error": "Usa POST con el JSON del paciente"}, HTTPStatus.METHOD_NOT_ALLOWED)

    def log_message(self, format: str, *args: Any) -> None:
        # Vercel ya registra cada solicitud; evita duplicar líneas en stderr.
        return
