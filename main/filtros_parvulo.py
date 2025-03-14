import pandas as pd

df = pd.read_excel(r"C:\Users\olgac\OneDrive\Desktop\bases_matricula_educacion\parvulo_2020\matricula_parvulo_2020.xlsx")

# Definir el criterio de filtrado (Ejemplo: Filtrar por columna "Categoría")
column_filter = "cod_reg_estab"

# Definir los filtros
filtro_13 = df[df[column_filter] == 13]  # Solo 13
filtro_norte = df[df[column_filter].isin([1, 2, 3, 4, 5, 15])]  # Grupo específico
filtro_sur = df[~df[column_filter].isin([13, 1, 2, 3, 4, 5, 15])]  # Todo lo demás

# Guardar los archivos filtrados
if not filtro_13.empty:
    filtro_13.to_excel("matricula_parvulo_rm_2020.xlsx", index=False)
    print("✅ Archivo generado: matricula_parvulo_13.xlsx")

if not filtro_norte.empty:
    filtro_norte.to_excel("matricula_parvulo_norte_2020.xlsx", index=False)
    print("✅ Archivo generado: matricula_parvulo_norte.xlsx")

if not filtro_sur.empty:
    filtro_sur.to_excel("matricula_parvulo_sur_2020.xlsx", index=False)
    print("✅ Archivo generado: matricula_parvulo_sur.xlsx")