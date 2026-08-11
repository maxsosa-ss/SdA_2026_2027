import pandas as pd
from pathlib import Path

_DATA_PATH   = Path(__file__).parents[2] / 'data' / 'raw'
_FILE        = _DATA_PATH / 'provision.parquet'
_FILE_DIARIO = _DATA_PATH / 'provision_diario.parquet'
_FILE_NC     = _DATA_PATH / 'provision_nc.parquet'


def stage(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE, index=False)
    print(f'✅ provision: {len(df)} registros en {_FILE.name}')


def stage_diario(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE_DIARIO, index=False)
    print(f'✅ provision_diario: {len(df)} registros en {_FILE_DIARIO.name}')


def stage_nc(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE_NC, index=False)
    print(f'✅ provision_nc: {len(df)} registros en {_FILE_NC.name}')


def read() -> pd.DataFrame:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. "
            "Corré extract_provision() y stage() primero."
        )
    return pd.read_parquet(_FILE)


def read_diario() -> pd.DataFrame:
    if not _FILE_DIARIO.exists():
        raise RuntimeError(
            f"El archivo '{_FILE_DIARIO.name}' no existe. "
            "Corré extract_provision_diario() y stage_diario() primero."
        )
    return pd.read_parquet(_FILE_DIARIO)


def read_nc() -> pd.DataFrame:
    if not _FILE_NC.exists():
        raise RuntimeError(
            f"El archivo '{_FILE_NC.name}' no existe. "
            "Corré extract_nc() y stage_nc() primero."
        )
    return pd.read_parquet(_FILE_NC)
