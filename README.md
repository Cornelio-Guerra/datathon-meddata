# Sistema de puntuación de riesgo de diabetes

**MedData Challenge — "Transformando datos médicos en soluciones inteligentes"**
Universidad Tecnológica de Panamá · 4 de septiembre de 2026

**Equipo:** Cornelio Guerra · Jesús

---

## El problema

El sistema de salud necesita detectar patrones de diabetes en miles de registros
y decidir **a quién derivar primero** a prueba confirmatoria, cuando los recursos
diagnósticos son limitados.

## La solución

Un **sistema de puntuación clínica** que asigna puntos por factor de riesgo y
clasifica al paciente en cuatro niveles. Se aplica **en papel, sin computadora y
sin laboratorio** — solo con preguntas de entrevista.

El método es el de **Sullivan (framework de Framingham)**: para cada factor se
calcula su *odds ratio* contra un nivel de referencia y se convierte a puntos
enteros dividiendo por una constante de calibración,

```
puntos = round( ln(OR) / B )
```

donde `B` es el menor `ln(OR)` positivo observado. Así **un punto equivale
siempre al mismo incremento de riesgo**, que es lo que hace el score sumable e
interpretable por un médico.

## Resultados

| Métrica | Valor |
|---|---|
| **AUC** | **0.798** — Mann-Whitney implementado a mano |
| **Sensibilidad** (corte ≥ 7) | **85.5%** — detecta 29,867 de 34,926 diabéticos |
| Especificidad | 58.5% |
| **Valor predictivo negativo** | **95.6%** |
| Inconsistencias detectadas | **24,704** |
| Registros | **253,680** crudos → **228,976** depurados → **224,364** calibrados |

**Estratificación de riesgo** — el score separa 11 veces entre extremos:

| Nivel | Score | Prevalencia de diabetes |
|---|---|---|
| Bajo | ≤ 6 | 4.4% |
| Moderado | 7–9 | 17.9% |
| Alto | 10–12 | 33.1% |
| Muy alto | ≥ 13 | 49.2% |

### Por qué el umbral está en 7

**No se eligió maximizando accuracy.** Se eligió por el costo clínico del error:
en tamizaje, un falso negativo es un paciente que se va a casa sin diagnóstico;
un falso positivo solo genera una prueba confirmatoria barata. Por eso se
priorizó sensibilidad.

## Hallazgos

1. **La limpieza de datos es una decisión, no un trámite — y la medimos en las dos
   direcciones.** Encontramos 23,899 filas exactamente repetidas (9.4%), 805 con
   IMC sobre 60 y 7,838 personas sin seguro que no reportan barrera de costo
   (esto último **no es contradicción**: es el 63% de los no asegurados, gente
   que no necesitó médico ese año; las conservamos). Verificamos si los
   duplicados eran errores de captura o colisiones de azar: las filas repetidas
   tienen **1.0% de diabetes contra 15.3% del resto y cero derrames** — el perfil
   joven-sano modal, la firma de una colisión estadística en una encuesta de 21
   variables casi todas binarias. Corrimos el pipeline en ambos escenarios: **sin
   deduplicar el AUC es 0.816; deduplicando, 0.798.** Reportamos la versión
   conservadora, la que nos deja peor.

2. **La salud autopercibida predice mejor que varios marcadores clínicos.** Quien
   califica su salud como "mala" tiene 38.9% de diabetes contra 3.3% de quien la
   califica "excelente" — un *odds ratio* de 18.8, el más alto de los 10 factores del score, por encima de presión alta (4.6) y colesterol (3.1). Es una
   pregunta que cuesta cero y ordena mejor que un análisis de sangre.

3. **Diez preguntas estratifican el riesgo 11 veces, sin laboratorio.** Derivando
   al 48% de mayor puntaje se captura el 85.5% de los diabéticos, y cuando el
   sistema dice "bajo riesgo" acierta el 95.6% de las veces.


## Justificabilidad — por qué cada decisión se puede defender

El enunciado pide una solución *precisa, eficiente y **justificable***. Esta es
la trazabilidad completa de cada pieza del sistema.

### ¿Por qué entra cada variable?

Ninguna variable entró por correlación ciega. Cada una es un factor de riesgo de
diabetes tipo 2 reconocido clínicamente, y su relación en estos datos se midió:

| Variable | Relación clínica conocida | OR medido aquí |
|---|---|---|
| Salud autopercibida | Marcador integrado de comorbilidad | **18.8** |
| Edad | El riesgo crece con la edad; deterioro de la función pancreática | 8.7 |
| IMC | La obesidad es el factor modificable principal | 6.0 |
| Presión alta | Componente del síndrome metabólico | 4.6 |
| Dificultad para caminar | Proxy de complicaciones y sedentarismo | 3.4 |
| Enfermedad cardíaca | Comorbilidad frecuente del síndrome metabólico | 3.3 |
| Colesterol alto | Componente del síndrome metabólico | 3.1 |
| Derrame previo | Consecuencia vascular compartida | 2.8 |
| Actividad física | **Protector** — mejora la sensibilidad a la insulina | 0.55 |
| Consumo alto de alcohol | **Protector aparente** — ver limitaciones | 0.33 |

Se **descartó** `CholCheck` pese a estar entre los OR más altos del dataset: mide
si la persona se hizo un chequeo de colesterol, no su estado de salud. Es un marcador de contacto con el
sistema sanitario, no un factor de riesgo. Incluirlo habría inflado la precisión
con una variable que no explica nada clínicamente.

### ¿De dónde sale cada punto?

De la fórmula `puntos = round(ln(OR) / B)`, con `B = 0.7532` (el menor `ln(OR)`
positivo observado). No hay pesos elegidos a mano ni ajustados por ensayo y error.

`B` es la unidad de conversión de ln(OR) a puntos. Medido sobre nuestra propia
salida, **cada punto multiplica los odds por ≈1.45**. Esa es toda la
interpretación que un médico necesita.

### ¿Por qué el corte en 7?

Se calcularon las métricas en **12 umbrales distintos** (visibles en el notebook).
El 7 no maximiza el accuracy: se eligió por el **costo asimétrico del error**.

En tamizaje, un falso negativo es un paciente que se va a casa sin diagnóstico;
un falso positivo solo genera una prueba confirmatoria barata. Por eso se
priorizó sensibilidad (85.5%) sobre especificidad (58.5%).

### ¿Qué significa cada métrica?

| Métrica | Qué responde | Valor |
|---|---|---|
| Sensibilidad | De todos los diabéticos, ¿a cuántos detecto? | 85.5% |
| Especificidad | De todos los sanos, ¿a cuántos descarto bien? | 58.5% |
| VPN | Cuando digo "bajo riesgo", ¿cuánto acierto? | **95.6%** |
| AUC | ¿Ordena bien a un enfermo por encima de un sano? | 0.798 |

El **AUC de 0.798** significa que, tomando un diabético y un no diabético al azar,
el sistema le asigna mayor puntaje al diabético el 79.8% de las veces.

## Cómo ejecutarlo

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/score_diabetes.py       # reproduce todas las cifras de arriba
```

### Windows / PowerShell

Con el entorno virtual ya creado, estos comandos equivalentes evitan depender de
la activación del entorno:

```powershell
# Dashboard y calculadora interactiva: http://127.0.0.1:8000
.\run_dashboard.ps1

# Motor estadístico, pruebas y notebooks
.\.venv\Scripts\python.exe .\src\score_diabetes.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\jupyter.exe lab
```

**Dashboard interactivo** (servidor con librería estándar; su sección de comparación usa scikit-learn):

```bash
cd dashboard && python app.py      # http://localhost:8000
```

> La primera carga procesa 253,680 registros y tarda ~10 s; a partir de ahí es
> instantánea gracias al caché.

## Estructura

```
src/score_diabetes.py                  motor de puntuación (sin dependencias de ML)
notebooks/analisis_cornelio.ipynb      análisis completo y hallazgos
notebooks/analisis/analisis_jesus.ipynb análisis complementario
dashboard/                             dashboard interactivo
outputs/                               gráficas y tabla de puntuación
USO_DE_IA.md                           declaración de uso de IA (exigida por el reglamento)
```

### Sobre el uso de machine learning

Los organizadores confirmaron que el ML está permitido. Lo usamos **solo como
contraste**: un Random Forest sobre el dataset crudo alcanza **AUC 0.823** frente
a 0.798 del score. Esos 25 milésimos cuestan un modelo que nadie aplica en papel
ni audita — y ese 0.823 está medido sobre datos sin deduplicar, donde parte del
conjunto de prueba son copias exactas del de entrenamiento. No son comparables.

## Limitaciones

- Los datos son **autorreportados** (BRFSS 2015 es una encuesta telefónica), por
  lo que los factores dependen de lo que el encuestado recuerda y declara.
- Se **excluyó la clase prediabetes** (1.8% de los registros) del ajuste, por ser
  un estado intermedio con pocos casos para calibrar pesos estables.
- El score se **calibró y validó sobre el mismo conjunto**. Con más tiempo
  correspondería una partición de validación independiente.
- Los *odds ratio* son **crudos, no ajustados por confusores**: factores
  correlacionados entre sí aportan puntos de forma parcialmente redundante.

## Uso de inteligencia artificial

Declarado en **[`USO_DE_IA.md`](USO_DE_IA.md)**, conforme al reglamento del
datatón: herramientas empleadas, qué produjo cada una, qué decidió el equipo y
los prompts principales.
