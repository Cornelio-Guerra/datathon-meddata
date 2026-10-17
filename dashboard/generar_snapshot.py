"""Genera outputs/dashboard_snapshot.json para el despliegue en Vercel.

Calcula una sola vez, en local, lo mismo que responde el servidor de
dashboard/app.py en GET /api/dashboard (sin filtros) y GET /api/score/summary,
y lo guarda como JSON. En Vercel ese archivo se sirve tal cual: no se sube el
CSV a las funciones ni se ejecuta src/score_diabetes.py en cada arranque.

Hay que volver a generarlo si cambian el CSV, src/score_diabetes.py o
dashboard/app.py. Desde la raíz del repositorio:

    .venv/bin/python dashboard/generar_snapshot.py              # macOS / Linux
    .\\.venv\\Scripts\\python.exe .\\dashboard\\generar_snapshot.py  # Windows

La primera carga procesa los 253,680 registros y entrena los modelos de
comparación, así que tarda alrededor de un minuto.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.app import data_health, find_dataset, load_dataset  # noqa: E402
from dashboard.score_adapter import SCORE_SCRIPT, get_score_summary  # noqa: E402

SNAPSHOT_PATH = ROOT / "outputs" / "dashboard_snapshot.json"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_snapshot() -> dict[str, Any]:
    """Devuelve las dos respuestas de la API en claves separadas, más metadatos."""
    rows, schema, headers = load_dataset()
    dashboard = data_health(rows, schema, headers, {})
    score_summary = get_score_summary()
    source = find_dataset()
    return {
        "meta": {
            "description": (
                "Respuestas precalculadas de GET /api/dashboard (sin filtros) y "
                "GET /api/score/summary del servidor local dashboard/app.py."
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "dashboard/generar_snapshot.py",
            "filters": {},
            "population_n": len(rows),
            "source_file": source.name,
            "source_sha256": sha256_of(source),
            "score_engine": SCORE_SCRIPT.relative_to(ROOT).as_posix(),
            "score_engine_sha256": sha256_of(SCORE_SCRIPT),
        },
        "dashboard": dashboard,
        "score_summary": score_summary,
    }


def main() -> None:
    snapshot = build_snapshot()
    # allow_nan=False: un NaN produciría JSON inválido para el navegador.
    text = json.dumps(snapshot, ensure_ascii=False, indent=1, allow_nan=False)
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(text + "\n", encoding="utf-8")

    summary = snapshot["score_summary"]
    metrics = summary["metrics"]
    print(f"Snapshot guardado en {SNAPSHOT_PATH.relative_to(ROOT)} ({len(text.encode('utf-8')):,} bytes)")
    print(f"  Registros en el dashboard: {snapshot['meta']['population_n']:,}")
    print(f"  Población del score:       {summary['population_n']:,}")
    print(f"  AUC {metrics['auc']} · sensibilidad {metrics['sensitivity']} % · "
          f"especificidad {metrics['specificity']} % · VPN {metrics['npv']} %")
    for level in summary["risk_distribution"]:
        print(f"  {level['level']:<9} {level['range']:<10} prevalencia {level['prevalence']} %")


if __name__ == "__main__":
    main()
