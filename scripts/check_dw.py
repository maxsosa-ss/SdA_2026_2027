import os
import pandas as pd
import requests
from mstrio.api import cubes
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn

REPORT_ID = '96B3AA41488F3ABAE3C37C97DB658B23'
IDS_INTERES = ['6', '37', '14', '17']

CUBOS_INTERES = [
    '5A0C8E704B69D749E96C4AB8911C2555',  # Seguimiento Internaciones
    'C74D6DAC5242DE0D4CBD0DBA74262207',  # Base Cirugías
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


def build_discord_message(tabla: pd.DataFrame, titulo: str, emoji: str, columna_nombre: str) -> str:
    lineas = [f'{emoji} **{titulo}**', '']
    for _, row in tabla.iterrows():
        ts = pd.to_datetime(row['Última Actualización'], errors='coerce')
        fecha_str = ts.strftime('%d/%m/%Y %H:%M') if pd.notna(ts) else str(row['Última Actualización'])
        lineas.append(f'🔹 **{row[columna_nombre]}**')
        lineas.append(f'   🕐 {fecha_str}')
        lineas.append('')
    return '\n'.join(lineas)


def post_discord(message: str) -> None:
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
    if not webhook_url:
        print(message)
        return
    requests.post(webhook_url, json={'content': message}, timeout=10)


if __name__ == '__main__':
    conn = get_mstr_conn()
    try:
        tabla = fetch_tabla_control(conn)
        post_discord(build_discord_message(tabla, 'Estado del DW', '🗄️', 'Proceso'))

        cubos = fetch_cubos_info(conn)
        post_discord(build_discord_message(cubos, 'Estado de Cubos', '📦', 'Cubo'))
    finally:
        conn.close()
