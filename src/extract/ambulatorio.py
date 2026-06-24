import pandas as pd
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn
from src.utils.gc_functions import leer_tabla_df

_REPORT_COMPLETE = '6FFDEA91D9424E4D3C903E800B8C8D52'
_REPORT_U6M      = '1C7CE23E3342D3623628C6837F197F57'

_SHEET_AUX      = '1l9dP8MK3GN8D1RymJ8Q8u-SRkrQPKmN-4wKChMBpYHQ'
_SHEET_NE       = '1RV39I7zo0rSBgDhmGHjaEPt0eBnLfle1L0XpvLIHI9M'
_SHEET_VAL_AMB  = '1sTDBzkvCmjJGOflB3-BafYWMgzWe0xFPcJmfquB8Nhw'
_SHEET_CONVERSOR = '1hc-Koy4z87doOled-5zLPSK9ysd1RNc7a9IbYL3ZpGQ'

_VU_ID_COLS = ['RUBRO', 'SUBRUBRO', 'ZONA', 'SUBZONA']


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


def extract_val_amb() -> pd.DataFrame:
    # VU: formato ancho → largo
    vu = leer_tabla_df(_SHEET_VAL_AMB, 'P_AMB!A1:Y2269')
    periodo_cols = [c for c in vu.columns if c not in _VU_ID_COLS]
    vu = vu.melt(id_vars=_VU_ID_COLS, value_vars=periodo_cols, var_name='Periodo', value_name='VU')
    vu.rename(columns={
        'RUBRO':    'Rubro',
        'SUBRUBRO': 'Subrubro',
        'ZONA':     'Zona DCA',
        'SUBZONA':  'Subzona DCA',
    }, inplace=True)
    vu['VU'] = pd.to_numeric(vu['VU'], errors='coerce').fillna(0)
    vu['Periodo'] = vu['Periodo'].astype(str)

    # M2: RUBRO, ZONA, PERIODO, M2
    m2 = leer_tabla_df(_SHEET_VAL_AMB, 'D_AMB!A1:D1891')
    m2.rename(columns={
        'RUBRO':   'Rubro',
        'ZONA':    'Zona DCA',
        'PERIODO': 'Periodo',
    }, inplace=True)
    m2['M2'] = pd.to_numeric(m2['M2'].astype(str).str.replace(',', '.'), errors='coerce').fillna(1)
    m2['Periodo'] = m2['Periodo'].astype(str)

    # Conversor
    conv = leer_tabla_df(_SHEET_CONVERSOR, 'conversor_amb!A1:E10207')
    conv.rename(columns={
        'Rubro PPTO':        'Rubro',
        'Subrubro PPTO':     'Subrubro',
        'Periodo Conversor': 'Periodo',
    }, inplace=True)
    conv['Conversor'] = pd.to_numeric(conv['Conversor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(1)
    conv['Periodo'] = conv['Periodo'].astype(str)

    # Joins
    val = vu.merge(
        m2[['Rubro', 'Zona DCA', 'Periodo', 'M2']],
        on=['Rubro', 'Zona DCA', 'Periodo'],
        how='left',
    )
    val = val.merge(
        conv[['Rubro', 'Subrubro', 'Zona DCA', 'Periodo', 'Conversor']],
        on=['Rubro', 'Subrubro', 'Zona DCA', 'Periodo'],
        how='left',
    )
    return val


def extract_feriados() -> dict:
    """
    Retorna dict con 3 DatetimeIndex: feriado, no_laborable, turistico.
    Columnas GSheets (feriados!A:C): Fecha | Feriado | Tipo
    """
    df = leer_tabla_df(_SHEET_AUX, 'feriados!A1:C200')
    df['Fecha'] = pd.to_datetime(df['Fecha'], dayfirst=True, errors='coerce')
    tipo = df['Tipo'].str.strip().str.lower()
    return dict(
        feriado      = pd.DatetimeIndex(df.loc[tipo == 'feriado',          'Fecha'].dropna()),
        no_laborable = pd.DatetimeIndex(df.loc[tipo == 'día no laborable', 'Fecha'].dropna()),
        turistico    = pd.DatetimeIndex(df.loc[tipo == 'turístico',        'Fecha'].dropna()),
    )
