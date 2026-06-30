import pandas as pd
from pathlib import Path

_DATA_PATH    = Path(__file__).parents[2] / 'data' / 'raw'
_FILE_SAN     = _DATA_PATH / 'internaciones_sanatorial.parquet'
_FILE_QUIR    = _DATA_PATH / 'internaciones_quirurgicas.parquet'


def stage_sanatorial(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE_SAN, index=False)
    print(f'✅ internaciones_sanatorial: {len(df)} registros en {_FILE_SAN.name}')


def stage_quirurgicas(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE_QUIR, index=False)
    print(f'✅ internaciones_quirurgicas: {len(df)} registros en {_FILE_QUIR.name}')


def read_sanatorial() -> pd.DataFrame:
    if not _FILE_SAN.exists():
        raise RuntimeError(
            f"El archivo '{_FILE_SAN.name}' no existe. "
            "Corré extract_sanatoriales() y stage_sanatorial() primero."
        )
    return pd.read_parquet(_FILE_SAN)


def read_quirurgicas() -> pd.DataFrame:
    if not _FILE_QUIR.exists():
        raise RuntimeError(
            f"El archivo '{_FILE_QUIR.name}' no existe. "
            "Corré extract_quirurgicas() y stage_quirurgicas() primero."
        )
    return pd.read_parquet(_FILE_QUIR)
