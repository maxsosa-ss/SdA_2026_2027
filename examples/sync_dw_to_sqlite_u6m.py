import pandas as pd
import sqlite3
import datetime
from mstrio.project_objects import Report
from utils.login import conn

# Obtener la fecha de hoy
today = datetime.date.today().strftime('%Y-%m-%d')
print(f'🗓️ Fecha de hoy: {today}')

# ---BASE DE DATOS SQLITE---
# Conectar a la base de datos SQLite
conn_sql = sqlite3.connect('sda_2025_2026.sqlite')

cursor = conn_sql.cursor()

# Filtrar últimos 6 meses desde hoy
fecha_limite = pd.Timestamp.today() - pd.DateOffset(months=6)

# Convertir la fecha límite a string compatible con SQLite
fecha_str = fecha_limite.strftime('%Y-%m-%d')

# Eliminar registros de los últimos 6 meses de la tabla 'ambulatorio' y 'farmvac'
cursor.execute("""
DELETE FROM ambulatorio
WHERE Fecha >= ?
""", (fecha_str,))

# Obtener la cantidad de registros eliminados
registros_eliminados_ambulatorio = cursor.rowcount

# Eliminar registros de los últimos 6 meses de la tabla 'farmvac'
cursor.execute("""
DELETE FROM farmvac
WHERE Fecha >= ?
""", (fecha_str,))

registros_eliminados_farmvac = cursor.rowcount

# Imprimir la cantidad de registros eliminados
print(f'🧮 Cantidad de registros eliminados en ambulatorio: {registros_eliminados_ambulatorio}')
print(f'🧮 Cantidad de registros eliminados en farmvac: {registros_eliminados_farmvac}')
print(f'🗑️ Registros eliminados desde {fecha_str} en la tabla ambulatorio y farmvac.')

# Confirmar y cerrar
conn_sql.commit()

# ---TABLAS STRATEGY---
# AMBULATORIO F57 y F4 Últimos 6 meses -> Tabla de 'autorizaciones'

# Autorizaciones AMBULATORIO F57 Últimos 6 meses
aut_AMB_f57_u6m_df = Report(id='A56FCF021448592FE462F582E9446136', connection=conn, progress_bar=False).to_dataframe()

# Convert 'Fecha Prestacion Conectividad' to datetime format
aut_AMB_f57_u6m_df['Fecha Prestacion Conectividad'] = pd.to_datetime(
    aut_AMB_f57_u6m_df['Fecha Prestacion Conectividad'], errors='coerce'
)

# Coonvierte 'Periodo' y 'Tipo Orden Transaccion' a formato numérico
aut_AMB_f57_u6m_df['Periodo'] = pd.to_numeric(aut_AMB_f57_u6m_df['Periodo'], errors='coerce')
aut_AMB_f57_u6m_df['Tipo Orden Transaccion'] = pd.to_numeric(aut_AMB_f57_u6m_df['Tipo Orden Transaccion'], errors='coerce')

df_rename_f57_u6m = aut_AMB_f57_u6m_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Prestacion Conectividad': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro Prestacion Gerencia Estrategica': 'Rubro',
    'Subrubro Prestacion Gerencia Estrategica': 'Subrubro',
    'Tipo Orden Transaccion': 'Transaccion',
    'Prestaciones': 'Prestaciones'
})

print(f'⚙️ Cantidad de registros en Autorizaciones AMBULATORIO F57 en los U6M: {len(df_rename_f57_u6m)}')

# Autorizaciones AMBULATORIO F4 Últimos 6 meses
aut_AMB_f4_u6m_df = Report(id='2C938EDEFE42E6C843E10FBACFA21A8B', connection=conn, progress_bar=False).to_dataframe()

# Convert 'Fecha Proceso Autorización' to datetime format
aut_AMB_f4_u6m_df['Fecha Proceso Autorización'] = pd.to_datetime(
    aut_AMB_f4_u6m_df['Fecha Proceso Autorización'], errors='coerce'
)

# Coonvierte 'Periodo' y 'Tipo Orden' a formato numérico
aut_AMB_f4_u6m_df['Periodo'] = pd.to_numeric(aut_AMB_f4_u6m_df['Periodo'], errors='coerce')
aut_AMB_f4_u6m_df['Tipo Orden'] = pd.to_numeric(aut_AMB_f4_u6m_df['Tipo Orden'], errors='coerce')

df_rename_f4_u6m = aut_AMB_f4_u6m_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Proceso Autorización': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro Prestacion Gerencia Estrategica': 'Rubro',
    'Subrubro Prestacion Gerencia Estrategica': 'Subrubro',
    'Tipo Orden': 'Transaccion',
    'Cantidad Prestaciones Aceptadas': 'Prestaciones'
})

print(f'⚙️ Cantidad de registros en Autorizaciones AMBULATORIO F4 en los U6M: {len(df_rename_f4_u6m)}')

# FARMACIA Y VACUNAS Últimos 6 meses -> tabla 'farmvac'

# Autorizaciones FARMACIA Últimos 6 meses
farm_df_u6m = Report(id='E9BB407DF04FA120D71037BB096A9E69', connection=conn, progress_bar=False).to_dataframe()

# Convierte 'Fecha Autorizacion Receta' a formato de fecha
farm_df_u6m['Fecha Autorizacion Receta'] = pd.to_datetime(
   farm_df_u6m['Fecha Autorizacion Receta'], errors='coerce'
)

# Coonvierte 'Periodo','Cantidad' e 'Importe' a formato numérico
farm_df_u6m['Periodo'] = pd.to_numeric(farm_df_u6m['Periodo'], errors='coerce')
farm_df_u6m['Cantidad Envases Renglón'] = pd.to_numeric(farm_df_u6m['Cantidad Envases Renglón'], errors='coerce')
farm_df_u6m['Importe Obra Social Renglón'] = pd.to_numeric(farm_df_u6m['Importe Obra Social Renglón'], errors='coerce')

# Renombrar las columnas
df_rename_farm_u6m = farm_df_u6m.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Autorizacion Receta': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro': 'Rubro',
    'Sistema Origen Receta': 'Origen',
    'Cantidad Envases Renglón': 'Cantidad',
    'Importe Obra Social Renglón': 'Importe'
})

print(f'⚙️ Cantidad de registros en Autorizaciones FARMACIA en los U6M: {len(df_rename_farm_u6m)}')

# Autorizaciones VACUNAS Últimos 6 meses
vac_df_u6m = Report(id='F214594EBE4A4BE491C1E99DD5B63992', connection=conn, progress_bar=False).to_dataframe()

# Convierte 'Fecha Autorizacion Receta' a formato de fecha
vac_df_u6m['Fecha Autorizacion Receta'] = pd.to_datetime(
   vac_df_u6m['Fecha Autorizacion Receta'], errors='coerce'
)

# Coonvierte 'Periodo','Cantidad' e 'Importe' a formato numérico
vac_df_u6m['Periodo'] = pd.to_numeric(vac_df_u6m['Periodo'], errors='coerce')
vac_df_u6m['Cantidad Envases Renglón'] = pd.to_numeric(vac_df_u6m['Cantidad Envases Renglón'], errors='coerce')
vac_df_u6m['Importe Obra Social Renglón'] = pd.to_numeric(vac_df_u6m['Importe Obra Social Renglón'], errors='coerce')

# Renombrar las columnas
df_rename_vac_u6m = vac_df_u6m.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Autorizacion Receta': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro': 'Rubro',
    'Sistema Origen Receta': 'Origen',
    'Cantidad Envases Renglón': 'Cantidad',
    'Importe Obra Social Renglón': 'Importe'
})

print(f'⚙️ Cantidad de registros en Autorizaciones VACUNAS en los U6M: {len(df_rename_vac_u6m)}')

# PROVISION -> tabla 'provision'

# Autorizaciones PROVISION ('Periodo' >= 202410)
prov_df = Report(id='FCBB48079E4A086C55DFECB0691349DB', connection=conn, progress_bar=False).to_dataframe()

# Convierte 'Periodo','Cantidad' e 'Importe' a formato numérico
prov_df['Periodo'] = pd.to_numeric(prov_df['Periodo'], errors='coerce')
prov_df['Cantidad Prestaciones Aceptadas'] = pd.to_numeric(prov_df['Cantidad Prestaciones Aceptadas'], errors='coerce')
prov_df['Importe Comprobante Prestacion'] = pd.to_numeric(prov_df['Importe Comprobante Prestacion'], errors='coerce')

# Renombrar las columnas para provision
df_rename_prov = prov_df.rename(columns={
    'Periodo': 'Periodo',
    'Provision Profesional Actuante': 'Provision',
    'Origen Autorización':'Origen',
    'Acreedor@ID': 'Acreedor_id',
    'Acreedor@DESC': 'Acreedor_descr',
    'Cantidad Prestaciones Aceptadas': 'Cantidad',
    'Importe Comprobante Prestacion': 'Importe'
})

print(f'⚙️ Cantidad de registros en Autorizaciones PROVISION: {len(df_rename_prov)}')

# DISCAPACIDAD -> tabla 'discapacidad'

# Autorizaciones DISCAPACIDAD ('Periodo' >= 202410)
disc_df = Report(id='FD63C01AB840B77D7CE7E198A8441644', connection=conn, progress_bar=False).to_dataframe()

# Convierte 'Periodo','Tipo Orden' y 'Cantidad Prestaciones Aceptadas' a formato numérico
disc_df['Periodo'] = pd.to_numeric(disc_df['Periodo'], errors='coerce')
disc_df['Tipo Orden'] = pd.to_numeric(disc_df['Tipo Orden'], errors='coerce')
disc_df['Cantidad Prestaciones Aceptadas'] = pd.to_numeric(disc_df['Cantidad Prestaciones Aceptadas'], errors='coerce')
disc_df['Prestacion@ID'] = disc_df['Prestacion@ID'].astype(str).str.strip()


# Renombrar las columnas
df_rename_disc = disc_df.rename(columns={
    'Periodo': 'Periodo',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Tipo Orden': 'Tipo',
    'Prestacion@ID': 'Prestacion_id',
    'Prestacion@DESC': 'Prestacion_descr',
    'Cantidad Prestaciones Aceptadas': 'Cantidad'
})

print(f'⚙️ Cantidad de registros en Autorizaciones DISCAPACIDAD: {len(df_rename_disc)}')

# PROTESIS -> tabla 'protesis'

# Autorizaciones PROTESIS ('Periodo' >= 202410)
prot_df = Report(id='6302B6E83346C3B12CC4AFA1E58A39AF', connection=conn, progress_bar=False).to_dataframe()

# Convierte 'Periodo', 'Cantidad Prestaciones Aceptadas' e 'Importe Comprobante Prestacion' a formato numérico
prot_df['Periodo'] = pd.to_numeric(prot_df['Periodo'], errors='coerce')
prot_df['Cantidad Prestaciones Aceptadas'] = pd.to_numeric(prot_df['Cantidad Prestaciones Aceptadas'], errors='coerce')
prot_df['Importe Comprobante Prestacion'] = pd.to_numeric(prot_df['Importe Comprobante Prestacion'], errors='coerce')

# Renombrar las columnas para protesis
df_rename_prot = prot_df.rename(columns={
    'Periodo': 'Periodo',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Origen Autorización': 'Origen',
    'Cantidad Prestaciones Aceptadas': 'Cantidad',
    'Importe Comprobante Prestacion': 'Importe'  
})

print(f'⚙️ Cantidad de registros en Autorizaciones PROTESIS: {len(df_rename_prot)}')

# ---INSERTAR DATOS EN SQLITE---
# Insertar los datos a la tabla 'autorizaciones'
df_rename_f57_u6m.to_sql('ambulatorio', conn_sql, if_exists='append', index=False)
print(f'🆗 Cantidad de registros agregados de Autorizaciones AMBULATORIOS F57: {len(df_rename_f57_u6m)}')

df_rename_f4_u6m.to_sql('ambulatorio', conn_sql, if_exists='append', index=False)
print(f'🆗 Cantidad de registros agregados de Autorizaciones AMBULATORIOS F4: {len(df_rename_f4_u6m)}')

# Insertar los datos a la tabla 'farmvac'
df_rename_farm_u6m.to_sql('farmvac', conn_sql, if_exists='append', index=False)
print(f'🆗 Cantidad de registros agregados de Autorizaciones FARMACIA: {len(df_rename_farm_u6m)}')

df_rename_vac_u6m.to_sql('farmvac', conn_sql, if_exists='append', index=False)
print(f'🆗 Cantidad de registros agregados de Autorizaciones VACUNAS: {len(df_rename_vac_u6m)}')

# Insertar los datos a la tabla 'provision'
df_rename_prov.to_sql('provision', conn_sql, if_exists='replace', index=False)
print(f'🆗 Cantidad de registros actualizados de Autorizaciones PROVISION: {len(df_rename_prov)}')

# Insertar los datos a la tabla 'discapacidad'
df_rename_disc.to_sql('discapacidad', conn_sql, if_exists='replace', index=False)
print(f'🆗 Cantidad de registros actualizados de Autorizaciones DISCAPACIDAD: {len(df_rename_disc)}')

# Insertar los datos a la tabla 'protesis'
df_rename_prot.to_sql('protesis', conn_sql, if_exists='replace', index=False)
print(f'🆗 Cantidad de registros actualizados de Autorizaciones PROTESIS: {len(df_rename_prot)}')

# Confirmar los cambios y cerrar la conexión
conn_sql.commit()
cursor.close()
conn_sql.close()
