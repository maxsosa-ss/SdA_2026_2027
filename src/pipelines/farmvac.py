from src.stage.farmvac import read as stage_read, stage_u6m
from src.extract.farmvac import (
    extract_farm_u6m,
    extract_vac_u6m,
    extract_ne_farmvac_q,
    extract_ne_farmvac_imp,
)
from src.extract.ambulatorio import extract_feriados
from src.transform.farmvac import preparar, proyeccion_diaria, proyeccion_ejercicio, proyeccion_importe, seg_proy_importe
from src.load.farmvac import load_proyeccion_diaria, load_proyeccion_ejercicio, load_proyeccion_importe, load_seg_proy_importe
from src.utils.discord import notify_success, notify_error


def run():
    stage_u6m(extract_farm_u6m(), extract_vac_u6m())

    df_raw = stage_read()
    ne_q   = extract_ne_farmvac_q()
    ne_imp = extract_ne_farmvac_imp()
    cal    = extract_feriados()

    df = preparar(df_raw)

    proy_dia = proyeccion_diaria(
        df,
        cal['feriado'],
        cal['no_laborable'],
        cal['turistico'],
        ne_q,
    )
    proy_ej  = proyeccion_ejercicio(df, proy_dia, ne_q)
    proy_imp    = proyeccion_importe(df, proy_dia, ne_imp)
    seg_imp_dia = seg_proy_importe(df, proy_dia, ne_imp)

    load_proyeccion_diaria(proy_dia)
    load_proyeccion_ejercicio(proy_ej)
    load_proyeccion_importe(proy_imp)
    load_seg_proy_importe(seg_imp_dia)

    notify_success(
        'Farmvac actualizado',
        fields=[
            {'name': 'Seguimiento diario',    'value': f'{len(proy_dia):,} filas',    'inline': True},
            {'name': 'General (ejercicio)',    'value': f'{len(proy_ej):,} filas',     'inline': True},
            {'name': 'Proy. importe diario',  'value': f'{len(seg_imp_dia):,} fila',  'inline': True},
        ],
    )


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        notify_error('Error en pipeline farmvac', exc)
        raise
