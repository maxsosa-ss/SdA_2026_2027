import pandas as pd
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn
from src.utils.gc_functions import leer_tabla_df

_REPORT_COMPLETE = '6FFDEA91D9424E4D3C903E800B8C8D52'
_REPORT_U6M      = '1C7CE23E3342D3623628C6837F197F57'

_SHEET_AUX = '1l9dP8MK3GN8D1RymJ8Q8u-SRkrQPKmN-4wKChMBpYHQ'
_SHEET_NE  = '1RV39I7zo0rSBgDhmGHjaEPt0eBnLfle1L0XpvLIHI9M'


def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_complete(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_COMPLETE, conn)


def extract_u6m(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_U6M, conn)


def extract_ne_amb() -> pd.DataFrame:
    df = leer_tabla_df(_SHEET_NE, 'NE_amb!A1:F47629')
    df.rename(columns={
        'Rubro PPTO':    'Rubro',
        'Subrubro PPTO': 'Subrubro',
        'NE':            'Nivel Esperado',
    }, inplace=True)
    df['Nivel Esperado'] = pd.to_numeric(df['Nivel Esperado'], errors='coerce').fillna(0)
    df['Periodo'] = df['Periodo'].astype(str)
    return df


def extract_feriados() -> dict:
    """
    Retorna dict con 4 DatetimeIndex: feriados, feriado_puro, no_laborables, fiestas.
    Columnas GSheets (feriados!A:C): Fecha | Feriado | Tipo
    """
    df = leer_tabla_df(_SHEET_AUX, 'feriados!A1:C166')
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    tipo = df['Tipo']
    return dict(
        feriados      = pd.DatetimeIndex(df['Fecha']),
        feriado_puro  = pd.DatetimeIndex(df.loc[tipo == 'Feriado Puro',  'Fecha']),
        no_laborables = pd.DatetimeIndex(df.loc[tipo == 'No Laborable',  'Fecha']),
        fiestas       = pd.DatetimeIndex(df.loc[tipo == 'Fiesta',        'Fecha']),
    )
