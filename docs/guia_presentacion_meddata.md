# Guía de presentación — MedData Challenge

## Idea central

Construimos una herramienta de apoyo al tamizaje poblacional de diabetes con BRFSS 2015. Combina un score estadístico interpretable con modelos de machine learning para comparar explicabilidad y desempeño técnico. No es un diagnóstico: prioriza a quién ofrecer evaluación clínica confirmatoria.

## Resumen de 30 segundos

> Analizamos 253,680 registros de salud para detectar patrones asociados con diabetes. Primero identificamos duplicados e inconsistencias; después construimos un score de riesgo basado en odds ratios y lo comparamos con Regresión Logística y Random Forest. El score alcanza AUC 0.798 y detecta 85.5% de los casos; Random Forest alcanza AUC 0.824. Así combinamos un benchmark técnico con una herramienta transparente para tamizaje.

## 1. Problema, pregunta y propósito

**Problema.** Los recursos de salud son limitados y no todos los pacientes pueden recibir el mismo nivel de tamizaje preventivo.

**Pregunta.** ¿Qué indicadores se asocian con mayor prevalencia de diabetes y qué tan bien prioriza un score simple la derivación a pruebas confirmatorias?

**Propósito.** Detectar problemas de calidad, estratificar riesgo, comparar el score con ML y traducir evidencia agregada en acciones preventivas.

## 2. Datos y calidad

| Elemento | Resultado |
|---|---:|
| Dataset | BRFSS 2015 Diabetes Health Indicators |
| Registros originales | 253,680 |
| Variables | 22, todas numéricas |
| Target | Diabetes_012: 0 sin diabetes, 1 prediabetes, 2 diabetes |
| Diabetes confirmada original | 35,346 (13.9%) |
| Duplicados exactos | 23,899 (9.4%) |
| BMI fuera de rango 12–60 | 805 |
| Inconsistencia seguro/costo | 7,838 |
| Registros eliminados | 24,704 |
| Registros finales del score | 228,976 |

**Qué decir:** “No empezamos modelando: limpiamos primero. Evitamos que duplicados o valores clínicamente improbables parezcan patrones reales.”

## 3. Score estadístico interpretable

El motor src/score_diabetes.py usa el marco Sullivan/Framingham:

1. Discretiza BMI, edad y salud autopercibida en categorías interpretables.
2. Calcula prevalencias y odds ratios contra una categoría de referencia.
3. Convierte ln(odds ratio) en puntos enteros con B = 0.7532.
4. Suma los puntos de 10 factores: BMI, edad, salud autopercibida, presión alta, colesterol alto, movilidad, enfermedad cardíaca, ACV, actividad física y alcohol.
5. Clasifica riesgo y recomienda derivación desde score ≥ 7.

| Riesgo | Personas | Casos | Prevalencia |
|---|---:|---:|---:|
| Bajo | 115,913 | 5,059 | 4.4% |
| Moderado | 56,450 | 10,103 | 17.9% |
| Alto | 36,137 | 11,965 | 33.1% |
| Muy alto | 15,864 | 7,799 | 49.2% |

**Mensaje clave:** la prevalencia pasa de 4.4% a 49.2%, más de 11 veces entre los extremos. El score permite explicar el resultado factor por factor.

## 4. Validación del score

| Métrica (corte score ≥ 7) | Valor |
|---|---:|
| Sensibilidad | 85.5% |
| Especificidad | 58.5% |
| Valor predictivo positivo | 27.5% |
| Valor predictivo negativo | 95.6% |
| AUC Mann–Whitney | 0.7976 |
| Población a derivar | 48.3% |

El corte favorece sensibilidad porque, en tamizaje, es preferible una prueba confirmatoria adicional a omitir a una persona con posible diabetes.

## 5. Machine learning: comparación técnica

Los modelos usan el mismo dataset, división estratificada 80/20 y random_state=42. Son un benchmark, no un reemplazo del score.

| Modelo | Preprocesamiento | Configuración |
|---|---|---|
| Regresión Logística | Imputación mediana + StandardScaler | max_iter=1500, class_weight="balanced" |
| Random Forest | Imputación mediana | 100 árboles, profundidad 12, min_samples_leaf=4, class_weight="balanced" |

| Enfoque | Accuracy | Precisión | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Score estadístico | — | 27.5% VPP | 85.5% | — | 0.798 |
| Regresión Logística | 0.732 | 0.311 | 0.761 | 0.441 | 0.820 |
| Random Forest | 0.732 | 0.313 | 0.770 | 0.445 | 0.824 |

**Cómo explicarlo:** “Random Forest mejora el AUC en 0.026, pero el score se puede auditar, aplicar sin infraestructura compleja y prioriza una sensibilidad alta. No elegimos entre ML y score: usamos ML para medir el techo y el score para la decisión explicable.”

## 6. Librerías y tecnologías

| Tecnología | Rol |
|---|---|
| Python | Lógica, API local y automatización. |
| pandas | Carga, limpieza, agrupaciones y prevalencias. |
| NumPy | Cálculos numéricos, odds ratios y AUC por rangos. |
| scikit-learn | Pipelines ML, imputación, escalado y métricas. |
| matplotlib | Gráficas del notebook de análisis. |
| Jupyter | Análisis reproducible y visualizaciones. |
| openpyxl | Intercambio con hojas de cálculo si se requiere. |
| HTML, CSS, JavaScript | Interfaz del dashboard. |
| http.server | Servidor local y API JSON sin framework web pesado. |

Entorno local verificado: pandas 3.0.5, NumPy 2.5.2, matplotlib 3.11.1, scikit-learn 1.9.0, Jupyter 1.1.1 y openpyxl 3.1.5.

## 7. Arquitectura

~~~
BRFSS 2015 CSV
  -> control de calidad y limpieza
  -> score Sullivan/Framingham + modelos ML
  -> API Python local
  -> dashboard HTML/CSS/JavaScript
  -> tamizaje, derivación y seguimiento
~~~

- src/score_diabetes.py: score estadístico y validación Mann–Whitney.
- dashboard/score_adapter.py: resumen y cálculo individual del score para API.
- dashboard/app.py: filtros, KPIs, ML, endpoints y recomendaciones.
- dashboard/static/: interfaz del dashboard.
- notebooks/analisis/analisis_jesus.ipynb: tres gráficas de apoyo.

## 8. Demo en vivo

1. Ejecutar ./run_dashboard.ps1 y abrir http://127.0.0.1:8000.
2. Mostrar población, prevalencia, sensibilidad y AUC del score.
3. Aplicar un filtro de edad o BMI y señalar el tamaño de muestra resultante.
4. Mostrar factores y segmentos prioritarios; hablar de asociaciones, no causas.
5. Explicar el score y sus cuatro niveles de riesgo.
6. Comparar score, Regresión Logística y Random Forest.
7. Cerrar con: problema → evidencia → tamizaje → confirmación clínica → seguimiento.

## 9. Guion de 6–7 minutos

| Tiempo | Diapositiva | Mensaje |
|---:|---|---|
| 0:00–0:40 | Problema | Detección temprana con recursos limitados. |
| 0:40–1:30 | Datos y calidad | 253,680 registros y depuración previa. |
| 1:30–2:40 | Score | Odds ratios convertidos en puntos claros. |
| 2:40–3:30 | Riesgo | Prevalencia: 4.4% a 49.2%. |
| 3:30–4:40 | ML | RF AUC 0.824 vs score 0.798. |
| 4:40–5:40 | Dashboard | Filtros, KPIs, calidad y acciones. |
| 5:40–6:30 | Ética | No diagnóstico, validación clínica obligatoria. |

## 10. Límites y preguntas del jurado

- Las asociaciones no prueban causalidad.
- La solución no diagnostica diabetes; prioriza tamizaje y confirmación clínica.
- El desempeño debe validarse de nuevo antes de usarlo en otra población.
- La IA está documentada en USO_DE_IA.md; las decisiones metodológicas y la validación final son responsabilidad del equipo.

**¿Por qué no usar solo Random Forest?** Porque el score es interpretable, auditable y útil donde no hay infraestructura de ML.

**¿Por qué priorizar sensibilidad?** Porque en prevención el costo de omitir un caso potencial puede ser mayor que enviar a una prueba confirmatoria adicional.

## Evidencia reproducible

~~~
.\.venv\Scripts\python.exe src\score_diabetes.py
.\.venv\Scripts\python.exe dashboard\app.py
~~~

La API expone GET /api/dashboard, GET /api/score/summary y POST /api/score/calculate.

