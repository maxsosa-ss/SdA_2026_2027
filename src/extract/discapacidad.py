import pandas as pd
import requests
from mstrio.project_objects import Report
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.utils.connections import get_mstr_conn
from src.utils.gc_functions import leer_tabla_df

_REPORT_DISCA = 'B60FDA19E4423A89A9B718BCC1952ECA'
_SHEET_AUX    = '1l9dP8MK3GN8D1RymJ8Q8u-SRkrQPKmN-4wKChMBpYHQ'
_RANGO_AUX    = 'discapacidad!A1:F75'


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_discapacidad(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    df = _fetch(_REPORT_DISCA, conn)
    df.rename(columns={
        'Zona Direccion Comercial Asociado':    'Zona',
        'Subzona Direccion Comercial Asociado': 'Subzona',
        'Tipo Orden':                           'Tipo',
        'Prestacion@ID':                        'Prestacion_id',
        'Prestacion@DESC':                      'Prestacion_descr',
        'Cantidad Prestaciones Aceptadas':      'Cantidad',
    }, inplace=True)
    df['Periodo']      = df['Periodo'].astype(str).str.strip()
    df['Tipo']         = pd.to_numeric(df['Tipo'],     errors='coerce')
    df['Cantidad']     = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Prestacion_id'] = df['Prestacion_id'].astype(str).str.strip()
    print(f'⚙️ Registros en Autorizaciones DISCAPACIDAD: {len(df)}')
    return df


def extract_aux_discapacidad() -> pd.DataFrame:
    df = leer_tabla_df(_SHEET_AUX, _RANGO_AUX)
    df.rename(columns={
        'Prestacion ID':   'Prestacion_id',
        'Prestacion DESC': 'Prestacion_descr',
    }, inplace=True)
    df['Prestacion_id'] = df['Prestacion_id'].astype(str).str.strip()
    return df
