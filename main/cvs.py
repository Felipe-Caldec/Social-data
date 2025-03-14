import pandas as pd


# 1️⃣ Cargar el archivo CSV
df = pd.read_csv(r"C:\Users\olgac\OneDrive\Desktop\matricula_basica_media_2020.csv", sep=";", quotechar='"')

# 2️⃣ Eliminar columnas que no están en 'columnas_modelo'
columnas_modelo = ["AGNO", "RBD", "NOM_RBD","GEN_ALU", "COD_REG_RBD", "NOM_REG_RBD_A", "COD_PRO_RBD",
                   "COD_COM_RBD", "NOM_COM_RBD", "COD_DEPROV_RBD", "NOM_DEPROV_RBD",
                   "COD_DEPE2", "RURAL_RBD", "COD_ENSE2", "COD_GRADO2", "MRUN", "EDAD_ALU",
                   "COD_COM_ALU", "NOM_COM_ALU", "ENS"]   

# Filtrar solo las columnas que necesitas
df = df[columnas_modelo]

# 3️⃣ Definir los filtros para 'ENS'
column_filter = "ENS"

# Filtro para Básica (valores: 3, 4, 9)
filtro_basica = df[df[column_filter].isin([3, 4, 9])]

# Filtro para Media (valores excluidos: 1, 2, 3, 4, 9)
filtro_media = df[~df[column_filter].isin([1, 2, 3, 4, 9])]

# 4️⃣ Verificar el número de filas en cada filtro
print(f"Filas en filtro_basica: {len(filtro_basica)}")
print(f"Filas en filtro_media: {len(filtro_media)}")

# 5️⃣ Definir el tamaño máximo por archivo (máximo permitido por Excel)
max_rows = 550_570  

# 6️⃣ Guardar los filtros en diferentes archivos Excel y verificar el conteo de filas

# Para el filtro 'Básica'
filas_basica = 0
print(f"Total de filas en filtro_basica: {len(filtro_basica)}")  # Verificar la cantidad total de filas antes de guardar

for i, start_row in enumerate(range(0, len(filtro_basica), max_rows)):
    archivo_salida = f"C:\\Users\\olgac\\OneDrive\\Desktop\\matriculas_basica_2020_parte_{i+1}.xlsx"
    
    # Calcular la última fila del rango para evitar desbordamientos
    final_row = min(start_row + max_rows, len(filtro_basica))  # Asegurarse de no exceder las filas disponibles
    
    # Verificar los rangos de las filas seleccionadas
    print(f"Guardando filas {start_row} a {final_row} en {archivo_salida}")
    
    # Verificar las filas seleccionadas
    selected_rows = filtro_basica.iloc[start_row:final_row]  # Usar .iloc para asegurar el índice correcto
    print(f"Filas seleccionadas: {selected_rows.shape[0]}")  # Imprimir la cantidad de filas seleccionadas
    
    # Comprobar algunas filas seleccionadas
    print(f"Primeras filas seleccionadas: \n{selected_rows.head()}")
    
    # Reiniciar el índice antes de guardar para evitar errores de filas
    selected_rows.reset_index(drop=True).to_excel(archivo_salida, index=False, engine="openpyxl")
    
    # Sumar filas guardadas
    filas_guardadas = selected_rows.shape[0]
    filas_basica += filas_guardadas  # Sumar filas guardadas
    print(f"✅ Archivo guardado: {archivo_salida}. Filas guardadas en este archivo: {filas_guardadas}")

# Para el filtro 'Media'
filas_media = 0
print(f"Total de filas en filtro_media: {len(filtro_media)}")  # Verificar la cantidad total de filas antes de guardar

for i, start_row in enumerate(range(0, len(filtro_media), max_rows)):
    archivo_salida = f"C:\\Users\\olgac\\OneDrive\\Desktop\\matriculas_media_2020_parte_{i+1}.xlsx"
    
    # Calcular la última fila del rango para evitar desbordamientos
    final_row = min(start_row + max_rows, len(filtro_media))  # Asegurarse de no exceder las filas disponibles
    
    # Verificar los rangos de las filas seleccionadas
    print(f"Guardando filas {start_row} a {final_row} en {archivo_salida}")
    
    # Verificar las filas seleccionadas
    selected_rows = filtro_media.iloc[start_row:final_row]  # Usar .iloc para asegurar el índice correcto
    print(f"Filas seleccionadas: {selected_rows.shape[0]}")  # Imprimir la cantidad de filas seleccionadas
    
    # Comprobar algunas filas seleccionadas
    print(f"Primeras filas seleccionadas: \n{selected_rows.head()}")
    
    # Reiniciar el índice antes de guardar para evitar errores de filas
    selected_rows.reset_index(drop=True).to_excel(archivo_salida, index=False, engine="openpyxl")
    
    # Sumar filas guardadas
    filas_guardadas = selected_rows.shape[0]
    filas_media += filas_guardadas  # Sumar filas guardadas
    print(f"✅ Archivo guardado: {archivo_salida}. Filas guardadas en este archivo: {filas_guardadas}")

# Verificar que las filas coinciden
total_filas = len(filtro_basica) + len(filtro_media)
print(f"\nFilas originales en filtro_basica: {len(filtro_basica)}")
print(f"Filas originales en filtro_media: {len(filtro_media)}")
print(f"Total de filas procesadas: {total_filas}")