import pandas as pd
from .gc_functions import leer_tabla_df

spreadsheet_id = '1l9dP8MK3GN8D1RymJ8Q8u-SRkrQPKmN-4wKChMBpYHQ'

aux_amb_rubros = leer_tabla_df(spreadsheet_id, 'amb_rubro!A1:C19')
aux_amb_subrubros = leer_tabla_df(spreadsheet_id, 'amb_subrubro!A1:D90')

# === Función para mapeo de rubros y subrubros ===
def amb_rubros_subrubros(df)-> pd.DataFrame:
    """
    Mapea rubros y subrubros de Ambulatorio de forma eficiente usando los datos auxiliares.
    """
    # Diccionario de rubros
    dict_rubros = dict(zip(
        aux_amb_rubros["Rubro GE"], 
        aux_amb_rubros["Rubro PPTO"]
    ))
   
    # Diccionario de subrubros
    dict_subrubros = dict(zip(
        aux_amb_subrubros["Rubro&Subrubro GE"], 
        aux_amb_subrubros["Subrubro PPTO"]
    )) 
     
    # Diccionario de subrubros NA
    dict_subrubro_na = dict(zip(
        aux_amb_rubros["Rubro PPTO"], 
        aux_amb_rubros['Subrubro PPTO NAN']
    ))
    
    # Aplicar mapeo
    df["Subrubro PPTO"] = (df["Rubro GE"] + df["Subrubro GE"]).map(dict_subrubros)
    df["Rubro PPTO"] = df["Rubro GE"].map(dict_rubros)
    mask_na = df["Subrubro PPTO"].isna()
    df.loc[mask_na, "Subrubro PPTO"] = df.loc[mask_na, "Rubro PPTO"].map(dict_subrubro_na)
    return df
