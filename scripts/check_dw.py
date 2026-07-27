import pandas as pd
from mstrio.api import cubes
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn
from src.utils.discord import notify_info

REPORT_ID = '96B3AA41488F3ABAE3C37C97DB658B23'
IDS_INTERES = ['6', '37', '14', '17']

CUBOS_INTERES = [
    '57F5D590984ABB21544132BEBB604990',  # Seguimiento Internaciones
    'CCB0D42F3B494099333E06B20AB873E1',  # Base Cirugías
]


def fetch_tabla_control(conn) -> pd.DataFrame:
    df = Report(id=REPORT_ID, connection=conn, progress_bar=False).to_dataframe()

    df = df[df['Nombre de Proceso@ID'].isin(IDS_INTERES)]
    return (
        df[['Nombre de Proceso@DESC', 'Ultima Fecha Actualización de Proceso']]
        .rename(columns={
            'Nombre de Proceso@DESC': 'Proceso',
            'Ultima Fecha Actualización de Proceso': 'Última Actualización',
        })
        .reset_index(drop=True)
    )


def fetch_cubos_info(conn) -> pd.DataFrame:
    filas = []
    for cubo_id in CUBOS_INTERES:
        info = cubes.cube_info(conn, cubo_id).json()
        cubo = info['cubesInfos'][0]
        filas.append({
            'Cubo': cubo['cubeName'],
            'Última Actualización': cubo['lastUpdateTime'],
        })
    return pd.DataFrame(filas)


def build_discord_fields(tabla: pd.DataFrame, columna_nombre: str) -> list[dict]:
    fields = []
    for _, row in tabla.iterrows():
        ts = pd.to_datetime(row['Última Actualización'], errors='coerce')
        fecha_str = ts.strftime('%d/%m/%Y %H:%M') if pd.notna(ts) else str(row['Última Actualización'])
        fields.append({'name': row[columna_nombre], 'value': f'🕐 {fecha_str}', 'inline': True})
    return fields


if __name__ == '__main__':
    conn = get_mstr_conn()
    try:
        tabla = fetch_tabla_control(conn)
        print(tabla)
        notify_info('Estado del DW', build_discord_fields(tabla, 'Proceso'))

        cubos = fetch_cubos_info(conn)
        print(cubos)
        notify_info('Estado de Cubos', build_discord_fields(cubos, 'Cubo'))
    finally:
        conn.close()
