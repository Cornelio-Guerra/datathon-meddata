# Prompt metodológico: diabetes y apoyo a decisiones

Usa este prompt como estructura para ampliar o evaluar el tablero sin convertir
sus resultados en un diagnóstico médico.

> Diseña un sistema de análisis y apoyo a decisiones sobre diabetes usando el
> dataset disponible. Estructúralo como un protocolo de investigación aplicado:
>
> 1. **Título y resumen:** delimita población, desenlace y propósito de salud
>    poblacional.
> 2. **Problema y pregunta:** formula una pregunta medible sobre la frecuencia o
>    capacidad de clasificación del desenlace de diabetes; evita prometer
>    causalidad.
> 3. **Justificación y uso:** explica qué decisión poblacional podrá orientar
>    (prevención, tamizaje, asignación de recursos o seguimiento), no decisiones
>    clínicas individuales.
> 4. **Objetivos:** incluye uno general y objetivos específicos para describir la
>    población, operacionalizar variables, analizar asociaciones, validar el
>    modelo y convertir hallazgos en acciones.
> 5. **Metodología:** especifica diseño observacional/analítico con datos
>    secundarios, unidad de análisis, población disponible, criterios de
>    inclusión/exclusión y manejo de faltantes o valores clínicamente improbables.
> 6. **Variables:** prepara un diccionario con nombre, rol (desenlace/predictor),
>    tipo, definición operacional y codificación. Documenta explícitamente la
>    regla del desenlace de diabetes.
> 7. **Control de calidad y ética:** verifica duplicados, faltantes, rangos
>    improbables y sesgos. Presenta datos agregados, protege identificadores y
>    requiere validación clínica antes de cualquier uso operativo.
> 8. **Plan de análisis:** reporta descriptivos para variables numéricas y
>    cualitativas; separa entrenamiento y prueba de forma estratificada; compara
>    regresión logística y Random Forest. Evalúa accuracy, precisión, recall, F1
>    y ROC-AUC. Para conjuntos desbalanceados, da prioridad a recall y ROC-AUC.
> 9. **Tablero:** organiza apartados desplegables para protocolo, KPIs,
>    distribución, factores asociados, segmentos, validación, calidad/ética y
>    una ruta de decisión problema -> evidencia -> prioridad -> acción ->
>    seguimiento.
> 10. **Límites:** declara que asociaciones no prueban causalidad y que la salida
>     del modelo es exploratoria, no un diagnóstico ni una recomendación médica
>     individual.

El resultado debe recalcular los indicadores con filtros, mostrar el tamaño de
muestra de cada segmento y conservar la trazabilidad entre dataset, reglas de
preprocesamiento, métricas y decisión sugerida.
