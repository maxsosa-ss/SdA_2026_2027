import os

import pandas as pd
import requests
from mstrio.connection import Connection
from mstrio.project_objects import Report

REPORT_ID = '96B3AA41488F3ABAE3C37C97DB658B23'
IDS_INTERES = ['6', '37', '14', '17']

MSTR_BASE_URL = 'https://tablerosancorsalud.cloud.microstrategy.com/MicroStrategyLibrary/api'
MSTR_PROJECT_ID = 'DAE6DF9811D67BD9500010A51D1D2ADA'


def fetch_tabla_control() -> pd.DataFrame:
    conn = Connection(
        MSTR_BASE_URL,
        os.environ['MSTR_USER'],
        os.environ['MSTR_PASSWORD'],
        project_id=MSTR_PROJECT_ID,
    )
    df = Report(id=REPORT_ID, connection=conn, progress_bar=False).to_dataframe()
    conn.close()

    df = df[df['Nombre de Proceso@ID'].isin(IDS_INTERES)]
    return (
        df[['Nombre de Proceso@DESC', 'Ultima Fecha Actualización de Proceso']]
        .rename(columns={
            'Nombre de Proceso@DESC': 'Proceso',
            'Ultima Fecha Actualización de Proceso': 'Última Actualización',
        })
        .reset_index(drop=True)
    )


def build_discord_message(tabla: pd.DataFrame) -> str:
    lineas = ['🗄️ **Estado del DW**', '']
    for _, row in tabla.iterrows():
        ts = pd.to_datetime(row['Última Actualización'], errors='coerce')
        fecha_str = ts.strftime('%d/%m/%Y %H:%M') if pd.notna(ts) else str(row['Última Actualización'])
        lineas.append(f'🔹 **{row["Proceso"]}**')
        lineas.append(f'   🕐 {fecha_str}')
    return '\n'.join(lineas)


def post_discord(message: str) -> None:
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL', '')
    if not webhook_url:
        print(message)
        return
    requests.post(webhook_url, json={'content': message}, timeout=10)


if __name__ == '__main__':
    tabla = fetch_tabla_control()
    post_discord(build_discord_message(tabla))
