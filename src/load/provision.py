import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT  = '1p7bvTZtdYbDwh4YYiLbE1knIicBlU6VeWmq1pX2YNiA'
# Rangos deliberadamente más anchos que las columnas que efectivamente
# escribe la pipeline, para que clear_first=True pise cualquier columna
# vieja con fórmulas manuales que haya quedado más a la derecha (p.ej.
# Auxiliar/Proyección Corregida/Día Semana/Periodo de versiones anteriores).
_RANGO_GRAL      = 'prov_gral!A1:Z1000'
_RANGO_DIARIO    = 'prov_diario!A1:Z1000'
_RANGO_NC        = 'NC!A1:Z1000'
_RANGO_DROGUERIA = 'drogueria!A1:Z1000'


def load_prov_gral(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL, _prepare(df), clear_first=True)
    save_snapshot(df, 'prov_gral')


def load_prov_diario(df: pd.DataFrame) -> None:
    # 'Proyección Importe' no se muestra en Sheets (no se usa), pero se
    # conserva en el snapshot SQLite porque prov_drogueria() y otras
    # consultas históricas la necesitan.
    df_sheet = df.drop(columns=['Proyección Importe'])
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_DIARIO, _prepare(df_sheet), clear_first=True)
    save_snapshot(df, 'prov_diario')


def load_prov_nc(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_NC, _prepare(df), clear_first=True)
    save_snapshot(df, 'prov_nc')


def load_prov_drogueria(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_DROGUERIA, _prepare(df), clear_first=True)
    save_snapshot(df, 'prov_drogueria')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df
