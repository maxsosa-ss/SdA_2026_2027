import pandas as pd
import requests
from mstrio.project_objects import Report
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.utils.connections import get_mstr_conn
from src.utils.gc_functions import leer_tabla_df

_REPORT_PROVISION        = 'C41EA844C04CDA01937C65A9DB6E3E86'
_REPORT_PROVISION_DIARIO = 'B9025BF74B447CED830040BECF1F02DE'
_REPORT_NC               = '375A58A94D45054EBD97B8AC17F1206F'

_SHEET_NE = '1RV39I7zo0rSBgDhmGHjaEPt0eBnLfle1L0XpvLIHI9M'
_RANGO_NE = 'NE_provision!A1:D127'
_RANGO_NE_NC = 'NE_provisionNC!A1:B60'


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_provision(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    df = _fetch(_REPORT_PROVISION, conn)
    df.rename(columns={
        'Provision Profesional Actuante':  'Provision',
        'Origen Autorización':             'Origen',
        'Acreedor@ID':                     'Acreedor_id',
        'Acreedor@DESC':                   'Acreedor_descr',
        'Cantidad Prestaciones Aceptadas': 'Cantidad',
        'Importe Comprobante Prestacion':  'Importe',
    }, inplace=True)
    df['Periodo']  = df['Periodo'].astype(str).str.strip()
    df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce').fillna(0)
    df['Importe']  = pd.to_numeric(df['Importe'],  errors='coerce').fillna(0)
    print(f'⚙️ Registros en Autorizaciones PROVISION: {len(df)}')
    return df


def extract_provision_diario(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    df = _fetch(_REPORT_PROVISION_DIARIO, conn)
    df.rename(columns={
        'Fecha Proceso Autorización':      'Fecha',
        'Importe Comprobante Prestacion':  'Autorizaciones $',
        'Cantidad Prestaciones Aceptadas': 'Autorizaciones QTY',
    }, inplace=True)
    df['Fecha']              = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Autorizaciones $']   = pd.to_numeric(df['Autorizaciones $'],   errors='coerce').fillna(0)
    df['Autorizaciones QTY'] = pd.to_numeric(df['Autorizaciones QTY'], errors='coerce').fillna(0)
    print(f'⚙️ Registros en PROVISION diario: {len(df)}')
    return df


def extract_nc(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    df = _fetch(_REPORT_NC, conn)
    df.rename(columns={
        'Fecha Proceso Origen Recepcionado': 'Fecha',
        'Acreedor@ID':                       'Acreedor ID',
        'Acreedor@DESC':                     'Acreedor DESC',
    }, inplace=True)
    df['Periodo']               = df['Periodo'].astype(str).str.strip()
    df['Fecha']                 = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Importe Recepcionado']  = pd.to_numeric(df['Importe Recepcionado'], errors='coerce').fillna(0)
    df = df[['Periodo', 'Fecha', 'Acreedor ID', 'Acreedor DESC', 'Nro Cursograma', 'Importe Recepcionado']]
    print(f'⚙️ Registros en PROVISION NC: {len(df)}')
    return df


def extract_ne_provision() -> pd.DataFrame:
    """
    Nivel Esperado en importe para Provisión.
    Columnas del tab: Provision AC | Origen | Periodo | $ Nivel Esperado
    """
    df = leer_tabla_df(_SHEET_NE, _RANGO_NE)
    df['$ Nivel Esperado'] = pd.to_numeric(
        df['$ Nivel Esperado'].astype(str).str.replace(',', '.'),
        errors='coerce',
    ).fillna(0)
    df['Periodo'] = df['Periodo'].astype(str).str.strip()
    return df


def extract_ne_provision_nc() -> pd.DataFrame:
    """
    Nivel Esperado de NC para Provisión Droguería.
    Columnas del tab: Periodo | $ Nivel Esperado NC
    """
    df = leer_tabla_df(_SHEET_NE, _RANGO_NE_NC)
    df['$ Nivel Esperado NC'] = pd.to_numeric(
        df['$ Nivel Esperado NC'].astype(str).str.replace(',', '.'),
        errors='coerce',
    ).fillna(0)
    df['Periodo'] = df['Periodo'].astype(str).str.strip()
    return df
