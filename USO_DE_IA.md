# Declaración de uso de inteligencia artificial

> Documento exigido por el reglamento del datatón. Registra con qué herramientas
> se trabajó, qué produjo cada una y qué decidió el equipo.

## 1. Herramientas utilizadas

| Herramienta | Integrante | Para qué se usó |
|---|---|---|
| **Claude Opus 5** (Claude Code, CLI) | Cornelio Guerra | Transcripción del audio de instrucciones, sistema de puntuación, análisis estadístico, coordinación del repositorio |
| **Codex** | Jesús | Preparación del entorno en Windows, revisión del repositorio, configuración de VS Code, dashboard y gráficas |

## 2. Qué produjo la IA

**Claude:**
- Transcribió el audio de instrucciones (10:10 min) con `mlx-whisper`
  (`whisper-large-v3-turbo`) ejecutado localmente. Transcripción completa en
  `docs/transcripcion_instrucciones.md`.
- Implementó `src/score_diabetes.py`: detección de inconsistencias, cálculo de
  odds ratio por factor, conversión a puntos enteros por el método de Sullivan
  (framework de Framingham), estratificación en cuatro grupos y validación.
- Calculó la curva de sensibilidad/especificidad en 12 umbrales para sustentar
  la elección del punto de corte.
- Redactó los issues de coordinación y gestionó los commits.

**Codex:**
- Preparó el entorno de Jesús en Windows y la configuración de VS Code.
- Construyó el dashboard (`dashboard/`): servidor HTTP con librería estándar de
  Python; su sección de comparación usa scikit-learn.
- Apoyó la estructura del notebook y las gráficas de la presentación.

## 3. Qué decidió el equipo

- **El método.** La IA propuso el framework de Sullivan; la decisión de adoptarlo
  fue del equipo.
- **El punto de corte en 7.** La IA presentó la tabla de 12 umbrales con sus
  compensaciones; el equipo eligió priorizar sensibilidad (85.5%) sobre
  especificidad, por criterio clínico: en tamizaje, un falso negativo es un
  paciente que se va sin diagnóstico, mientras un falso positivo solo genera una
  prueba confirmatoria barata.
- **Los criterios de depuración** de datos y qué registros se descartan.
- **La interpretación** de los resultados y qué hallazgos llevar a la exposición.

## 4. Prompts principales (textuales)

**De Cornelio a Claude:**
1. *"elimina los datos de práctica, ya subí los reales a la carpeta de datos, en
   el mp4 están las instrucciones, descarga lo que necesites para transcribirla"*
2. *"actualiza el repo siempre que puedas pero a una velocidad humana, después
   actualiza la carpeta mía para ver los cambios, después el corte 7"*
3. *"divide el trabajo, yo la depuración de los datos y jesus el dashboard"*

**De Jesús a Codex:**
1. *"necesito que me prepares el entorno para un datathon de análisis de datos de
   salud que empieza hoy a la 1 pm"*
2. *"necesito que hagas commit a los cambios que estoy haciendo en vs code y
   revisa los issues que me ha enviado cornelio"*
3. *"alinea el dashboard con las cifras del score y agrega una calculadora
   individual"*

## 5. Verificación

Todo el código fue ejecutado y sus salidas revisadas por el equipo. Ninguna cifra
de la presentación proviene de una afirmación no ejecutada. El AUC de 0.798 se
calculó con el estadístico de Mann-Whitney implementado a mano, sin librerías de
machine learning, y es reproducible corriendo `python src/score_diabetes.py`.

## 6. Limitaciones declaradas

- **Se excluyó la clase de prediabetes** (1.8% de los registros) del ajuste del
  score, por ser un estado intermedio con muy pocos casos. Es una decisión
  metodológica discutible y se declara como tal.
- **Los datos son autorreportados**: BRFSS 2015 es una encuesta telefónica, por
  lo que los factores de riesgo dependen de lo que el encuestado recuerda y
  declara, no de una medición clínica.
- **El score se validó sobre el mismo conjunto** con el que se calibraron los
  pesos. Con más tiempo correspondería una partición de validación independiente.

## 7. Nota sobre una corrección durante el reto

La transcripción automática del audio indica *"utilizando únicamente reglas
matemáticas y métodos estadísticos"*, lo que se interpretó inicialmente como una
prohibición de usar machine learning. El equipo **confirmó con los organizadores
en persona que el ML sí está permitido**. El sistema de puntuación se mantuvo
igualmente por ser interpretable y aplicable sin computadora, que es su valor
diferencial.
