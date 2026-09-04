# DEFENSA — Datathon MedData, entrega 4:00 pm

**Lee esto completo (10 min), haz los arreglos de la sección 1 (25 min), memoriza la tarjeta del final.**

Tu motor estadístico está bien. Las 8 cifras del pitch se reproducen exactas desde cero y el AUC calculado a mano coincide con sklearn hasta el último bit. **No vas a caer por las cifras: vas a caer por frases escritas en tus propios archivos que un jurado refuta abriendo un archivo.** Eso es lo que arreglamos ahora.

**Regla de oro para hoy: no toques el binning del IMC, ni la constante B, ni los odds ratio, ni los cortes.** Cambiar cualquiera de esos re-escribe las 8 cifras del pitch, del notebook, de las 3 gráficas y del README. Con 40 minutos eso te deja con diapositivas que no cuadran con el código, que es peor que el problema que arreglas. Todos esos puntos tienen respuesta hablada preparada más abajo.

---

## 1. ARREGLAR YA

Ordenado por impacto. Total: ~25 minutos.

### 1.1 — Falta el entregable que el enunciado pide con todas sus letras (12 min) — MÁXIMA PRIORIDAD

El enunciado dice *"clasifique nuevos pacientes"*. Hoy no existe ninguna función que reciba **un** paciente. El módulo solo puntúa el dataframe con el que se calibró. Es el único hueco de **requisito**, no de calidad.

Pega esto al final de `src/score_diabetes.py`, **antes** del bloque `if __name__ == "__main__":`

```python
# ------------------------------- 8. CLASIFICAR UN PACIENTE NUEVO
# Mismos cortes que la calibracion (seccion 3): resultado identico al pipeline.
PREV_POR_NIVEL = grupos["prev_%"].to_dict()

def _nivel_bmi(b):  return 0 if b <= 25 else 1 if b <= 30 else 2 if b <= 35 else 3
def _nivel_edad(a): return 0 if a <= 4 else 1 if a <= 7 else 2 if a <= 9 else 3 if a <= 11 else 4

def puntuar_paciente(p):
    """Recibe un dict con las 10 variables crudas y devuelve score, nivel de
    riesgo y la prevalencia observada de ese nivel. Falla si un dato no mapea."""
    niveles = {"f_bmi": _nivel_bmi(p["BMI"]), "f_edad": _nivel_edad(p["Age"]),
               "f_salud": int(p["GenHlth"]) - 1,
               **{c: int(p[c]) for c in ("HighBP", "HighChol", "DiffWalk",
                    "HeartDiseaseorAttack", "Stroke", "PhysActivity",
                    "HvyAlcoholConsump")}}
    detalle, score = {}, 0
    for c, lv in niveles.items():
        pts = mapas[c].get(lv, mapas[c].get(float(lv)))
        if pts is None:
            raise ValueError(f"Nivel {lv} no valido para el factor {c}")
        detalle[FACTORES[c]] = int(pts); score += int(pts)
    riesgo = clasificar(score)
    return {"score": score, "riesgo": riesgo,
            "prevalencia_observada_%": PREV_POR_NIVEL[riesgo],
            "derivar": score >= CORTE_DERIVACION, "detalle": detalle}
```

Y dentro de `__main__`, al final:

```python
    ejemplo = {"BMI": 33, "Age": 9, "GenHlth": 3, "HighBP": 1, "HighChol": 1,
               "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
               "PhysActivity": 0, "HvyAlcoholConsump": 0}
    r = puntuar_paciente(ejemplo)
    print(f"\n=== PACIENTE NUEVO (hombre 60-64, IMC 33, salud regular, HTA, colesterol) ===")
    print(f"  Score {r['score']} -> {r['riesgo']} | prevalencia observada {r['prevalencia_observada_%']}% "
          f"| derivar: {'SI' if r['derivar'] else 'NO'}")
    print(f"  Desglose: {r['detalle']}")
```

**Ya lo probé en tu entorno: sale `Score 11 → Alto → 33.1% → derivar SÍ`, y reproduce exactamente el score del pipeline en 500 filas al azar tomadas al azar del dataset.** Puedes decir esa frase en voz alta: *"la función de paciente individual reproduce el score del pipeline, lo verificamos en 500 casos"*.

**Plan B si algo falla en vivo:** ese mismo paciente se suma con lápiz en pantalla — IMC 33 = 2, edad 2, salud regular 3, hipertensión 2, colesterol 2 → **11 puntos, Alto, 33.1%**. Ese es tu mejor momento de la presentación. Ensáyalo.

### 1.2 — Borra las cinco frases que un jurado refuta en 30 segundos (5 min)

| Archivo | Dice | Debe decir |
|---|---|---|
| `src/score_diabetes.py:3` | "los odds ratio **ajustados**" | "los odds ratio **crudos (bivariados)**" |
| `README.md:69` y notebook celda 13 | "el más alto de **las 22 variables**" | "el más alto de **los 10 factores del score**" |
| `README.md:30-32` | "un punto equivale **siempre al mismo incremento de riesgo**" | "B es la unidad de conversión de ln(OR) a puntos; medido sobre nuestra salida, cada punto multiplica los odds por ≈1.45" |
| `README.md:63-65` y notebook celda 13 (Hallazgo 1) | "el 10% del dataset es **ruido duplicado que inflaría cualquier análisis**… **7,838 contradicciones lógicas**… IMC **fisiológicamente imposibles**" | texto nuevo abajo |
| Notebook celda 12 | `← si dice bajo riesgo, acierta 95.6%` (número escrito a mano al lado del calculado) | `← si dice bajo riesgo, acierta esa proporción de las veces` |

**Texto nuevo para el Hallazgo 1** (cópialo tal cual, es tu mejor carta convertida en fortaleza):

> **1. La limpieza de datos es una decisión, no un trámite — y la medimos en las dos direcciones.**
> Encontramos 23,899 filas exactamente repetidas (9.4%), 805 registros con IMC sobre 60 y 7,838 personas sin seguro que no reportan barrera de costo (esto último **no es una contradicción**: es el 63% de los no asegurados, gente que simplemente no necesitó médico ese año; lo conservamos). Verificamos si los duplicados eran errores de captura o colisiones de azar: las filas repetidas tienen 1.0% de diabetes contra 15.3% del resto y cero derrames, o sea el perfil joven-sano modal, la firma de una colisión estadística en una encuesta de 21 variables casi todas binarias. Corrimos el pipeline completo en los dos escenarios: **sin deduplicar el AUC es 0.816; deduplicando, 0.798.** Reportamos la versión conservadora, la que nos deja peor.

### 1.3 — Di los DOS números de población (2 min)

En `README.md:43` y en la diapositiva: **253,680 crudos → 228,976 tras depuración → 224,364 calibrados** (se excluyen 4,612 de prediabetes). Los tres juntos, siempre. Si sumas la columna `n` de tu tabla de estratificación te da 224,364; el jurado lo va a sumar.

### 1.4 — Borra el borrador (30 segundos)

```bash
rm docs/USO_DE_IA_borrador_local.md
```

Sigue en disco (fuera de git, pero viaja en un USB o en un zip). Dice que tu compañero "no registra commits" — falso, el git log muestra 3 — y que el ML está prohibido, contradiciendo tu propia declaración final.

### 1.5 — Alinea la declaración de IA con el código (3 min)

`README.md:87` y `USO_DE_IA.md:28-29` dicen que el dashboard **no usa dependencias externas**. `dashboard/app.py` importa sklearn y entrena Random Forest. Es falsificable abriendo un archivo, y está justo en el documento cuyo único valor es la credibilidad.

- `README.md:87` → "Dashboard interactivo (servidor con librería estándar; la sección de comparación usa scikit-learn)"
- `USO_DE_IA.md:28-29` → "servidor HTTP con librería estándar; la comparación con machine learning usa scikit-learn"

Y añade este párrafo al README, que convierte el problema en argumento:

> Los organizadores confirmaron que el ML está permitido. Lo usamos solo como contraste: un Random Forest sobre el dataset **crudo** alcanza AUC 0.823 frente a 0.798 del score. Esos 25 milésimos cuestan un modelo que nadie aplica en papel ni audita, y además ese 0.823 está medido sobre datos sin deduplicar, donde el 12% del conjunto de prueba son copias exactas del de entrenamiento. No son comparables.

### 1.6 — Decisión sobre el dashboard: NO lo abras

No comparte una sola cifra con tu score (nunca importa `score_diabetes.py`). En pantalla muestra 253,680 registros, 13.9% de prevalencia, un panel de calidad que dice literalmente *"No se detectaron campos vacíos o reglas especiales en esta fuente"* — justo en el reto que pide identificar inconsistencias — y un Random Forest que le gana a tu score. Además tarda 10 s en frío y un fetch fallido mata la página hasta un F5.

**No es parte de la presentación.** Si el jurado lo pide, ver pregunta 4.

---

## 2. LAS 6 PREGUNTAS MÁS PROBABLES

Respuestas para decir en voz alta. Frases cortas. No leas de corrido: quédate con los números en negrita.

### P1. "¿Sobre cuánta gente están hablando? Veo 253,680, 228,976 y si sumo su tabla me da 224,364."

> "Los tres son correctos y debimos declararlos juntos: **253,680 crudos, 228,976 tras depuración, 224,364 calibrados** porque el modelo excluye 4,612 de prediabetes. Todas las métricas, el VPN incluido, están sobre 224,364.
>
> Y las dos decisiones que llevan de un número al otro las tratamos como análisis de sensibilidad, no como limpieza obvia. **Deduplicación: sin deduplicar el AUC es 0.816 y la estratificación separa 13.4 veces; deduplicando, 0.798 y 11.2 veces.** Reportamos la versión que nos deja peor. **Prediabetes: si la contamos como caso, la sensibilidad baja de 85.5% a 84.1% y el VPN de 95.6% a 94.6%** — el sistema no depende de haberla excluido. De hecho el score deriva al 73% de los prediabéticos sin haberlos usado nunca para calibrar."

### P2. "Su código dice odds ratio AJUSTADOS y su función es una tabla 2x2. Y le restan un punto al que hace ejercicio."

Concede de inmediato. No discutas.

> "Tiene razón, y son dos cosas distintas. La primera es un error de redacción nuestro: son **odds ratio crudos, bivariados**, y así hay que llamarlos. Ya está corregido.
>
> La segunda es de fondo y la medimos. Ajustando por regresión logística multivariable, **presión alta baja de 4.6 a 2.1, dificultad para caminar de 3.4 a 1.15, y actividad física pasa de 0.55 a 0.97 — o sea deja de existir**. Ese menos uno es confusión por edad y comorbilidad, no un efecto protector. Es la corrección número uno de nuestra lista.
>
> Elegimos ORs crudos a propósito para que un médico pueda recalcular cualquier celda con una tabla de dos por dos y un lápiz. **Y medimos el costo: la versión ajustada da AUC 0.8016 contra nuestro 0.7976. Cuatro milésimas.** Lo que la versión cruda no aguanta es la interpretación puntual del coeficiente, y por eso el odds ratio de salud autopercibida hay que leerlo como **6.9 ajustado**, no 18.8 crudo."

### P3. "Su punto no vale 2.12. Y B cuelga de una sola celda."

> "Correcto, y la frase está mal escrita en nuestro notebook. **2.12 es e elevado a B: una propiedad de la construcción, no del comportamiento del score sumado.** El valor empírico, midiendo la pendiente del logit de la prevalencia sobre el score, es **alrededor de 1.45 por punto**. La razón es que sumamos log-ORs de factores correlacionados, así que cada punto adicional vale menos de lo que la fórmula sugiere.
>
> Sobre B, tiene razón y es la debilidad conocida del método. Al ser un mínimo es el estimado más ruidoso de la tabla y no es invariante frente al conjunto de variables. **Colesterol alto cae a tres milésimas de la frontera de redondeo: en bootstrap recibe 2 puntos en la mitad de los remuestreos.** Por eso la lectura honesta es que colesterol y salud regular tienen incertidumbre de más o menos un punto, y que **la sensibilidad está entre 78% y 88%**, no en un 85.5% con un decimal. La corrección correcta es fijar B a priori, como hace Framingham. Lo probamos con B = 0.5 y ORs ajustados: el error de la promesa cae de 49% a 2%, el rango se comprime de 0-18 a 0-13 y el AUC sube a 0.8016.
>
> Lo que sí sostenemos sin matices es el **orden**: las prevalencias por estrato son observadas, no extrapoladas. 4.4%, 17.9%, 33.1%, 49.2%."

### P4. "Voy a abrir su dashboard."

Adelántate antes de que lo proyecte.

> "Antes de abrirlo se lo describo yo, porque lo auditamos nosotros. **Nuestra solución es `src/score_diabetes.py`.** El dashboard es un anexo exploratorio construido en paralelo sobre el dataset crudo y **no debe leerse como validación del score**: usa otro denominador, otra definición de caso y no importa el motor de puntuación.
>
> Sobre el AUC 0.823 que verá ahí: **no es válido, y le decimos por qué. Como ese anexo no deduplica, más del 12% del conjunto de prueba son copias exactas de filas de entrenamiento.** Es fuga de datos, y es exactamente por eso que sale más alto que nuestro 0.798, que sí está medido sobre datos limpios. Lo dejamos documentado como limitación, no como resultado."

### P5. "Su desenlace es 'un médico le dijo'. Su score predice contacto con el sistema de salud, y le resta puntos al que no tiene acceso."

La pregunta más seria. Concede el constructo, defiende el uso.

> "Tiene razón en el constructo y lo decimos de frente: nuestro desenlace es **diabetes diagnosticada**, y con BRFSS no podemos medir detección de casos nuevos porque el no diagnosticado está codificado como negativo. Por eso esto **no es un test diagnóstico: es un priorizador de a quién le hacemos la glucemia primero cuando no alcanza para todos.** Para ese uso, ordenar bien es suficiente.
>
> Dos evidencias de que ordena riesgo metabólico real y no memoria de diagnóstico. Una: **el score deriva al 73% de los prediabéticos, y los prediabéticos nunca entraron en la calibración.** Dos: **si quitamos los cuatro factores de tipo 'le dijeron que' — presión, colesterol, cardiopatía, derrame — y dejamos solo lo que cualquiera responde sin haber visto un médico, el AUC baja de 0.798 a 0.769.** El poder no vive en el historial clínico, vive en la edad y en la salud autopercibida.
>
> Y el sesgo de acceso lo medimos en vez de suponerlo: **sin seguro la sensibilidad es 82% frente a 85.7% con seguro.** Por eso proponemos dos versiones del mismo instrumento con la misma tabla: la de diez factores donde hay registro clínico, y la de seis para gira rural y población sin seguro. La validación que usted necesita antes de cualquier despliegue es una HbA1c contra el score en una muestra suya; ese es el siguiente paso."

### P6. "Deriva al 48% de la población. Mi red no aguanta. Y la regla de la ADA es gratis y detecta más."

Aquí ganas. Lleva estos números.

> "El 7 no es una propiedad del sistema: **es la perilla de política sanitaria.** El score es una escala y el corte lo fija su capacidad instalada. **Corte 7: 48.3% derivado, 85.5% de sensibilidad, 3.6 pruebas por caso. Corte 9: 30.6% y 67.6%. Corte 11: 16.4% derivado, 43.9% de sensibilidad y VPP de 41.7%.** Con su restricción de 16 mil pruebas por cada 100 mil tamizados, su corte es 11. Le entregamos la frontera de decisión completa, no un umbral.
>
> Sobre la regla de la ADA, la comparamos: **la ADA da 87.1% de sensibilidad derivando al 66.5% de la población; nuestro score da 85.5% derivando al 48.3%. Son 18,200 pruebas confirmatorias evitadas por cada 100,000 tamizados, a cambio de 1.6 puntos de sensibilidad. El VPP sube de 20.4% a 27.5%.** Y si prefiere igualar sensibilidad en vez de ahorrar, bajamos a corte 6: 91.4%, cuatro puntos por encima de la ADA, todavía derivando nueve puntos menos de población. **En los dos puntos de operación el score domina a la regla vigente.** Además la ADA no estratifica: dice sí o no. Nosotros entregamos cuatro grupos de 4.4%, 17.9%, 33.1% y 49.2%, que es lo que permite ordenar una cola de laboratorio que no alcanza para todos."

**Si además preguntan por los jóvenes** (sensibilidad muy baja en menores de 45): concede sin cifra exacta si no la mediste tú. *"En menores de 45 nuestra sensibilidad cae a menos de la mitad, porque el binning de edad les da cero puntos y la prevalencia de ese grupo es 4.5% contra 22% en mayores de 65. Un corte único perjudica a los jóvenes. La solución es un corte estratificado por edad — más bajo en jóvenes, más alto en mayores de 65 — y un override clínico obligatorio: menor de 45 con IMC sobre 30 se deriva aunque el score diga bajo, igual que hace la ADA. Un score que no se puede sobrescribir con juicio clínico no debería usarse en consulta."*

---

## 3. DÓNDE NO HAY DEFENSA

Estos golpes se encajan. **Reconocerlos rápido y con precisión suma; inventar una excusa destruye.** Frases exactas:

1. **El menos 1 por actividad física.** — *"Ajustado, ese odds ratio es 0.97. No es un efecto protector, es confusión. Sale del score."* No lo defiendas con literatura general sobre ejercicio: la pregunta no es si el ejercicio protege, es si tu dato lo sostiene, y no lo sostiene.

2. **"Odds ratio ajustados" en el código.** — *"Es un error de redacción y ya está corregido: son crudos bivariados."* Punto. No lo expliques más.

3. **"1 punto = OR 2.12".** — *"Esa cifra es e elevado a B, no el comportamiento del score. El valor real es 1.45. La frase está mal enunciada y la retiramos."*

4. **Los tres N.** — *"Error de orden de operaciones: el contador de filas finales se fija antes de excluir prediabetes. Los dos números correctos son 228,976 y 224,364."*

5. **El binning del IMC** (si alguien nota que 30.0 cae en "sobrepeso"). — *"Usamos intervalos cerrados por la derecha; la convención OMS es la contraria. Lo detectamos en nuestra propia auditoría: con el corte OMS el AUC sube a 0.8017 y la sensibilidad a 88.1%. No lo cambiamos a última hora para no entregar cifras distintas de las que auditamos, y va como primera corrección."* Esto suma: demuestra que auditaste tu propio trabajo y que la corrección te favorece.

6. **No pueden medir casos nuevos detectados.** — *"Con BRFSS no se puede: el no diagnosticado está codificado como negativo. No prometemos detección de casos nuevos; prometemos identificación de perfil de riesgo, y la validación con HbA1c es el paso obligado antes de desplegar."*

7. **El dashboard.** — *"Es un anexo exploratorio que no comparte pipeline con el score. Debió estar etiquetado como tal y no lo estaba."*

8. **"7,838 contradicciones lógicas".** — *"Retiramos la palabra contradicción: son el 63% de los no asegurados comportándose de forma perfectamente coherente. El hallazgo que sí está en los datos y no habíamos contado es que 16,775 personas CON seguro sí reportan barrera de costo: copagos y deducibles."*

---

## 4. ARGUMENTO DE CIERRE

> **Construimos un instrumento de diez preguntas que se aplica con lápiz, sin laboratorio y sin computadora, y que ordena a 224 mil personas en cuatro grupos con 4.4%, 17.9%, 33.1% y 49.2% de prevalencia observada — AUC 0.798 calculado a mano por Mann-Whitney, reproducible en medio segundo y auditable celda por celda.**
>
> **Frente a la regla de tamizaje que hoy se usa, alcanzamos prácticamente la misma sensibilidad derivando 18 puntos menos de población: 18,200 pruebas confirmatorias evitadas por cada 100,000 personas tamizadas, con el valor predictivo positivo subiendo de 20% a 27.5%.**
>
> **Y cada decisión que tomamos está medida en las dos direcciones, incluso cuando el resultado no nos favorece: nuestra limpieza de datos nos costó 18 milésimas de AUC y la reportamos igual. Eso es lo que significa que una solución sea justificable.**

---

## TARJETA DE BOLSILLO

**Verificado hoy corriendo el código (puedes decir "lo medimos"):**

| | |
|---|---|
| AUC | **0.7976** (Mann-Whitney a mano = sklearn = trapezoidal) |
| Sens / Esp / VPP / VPN | 85.5% / 58.5% / 27.5% / 95.6% |
| Estratificación | 4.4 / 17.9 / 33.1 / 49.2 (separa 11.2x) |
| Poblaciones | 253,680 → 228,976 → 224,364 |
| **Sin deduplicar** | **AUC 0.8158**, sens 86.2%, VPN 96.4%, estratos 3.6/16.6/31.7/48.1 (separa **13.4x**), n=248,261 |
| Paciente ejemplo | IMC 33 + 60-64 años + salud regular + HTA + colesterol = **11 pts → Alto → 33.1%** |
| Optimismo (70/30, 30 particiones) | ≈ 0 (entrena 0.7981 / prueba 0.7986) |

**De la auditoría — di "lo estimamos" si no puedes reproducirlo en vivo:** OR ajustados (GenHlth 6.9, HighBP 2.07, DiffWalk 1.15, PhysActivity 0.97) · AUC ajustado 0.8016 · OR empírico por punto ≈1.45 · bootstrap HighChol 2 pts en ~50% · sin las 4 variables "le dijeron" AUC 0.769 · prediabéticos derivados 73% · ADA 87.1% derivando 66.5% · cortes 9→30.6%/67.6%, 11→16.4%/43.9%/VPP 41.7% · sin seguro sens 82.0% vs 85.7%.