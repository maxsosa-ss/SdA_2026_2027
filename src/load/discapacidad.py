import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT = '12Em-k3tmAlhWLYjW1d62J8a8x3o63lYFFQvZ4f9KTIM'
_RANGO_GRAL   = 'discapacidad!A1'


def load_disca_gral(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL, _prepare(df), clear_first=True)
    save_snapshot(df, 'discapacidad')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    # Int64 (nullable) no es compatible con fillna('') en gc_functions; convertir a object
    for col in df.select_dtypes(include='Int64').columns:
        df[col] = [int(v) if pd.notna(v) else '' for v in df[col]]
    return df
