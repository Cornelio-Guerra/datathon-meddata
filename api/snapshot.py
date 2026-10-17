"""Función de Vercel que sirve las vistas precalculadas del dashboard.

vercel.json reescribe GET /api/dashboard y GET /api/score/summary hacia esta
función. Responde con la clave correspondiente de outputs/dashboard_snapshot.json,
generado en local con dashboard/generar_snapshot.py, así que en Vercel no se
sube el CSV ni se ejecuta src/score_diabetes.py.

A la respuesta de /api/dashboard le agrega la clave "snapshot" con los
metadatos del archivo. El frontend la usa para saber que la vista es fija y
deshabilitar los filtros; el servidor local nunca la envía.
"""

from __future__ import annotations

import functools
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "outputs" / "dashboard_snapshot.json"
VIEWS = ("dashboard", "score_summary")


@functools.lru_cache(maxsize=1)
def load_snapshot() -> dict[str, Any]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def resolve_view(raw_path: str) -> str:
    """Decide qué vista pidió el cliente.

    Vercel entrega a la función la ruta original (/api/dashboard o
    /api/score/summary), así que esa manda. Si llegara la ruta de destino
    (/api/snapshot), se usa el parámetro ?view= que agrega el rewrite.
    """
    parsed = urlparse(raw_path)
    path = parsed.path.rstrip("/")
    if path.endswith("/score/summary"):
        return "score_summary"
    if path.endswith("/dashboard"):
        return "dashboard"
    view = parse_qs(parsed.query).get("view", [""])[-1]
    return view if view in VIEWS else "dashboard"


def build_response(view: str) -> dict[str, Any]:
    snapshot = load_snapshot()
    if view == "dashboard":
        return {**snapshot["dashboard"], "snapshot": snapshot["meta"]}
    return snapshot["score_summary"]


class handler(BaseHTTPRequestHandler):  # noqa: N801 - Vercel exige este nombre
    def send_json(self, content: Any, status: int = HTTPStatus.OK, cacheable: bool = False) -> None:
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # El archivo no cambia dentro de un mismo despliegue: la CDN puede guardarlo.
        self.send_header("Cache-Control", "public, max-age=0, s-maxage=86400" if cacheable else "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        try:
            return self.send_json(build_response(resolve_view(self.path)), cacheable=True)
        except (FileNotFoundError, KeyError, ValueError, OSError) as error:
            return self.send_json({"error": f"Snapshot no disponible: {error}"}, HTTPStatus.SERVICE_UNAVAILABLE)

    def log_message(self, format: str, *args: Any) -> None:
        return
