import pandas as pd
from src.utils.gc_functions import escribir_tabla_df, leer_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT     = '10R2K2tOtMjVDaModPg4cEVoDnundpysvDhhq1itFHI0'
_RANGO_SAN        = 'sanatorial!A1'
_RANGO_QUIR       = 'quirurgicas!A1'
_RANGO_CONS_SAN   = 'consolidado_sanatorial'
_RANGO_CONS_QUIR  = 'consolidado_quirurgicas'


def load_sanatorial(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_SAN, _prepare(df), clear_first=True)
    save_snapshot(df, 'internaciones_sanatorial')


def load_quirurgicas(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_QUIR, _prepare(df), clear_first=True)
    save_snapshot(df, 'internaciones_quirurgicas')


def load_consolidado_sanatorial(df: pd.DataFrame) -> None:
    _load_consolidado(df, _RANGO_CONS_SAN, 'internaciones_consolidado_sanatorial')


def load_consolidado_quirurgicas(df: pd.DataFrame) -> None:
    _load_consolidado(df, _RANGO_CONS_QUIR, 'internaciones_consolidado_quirurgicas')


def _load_consolidado(df: pd.DataFrame, rango: str, table_name: str) -> None:
    nueva = _prepare(df)
    fecha_hoy = pd.Timestamp.today().normalize().strftime('%Y-%m-%d')
    nueva.insert(0, 'Fecha_Carga', fecha_hoy)

    historial = leer_tabla_df(_SHEET_OUTPUT, rango)

    # Validar que la lectura devolvió las columnas esperadas antes de confiar en ella.
    # Un resultado vacío cuando se espera historial es más seguro de abortar
    # que sobrescribir silenciosamente filas acumuladas.
    columnas_esperadas = set(nueva.columns)
    if not historial.empty:
        if not columnas_esperadas.issubset(set(historial.columns)):
            raise RuntimeError(
                f"leer_tabla_df devolvió columnas inesperadas: {list(historial.columns)}"
            )
        historial = historial[historial['Fecha_Carga'] != fecha_hoy]

    resultado = pd.concat([historial, nueva], ignore_index=True)
    escribir_tabla_df(_SHEET_OUTPUT, rango, resultado, clear_first=True)
    save_snapshot(df, table_name)


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    for col in df.columns:
        if str(df[col].dtype) == 'Int64':
            df[col] = df[col].astype(object).where(df[col].notna(), other='')
    return df
