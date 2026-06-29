import pandas as pd
from pathlib import Path

_DATA_PATH = Path(__file__).parents[2] / 'data' / 'raw'
_FILE      = _DATA_PATH / 'discapacidad.parquet'


def stage(df: pd.DataFrame) -> None:
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE, index=False)
    print(f'✅ discapacidad: {len(df)} registros en {_FILE.name}')


def read() -> pd.DataFrame:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. "
            "Corré extract_discapacidad() y stage() primero."
        )
    return pd.read_parquet(_FILE)
