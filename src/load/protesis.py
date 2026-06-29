import pandas as pd
from src.utils.gc_functions import escribir_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT = '1im5bWXvib9uVRGQ5GRFre2gy2S-Jaq9ThPL5lxraYMM'
_RANGO_GRAL   = 'protesis!A1'


def load_protesis_gral(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL, _prepare(df), clear_first=True)
    save_snapshot(df, 'protesis')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    # Int64 (nullable) no acepta fillna('') en gc_functions → convertir a object
    for col in df.columns:
        if str(df[col].dtype) == 'Int64':
            df[col] = df[col].astype(object).where(df[col].notna(), other='')
    return df
