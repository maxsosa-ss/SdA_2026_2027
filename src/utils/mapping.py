import pandas as pd
from .gc_functions import leer_tabla_df

_SPREADSHEET_ID = '1l9dP8MK3GN8D1RymJ8Q8u-SRkrQPKmN-4wKChMBpYHQ'

_aux_amb_rubros = None
_aux_amb_subrubros = None


def _get_aux_amb():
    """Carga (una sola vez, perezosamente) los auxiliares de rubros/subrubros desde Sheets."""
    global _aux_amb_rubros, _aux_amb_subrubros
    if _aux_amb_rubros is None:
        _aux_amb_rubros = leer_tabla_df(_SPREADSHEET_ID, 'amb_rubro!A1:C19')
        _aux_amb_subrubros = leer_tabla_df(_SPREADSHEET_ID, 'amb_subrubro!A1:D90')
    return _aux_amb_rubros, _aux_amb_subrubros


# === Función para mapeo de rubros y subrubros ===
def amb_rubros_subrubros(df)-> pd.DataFrame:
    """
    Mapea rubros y subrubros de Ambulatorio de forma eficiente usando los datos auxiliares.
    """
    aux_amb_rubros, aux_amb_subrubros = _get_aux_amb()

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
