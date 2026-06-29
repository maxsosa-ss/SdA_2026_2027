import pandas as pd
from src.utils.gc_functions import escribir_tabla_df, leer_tabla_df
from src.load.sqlite import save_snapshot

_SHEET_OUTPUT        = '1DNpmKUjIOuHPCBrMN8Ww5xlmJ1XQAvGcH3wMFujvMNU'
_RANGO_DIARIO        = 'farmvac_seg_diario!A1'
_RANGO_GRAL_Q        = 'farmvac_gral_Q!A1'
_RANGO_GRAL_IMP      = 'farmvac_gral_imp!A1'
_RANGO_SEG_PROY_IMP  = 'farm_proy_imp_diario'


def load_proyeccion_diaria(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_DIARIO, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_seg_diario')


def load_proyeccion_ejercicio(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL_Q, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_gral_q')


def load_proyeccion_importe(df: pd.DataFrame) -> None:
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_GRAL_IMP, _prepare(df), clear_first=True)
    save_snapshot(df, 'farm_gral_imp')


def load_seg_proy_importe(df: pd.DataFrame) -> None:
    nueva_fila = _prepare(df)
    fecha_hoy = nueva_fila['Fecha'].iloc[0]

    historial = leer_tabla_df(_SHEET_OUTPUT, _RANGO_SEG_PROY_IMP)

    # Validate that the read returned expected columns before trusting it.
    # An empty result when we expect history is safer to abort than to silently
    # overwrite accumulated rows.
    columnas_esperadas = set(nueva_fila.columns)
    if not historial.empty:
        if not columnas_esperadas.issubset(set(historial.columns)):
            raise RuntimeError(
                f"leer_tabla_df devolvió columnas inesperadas: {list(historial.columns)}"
            )
        historial = historial[historial['Fecha'] != fecha_hoy]

    resultado = pd.concat([historial, nueva_fila], ignore_index=True)
    escribir_tabla_df(_SHEET_OUTPUT, _RANGO_SEG_PROY_IMP, resultado, clear_first=True)
    save_snapshot(df, 'farm_seg_proy_imp')


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include='datetime64[ns]').columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')
    return df
