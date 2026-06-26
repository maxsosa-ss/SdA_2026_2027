import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT  = '1p7bvTZtdYbDwh4YYiLbE1knIicBlU6VeWmq1pX2YNiA'
_RANGO_GRAL    = 'prov_gral!A1'
_RANGO_DIARIO  = 'prov_diario!A1'


def load_prov_gral(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL, _prepare(df), clear_first=True)
    save_snapshot(df, 'prov_gral')


def load_prov_diario(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_DIARIO, _prepare(df), clear_first=True)
    save_snapshot(df, 'prov_diario')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df
