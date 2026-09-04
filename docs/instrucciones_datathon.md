# Datatón MedData — Instrucciones del reto

> Extraído de la grabación de la apertura (`data/Universidad Tecnológica de Panamá.m4a`, 10:10 min).
> Transcripción completa y literal en [`transcripcion_datathon.md`](transcripcion_datathon.md).

## Identificación

| | |
|---|---|
| **Evento** | Datatón / hackathon dentro del congreso **CONTEC** (Congreso de Tecnología y Ciencia), Universidad Tecnológica de Panamá |
| **Organiza** | Rama estudiantil **IEEE EMBS** *(Engineering in Medicine and Biology Society)* — "la rama que ve las aplicaciones de la ingeniería en medicina y biología". Es su **primera** hackathon |
| **Facultad** | Ingeniería de Sistemas Computacionales |
| **Nombre del challenge** | **"Transformando datos médicos en soluciones inteligentes"** |
| **Tema** | Diabetes |

## Reglas operativas

- **Hora límite de entrega: 4:00 p. m.** (min. 6:14 del audio: *"el horario es hasta las 4 para resolver el reto"*).
- **Break** entre las **3:00 y 3:30 p. m.**
- El **dataset se envía por WhatsApp**, al grupo creado para el evento — no se descarga de otro lado.
- Se trabaja **en equipo**.

## Uso de IA generativa — permitido, pero con condiciones

> *"Ya sabemos que estamos en el 2026: tienen permitido cualquier tipo de uso de inteligencia artificial generativa, ya sea Claude, Codex, OpenCode y demás. Nada más que tienen que estar sustentados y documentados."*

Reglas concretas:

1. **Está permitido** usar cualquier IA generativa (Claude / Claude Code, Codex, OpenCode, etc.).
2. **Es obligatorio documentarlo**: debe existir una parte del entregable donde se declare qué herramienta se usó.
3. **Hay que sustentarlo**: incluir los **prompts específicos** relevantes que se utilizaron.
4. No vale ocultarlo ni negar que se usó.

## El enunciado del reto

> El sistema de salud necesita una herramienta capaz de analizar automáticamente **miles de registros de pacientes** y **detectar patrones relacionados con la diabetes**.
>
> Su equipo deberá desarrollar un **sistema de puntuación** que:
> 1. **Procese los datos**
> 2. **Identifique inconsistencias**
> 3. **Analice factores clínicos**
> 4. **Genere un sistema de puntuación (score)**
> 5. **Clasifique nuevos pacientes**
>
> …utilizando **únicamente reglas matemáticas y métodos estadísticos**.
>
> El equipo que presente la solución **más precisa, eficiente y justificable** será el ganador.

## Restricción crítica

**"Únicamente reglas matemáticas y métodos estadísticos"** — esto excluye modelos de machine learning entrenados (clasificadores aprendidos, árboles, random forest, boosting, redes neuronales). Lo que se pide es un **score interpretable**, construido a mano a partir del análisis estadístico de los factores clínicos.

## Criterios de evaluación

El jurado premia la solución que sea, en el orden explícito del enunciado:

1. **Precisa** — que clasifique bien.
2. **Eficiente** — que procese los miles de registros sin desperdicio.
3. **Justificable** — que cada punto del score tenga una razón estadística/clínica defendible.

## Checklist de entregable

- [ ] Limpieza de datos y reporte de **inconsistencias** encontradas.
- [ ] Análisis de **factores clínicos** (asociación de cada variable con diabetes).
- [ ] **Sistema de puntuación** con pesos justificados estadísticamente.
- [ ] **Punto de corte** para clasificar pacientes nuevos, con su justificación.
- [ ] **Métricas** de desempeño del score.
- [ ] Sección de **declaración de uso de IA** con herramientas y prompts.
