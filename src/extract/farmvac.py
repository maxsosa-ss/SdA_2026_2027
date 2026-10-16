import pandas as pd
import requests
from mstrio.project_objects import Report
from mstrio.project_objects.prompt import Prompt
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from src.utils.connections import get_mstr_conn
from src.utils.gc_functions import leer_tabla_df

_REPORT_FARM_COMPLETE = 'F843D1834F4819163BF3A796DDBD809C'
_REPORT_FARM_U6M      = 'C50E5F1FDA44AD22759E94908AE08311'
_REPORT_VAC_COMPLETE  = '82E20970FA4DD5A85F58C491779ADBF4'
_REPORT_VAC_U6M       = '0DF2498E204C203483BA2BA9A8C2005D'

_PROMPT_PERIODO_KEY_FARM = 'F22CD4FF8948B38AADF79AAAC45AD468@0@10'  # prompt "Valor de Periodo" de _REPORT_FARM_COMPLETE
_PROMPT_PERIODO_KEY_VAC  = 'F37EF0D6AC4D534B8A256F8669BC75A3@0@10'  # prompt "Valor de Periodo" de _REPORT_VAC_COMPLETE

_SHEET_NE     = '1RV39I7zo0rSBgDhmGHjaEPt0eBnLfle1L0XpvLIHI9M'
_RANGO_NE_Q   = 'NE_farm_Q!A1:F1765'
_RANGO_NE_IMP = 'NE_farm_imp!A1:F1765'


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    stop=stop_after_attempt(3),
    wait=wait_fixed(10),
    reraise=True,
)
def _fetch_periodo(report_id: str, prompt_key: str, periodo: str, conn) -> pd.DataFrame:
    report = Report(id=report_id, connection=conn, progress_bar=False)
    return report.to_dataframe(
        prompt_answers=[Prompt(type='VALUE', key=prompt_key, answers=periodo)]
    )


def _extract_complete_por_periodo(
    report_id: str, prompt_key: str, nombre: str, desde: str, hasta: str, conn
) -> pd.DataFrame:
    periodos = pd.period_range(desde, hasta, freq='M').strftime('%Y%m')
    partes = []
    for periodo in periodos:
        df = _fetch_periodo(report_id, prompt_key, periodo, conn)
        print(f'⚙️ {nombre} {periodo}: {len(df)} registros')
        partes.append(df)
    return pd.concat(partes, ignore_index=True)


def extract_farm_complete_por_periodo(desde: str, hasta: str, conn=None) -> pd.DataFrame:
    """
    Base completa de Farmacia bajada periodo a periodo, respondiendo el prompt
    'Valor de Periodo' del reporte completo. desde / hasta: 'YYYYMM' inclusive.
    """
    conn = conn or get_mstr_conn()
    return _extract_complete_por_periodo(
        _REPORT_FARM_COMPLETE, _PROMPT_PERIODO_KEY_FARM, 'Farmacia', desde, hasta, conn
    )


def extract_vac_complete_por_periodo(desde: str, hasta: str, conn=None) -> pd.DataFrame:
    """
    Base completa de Vacunas bajada periodo a periodo, respondiendo el prompt
    'Valor de Periodo' del reporte completo. desde / hasta: 'YYYYMM' inclusive.
    """
    conn = conn or get_mstr_conn()
    return _extract_complete_por_periodo(
        _REPORT_VAC_COMPLETE, _PROMPT_PERIODO_KEY_VAC, 'Vacunas', desde, hasta, conn
    )


def extract_farm_complete(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_FARM_COMPLETE, conn)


def extract_farm_u6m(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_FARM_U6M, conn)


def extract_vac_complete(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_VAC_COMPLETE, conn)


def extract_vac_u6m(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_VAC_U6M, conn)


def extract_ne_farmvac_q() -> pd.DataFrame:
    """
    Nivel Esperado en cantidad para Farmacia y Vacunas.
    Columnas del tab: Rubro PPTO | Subrubro PPTO | Zona DCA | Subzona DCA | Periodo | NE
    """
    df = leer_tabla_df(_SHEET_NE, _RANGO_NE_Q)
    df.rename(columns={
        'Rubro PPTO':    'Rubro',
        'Subrubro PPTO': 'Subrubro',
        'NE':            'Nivel Esperado',
    }, inplace=True)
    df['Nivel Esperado'] = pd.to_numeric(df['Nivel Esperado'], errors='coerce').fillna(0)
    df['Periodo'] = df['Periodo'].astype(str)
    return df


def extract_ne_farmvac_imp() -> pd.DataFrame:
    """
    Nivel Esperado en importe ($) para Farmacia y Vacunas.
    Columnas del tab: Rubro PPTO | Subrubro PPTO | Zona DCA | Subzona DCA | Periodo | NE
    (NE aquí representa el NE en pesos → se renombra a 'Nivel Esperado $')
    """
    df = leer_tabla_df(_SHEET_NE, _RANGO_NE_IMP)
    df.rename(columns={
        'Rubro PPTO':    'Rubro',
        'Subrubro PPTO': 'Subrubro',
        'NE':            'Nivel Esperado $',
    }, inplace=True)
    df['Nivel Esperado $'] = pd.to_numeric(
        df['Nivel Esperado $'].astype(str).str.replace(',', '.'),
        errors='coerce'
    ).fillna(0)
    df['Periodo'] = df['Periodo'].astype(str)
    return df
