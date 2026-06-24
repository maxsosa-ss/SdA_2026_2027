import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT    = '1DNpmKUjIOuHPCBrMN8Ww5xlmJ1XQAvGcH3wMFujvMNU'
_RANGO_DIARIO    = 'farmvac_seg_diario!A1'
_RANGO_GRAL_Q    = 'farmvac_gral_Q!A1'
_RANGO_GRAL_IMP  = 'farmvac_gral_imp!A1'


def load_proyeccion_diaria(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_DIARIO, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_seg_diario')


def load_proyeccion_ejercicio(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL_Q, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_gral_q')


def load_proyeccion_importe(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL_IMP, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_gral_imp')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df
