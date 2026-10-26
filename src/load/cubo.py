import json
import os
from pathlib import Path

import pandas as pd
from smpy.connectors.pipeline import dataframe_to_supercube

from src.utils.connections import get_mstr_conn
from src.utils.discord import notify_warning

_CUBOS_JSON = Path(__file__).parents[2] / 'config' / 'cubos.json'
_FOLDER_CUBOS = '2C35209C1F4DEA269AFEBA80EBEACF1E'  # carpeta "Cubos SdA"
_PREFIJO_NOMBRE = 'SdA - '


def subir_a_cubo(
    df: pd.DataFrame,
    table_name: str,
    cube_id: str | None = None,
    cube_name: str | None = None,
    policy: str = 'replace',
    folder_id: str | None = None,
    to_attribute: list[str] | None = None,
    to_metric: list[str] | None = None,
    conn=None,
) -> str:
    """
    Sube un DataFrame a un super cube de MicroStrategy y devuelve el ID del cubo.

    - Con `cube_id` actualiza ese cubo según `policy` (replace | add | update | upsert).
    - Sin `cube_id` crea uno nuevo llamado `cube_name` (en `folder_id`, o MSTR_FOLDER_ID, o "My Reports").
      Guardar el ID devuelto: volver a llamar solo con `cube_name` intenta crear otro cubo.
    - `table_name` es el nombre lógico de la tabla dentro del cubo y debe ser el mismo en cada
      actualización.
    - Las columnas numéricas se suben como métricas y el resto como atributos. Periodo ('YYYYMM')
      conviene como atributo: pasar `to_attribute=['Periodo']`.

    Reutiliza la conexión del proyecto (`get_mstr_conn`), así no hacen falta MSTR_BASE_URL ni
    MSTR_PROJECT_ID. Si se pasa `conn`, no se cierra; si no, se abre y se cierra acá.
    """
    propia = conn is None
    conn = conn or get_mstr_conn()
    try:
        return dataframe_to_supercube(
            df,
            table_name,
            cube_id=cube_id,
            cube_name=cube_name,
            policy=policy,
            folder_id=folder_id,
            to_attribute=to_attribute,
            to_metric=to_metric,
            conn=conn,
        )
    finally:
        if propia:
            conn.close()


def _leer_ids() -> dict:
    return json.loads(_CUBOS_JSON.read_text(encoding='utf-8')) if _CUBOS_JSON.exists() else {}


def _guardar_id(table_name: str, cube_id: str) -> None:
    ids = _leer_ids()
    ids[table_name] = cube_id
    _CUBOS_JSON.parent.mkdir(exist_ok=True)
    _CUBOS_JSON.write_text(json.dumps(ids, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')


def _para_cubo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza los tipos antes de subir al cubo.

    - Todas las columnas numéricas (int, Int64, float...) pasan a float64. El cubo fija el tipo de
      cada métrica al crearse y no lo cambia: una métrica `integer` es de 32 bits, y actualizarla
      con valores que no caben (importes en $) o con otro tipo la deja NULA sin dar error.
      Con float64 la métrica es siempre `double`.
    - `Periodo` ('YYYYMM') va como texto, para que sea atributo y no métrica.
    - Las fechas pasan a datetime64[ns], la única resolución que acepta mstrio.
    """
    df = df.copy()
    for col in df.columns:
        if col == 'Periodo':
            df[col] = df[col].astype(str)
        elif pd.api.types.is_datetime64_any_dtype(df[col].dtype):
            df[col] = df[col].astype('datetime64[ns]')  # mstrio no acepta otras resoluciones (ej. [us])
        elif pd.api.types.is_numeric_dtype(df[col].dtype) and not pd.api.types.is_bool_dtype(df[col].dtype):
            df[col] = df[col].astype('float64')
    return df


def subir_tabla(df: pd.DataFrame, table_name: str) -> None:
    """
    Actualiza (replace) el cubo de `table_name` según config/cubos.json. Pasar el DataFrame sin
    `_prepare`, así las fechas llegan como fecha real.

    Nunca interrumpe el pipeline: ante cualquier problema avisa por Discord (warning) y sigue.
    Si la tabla no tiene cubo registrado, solo lo crea con CREAR_CUBOS=1 (uso local, después hay que
    commitear config/cubos.json). En GitHub Actions no se crea nada: el archivo no se commitea de
    vuelta y cada corrida crearía un cubo duplicado.
    """
    try:
        cube_id = _leer_ids().get(table_name)
        if not cube_id and os.getenv('CREAR_CUBOS') != '1':
            notify_warning(
                f'Cubo sin registrar: {table_name}',
                fields=[{'name': 'Qué hacer', 'value': 'Correr local con CREAR_CUBOS=1 y commitear config/cubos.json', 'inline': False}],
            )
            return
        nuevo_id = subir_a_cubo(
            _para_cubo(df),
            table_name,
            cube_id=cube_id,
            cube_name=None if cube_id else f'{_PREFIJO_NOMBRE}{table_name}',
            folder_id=_FOLDER_CUBOS,
        )
        if not cube_id:
            _guardar_id(table_name, nuevo_id)
        print(f'[cubo] {table_name}: {len(df)} filas -> {nuevo_id}')
    except Exception as exc:
        print(f'[cubo] ERROR {table_name}: {exc}')
        notify_warning(
            f'No se pudo actualizar el cubo {table_name}',
            fields=[{'name': 'Error', 'value': f'{type(exc).__name__}: {exc}'[:900], 'inline': False}],
        )
