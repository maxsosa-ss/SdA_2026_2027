from src.extract.provision import extract_provision, extract_provision_diario, extract_ne_provision
from src.stage.provision import read as stage_read, read_diario as stage_read_diario, stage, stage_diario
from src.transform.provision import prov_gral, prov_diario
from src.load.provision import load_prov_gral, load_prov_diario
from src.utils.dates import fecha_hoy
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage(extract_provision())
    stage_diario(extract_provision_diario())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que los parquets ya están staged."""
    df     = stage_read()
    df_dia = stage_read_diario()
    ne     = extract_ne_provision()
    hoy    = fecha_hoy.normalize()

    gral   = prov_gral(df, ne)
    diario = prov_diario(df_dia, hoy)

    load_prov_gral(gral)
    load_prov_diario(diario)

    notify_success(
        'Provisión actualizada',
        fields=[
            {'name': 'General (ejercicio)', 'value': f'{len(gral):,} filas',   'inline': True},
            {'name': 'Diario',              'value': f'{len(diario):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline provisión', exc)
        raise
