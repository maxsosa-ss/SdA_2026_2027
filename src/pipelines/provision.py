from src.extract.provision import (
    extract_provision, extract_provision_diario, extract_nc,
    extract_ne_provision, extract_ne_provision_nc,
)
from src.extract.ambulatorio import extract_feriados
from src.stage.provision import (
    read as stage_read, read_diario as stage_read_diario, read_nc as stage_read_nc,
    stage, stage_diario, stage_nc,
)
from src.transform.provision import prov_gral, prov_diario, prov_drogueria
from src.load.provision import load_prov_gral, load_prov_diario, load_prov_nc, load_prov_drogueria
from src.utils.dates import fecha_hoy, p_actual
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage(extract_provision())
    stage_diario(extract_provision_diario())
    stage_nc(extract_nc())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que los parquets ya están staged."""
    df     = stage_read()
    df_dia = stage_read_diario()
    df_nc  = stage_read_nc()
    ne       = extract_ne_provision()
    ne_nc    = extract_ne_provision_nc()
    cal      = extract_feriados()
    hoy      = fecha_hoy.normalize()

    gral   = prov_gral(df, ne)
    diario = prov_diario(df_dia, hoy, feriados=cal, ne_gral=gral)

    # Proyección Importe de prov_gral: para el período corriente, usa el total
    # de fin de mes proyectado en prov_diario (mismo valor por Origen, sin
    # desglosar por categoría); para períodos cerrados, usa la propia
    # Autorizaciones $ de la fila.
    diario_totales = diario.groupby('Origen Autorización')['Proyección Importe'].first()
    gral['Proyección Importe'] = gral['Autorizaciones $']
    es_actual = gral['Periodo'] == p_actual
    gral.loc[es_actual, 'Proyección Importe'] = gral.loc[es_actual, 'Origen'].map(diario_totales)

    drogueria = prov_drogueria(gral, df_nc, ne_nc)

    load_prov_gral(gral)
    load_prov_diario(diario)
    load_prov_nc(df_nc)
    load_prov_drogueria(drogueria)

    notify_success(
        'Provisión actualizada',
        fields=[
            {'name': 'General (ejercicio)', 'value': f'{len(gral):,} filas',   'inline': True},
            {'name': 'Diario',              'value': f'{len(diario):,} filas', 'inline': True},
            {'name': 'NC',                  'value': f'{len(df_nc):,} filas',  'inline': True},
            {'name': 'Droguería',           'value': f'{len(drogueria):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline provisión', exc)
        raise
