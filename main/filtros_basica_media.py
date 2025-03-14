import pandas as pd

df = pd.read_excel(r"C:\Users\olgac\OneDrive\Desktop\matriculas_media_basica_2020.xlsx")

# Definir el criterio de filtrado (Ejemplo: Filtrar por columna "Categoría")
column_filter = "ENS"

# Definir los filtros
filtro_basica = df[df[column_filter].isin([3, 4, 9])]  # Grupo específico
filtro_media = df[~df[column_filter].isin([1, 2, 3, 4, 9])]  # Todo lo demás

# Guardar los archivos filtrados

if not filtro_basica.empty:
    filtro_basica.to_excel("matricula_basica_2020.xlsx", index=False)
    print("✅ Archivo generado: matricula_basica.xlsx")

if not filtro_media.empty:
    filtro_media.to_excel("matricula_media_2020.xlsx", index=False)
    print("✅ Archivo generado: matricula_basica.xlsx")