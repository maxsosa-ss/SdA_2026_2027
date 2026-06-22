from src.stage.ambulatorio import read as stage_read
from src.extract.ambulatorio import extract_ne_amb, extract_feriados
from src.transform.ambulatorio import preparar, proyeccion_diaria, proyeccion_ejercicio
from src.load.ambulatorio import load_proyeccion_diaria, load_proyeccion_ejercicio
from src.utils.discord import notify_success, notify_error


def run():
    df_raw = stage_read()
    ne_amb = extract_ne_amb()
    cal    = extract_feriados()

    df = preparar(df_raw)

    proyamb_dia = proyeccion_diaria(
        df,
        cal['feriados'],
        cal['feriado_puro'],
        cal['no_laborables'],
        cal['fiestas'],
        ne_amb,
    )
    proyamb_ej = proyeccion_ejercicio(
        df,
        proyamb_dia,
        ne_amb,
        val_amb=None,   # TODO: agregar extract_val_amb() cuando esté disponible
    )

    load_proyeccion_diaria(proyamb_dia)
    load_proyeccion_ejercicio(proyamb_ej)

    notify_success(
        'Ambulatorio actualizado',
        fields=[
            {'name': 'Seguimiento diario',  'value': f'{len(proyamb_dia):,} filas', 'inline': True},
            {'name': 'General (ejercicio)', 'value': f'{len(proyamb_ej):,} filas',  'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        notify_error('Error en pipeline ambulatorio', exc)
        raise
