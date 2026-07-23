import pandas as pd
from pathlib import Path

_DATA_PATH = Path(__file__).parents[2] / 'data' / 'raw'
_FILE      = _DATA_PATH / 'ambulatorio.parquet'
_FILE_RESTO = _DATA_PATH / 'ambulatorio_resto.parquet'
_DATE_COL  = 'Fecha Proceso Autorización'


def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[_DATE_COL] = pd.to_datetime(df[_DATE_COL], errors='coerce')
    return df


def stage_complete(df: pd.DataFrame) -> None:
    df = _normalize_dates(df)
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE, index=False)
    print(f'✅ ambulatorio (complete): {len(df)} registros en {_FILE.name}')


def stage_u6m(df: pd.DataFrame) -> None:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. "
            "Corré stage_complete() primero para cargar el historial completo."
        )
    df = _normalize_dates(df)
    fecha_limite = pd.Timestamp.today().normalize() - pd.DateOffset(months=6)

    existente = pd.read_parquet(_FILE)
    existente[_DATE_COL] = pd.to_datetime(existente[_DATE_COL], errors='coerce')

    antes = len(existente)
    existente = existente[existente[_DATE_COL] < fecha_limite]
    eliminados = antes - len(existente)

    resultado = pd.concat([existente, df], ignore_index=True)
    resultado.to_parquet(_FILE, index=False)

    print(f'🗑️  Eliminados desde {fecha_limite.date()}: {eliminados} registros')
    print(f'✅ ambulatorio (u6m): {len(resultado)} registros en {_FILE.name}')


def read() -> pd.DataFrame:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. Corré stage_complete() primero."
        )
    return pd.read_parquet(_FILE)


def stage_resto(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE_RESTO, index=False)
    print(f'✅ ambulatorio (resto): {len(df)} registros en {_FILE_RESTO.name}')


def read_resto() -> pd.DataFrame:
    if not _FILE_RESTO.exists():
        raise RuntimeError(
            f"El archivo '{_FILE_RESTO.name}' no existe. Corré extract_resto() y stage_resto() primero."
        )
    return pd.read_parquet(_FILE_RESTO)
