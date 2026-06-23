import os
import pandas as pd
import requests
from mstrio.project_objects import Report
from src.utils.connections import get_mstr_conn

REPORT_ID = '96B3AA41488F3ABAE3C37C97DB658B23'
IDS_INTERES = ['6', '37', '14', '17']


def fetch_tabla_control() -> pd.DataFrame:
    conn = get_mstr_conn()
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
        lineas.append('')
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
