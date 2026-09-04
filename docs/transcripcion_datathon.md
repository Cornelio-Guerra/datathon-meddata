# Transcripción — Apertura del Datatón MedData (CONTEC, UTP)

**Fuente:** `data/Universidad Tecnológica de Panamá.m4a` — 10 min 10 s, mono, AAC 66 kbps.
**Método:** 4 pasadas de Whisper en Apple Silicon (`mlx-whisper`), consolidadas por consenso.
Detalle del procedimiento al final del documento. Las instrucciones destiladas del reto están en
[`instrucciones_datathon.md`](instrucciones_datathon.md).

**Convenciones**

- `[mm:ss]` = marca de tiempo del audio.
- `[?]` = palabra o nombre que las cuatro pasadas no resuelven con seguridad.
- `[…]` = fragmento inaudible o pisado por otra voz.
- Los nombres propios y siglas se normalizan al término real (EMBS, CONTEC, Claude, Codex…);
  cuando el audio es realmente ambiguo se deja marcado.

---

## 1. Bienvenida — Rama estudiantil IEEE EMBS `[00:00 – 01:02]`

**Organizadora (IEEE EMBS):**

> `[00:00]` […] de la rama de **EMBS**, que es la rama que ve las aplicaciones de la ingeniería en medicina y biología.
>
> `[00:07]` Es la primera hackathon que hace EMBS, así que la verdad estoy muy agradecida por todos los que se inscribieron.
>
> `[00:15]` Bueno, obviamente ya es la hackathon número no sé cuánto de **CONTEC**, pero especialmente de parte de EMBS pues estamos muy agradecidos por haber aceptado el reto.
>
> `[00:27]` Espero que les vaya muy bien a todos. Yo traté de que sea un reto ni tan complicado pero tampoco tan fácil, porque la gran mayoría son de sistemas. Así que espero que les vaya muy bien.

**Coordinador del congreso CONTEC:**

> `[00:40]` Mi nombre es […] `[?]`, espero que ya la mayoría de ustedes me conozcan. Soy el coordinador actual del congreso de la facultad, del **CONTEC**, el Congreso de Tecnología y Ciencia.
>
> `[00:51]` Y bueno, espero que les vaya bien en este mini-hackathon que vamos a tener hoy, y que puedan resolver el reto que mencionamos.

---

## 2. Palabras del coordinador de extensión `[01:10 – 03:25]`

**Prof. Picota** *(el audio alterna entre "Juan" y "Pablo"; el apellido se oye claramente como Picota)* — coordinador de extensión, Facultad de Ingeniería de Sistemas Computacionales:

> `[01:10]` Bueno chicos, ¿cómo están? Buenas tardes. […] Para los que no me conocen, mi nombre es **[Juan/Pablo] Picota** `[?]`, yo estoy como coordinador de extensión en la Facultad de Sistemas, y de parte del señor decano y de toda la administración de la facultad queremos, primero, darles las gracias por aceptar el reto.
>
> `[01:29]` Entrar a una hackathon… si es tu primera hackathon, levanta la mano. ¿Es su primera hackathon? Excelente.
>
> `[01:39]` Si es tu primera hackathon, es interesante y a la vez retador: no sabes lo que va a pasar. Tienes una idea más o menos de lo que te explicaron, de lo que tienes que hacer, pero hasta que veas el reto en realidad no te vas a dar cuenta de qué va la cosa, de qué es lo que tienes que aplicar y lo que tienes que hacer.
>
> `[01:55]` Yo quiero felicitarlos por aceptar eso. No es cualquiera el que lo hace. Dense cuenta que ustedes […] `[…]`. Ustedes se atrevieron, tomaron el reto, y eso ya es el beneficio, eso ya es el *profit*.
>
> `[02:14]` Ustedes van a aprender algunas habilidades interesantes: en la resolución de problemas, en el trabajo en equipo, y en adaptarse a una situación desconocida.
>
> `[02:26]` ¿Ya saben ustedes cuál es el reto? ¿Ya se lo dieron? No, ¿verdad? Entonces, cuando vean, cuando abran el paquete, cuando abran la caja de Pandora, van a tener que adaptarse; van a tener que utilizar todas las habilidades mentales, emocionales y de investigación para buscar la solución en el tiempo que tienen, que es un tiempo bastante corto.
>
> `[02:45]` Yo les deseo la mejor de la suerte. Los invito a seguir participando, no solamente en temas de CONTEC sino en todas las actividades que la facultad prepara para ustedes.
>
> `[02:55]` Porque al final, lo que ustedes están haciendo es currículum. Todo esto que ustedes están haciendo no es para tomarme una foto a mí, sino para que ustedes tengan qué poner en su hoja de vida: son habilidades blandas, habilidades de investigación, habilidades de tecnología, habilidades de manejo de personal, manejo de estrés. Todo eso es lo que tú vas a ver en esas ofertas laborales, y estas acciones los van a ayudar a eso.
>
> `[03:20]` La mejor de la suerte, muchachos, y que gane el mejor.

---

## 3. Pausa / conversación de sala `[03:30 – 05:45]`

Tramo sin contenido del reto: micrófono abierto sobre conversaciones sueltas del staff
(equipo, cables, hora, quién habla después). Whisper produce texto poco fiable aquí en
todas las pasadas; se omite por no aportar información del datatón.

Único dato de contexto recuperable: `[04:09]` *"Nada más la bienvenida, no has dicho nada… no hay tiempo para hablar la parte técnica."*

---

## 4. ⭐ Reglamento del datatón `[05:52 – 07:23]`

**Organizador:**

> `[05:52]` Bueno chicos, voy a presentar más o menos cómo es el reglamento del **datatón**.
>
> `[05:57]` El challenge que viene se trata sobre **diabetes**. El challenge se llama **"Transformando datos médicos en soluciones inteligentes"**.
>
> `[06:09]` Bueno, ya saben el nombre del datatón, quiénes lo organizan… **El horario es hasta las 4:00 para resolver el reto**, y ya saben la temática.
>
> `[06:20]` **El dataset, en unos minutos, se les va a estar enviando al WhatsApp**, al grupo de WhatsApp creado […] `[?]`.
>
> `[06:38]` Y bueno, ya sabemos que estamos en el **2026**: **tienen permitido cualquier tipo de uso de inteligencia artificial generativa** — ya sea **Claude**, **Codex**, **OpenCode** y demás. **Nada más que tienen que estar sustentados y documentados.**
>
> `[06:56]` No pueden decir que no es posible —obvio, eso lo creo yo—; **tiene que estar una parte donde diga "usé tal herramienta"**, más o menos, **y si usaron algún prompt en específico** y demás.
>
> `[07:14]` A las 3:00 – 3:30 van a tener un pequeño break, un **coffee break**.

---

## 5. ⭐ Enunciado del reto `[07:50 – 08:30]`

> `[07:50]` El sistema de salud necesita una herramienta capaz de analizar automáticamente **miles de registros de pacientes** y **detectar patrones relacionados con la diabetes**.
>
> `[08:03]` Su equipo deberá desarrollar un **sistema de puntuación** que:
> - **procese los datos**,
> - **identifique inconsistencias**,
> - **analice factores clínicos**,
> - **genere un sistema de puntuación**, y
> - **clasifique nuevos pacientes**
>
> `[08:17]` …**utilizando únicamente reglas matemáticas y métodos estadísticos**.
>
> `[08:23]` **El equipo que presente la solución más precisa, eficiente y justificable será el ganador.**

> **Nota de transcripción:** en `[08:03]` el orador dice literalmente *"un sistema puntuacional"*
> (así en las cuatro pasadas); en `[08:14]` repite *"un sistema de puntuación"*.

---

## 6. Cierre `[08:41 – 09:30]`

**Prof. Picota:**

> `[08:41]` Bueno, espero que den lo mejor de ustedes. En verdad esto es una oportunidad para que ustedes puedan verse y ponerse a prueba en lo que son capaces de hacer, porque al final —aunque sea la inteligencia artificial lo que utilicen— al final lo que importa es la idea que ustedes tengan, lo que ustedes quieran dar.
>
> `[09:05]` Al final, obviamente, aquí hay ganadores, pero para mí, y yo siempre lo voy a decir, **todos son ganadores**: todos tienen ese esfuerzo, esas ganas de probarse a sí mismos, de competir, de entender sus ideas, de comprender las soluciones que vienen con el problema. Eso es lo importante.
>
> `[09:23]` Así que un éxito a todos, y que en verdad dé lo mejor cada uno. Muchas gracias.

---

## Anexo — Cómo se generó esta transcripción

En la Mac no hay CUDA, así que el equivalente al comando de whisper con `--device cuda` es
`mlx-whisper`, que corre sobre Metal en Apple Silicon.

Se hicieron cuatro pasadas y se consolidaron por consenso:

| # | Modelo | Audio | Prompt de dominio | Rol |
|---|--------|-------|-------------------|-----|
| 1 | `large-v3-turbo` | crudo | no | Sondeo: descubrir el vocabulario real (~46 s) |
| 2 | `large-v3-turbo` | filtrado | sí | Descartada: el filtrado provocó bucles de alucinación (~104 s) |
| 3 | `large-v3-turbo` | crudo | sí | Aportó "2026" y "el horario es hasta las 4" (~104 s) |
| 4 | **`large-v3`** | crudo | sí | Pasada de referencia: aportó "ingeniería" (no "minería") y "será el ganador" (~7 min) |

Comando de la pasada de referencia (equivalente en Mac al de la PC):

```bash
# Instalación:  pip install mlx-whisper   (y  brew install ffmpeg)
# Audio a 16 kHz mono:
ffmpeg -i "audio.m4a" -ac 1 -ar 16000 -c:a pcm_s16le audio.wav

mlx_whisper audio.wav \
  --model mlx-community/whisper-large-v3-mlx \
  --language es --task transcribe \
  --condition-on-previous-text False \
  --compression-ratio-threshold 1.9 \
  --word-timestamps True \
  --hallucination-silence-threshold 1.5 \
  --output-format all --output-dir transcripciones \
  --initial-prompt "Datatón MedData del congreso CONTEC de la Universidad Tecnológica de Panamá, organizado por la rama estudiantil IEEE EMBS..."
```

Equivalencias con el comando de la PC:

| PC (whisper + CUDA) | Mac (mlx-whisper + Metal) |
|---|---|
| `--model large-v3` | `--model mlx-community/whisper-large-v3-mlx` |
| `--device cuda` | (implícito: Metal) |
| `--language Spanish` | `--language es` |
| `--condition_on_previous_text False` | `--condition-on-previous-text False` |
| `--compression_ratio_threshold 1.9` | `--compression-ratio-threshold 1.9` |
| `--output_format all` | `--output-format all` |
| `--initial_prompt "..."` | `--initial-prompt "..."` |

Dos ajustes añadidos que el comando original no tiene y que aquí importaron:
`--word-timestamps True` + `--hallucination-silence-threshold 1.5`, para cortar los bucles
de repetición que Whisper genera en los tramos de silencio y conversación de fondo
(minutos 3:30–5:45 de esta grabación).

Salidas crudas de la pasada de referencia (sin editar) en
[`transcripciones_crudas/`](transcripciones_crudas/): `.txt`, `.srt`, `.vtt` y `.json` con
tiempos por palabra.
