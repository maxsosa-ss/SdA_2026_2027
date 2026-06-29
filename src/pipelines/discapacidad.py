from src.extract.discapacidad import extract_discapacidad, extract_aux_discapacidad
from src.stage.discapacidad import read as stage_read, stage
from src.transform.discapacidad import disca_gral
from src.load.discapacidad import load_disca_gral
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage(extract_discapacidad())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que el parquet ya está staged."""
    df  = stage_read()
    aux = extract_aux_discapacidad()

    result = disca_gral(df, aux)

    load_disca_gral(result)

    notify_success(
        'Discapacidad actualizada',
        fields=[
            {'name': 'General (ejercicio)', 'value': f'{len(result):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline discapacidad', exc)
        raise
