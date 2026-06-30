from src.extract.internaciones import extract_sanatoriales, extract_quirurgicas
from src.stage.internaciones import (
    stage_sanatorial, stage_quirurgicas,
    read_sanatorial as stage_read_sanatorial,
    read_quirurgicas as stage_read_quirurgicas,
)
from src.load.internaciones import (
    load_sanatorial, load_quirurgicas,
    load_consolidado_sanatorial, load_consolidado_quirurgicas,
)
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage_sanatorial(extract_sanatoriales())
    stage_quirurgicas(extract_quirurgicas())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que los parquets ya están staged."""
    san = stage_read_sanatorial()
    quir = stage_read_quirurgicas()

    load_sanatorial(san)
    load_quirurgicas(quir)
    load_consolidado_sanatorial(san)
    load_consolidado_quirurgicas(quir)

    notify_success(
        'Internaciones actualizada',
        fields=[
            {'name': 'Sanatorial', 'value': f'{len(san):,} filas', 'inline': True},
            {'name': 'Quirúrgicas', 'value': f'{len(quir):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline internaciones', exc)
        raise
