import pandas as pd
import requests
from mstrio.project_objects import Report
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.utils.connections import get_mstr_conn

_R_QUIR_QTY_VAL = 'E5D59D0A824A139CA57DB8A56084BF24'
_R_QUIR_NE_PTTO = 'EA2159D88A49B2D8E2D8F7A78A1FF672'
_R_SAN_QTY      = 'C71DAF365641E079133675B4BA255443'
_R_SAN_NE       = '14772FE4A2472411C34CF3B8934268BA'


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_quirurgicas(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()

    qty_val = _fetch(_R_QUIR_QTY_VAL, conn)
    qty_val.rename(columns={'Periodo Cirugía': 'Periodo'}, inplace=True)

    ne_ptto = _fetch(_R_QUIR_NE_PTTO, conn)

    df = pd.merge(qty_val, ne_ptto, on='Periodo', how='outer')
    df['Periodo'] = df['Periodo'].astype(int)
    cols = ['Periodo', 'Eventos totales', 'Aut. Valorizadas', 'NE', 'PTTO']
    df = df[cols]
    print(f'⚙️ Registros en Quirúrgicas: {len(df)}')
    return df


def extract_sanatoriales(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()

    qty = _fetch(_R_SAN_QTY, conn)
    qty.rename(columns={
        'Periodo ID': 'Periodo',
        'Recuento de Ordenes + Pendientes': 'Cantidad Internaciones',
    }, inplace=True)

    ne = _fetch(_R_SAN_NE, conn)
    ne.rename(columns={'Periodo ID': 'Periodo'}, inplace=True)

    df = pd.merge(qty, ne, on='Periodo', how='outer')
    df['Periodo'] = df['Periodo'].astype(int)
    cols = ['Periodo', 'Dias Internación', 'Cantidad Internaciones',
            'Nivel Esperado Días', 'Nivel Esperados Internación']
    df = df[cols]
    print(f'⚙️ Registros en Sanatoriales: {len(df)}')
    return df
