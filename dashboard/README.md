# MedData Decision Dashboard

Aplicación local de análisis y apoyo a decisiones sobre diabetes. Tiene un
backend Python que lee el CSV, calcula las tasas y aplica filtros; la interfaz
web consume esa API y muestra los resultados en apartados desplegables.

La estructura analítica está documentada en
[`PROMPT_METODOLOGICO_DIABETES.md`](PROMPT_METODOLOGICO_DIABETES.md): problema,
pregunta, objetivos, diseño, variables, calidad, validación, ética y decisión.

## Ejecutar

Desde la raíz del repositorio y usando el entorno virtual:

```powershell
.\.venv\Scripts\python.exe .\dashboard\app.py
```

Después abre `http://127.0.0.1:8000`.

## Fuente de datos

El servidor prioriza un CSV BRFSS que tenga la columna `Diabetes_012` dentro de
`data/` (por ejemplo `diabetes_012_health_indicators_BRFSS2015.csv`). Mientras
ese archivo no esté en el repositorio, utiliza `pima_diabetes.csv` como respaldo
para que el tablero siga funcional. Al agregar BRFSS no hay que cambiar código:
reinicia el servidor y detectará la nueva fuente.

## Criterio de decisión

Cada lectura sigue: **problema → evidencia → priorización → acción →
seguimiento**. Las tasas y factores son asociaciones descriptivas de la muestra,
no diagnósticos ni demostraciones de causalidad. La sección de validación separa
80% de entrenamiento y 20% de prueba, compara regresión logística con Random
Forest y reporta accuracy, precisión, recall, F1 y ROC-AUC.
