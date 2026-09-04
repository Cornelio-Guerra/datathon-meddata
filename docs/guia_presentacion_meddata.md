# Guía de presentación — 5 minutos

**MedData Challenge · IEEE EMBS · CONTEC · UTP**
Equipo: Cornelio Guerra · Jesús

> ⏱️ **El límite es 5 minutos.** Esta guía sustituye al guion de 6–7 min anterior.
> Los 4 puntos que exige el jurado están cubiertos: metodología, resultados,
> visualizaciones e impacto.

---

## Reparto

| Quién | Lleva |
|---|---|
| **Cornelio** | Problema, metodología, resultados (0:00 – 2:30) |
| **Jesús** | Dashboard y paciente en vivo, impacto, cierre (2:30 – 5:00) |
| Quien no habla | Opera la pantalla |

⚠️ **Abrir el dashboard 2 minutos antes de empezar.** La primera carga tarda ~10 s.

---

## Cifras oficiales — que ambos citen las mismas

| Métrica | Valor |
|---|---|
| Población | **253,680** crudos → **228,976** depurados → **224,364** calibrados |
| Inconsistencias detectadas | **24,704** |
| AUC del score (Mann-Whitney) | **0.798** |
| Sensibilidad (corte ≥7) | **85.5%** — 29,867 de 34,926 |
| Especificidad | 58.5% |
| VPN | **95.6%** |
| Estratificación | 4.4% / 17.9% / 33.1% / 49.2% |
| Random Forest (contraste) | **0.823** |

> Los tres números de población se dicen **siempre juntos**. Si el jurado suma la
> columna `n` de la tabla de estratificación le da 224,364.

---

## Timeline

### 0:00 – 0:40 · El problema — *Cornelio*
Pantalla: portada.

> "Un sistema de salud tiene 253,680 registros y capacidad para estudiar solo a
> una fracción. La pregunta no es quién tiene diabetes: es **a quién derivar
> primero**."

> "Construimos un sistema de puntuación que responde eso con diez preguntas de
> entrevista, sin laboratorio."

### 0:40 – 1:40 · Metodología — *Cornelio*
Pantalla: panel de calidad del dashboard.

> "Encontramos 24,704 inconsistencias: 23,899 duplicados exactos y 805 IMC
> fisiológicamente imposibles."

> "Usamos el framework de Sullivan, el mismo de Framingham: cada factor aporta
> puntos derivados de su odds ratio. **Cada punto multiplica las probabilidades
> por 1.45.** No hay pesos elegidos a mano."

🎯 **La frase que los separa del resto:**

> "Verificamos si los duplicados eran errores o azar: tienen 1% de diabetes
> contra 15% del resto. Corrimos ambos escenarios — sin deduplicar el AUC es
> 0.816, deduplicando 0.798. **Presentamos la cifra que nos deja peor.**"

### 1:40 – 2:30 · Resultados — *Cornelio*
Pantalla: gráfica de estratificación.

> "AUC 0.798, calculado con Mann-Whitney implementado a mano. Sensibilidad 85.5%:
> detectamos 29,867 de 34,926 diabéticos."

> "El score separa 11 veces: del 4.4% en el grupo bajo al 49.2% en el muy alto."

**Adelántense a la pregunta del umbral:**

> "El corte en 7 no maximiza el accuracy. Lo elegimos por el costo del error: un
> falso negativo es un paciente que se va sin diagnóstico; un falso positivo solo
> genera una prueba confirmatoria barata."

### 2:30 – 3:30 · 🌟 Paciente en vivo — *Jesús*
Pantalla: **calculadora individual del dashboard.**

Entrada: **IMC 33 · 60-64 años · salud regular · hipertensión · colesterol alto**

> "11 puntos. Riesgo alto. Prevalencia esperada 33.1%. Derivación prioritaria."

Señalando el desglose por factor:

> "Aquí está de dónde sale cada punto. Un médico puede auditar esta decisión
> factor por factor. Con un modelo de caja negra no podría — y esto se suma
> también en papel, sin computadora."

**Plan B si el dashboard falla:** sumarlo en voz alta.
`IMC 2 + Edad 2 + Salud 3 + Hipertensión 2 + Colesterol 2 = 11 → Alto → 33.1%`

### 3:30 – 4:20 · Impacto — *Jesús*
Pantalla: gráfica de puntos por factor.

> "Tamizaje sin costo marginal: diez preguntas, aplicables por teléfono."
> "Derivando al 48% de mayor puntaje capturamos el 85.5% de los casos."
> "Y cuando el sistema dice bajo riesgo, acierta el 95.6% — permite descartar con
> confianza a la mitad de la población."

Si sobra tiempo, el hallazgo que sorprende:

> "La salud autopercibida resultó el factor más fuerte: odds ratio 18.8, por
> encima de presión alta y colesterol. Una pregunta que cuesta cero ordena mejor
> que un análisis de sangre."

### 4:20 – 5:00 · Límites y cierre — *Jesús*

**Digan las limitaciones ustedes primero. Suma credibilidad.**

> "Tres límites: los datos son autorreportados; nuestros odds ratio son crudos,
> no ajustados por confusores; y calibramos y validamos sobre el mismo conjunto."

**Cierre — el ML en 15 segundos, no en un minuto:**

> "Los organizadores permitían machine learning. Probamos un Random Forest: 0.823
> contra nuestro 0.798. **No elegimos entre ML y score: usamos ML para medir el
> techo y el score para la decisión explicable.** Elegimos perder 25 milésimos a
> cambio de un sistema que un médico puede auditar, aplicar en papel y explicarle
> al paciente. Eso es lo que entendemos por justificable."

Si sobran 10 segundos:

> "Y es una herramienta de tamizaje, no de diagnóstico: requiere validación
> clínica antes de cualquier uso real."

---

## Comparación de enfoques (por si la piden)

| Enfoque | Recall | VPP | ROC-AUC | Auditable |
|---|---|---|---|---|
| Score estadístico | **85.5%** | 27.5% | 0.798 | **Sí, factor por factor** |
| Random Forest | — | — | 0.823 | No |

El 0.823 está medido sobre datos **sin deduplicar**, donde parte del conjunto de
prueba son copias exactas del de entrenamiento. No son directamente comparables.

---

## Preguntas probables

**"¿Por qué eliminaron 24,704 registros?"**
> "23,899 eran duplicados exactos. En una encuesta de 22 variables la coincidencia
> idéntica por azar en el perfil sano-modal es esperable, no un error de captura.
> Por eso reportamos ambos escenarios."

**"¿Por qué excluyeron la prediabetes?"**
> "Es un estado intermedio con solo 1.8% de los casos, insuficiente para calibrar
> pesos estables. Lo declaramos como limitación, no lo escondemos."

**"¿Por qué no ajustaron por confusores?"**
> "Es nuestra principal limitación y está declarada. Los odds ratio son crudos,
> así que factores correlacionados aportan puntos de forma parcialmente
> redundante. Con más tiempo, una regresión multivariable daría los pesos
> ajustados."

**"¿Validaron con datos independientes?"**
> "No. Calibramos y validamos sobre el mismo conjunto, y está declarado en el
> documento. Es lo primero que haríamos con más tiempo."

---

## Reglas

1. **Si van tarde, corten metodología.** Nunca el paciente en vivo.
2. **Ningún número que no esté en el PDF.** Todos los de esta guía están verificados.
3. **Si no saben algo:** *"No lo medimos, y no quiero inventar una respuesta."*
   El jurado castiga más el bluff que el "no sé".
