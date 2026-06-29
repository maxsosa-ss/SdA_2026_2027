from src.extract.protesis import extract_protesis
from src.stage.protesis import read as stage_read, stage
from src.transform.protesis import protesis_gral
from src.load.protesis import load_protesis_gral
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage(extract_protesis())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que el parquet ya está staged."""
    df = stage_read()

    result = protesis_gral(df)

    load_protesis_gral(result)

    notify_success(
        'Prótesis actualizada',
        fields=[
            {'name': 'General (ejercicio)', 'value': f'{len(result):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline protesis', exc)
        raise
