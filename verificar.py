import pandas as pd


path = "data/diabetes_012_health_indicators_BRFSS2015.csv"
df = pd.read_csv(path)
print(path, df.shape)
print("columnas", len(df.columns))
print("target", df["Diabetes_012"].value_counts().sort_index().to_dict())
