# Snippets de supervivencia — Datathon MedData

Chuleta para copiar y pegar bajo presión. Ordenada por lo que más vas a necesitar.
`Cmd+F` es tu amigo.

---

## 0. Arranque en 30 segundos

```python
import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns
pd.set_option("display.max_columns", 50)
sns.set_theme(style="whitegrid")

df = pd.read_csv("../data/archivo.csv")
df.shape, df.info(), df.describe().T
```

Lectura cuando el CSV viene torcido:

```python
pd.read_csv(p, sep=";")                                # separador punto y coma
pd.read_csv(p, encoding="latin-1")                     # UnicodeDecodeError / acentos rotos
pd.read_csv(p, na_values=["?", "NA", "", "-", "N/A"])  # nulos disfrazados
pd.read_csv(p, decimal=",")                            # números "3,14"
pd.read_csv(p, header=None, names=["a","b","c"])       # sin encabezado
pd.read_excel(p, sheet_name=0)                         # .xlsx
```

---

## 1. `value_counts` — el más rentable

```python
df["col"].value_counts()                        # conteos
df["col"].value_counts(normalize=True) * 100    # PORCENTAJES  <- el que citas al jurado
df["col"].value_counts(dropna=False)            # incluye NaN
df["col"].value_counts(normalize=True).round(3).mul(100)

# Numérica continua -> por rangos
pd.cut(df["edad"], bins=[0,18,40,60,120],
       labels=["0-18","19-40","41-60","60+"]).value_counts().sort_index()
pd.qcut(df["glucosa"], q=4).value_counts().sort_index()   # cuartiles

# Cruce de dos categóricas con % por fila
pd.crosstab(df["sexo"], df["target"], normalize="index").round(3) * 100
```

---

## 2. `groupby` — de dónde salen los hallazgos

```python
df.groupby("grupo")["valor"].mean()
df.groupby("grupo")["valor"].agg(["count","mean","median","std","min","max"]).round(2)

# Varias columnas, varias funciones, con nombres limpios
df.groupby("grupo").agg(
    n=("id", "count"),
    edad_media=("edad", "mean"),
    tasa_evento=("target", "mean"),      # media de un 0/1 = TASA. Úsalo mucho.
).round(3).sort_values("tasa_evento", ascending=False)

df.groupby(["sexo","fumador"])["target"].mean().unstack().round(3)
df.groupby("grupo", as_index=False)["valor"].sum()      # grupo como columna, no índice
df.groupby("grupo", dropna=False)                        # no tirar los NaN

# transform: devuelve la misma longitud (para crear columnas)
df["media_del_grupo"] = df.groupby("grupo")["valor"].transform("mean")
df["desv_vs_grupo"]   = df["valor"] - df["media_del_grupo"]
```

---

## 3. `pivot_table`

```python
pd.pivot_table(df, index="sexo", columns="target",
               values="edad", aggfunc="mean").round(2)

pd.pivot_table(df, index="work_type", columns="sexo", values="stroke",
               aggfunc=["mean","count"], margins=True,   # margins = totales
               fill_value=0).round(3)

# Pivot listo para heatmap
tabla = pd.pivot_table(df, index="a", columns="b", values="target", aggfunc="mean")
sns.heatmap(tabla, annot=True, fmt=".2f", cmap="coolwarm")
```

---

## 4. `merge` / concat

```python
pd.merge(a, b, on="id", how="left")                    # left | inner | outer | right
pd.merge(a, b, left_on="id_pac", right_on="paciente_id", how="inner")
pd.merge(a, b, on="id", how="left", suffixes=("_a","_b"))

# SIEMPRE valida: si las filas crecen, tenías duplicados en la llave
print(a.shape, "->", pd.merge(a, b, on="id", how="left").shape)
pd.merge(a, b, on="id", how="left", validate="one_to_one")   # revienta si no lo es
pd.merge(a, b, on="id", how="outer", indicator=True)["_merge"].value_counts()

pd.concat([df1, df2], ignore_index=True)   # apilar filas
pd.concat([df1, df2], axis=1)              # pegar columnas
```

---

## 5. Fechas

```python
df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")   # lo que falle -> NaT
df["fecha"] = pd.to_datetime(df["fecha"], dayfirst=True)     # DD/MM/AAAA
df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d") # más rápido y estricto

df["anio"]     = df["fecha"].dt.year
df["mes"]      = df["fecha"].dt.month
df["dia_sem"]  = df["fecha"].dt.dayofweek        # 0=lunes
df["nom_mes"]  = df["fecha"].dt.month_name()
df["periodo"]  = df["fecha"].dt.to_period("M")   # agrupar por mes

df["dias_estancia"] = (df["fecha_alta"] - df["fecha_ingreso"]).dt.days
df["edad"] = ((pd.Timestamp("today") - df["nacimiento"]).dt.days / 365.25).astype(int)

df[df["fecha"].between("2020-01-01", "2020-12-31")]

# Serie temporal
df.set_index("fecha").resample("M")["casos"].sum().plot()
```

---

## 6. Nulos y duplicados

```python
df.isna().sum().sort_values(ascending=False)
(df.isna().mean()*100).round(2)                 # % de nulos

df["col"] = df["col"].fillna(df["col"].median())          # numérica
df["col"] = df["col"].fillna(df["col"].mode()[0])         # categórica
df["col"] = df["col"].fillna("Desconocido")
df = df.dropna(subset=["target"])                          # sin target no sirve
df = df.drop(columns=df.columns[df.isna().mean() > 0.5])   # >50% nulo, fuera

# Nulos disfrazados de cero (clásico en datos clínicos)
df[["Glucose","BloodPressure","BMI"]] = df[["Glucose","BloodPressure","BMI"]].replace(0, np.nan)

# Imputar por grupo (mejor que la mediana global)
df["bmi"] = df.groupby("sexo")["bmi"].transform(lambda s: s.fillna(s.median()))

df.duplicated().sum()
df = df.drop_duplicates().reset_index(drop=True)
df = df.drop_duplicates(subset=["id"], keep="first")
```

---

## 7. Encoding

```python
# One-hot (lo normal)
df = pd.get_dummies(df, columns=["sexo","work_type"], drop_first=True, dtype=int)
df = pd.get_dummies(df, drop_first=True, dtype=int)   # todas las object de golpe

# Binaria a mano
df["fuma"] = df["fuma"].map({"Yes":1, "No":0})
df["target"] = (df["num"] > 0).astype(int)            # binarizar escala 0-4

# Ordinal con orden REAL
orden = {"leve":0, "moderado":1, "grave":2}
df["sev"] = df["severidad"].map(orden)

# Muchas categorías: quédate con el top N
top = df["ciudad"].value_counts().nlargest(10).index
df["ciudad"] = df["ciudad"].where(df["ciudad"].isin(top), "Otros")

from sklearn.preprocessing import LabelEncoder      # SOLO para el target
y = LabelEncoder().fit_transform(df["clase"])
```

> Trampa: si codificas antes de partir train/test y luego el test tiene una
> categoría que el train no vio, las columnas no coinciden. Codifica el DataFrame
> completo *antes* del `train_test_split`, o usa `X_test.reindex(columns=X_train.columns, fill_value=0)`.

---

## 8. Escalado

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

sc = StandardScaler()            # media 0, desv 1  (el default)
X_train_sc = sc.fit_transform(X_train)   # fit SOLO con train
X_test_sc  = sc.transform(X_test)        # test solo transform  <- no lo olvides

MinMaxScaler()   # a rango [0,1]
RobustScaler()   # usa mediana/IQR: mejor si hay outliers fuertes

# Conservando el DataFrame (para seguir viendo nombres de columnas)
X_train_sc = pd.DataFrame(sc.fit_transform(X_train),
                          columns=X_train.columns, index=X_train.index)
```

Quién necesita escalado: **LogisticRegression, SVM, KNN, redes → SÍ.**
**Árboles / RandomForest / GradientBoosting → NO hace falta.**

---

## 9. Modelado exprés

```python
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score

X, y = df.drop(columns=["target"]), df["target"]
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)   # stratify SIEMPRE en clasificación

m = RandomForestClassifier(n_estimators=300, class_weight="balanced",
                           random_state=42, n_jobs=-1).fit(X_tr, y_tr)
pred = m.predict(X_te)

print(classification_report(y_te, pred, digits=3))
print(confusion_matrix(y_te, pred))
print("AUC:", roc_auc_score(y_te, m.predict_proba(X_te)[:,1]).round(3))

# Importancia de variables -> material directo para tus hallazgos
pd.Series(m.feature_importances_, index=X.columns).sort_values(ascending=False).head(10)

# Dirección del efecto (la da la logística, no el bosque)
lr = LogisticRegression(max_iter=1000, class_weight="balanced").fit(X_tr_sc, y_tr)
pd.Series(lr.coef_[0], index=X.columns).sort_values(key=abs, ascending=False).head(10)

# Validación cruzada si te sobra tiempo (normalmente no te sobra)
cross_val_score(m, X, y, cv=5, scoring="roc_auc").mean().round(3)
```

**Clases desbalanceadas** (ej. stroke: 5% positivos): el accuracy miente — predecir
"todos sanos" da 95%. Usa `class_weight="balanced"`, y reporta **recall de la clase 1** y **ROC-AUC**.

---

## 10. Gráficas de un renglón

```python
df["col"].hist(bins=30)
df[num_cols].hist(figsize=(14,10), bins=30); plt.tight_layout()

sns.boxplot(data=df, x="target", y="edad")
sns.countplot(data=df, x="target")
sns.barplot(data=df, x="grupo", y="valor")           # con IC automático
sns.scatterplot(data=df, x="edad", y="glucosa", hue="target")
sns.histplot(data=df, x="edad", hue="target", kde=True, multiple="stack")

sns.heatmap(df.corr(numeric_only=True), annot=True, fmt=".2f", cmap="coolwarm", center=0)
df.corr(numeric_only=True)["target"].drop("target").sort_values(key=abs, ascending=False)

plt.title("..."); plt.xlabel("..."); plt.ylabel("...")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("../outputs/gr.png", dpi=110, bbox_inches="tight")
```

---

## 11. Selección y filtrado

```python
df[df["edad"] > 60]
df[(df["edad"] > 60) & (df["sexo"] == "M")]        # & | ~ y PARÉNTESIS obligatorios
df[df["ciudad"].isin(["A","B"])]
df.query("edad > 60 and sexo == 'M'")               # más legible
df.loc[df["edad"] > 60, ["id","edad"]]              # .loc = etiquetas
df.iloc[0:5, 0:3]                                   # .iloc = posiciones

df.nlargest(10, "valor"); df.nsmallest(10, "valor")
df.sort_values(["a","b"], ascending=[True, False])

df["cat"] = np.where(df["edad"] > 60, "mayor", "menor")
df["cat"] = np.select([df.e<18, df.e<65], ["menor","adulto"], default="mayor")

df = df.rename(columns={"viejo":"nuevo"})
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")   # limpia nombres
```

---

## 12. Errores que te van a salir mañana

| Error | Causa | Arreglo |
|---|---|---|
| `KeyError: 'col'` | nombre con espacio/mayúscula | `df.columns.tolist()` y compara |
| `SettingWithCopyWarning` | asignas sobre un slice | usa `.loc[fila, col] = x` o `.copy()` |
| `ValueError: could not convert string to float` | texto en columna numérica | `pd.to_numeric(df.c, errors="coerce")` |
| `ValueError: Input contains NaN` | nulos al hacer `.fit()` | imputa **antes** de modelar |
| `ValueError: could not convert string to float: 'Male'` | categóricas sin codificar | `pd.get_dummies(...)` |
| `Found input variables with inconsistent numbers of samples` | X e y de distinto largo | filtraste uno y no el otro |
| `ValueError: The truth value of a Series is ambiguous` | usaste `and`/`or` | usa `&` / `|` con paréntesis |
| `ConvergenceWarning` en LogisticRegression | no escalaste | `StandardScaler` + `max_iter=1000` |
| El gráfico no aparece | falta mostrarlo | `plt.show()` |
| `MemoryError` / va lentísimo | dataset grande | `df.sample(20000)` para explorar |

---

## 13. Guardar resultados

```python
df.to_csv("../outputs/limpio.csv", index=False)      # index=False SIEMPRE
df.to_excel("../outputs/resultado.xlsx", index=False)
resumen.round(3).to_markdown()                        # tabla lista para pegar en slides
```

---

## 14. Antes de exponer — checklist de 60 segundos

- [ ] ¿Puedo decir el **shape** del dataset y el **% de la clase positiva**?
- [ ] ¿Tengo **3 números concretos** que respalden mis 3 hallazgos?
- [ ] ¿Mis gráficas tienen **título y ejes con nombre**?
- [ ] ¿Dije qué **recomendaría hacer** con cada hallazgo, no solo qué vi?
- [ ] ¿Mencioné **una limitación**? (suma credibilidad, no la resta)
