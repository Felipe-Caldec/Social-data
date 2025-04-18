import pandas as pd
from decimal import Decimal, InvalidOperation

df = pd.read_csv(r"C:\Users\olgac\OneDrive\Desktop\base_rendimiento_2023l.csv",sep=",", quotechar='"')


# 2️⃣ Eliminar columnas que no están en 'columnas_modelo'
columnas_modelo = ["AGNO","RBD","NOM_RBD", "COD_REG_RBD", "COD_PRO_RBD", "COD_COM_RBD",
                   "NOM_COM_RBD", "COD_DEPE2", "COD_DEPE","COD_ENSE2", "RURAL_RBD","GEN_ALU", "MRUN",
                   "EDAD_ALU", "NOM_COM_ALU", "COD_JOR", "PROM_GRAL", "ASISTENCIA", "SIT_FIN_R"]   


# Filtrar solo las columnas que necesitas
df = df[columnas_modelo]

#  Definir el tamaño máximo por archivo (máximo permitido por Excel)
max_rows = 800_570  

# Guardar los datos en diferentes archivos Excel y verificar el conteo de filas
filas_guardadas_total = 0
print(f"Total de filas en el dataset: {len(df)}")  # Verificar la cantidad total de filas antes de guardar

for i, start_row in enumerate(range(0, len(df), max_rows)):
    archivo_salida = f"C:\\Users\\olgac\\OneDrive\\Desktop\\base_rendimiento_2023_parte_{i+1}.csv"
    final_row = min(start_row + max_rows, len(df))  # Asegurarse de no exceder las filas disponibles
    
    # Verificar los rangos de las filas seleccionadas
    print(f"Guardando filas {start_row} a {final_row} en {archivo_salida}")
    selected_rows = df.iloc[start_row:final_row]
    print(f"Filas seleccionadas: {selected_rows.shape[0]}")
    
    # Guardar archivo
    selected_rows.reset_index(drop=True).to_csv(archivo_salida, index=False)
    
    # Contar filas guardadas
    filas_guardadas = selected_rows.shape[0]
    filas_guardadas_total += filas_guardadas
    print(f"✅ Archivo guardado: {archivo_salida}. Filas guardadas en este archivo: {filas_guardadas}")

# Verificación final
print(f"\nTotal de filas procesadas y guardadas: {filas_guardadas_total}")
