import requests
import pandas as pd
# URL para la descarga del archivo XLS (ajustar fechas según sea necesario)
from io import StringIO
def get_url(fondo):
    return f"https://www.spensiones.cl/apps/valoresCuotaFondo/vcfAFPxls.php?aaaaini=2005&aaaafin=2025&tf={fondo}&fecconf=20241231"


# Hacer la solicitud GET


def load_file(url):
        response = requests.get(url)
        data=StringIO(response.text)
        return pd.read_csv(data,sep=';',names=range(15))



def get_retornos_flujos(url):
    datos_original=load_file(url)
    index_super=datos_original.loc[(datos_original.iloc[:,0]=="Valores Confirmados") | (datos_original.iloc[:,0]=="Valores Provisorios - Sujetos a Confirmación"),:].index
    index_iter=pd.DataFrame({'sup':index_super}).assign(inf=lambda df_:df_.sup.shift(-1).fillna(datos_original.shape[0]))
    datos_fix=pd.DataFrame()
    for inf, sup in zip(index_iter.inf,index_iter.sup):
        if inf==0:
            inf=sup
        else:
            inf=int(inf)
        datos_filter=datos_original.iloc[int(inf):int(sup),:].reset_index()
        cols_name=(datos_filter.iloc[0,:].fillna(method="ffill")+datos_filter.iloc[1,:])
        cols_name[0]="fecha"
        datos_filter.columns=cols_name
        datos_filter=(
            datos_filter
            .iloc[3:,1:]
            .set_index("fecha")
            .stack()
            .rename('mmus')
            .reset_index()
            .assign(
                afp=lambda df_: df_["level_1"].str.split("Valor").str[0].str.strip(),
                tipo=lambda df_: df_["level_1"].str.split("Valor").str[1].str.strip(),
                valor=lambda df_: df_['mmus'].str.replace(".", "").str.replace(",", ".").astype(float)
            )
            .drop(["level_1"],axis=1)
        )
        datos_fix=pd.concat([datos_filter,datos_fix])
    return datos_fix


datos_full=list()
for fondo in 'ABCDE':
    datos_full.append(get_retornos_flujos(get_url(fondo)).assign(fondo=fondo))

datos_full=pd.concat(datos_full)

