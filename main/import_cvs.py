import pandas as pd

df = pd.read_csv(r"C:\Users\olgac\OneDrive\Desktop\base_docentes_2020.csv",sep=";", quotechar='"',encoding="utf-8")


# 2️⃣ Eliminar columnas que no están en 'columnas_modelo'
columnas_modelo = ["AGNO","NOM_RBD","COD_REG_RBD", "NOM_REG_RBD_A", "COD_PRO_RBD", "COD_COM_RBD",
                   "NOM_COM_RBD", "COD_DEPROV_RBD", "NOM_DEPROV_RBD", "COD_DEPE","COD_DEPE2", "RURAL_RBD",
                    "DC_A","HH_A","DC_UTP","HH_UTP","DC_PDIR","HH_PDIR","DC_DIR","HH_DIR","DC_OES","HH_OES",
                    "DC_OF","HH_OF","DC_JUTP","HH_JUTP","DC_IG","HH_IG","DC_OR","HH_OR","DC_DIR_SOST","HH_DIR_SOST",
                    "DC_TP_SOST","HH_TP_SOST","DC_SUP_SOST","HH_SUP_SOST","DC_SUBDIR","HH_SUBDIR",
                    "DC_PROF_ENC","HH_PROF_ENC","DC_EDUC_TRAD","HH_EDUC_TRAD","DC_TOT","HH_TOT"]

# Filtrar solo las columnas que necesitas
df = df[columnas_modelo]

df.to_csv(r"C:\Users\olgac\OneDrive\Desktop\base_docentes_2020_filtrado.csv", sep=";", index=False, encoding="utf-8")