# Contexto del MedData Challenge

## Entorno

- Sistema operativo: Windows, PowerShell.
- Usar siempre el entorno virtual del repositorio: `.venv`.
- Intérprete: `.venv/Scripts/python.exe`.
- El análisis personal de Jesus va únicamente en `notebooks/analisis/analisis_jesus.ipynb`.
- No modificar ni ejecutar para guardar cambios el notebook de Cornelio: `notebooks/analisis_cornelio.ipynb`.

## Trabajo colaborativo

- Cada integrante trabaja en su propio notebook; no mezclar cambios entre ambos `.ipynb`.
- Antes de editar, revisar `git status` y preservar cambios existentes.
- Los commits deben usar la identidad Git local `jesus12ga` y su correo noreply configurado.
- No crear análisis nuevo ni cambiar datasets salvo que Jesus lo solicite explícitamente.

## Datos disponibles

- `data/diabetes_012_health_indicators_BRFSS2015.csv`: 253,680 filas y 22 columnas.
- Target `Diabetes_012`: 0 = sin diabetes, 1 = prediabetes, 2 = diabetes.
- `src/score_diabetes.py` contiene el sistema de puntuación estadístico de Cornelio.

## Calidad y salud

- Identificar duplicados, BMI fuera de rango, contradicciones de seguro/costo y días inválidos.
- Machine learning sí está permitido como comparación, según la aclaración más reciente de los organizadores.
- Mantener el score estadístico como enfoque interpretable y compararlo con ML solo cuando sea útil.
- Validar el score con prevalencias por nivel de riesgo, sensibilidad, especificidad y AUC de Mann-Whitney.
- No presentar correlación o predicción como causalidad clínica.
- No incluir datos personales ni secretos en notebooks, commits o outputs.

## Flujo recomendado

1. Leer `README.md`, los issues abiertos y `notebooks/snippets.md` si existe.
2. Trabajar solo en `analisis_jesus.ipynb`.
3. Guardar gráficas y entregables en `outputs/`.
4. Ejecutar la verificación del entorno antes de cerrar.
