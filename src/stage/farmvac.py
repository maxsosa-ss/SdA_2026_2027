import pandas as pd
from pathlib import Path

_DATA_PATH = Path(__file__).parents[2] / 'data' / 'raw'
_FILE      = _DATA_PATH / 'farmvac.parquet'
_DATE_COL  = 'Fecha Autorizacion Receta'


def _normalize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[_DATE_COL] = pd.to_datetime(df[_DATE_COL], errors='coerce')
    return df


def stage_complete(farm_df: pd.DataFrame, vac_df: pd.DataFrame) -> None:
    df = _normalize_dates(pd.concat([farm_df, vac_df], ignore_index=True))
    _DATA_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_FILE, index=False)
    print(f'✅ farmvac (complete): {len(df)} registros en {_FILE.name}')


def stage_u6m(farm_df: pd.DataFrame, vac_df: pd.DataFrame) -> None:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. "
            "Corré stage_complete() primero para cargar el historial completo."
        )
    nuevo = _normalize_dates(pd.concat([farm_df, vac_df], ignore_index=True))
    fecha_limite = pd.Timestamp.today().normalize() - pd.DateOffset(months=6)

    existente = pd.read_parquet(_FILE)
    existente[_DATE_COL] = pd.to_datetime(existente[_DATE_COL], errors='coerce')

    antes = len(existente)
    existente = existente[existente[_DATE_COL] < fecha_limite]
    eliminados = antes - len(existente)

    resultado = pd.concat([existente, nuevo], ignore_index=True)
    resultado.to_parquet(_FILE, index=False)

    print(f'🗑️  Eliminados desde {fecha_limite.date()}: {eliminados} registros')
    print(f'✅ farmvac (u6m): {len(resultado)} registros en {_FILE.name}')


def read() -> pd.DataFrame:
    if not _FILE.exists():
        raise RuntimeError(
            f"El archivo '{_FILE.name}' no existe. Corré stage_complete() primero."
        )
    return pd.read_parquet(_FILE)
