import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_PROYECCION_DIARIA    = '1x0vover_16Q-XQZfJgeGBkfpi_R44PVO7y2x7U8Kz1Y'
_SHEET_PROYECCION_EJERCICIO = '1x0vover_16Q-XQZfJgeGBkfpi_R44PVO7y2x7U8Kz1Y'
_SHEET_RESTO                = '1x0vover_16Q-XQZfJgeGBkfpi_R44PVO7y2x7U8Kz1Y'

_RANGO_PROYECCION_DIARIA    = 'amb_seg_diario!A1'
_RANGO_PROYECCION_EJERCICIO = 'amb_general!A1'
_RANGO_RESTO                = 'amb_resto!A1'


def load_proyeccion_diaria(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_PROYECCION_DIARIA, _RANGO_PROYECCION_DIARIA, _prepare(df), clear_first=True)
    save_snapshot(df, 'amb_seg_diario')


def load_proyeccion_ejercicio(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_PROYECCION_EJERCICIO, _RANGO_PROYECCION_EJERCICIO, _prepare(df), clear_first=True)
    save_snapshot(df, 'amb_general')


def load_resto(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_RESTO, _RANGO_RESTO, _prepare(df), clear_first=True)
    save_snapshot(df, 'amb_resto')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df
