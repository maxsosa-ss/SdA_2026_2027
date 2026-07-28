from src.stage.ambulatorio import read as stage_read, stage_u6m, stage_resto, read_resto as stage_read_resto
from src.extract.ambulatorio import extract_u6m, extract_ne_amb, extract_feriados, extract_val_amb, extract_resto
from src.transform.ambulatorio import preparar, proyeccion_diaria, proyeccion_ejercicio, medidas
from src.load.ambulatorio import load_proyeccion_diaria, load_proyeccion_ejercicio, load_resto, load_medidas
from src.utils.discord import notify_success, notify_error


def run():
    """E→S→T→L completo (uso local)."""
    stage_u6m(extract_u6m())
    stage_resto(extract_resto())
    _run_tl()


def _run_tl():
    """T→L únicamente; asume que el parquet ya está staged."""
    df_raw  = stage_read()
    ne_amb  = extract_ne_amb()
    cal     = extract_feriados()
    val_amb = extract_val_amb()
    resto   = stage_read_resto()

    df = preparar(df_raw)

    proyamb_dia = proyeccion_diaria(
        df,
        cal['feriado'],
        cal['no_laborable'],
        cal['turistico'],
        ne_amb,
    )
    proyamb_ej = proyeccion_ejercicio(
        df,
        proyamb_dia,
        ne_amb,
        val_amb=val_amb,
    )
    amb_medidas = medidas(
        df,
        proyamb_dia,
        ne_amb,
        val_amb=val_amb,
    )

    load_proyeccion_diaria(proyamb_dia)
    load_proyeccion_ejercicio(proyamb_ej)
    load_resto(resto)
    load_medidas(amb_medidas)

    notify_success(
        'Ambulatorio actualizado',
        fields=[
            {'name': 'Seguimiento diario',  'value': f'{len(proyamb_dia):,} filas', 'inline': True},
            {'name': 'General (ejercicio)', 'value': f'{len(proyamb_ej):,} filas',  'inline': True},
            {'name': 'Resto',               'value': f'{len(resto):,} filas',       'inline': True},
            {'name': 'Medidas',             'value': f'{len(amb_medidas):,} filas', 'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        _run_tl()
    except Exception as exc:
        notify_error('Error en pipeline ambulatorio', exc)
        raise
