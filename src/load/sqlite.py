import sqlite3
from pathlib import Path

import pandas as pd

_DB_PATH = Path(__file__).parents[2] / 'data' / 'processed' / 'sda.sqlite'


def save_snapshot(df: pd.DataFrame, table_name: str, fecha_carga: pd.Timestamp = None) -> None:
    """
    Guarda un snapshot diario de `df` en la tabla `table_name` de sda.sqlite.

    - Agrega la columna `fecha_carga` (fecha de ejecución del pipeline).
    - Si ya existen filas para esa fecha en la tabla, las reemplaza
      (permite re-runs sin duplicar).

    Parámetros
    ----------
    df : DataFrame con los datos a persistir.
    table_name : nombre de la tabla destino (se crea si no existe).
    fecha_carga : timestamp de referencia; por defecto = hoy normalizado.
    """
    if fecha_carga is None:
        fecha_carga = pd.Timestamp.today().normalize()

    fecha_str = fecha_carga.strftime('%Y-%m-%d')

    snapshot = df.copy()
    # Normalizar columnas datetime a string para compatibilidad con SQLite
    for col in snapshot.select_dtypes(include='datetime64[ns]').columns:
        snapshot[col] = snapshot[col].dt.strftime('%Y-%m-%d')
    snapshot.insert(0, 'fecha_carga', fecha_str)

    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(_DB_PATH) as con:
        # Eliminar el snapshot de hoy si la tabla ya existe (idempotente)
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if table_name in tables:
            con.execute(
                f"DELETE FROM {table_name} WHERE fecha_carga = ?",  # noqa: S608
                (fecha_str,),
            )
            # Agregar columnas nuevas si el DataFrame trae columnas que la tabla
            # todavía no tiene (p.ej. tras un cambio de esquema del pipeline).
            columnas_existentes = {r[1] for r in con.execute(f"PRAGMA table_info({table_name})")}  # noqa: S608
            for col in snapshot.columns:
                if col not in columnas_existentes:
                    con.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}"')  # noqa: S608
        snapshot.to_sql(table_name, con, if_exists='append', index=False)

    print(f'💾 {table_name}: {len(snapshot)} filas guardadas ({fecha_str}) → {_DB_PATH.name}')
