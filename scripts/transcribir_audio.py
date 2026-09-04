import sys, json, time, os
import mlx_whisper
from mlx_whisper.writers import get_writer

AUDIO   = sys.argv[1]
MODEL   = sys.argv[2]
OUTDIR  = sys.argv[3]
NAME    = sys.argv[4]

PROMPT = (
    "Datatón MedData del congreso CONTEC de la Universidad Tecnológica de Panamá, "
    "organizado por la rama estudiantil IEEE EMBS (Engineering in Medicine and Biology Society), "
    "que ve las aplicaciones de la ingeniería en la medicina y la biología. "
    "Hackathon, datatón, reto, challenge, equipos, reglamento, rúbrica, entregable, break, refrigerio. "
    "El challenge se llama «Transformando datos médicos en soluciones inteligentes» y trata sobre diabetes. "
    "Se entrega un dataset con miles de registros de pacientes; hay que detectar patrones, "
    "identificar inconsistencias, analizar factores clínicos, generar un sistema de puntuación (score) "
    "y clasificar nuevos pacientes usando únicamente reglas matemáticas y métodos estadísticos, sin machine learning. "
    "Se permite el uso de inteligencia artificial generativa: Claude, Claude Code, ChatGPT, Codex, Copilot, Gemini, OpenCode, "
    "siempre que se documente y se sustente el prompt utilizado. "
    "Facultad de Ingeniería de Sistemas Computacionales, decano, coordinador de extensión, "
    "grupo de WhatsApp, código QR, currículum, habilidades blandas."
)

os.makedirs(OUTDIR, exist_ok=True)
t0 = time.time()
res = mlx_whisper.transcribe(
    AUDIO,
    path_or_hf_repo=MODEL,
    language="es",
    task="transcribe",
    initial_prompt=PROMPT,
    condition_on_previous_text=False,      # evita arrastrar errores entre bloques
    temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),  # fallback si el bloque sale mal
    compression_ratio_threshold=1.9,       # dispara el fallback ante repeticiones
    logprob_threshold=-1.0,
    no_speech_threshold=0.55,
    word_timestamps=True,
    hallucination_silence_threshold=1.5,   # salta silencios donde alucina "y y y..."
    verbose=None,
)
dt = time.time() - t0

for fmt in ("txt", "srt", "vtt", "json"):
    get_writer(fmt, OUTDIR)(res, NAME + ".wav", {
        "highlight_words": False, "max_line_width": None,
        "max_line_count": None, "max_words_per_line": None,
    })
print(f"\n[OK] {MODEL} -> {OUTDIR}/{NAME}.*  ({dt:.1f}s, {len(res['segments'])} segmentos)")
