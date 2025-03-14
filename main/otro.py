"""df = pd.read_csv(r"C:\Users\olgac\OneDrive\Desktop\20230906.csv", sep=";", quotechar='"')



# Lista de columnas que el modelo espera (ajústala según tu modelo)
columnas_modelo = ["AGNO", "RBD", "NOM_RBD", "COD_REG_RBD", "NOM_REG_RBD_A","COD_PRO_RBD",
                   "COD_COM_RBD", "NOM_COM_RBD", "COD_DEPROV_RBD", "NOM_DEPROV_RBD",
                   "COD_DEPE2","RURAL_RBD","COD_ENSE2","COD_GRADO2","MRUN","EDAD_ALU","COD_COM_ALU",
                   "NOM_COM_ALU","ENS"]     
    
# 3️⃣ Eliminar espacios en los nombres de las columnas por si hay problemas
df.columns = df.columns.str.strip()

# 4️⃣ Verificar qué columnas del modelo realmente existen en el CSV
columnas_disponibles = [col for col in columnas_modelo if col in df.columns]
columnas_faltantes = [col for col in columnas_modelo if col not in df.columns]

print("\n Columnas que se usarán:", columnas_disponibles)
print(" Columnas que faltan en el CSV y serán ignoradas:", columnas_faltantes)

# 5️⃣ Filtrar solo las columnas disponibles
df_filtrado = df[columnas_disponibles]

# 6️⃣ Aplicar el filtro para la Región 13 (si la columna existe)
if "COD_REG_RBD" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["COD_REG_RBD"] == 13]
else:
    print("\n Advertencia: No se encontró la columna 'COD_REG_RBD', no se aplicó el filtro de región.")

# 7️⃣ Definir el tamaño máximo por archivo (para evitar el límite de Excel)
max_filas = 1_000_000  

# 8️⃣ Dividir el archivo en varios CSV más pequeños
num_archivo = 1
for i in range(0, len(df_filtrado), max_filas):
    archivo_salida = f"matriculas_RM_2023_parte{num_archivo}.csv"
    df_filtrado.iloc[i:i + max_filas].to_csv(archivo_salida, index=False, sep=";")
    print(f"\n📂 Guardado: {archivo_salida}")
    num_archivo += 1

print("\n🎉 Archivos divididos y guardados con éxito.")"""


def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        print(f"Dry Run: {dry_run}")  # Para verificar si está en ejecución real
        if not dry_run:  # Solo ejecuta en importación real
            for row in dataset.dict:  # Itera sobre cada fila del dataset
                print("Fila procesada:", row)  # Verifica la fila antes de insertarla
