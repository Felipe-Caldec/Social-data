import pandas as pd

# Leer el archivo con los decimales con coma
df = pd.read_csv(r"C:\Users\olgac\OneDrive\Desktop\base_rendimiento_2023.csv", sep=';')

# Reemplazar coma por punto en la columna y convertir a float
df['PROM_GRAL'] = df['PROM_GRAL'].str.replace(',', '.').astype(float)

# Guardar nuevo CSV limpio
df.to_csv("base_rendimiento_2023l.csv")