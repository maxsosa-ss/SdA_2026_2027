import pandas as pd
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn

_REPORT_COMPLETE = '6FFDEA91D9424E4D3C903E800B8C8D52'
_REPORT_U6M      = '1C7CE23E3342D3623628C6837F197F57'


def _fetch(report_id: str, conn) -> pd.DataFrame:
    return Report(id=report_id, connection=conn, progress_bar=False).to_dataframe()


def extract_complete(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_COMPLETE, conn)


def extract_u6m(conn=None) -> pd.DataFrame:
    conn = conn or get_mstr_conn()
    return _fetch(_REPORT_U6M, conn)
