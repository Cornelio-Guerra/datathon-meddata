"""
Sistema de puntuacion de riesgo de diabetes — SIN machine learning.
Metodo: Sullivan et al. (framework de Framingham): los odds ratio crudos
(bivariados) se
convierten en puntos enteros dividiendo por una constante de referencia.
Solo estadistica descriptiva, tablas de contingencia y aritmetica.
"""
import numpy as np, pandas as pd
from pathlib import Path

# Ruta absoluta respecto a este archivo: funciona desde cualquier carpeta
# (raiz, notebooks/ o dashboard/)
RAIZ = Path(__file__).resolve().parent.parent
RUTA = RAIZ / "data" / "diabetes_012_health_indicators_BRFSS2015.csv"

# ---------------------------------------------------------------- 1. CARGA
df = pd.read_csv(RUTA)
n0 = len(df)

# ---------------------------------------------------- 2. INCONSISTENCIAS
inconsistencias = {
    "duplicados_exactos":      int(df.duplicated().sum()),
    "bmi_fuera_de_rango":      int(((df.BMI < 12) | (df.BMI > 60)).sum()),
    "sin_seguro_sin_costo":    int(((df.AnyHealthcare == 0) & (df.NoDocbcCost == 0)).sum()),
    "dias_malestar_invalidos": int(((df.MentHlth > 30) | (df.PhysHlth > 30)).sum()),
}

# Limpieza: quitamos duplicados y BMI fisiologicamente imposible
df = df.drop_duplicates().reset_index(drop=True)
df = df[(df.BMI >= 12) & (df.BMI <= 60)].reset_index(drop=True)
inconsistencias["filas_eliminadas"] = n0 - len(df)
inconsistencias["filas_finales"] = len(df)

# Target: diabetes confirmada (clase 2). La prediabetes (1) se excluye del
# ajuste por ser un estado intermedio con solo 1.8% de los casos.
df = df[df.Diabetes_012 != 1].copy()
df["dm"] = (df.Diabetes_012 == 2).astype(int)

# ------------------------------------------------- 3. FACTORES Y NIVELES
# Cada factor se discretiza en niveles clinicamente interpretables.
df["f_bmi"]  = pd.cut(df.BMI, [0, 25, 30, 35, 100], labels=[0, 1, 2, 3]).astype(int)
df["f_edad"] = pd.cut(df.Age, [0, 4, 7, 9, 11, 13], labels=[0, 1, 2, 3, 4]).astype(int)
df["f_salud"] = df.GenHlth.astype(int) - 1          # 0..4
FACTORES = {
    "f_bmi":    "IMC",
    "f_edad":   "Edad",
    "f_salud":  "Salud autopercibida",
    "HighBP":   "Presion alta",
    "HighChol": "Colesterol alto",
    "DiffWalk": "Dificultad para caminar",
    "HeartDiseaseorAttack": "Enfermedad cardiaca",
    "Stroke":   "Derrame previo",
    "PhysActivity": "Actividad fisica",
    "HvyAlcoholConsump": "Consumo alto de alcohol",
}

# ------------------------------------- 4. ODDS RATIO -> PUNTOS (Sullivan)
def odds_ratio(sub, ref_mask, lvl_mask):
    a = sub.loc[lvl_mask, "dm"].mean(); b = sub.loc[ref_mask, "dm"].mean()
    if not (0 < a < 1 and 0 < b < 1): return np.nan
    return (a / (1 - a)) / (b / (1 - b))

tabla = []
for col, nombre in FACTORES.items():
    niveles = sorted(df[col].unique())
    ref = niveles[0]
    for lv in niveles:
        orr = odds_ratio(df, df[col] == ref, df[col] == lv)
        tabla.append({"factor": col, "nombre": nombre, "nivel": lv,
                      "n": int((df[col] == lv).sum()),
                      "prev_%": round(df.loc[df[col] == lv, "dm"].mean() * 100, 1),
                      "OR": round(orr, 3) if orr == orr else 1.0,
                      "ln_OR": round(np.log(orr), 4) if orr == orr and orr > 0 else 0.0})
T = pd.DataFrame(tabla)

# Constante de referencia: el menor ln(OR) positivo distinto de cero.
# Cada punto del score equivale a ese incremento de riesgo -> puntos enteros.
B = T.loc[T.ln_OR > 0.01, "ln_OR"].min()
T["puntos"] = (T.ln_OR / B).round().astype(int).clip(lower=-3)

# --------------------------------------------- 5. SCORE POR PACIENTE
mapas = {c: dict(zip(g.nivel, g.puntos)) for c, g in T.groupby("factor")}
df["SCORE"] = sum(df[c].map(m).fillna(0) for c, m in mapas.items()).astype(int)

# ------------------------------------ 6. UMBRALES CLINICOS
# El corte de derivacion NO se elige maximizando accuracy, sino por el costo
# clinico del error: en tamizaje un falso negativo es un paciente que se va sin
# diagnostico; un falso positivo solo genera una prueba confirmatoria barata.
# Por eso se prioriza sensibilidad. Corte >=7: sensibilidad 85.5%.
CORTE_DERIVACION = 7
cortes = [6, 9, 12]          # Bajo <=6 | Moderado 7-9 | Alto 10-12 | Muy alto >=13
def clasificar(s):
    if s <= cortes[0]: return "Bajo"
    if s <= cortes[1]: return "Moderado"
    if s <= cortes[2]: return "Alto"
    return "Muy alto"
df["RIESGO"] = df.SCORE.apply(clasificar)
df["DERIVAR"] = (df.SCORE >= CORTE_DERIVACION).astype(int)

# ------------------------------------------------- 7. VALIDACION (a mano)
grupos = (df.groupby("RIESGO").dm.agg(n="size", casos="sum", prev="mean")
            .reindex(["Bajo", "Moderado", "Alto", "Muy alto"]))
grupos["prev_%"] = (grupos.prev * 100).round(1)
grupos = grupos.drop(columns="prev")

# Metricas para el corte "Alto o mas", calculadas con aritmetica pura
pos = df.SCORE >= CORTE_DERIVACION
VP = int((pos & (df.dm == 1)).sum()); FP = int((pos & (df.dm == 0)).sum())
FN = int((~pos & (df.dm == 1)).sum()); VN = int((~pos & (df.dm == 0)).sum())
sens = VP / (VP + FN); esp = VN / (VN + FP)
vpp = VP / (VP + FP); vpn = VN / (VN + FN)

# AUC por el metodo de Mann-Whitney (rangos), sin sklearn
r = df.SCORE.rank()
n1, n0_ = int(df.dm.sum()), int((df.dm == 0).sum())
auc = (r[df.dm == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0_)

# ------------------------------- 8. CLASIFICAR UN PACIENTE NUEVO
# El enunciado pide "clasifique nuevos pacientes". Usa los mismos mapas de puntos
# y los mismos cortes de la calibracion: resultado identico al del pipeline.
PREV_POR_NIVEL = grupos["prev_%"].to_dict()

def _nivel_bmi(b):  return 0 if b <= 25 else 1 if b <= 30 else 2 if b <= 35 else 3
def _nivel_edad(a): return 0 if a <= 4 else 1 if a <= 7 else 2 if a <= 9 else 3 if a <= 11 else 4

def puntuar_paciente(p):
    """Recibe un dict con las 10 variables crudas y devuelve score, nivel de
    riesgo y la prevalencia observada de ese nivel."""
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


if __name__ == "__main__":
    print("=== INCONSISTENCIAS DETECTADAS ===")
    for k, v in inconsistencias.items(): print(f"  {k:26s}: {v:,}")
    print("\n=== TABLA DE PUNTUACION ===")
    print(T[["nombre","nivel","n","prev_%","OR","puntos"]].to_string(index=False))
    print(f"\nConstante de calibracion B = {B:.4f}  (1 punto = OR de {np.exp(B):.2f})")
    print(f"\nRango del score: {df.SCORE.min()} a {df.SCORE.max()}")
    print(f"Cortes de categoria: {cortes}  | corte de derivacion: >={CORTE_DERIVACION}")
    print(f"Poblacion derivada: {df.DERIVAR.mean()*100:.1f}%")
    print("\n=== ESTRATIFICACION DE RIESGO ===")
    print(grupos.to_string())
    print(f"\n=== VALIDACION (corte de derivacion: score >= {CORTE_DERIVACION}) ===")
    print(f"  Sensibilidad : {sens*100:.1f}%   (detecta {VP:,} de {VP+FN:,} diabeticos)")
    print(f"  Especificidad: {esp*100:.1f}%")
    print(f"  VPP          : {vpp*100:.1f}%")
    print(f"  VPN          : {vpn*100:.1f}%")
    print(f"  AUC (Mann-Whitney, sin sklearn): {auc:.4f}")
    T.to_csv(RAIZ / "outputs" / "tabla_puntuacion.csv", index=False)

    ejemplo = {"BMI": 33, "Age": 9, "GenHlth": 3, "HighBP": 1, "HighChol": 1,
               "DiffWalk": 0, "HeartDiseaseorAttack": 0, "Stroke": 0,
               "PhysActivity": 0, "HvyAlcoholConsump": 0}
    r = puntuar_paciente(ejemplo)
    print("\n=== CLASIFICAR UN PACIENTE NUEVO ===")
    print("  Perfil: 60-64 anios, IMC 33, salud regular, hipertension, colesterol alto")
    print(f"  Score {r['score']} -> {r['riesgo']} | prevalencia observada {r['prevalencia_observada_%']}%"
          f" | derivar: {'SI' if r['derivar'] else 'NO'}")
    print(f"  Desglose: {r['detalle']}")
