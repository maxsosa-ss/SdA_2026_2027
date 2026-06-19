import sqlite3
import pandas as pd
from pathlib import Path

_DB_PATH = Path(__file__).parents[2] / 'data' / 'raw' / 'raw.sqlite'
_TABLE   = 'ambulatorio'
_DATE_COL = 'Fecha Proceso Autorización'


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(_DB_PATH)


def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[_DATE_COL] = pd.to_datetime(df[_DATE_COL], errors='coerce').dt.strftime('%Y-%m-%d')
    return df


def load_complete(df: pd.DataFrame) -> None:
    df = _normalize_dates(df)
    conn = _connect()
    try:
        with conn:
            df.to_sql(_TABLE, conn, if_exists='replace', index=False)
            count = conn.execute(f'SELECT COUNT(*) FROM {_TABLE}').fetchone()[0]
    finally:
        conn.close()
    print(f'✅ ambulatorio (complete): {count} registros en {_DB_PATH.name}')


def load_u6m(df: pd.DataFrame) -> None:
    df = _normalize_dates(df)
    fecha_limite = (pd.Timestamp.today() - pd.DateOffset(months=6)).strftime('%Y-%m-%d')
    conn = _connect()
    try:
        with conn:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (_TABLE,)
            ).fetchone()
            if not exists:
                raise RuntimeError(
                    f"La tabla '{_TABLE}' no existe en {_DB_PATH.name}. "
                    "Corré load_complete() primero para cargar el historial completo."
                )
            conn.execute(f'DELETE FROM {_TABLE} WHERE [{_DATE_COL}] >= ?', (fecha_limite,))
            eliminados = conn.execute('SELECT changes()').fetchone()[0]
            df.to_sql(_TABLE, conn, if_exists='append', index=False)
            count = conn.execute(f'SELECT COUNT(*) FROM {_TABLE}').fetchone()[0]
    finally:
        conn.close()
    print(f'🗑️  Eliminados desde {fecha_limite}: {eliminados} registros')
    print(f'✅ ambulatorio (u6m): {count} registros en {_DB_PATH.name}')
