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
| Registros depurados | 253,680 → **228,976** (se eliminan duplicados e IMC imposible) |
| Registros analizados en el score | **224,364** (se excluyen además 4,612 prediabéticos) |

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

1. **El 10% del dataset es ruido duplicado.** 23,899 duplicados exactos, 805 IMC
   fisiológicamente imposibles y 7,838 contradicciones lógicas. Sin un control de
   calidad previo, una de cada diez decisiones se toma sobre un registro repetido.

2. **La salud autopercibida predice mejor que varios marcadores clínicos.** Quien
   califica su salud como "mala" tiene 38.9% de diabetes contra 3.3% de quien la
   califica "excelente" — un *odds ratio* de 18.8, el más alto de las 22
   variables, por encima de presión alta (4.6) y colesterol (3.1). Es una
   pregunta que cuesta cero y ordena mejor que un análisis de sangre.

3. **Diez preguntas estratifican el riesgo 11 veces, sin laboratorio.** Derivando
   al 48% de mayor puntaje se captura el 85.5% de los diabéticos, y cuando el
   sistema dice "bajo riesgo" acierta el 95.6% de las veces.

## Cómo ejecutarlo

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

python src/score_diabetes.py       # reproduce todas las cifras de arriba
```

**Dashboard interactivo** (no requiere dependencias externas):

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
docs/transcripcion_instrucciones.md    transcripción del audio del reto
outputs/                               gráficas y tabla de puntuación
USO_DE_IA.md                           declaración de uso de IA (exigida por el reglamento)
```

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
