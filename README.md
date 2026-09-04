# Datathon MedData Challenge — entorno de trabajo

**Evento:** jueves 4 de septiembre de 2026, 1:00–4:00 pm · presencial · 3 horas
· análisis de datos de salud.

---

## Activar el entorno

Desde la carpeta `datathon-meddata/`:

```bash
source .venv/bin/activate
```

Comando completo desde cualquier ubicación (cópialo tal cual):

```bash
source /Users/cornelio/Desktop/UTP/2026/Concursos/Medata/datathon-meddata/.venv/bin/activate
```

Para salir: `deactivate`. Verás `(.venv)` al inicio del prompt cuando esté activo.

### Abrir Jupyter

```bash
cd /Users/cornelio/Desktop/UTP/2026/Concursos/Medata/datathon-meddata
source .venv/bin/activate
jupyter lab            # o: jupyter notebook
```

### Comprobar que todo está bien (5 segundos)

```bash
python -c "import pandas, numpy, matplotlib, seaborn, sklearn, openpyxl; print('OK')"
```

### Si algo se rompe y hay que reinstalar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Estructura

```
datathon-meddata/
├── .venv/                  entorno virtual (Python 3.9.6)
├── data/                   datasets de práctica
│   ├── pima_diabetes.csv
│   ├── heart_disease.csv
│   └── stroke_prediction.csv
├── notebooks/
│   ├── plantilla_eda.ipynb              plantilla lista para usar
│   ├── snippets.md                      chuleta de pandas/sklearn
│   └── _ejecutada_pima_referencia.ipynb copia ya ejecutada, para ver salidas
├── outputs/                gráficas y entregables (se llena solo)
├── requirements.txt        dependencias directas
└── requirements-lock.txt   freeze completo (119 paquetes)
```

---

## Versiones instaladas

Python **3.9.6** (el del sistema; no había otro disponible en esta Mac).
Las librerías quedaron en las últimas versiones compatibles con 3.9:

| Paquete | Versión |
|---|---|
| pandas | 2.3.3 |
| numpy | 2.0.2 |
| matplotlib | 3.9.4 |
| seaborn | 0.13.2 |
| scikit-learn | 1.6.1 |
| jupyter | 1.1.1 |
| openpyxl | 3.1.5 |

---

## Cómo usar la plantilla

`notebooks/plantilla_eda.ipynb` está pensada para tocar **una sola celda**:

```python
RUTA_CSV = Path("../data/pima_diabetes.csv")   # el archivo
TARGET    = "Outcome"                          # lo que quieres predecir
COLS_A_ELIMINAR = []                           # ["id"] en stroke
```

Luego `Kernel > Restart & Run All` y tienes EDA + dos modelos base + métricas
+ seis gráficas guardadas en `outputs/`.

Valores por dataset:

| Dataset | `RUTA_CSV` | `TARGET` | `COLS_A_ELIMINAR` |
|---|---|---|---|
| Diabetes | `../data/pima_diabetes.csv` | `Outcome` | `[]` |
| Corazón | `../data/heart_disease.csv` | `num` | `[]` |
| Derrame | `../data/stroke_prediction.csv` | `stroke` | `["id"]` |

El notebook binariza solo el target si viene en escala (el caso de `num`, 0–4).

---

## Datasets — fuentes usadas

Ninguno requiere login. **No se usó Kaggle** (habría pedido credenciales que no
están configuradas), así que fueron mirrors públicos y UCI directo:

| Archivo | Filas × cols | Target | Fuente |
|---|---|---|---|
| `pima_diabetes.csv` | 768 × 9 | `Outcome` (34.9% positivos) | `raw.githubusercontent.com/plotly/datasets/master/diabetes.csv` |
| `heart_disease.csv` | 303 × 14 | `num` 0–4 (45.9% con enfermedad) | UCI ML Repository, dataset 45 (Cleveland): `archive.ics.uci.edu/static/public/45/data.csv` |
| `stroke_prediction.csv` | 5110 × 12 | `stroke` (4.87% positivos) | mirror del dataset de Kaggle en `raw.githubusercontent.com/bishopce16/stroke_prediction_analysis/main/resources/healthcare-dataset-stroke-data.csv` |

Notas de calidad, ya verificadas:

- **Pima**: sin NaN declarados, pero con **ceros imposibles** (`Glucose`,
  `BloodPressure`, `SkinThickness`, `Insulin`, `BMI` = 0). Son nulos disfrazados.
  La celda 6a tiene el bloque para convertirlos a `NaN`.
- **Heart**: 6 nulos en `ca` y `thal`. Target `num` en escala 0–4 → binarizar.
- **Stroke**: 201 nulos en `bmi` (3.9%). Fuertemente **desbalanceado (4.87%)**:
  el accuracy no sirve como métrica, usa recall de la clase 1 y ROC-AUC.

---

## Verificaciones hechas

- Los 7 paquetes importan sin error en el venv.
- Los 3 CSV cargan con `pd.read_csv` (shapes confirmados arriba).
- `plantilla_eda.ipynb` corre **de principio a fin sin errores** con Pima
  (LogReg: acc 0.734 / AUC 0.825 — RF: acc 0.766 / AUC 0.824).
- También corre completa con Heart Disease
  (LogReg: acc 0.869 / AUC 0.950 — RF: acc 0.918 / AUC 0.959).
- Pipeline de Stroke verificado por separado (acc 0.746 con `class_weight="balanced"`).

> Puede que veas `RuntimeWarning: ... encountered in matmul` en algunos ajustes.
> Es un artefacto conocido de numpy con el BLAS Accelerate de macOS: se comprobó
> que `lbfgs`, `liblinear` y `newton-cg` dan resultados idénticos, así que no
> afecta los números. El notebook ya los silencia.

---

## Recordatorio para el día del evento

**El objetivo es terminar, no optimizar.** Un análisis completo y mediocre gana a
uno brillante a medio hacer. Reparto sugerido de las 3 horas:

| Tiempo | Qué |
|---|---|
| 0:00–0:20 | Cargar, entender el problema, ver `shape` / nulos / balance del target |
| 0:20–1:00 | EDA con gráficas — anota hallazgos **mientras** los ves, no después |
| 1:00–1:40 | Limpieza + modelo base. Uno solo. No afines hiperparámetros. |
| 1:40–2:20 | Interpretación: qué variables pesan y qué significan clínicamente |
| 2:20–3:00 | **Slides y ensayo en voz alta.** Reserva esto de verdad. |

Estructura de cada hallazgo: **problema → qué encontré → qué recomendaría.**
Cada afirmación con un número detrás.
