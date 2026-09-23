import pandas as pd
import requests
from mstrio.project_objects import Report
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.utils.connections import get_mstr_conn

_REPORT_PROT = '487C19731D407E266563C5B41CC94F85'

@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_protesis(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    df = _fetch(_REPORT_PROT, conn)
    df.rename(columns={
        'Zona Direccion Comercial Asociado':    'Zona',
        'Subzona Direccion Comercial Asociado': 'Subzona',
        'Origen Autorización':                  'Origen',
        'Cantidad Prestaciones Aceptadas':      'Cantidad',
        'Importe Comprobante Prestacion':       'Importe',
    }, inplace=True)
    df['Periodo']  = df['Periodo'].astype(str).str.strip()
    df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Importe']  = pd.to_numeric(df['Importe'],  errors='coerce').fillna(0)
    print(f'⚙️ Registros en Autorizaciones PROTESIS: {len(df)}')
    return df
