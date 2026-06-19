import pandas as pd
import sqlite3
import datetime
from mstrio.project_objects import Report
from utils.login import conn

# Obtener la fecha de hoy
today = datetime.date.today().strftime('%Y-%m-%d')
print(f'Fecha de hoy: {today} 🗓️')

# ---BASE DE DATOS SQLITE---
# Conectar a la base de datos SQLite
conn_sql = sqlite3.connect('sda_2025_2026.sqlite')

cursor = conn_sql.cursor()

# Crear las tablas si no existen
cursor.executescript("""
CREATE TABLE IF NOT EXISTS ambulatorio (
    Periodo INTEGER,
    Fecha TEXT,
    Zona TEXT,
    Subzona TEXT,
    Rubro TEXT,
    Subrubro TEXT,
    Transaccion INTEGER,
    Prestaciones INTEGER
);

CREATE TABLE IF NOT EXISTS farmvac (
    Periodo INTEGER,
    Fecha TEXT,
    Zona TEXT,
    Subzona TEXT,
    Rubro TEXT,
    Origen TEXT,
    Cantidad INTEGER,
    Importe INTEGER
);
                     
CREATE TABLE IF NOT EXISTS provision (
    Periodo INTEGER,
    Provision TEXT,
    Origen TEXT,
    Acreedor_id INTEGER,
    Acreedor_descr TEXT,                                                                    
    Cantidad INTEGER,
    Importe INTEGER
);                    

CREATE TABLE IF NOT EXISTS discapacidad (
    Periodo INTEGER,
    Zona TEXT,
    Subzona TEXT,
    Tipo INTEGER,
    Prestacion_id TEXT,
    Prestacion_descr TEXT,
    Cantidad INTEGER
);

CREATE TABLE IF NOT EXISTS protesis (
    Periodo INTEGER,
    Zona TEXT,
    Subzona TEXT,
    Origen TEXT,
    Cantidad INTEGER,
    Importe INTEGER
);                                                                        
""")

# Confirmar los cambios
conn_sql.commit()

# ---TABLAS STRATEGY---

# AMBULATORIO F57 y F4 -> tabla 'autorizaciones'

# Autorizaciones AMBULATORIO F57 ('Periodo' >= 202410)
aut_AMB_f57_df = Report(id='E22B811F73477D450342B0BD0AFEBF21', connection=conn).to_dataframe()

# Convierte 'Fecha Prestacion Conectividad' a formato de fecha
aut_AMB_f57_df['Fecha Prestacion Conectividad'] = pd.to_datetime(
    aut_AMB_f57_df['Fecha Prestacion Conectividad'], errors='coerce'
)

# Convierte 'Periodo' y 'Tipo Orden Transaccion' a formato numérico
aut_AMB_f57_df['Periodo'] = pd.to_numeric(aut_AMB_f57_df['Periodo'], errors='coerce')
aut_AMB_f57_df['Tipo Orden Transaccion'] = pd.to_numeric(aut_AMB_f57_df['Tipo Orden Transaccion'], errors='coerce')

# Renombrar las columnas
df_rename_f57 = aut_AMB_f57_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Prestacion Conectividad': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro Prestacion Gerencia Estrategica': 'Rubro',
    'Subrubro Prestacion Gerencia Estrategica': 'Subrubro',
    'Tipo Orden Transaccion': 'Transaccion',
    'Prestaciones': 'Prestaciones'
})

# Autorizaciones AMBULATORIO F4 ('Periodo' >= 202410)
aut_AMB_f4_df = Report(id='8B41E3EED847B8CFCF27FB8330E95123', connection=conn).to_dataframe()

# Convierte 'Fecha Proceso Autorización' a formato de fecha
aut_AMB_f4_df['Fecha Proceso Autorización'] = pd.to_datetime(
    aut_AMB_f4_df['Fecha Proceso Autorización'], errors='coerce'
)

# Coonvierte 'Periodo' y 'Tipo Orden' a formato numérico
aut_AMB_f4_df['Periodo'] = pd.to_numeric(aut_AMB_f4_df['Periodo'], errors='coerce')
aut_AMB_f4_df['Tipo Orden'] = pd.to_numeric(aut_AMB_f4_df['Tipo Orden'], errors='coerce')

# Renombrar las columnas
df_rename_f4 = aut_AMB_f4_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Proceso Autorización': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro Prestacion Gerencia Estrategica': 'Rubro',
    'Subrubro Prestacion Gerencia Estrategica': 'Subrubro',
    'Tipo Orden': 'Transaccion',
    'Cantidad Prestaciones Aceptadas': 'Prestaciones'
})

# FARMACIA Y VACUNAS -> tabla 'farmvac'

# Autorizaciones FARMACIA ('Periodo' >= 202410)
farm_df = Report(id='0A3C64ABA64E7C539FC272829EBF9691', connection=conn).to_dataframe()

# Convierte 'Fecha Autorizacion Receta' a formato de fecha
farm_df['Fecha Autorizacion Receta'] = pd.to_datetime(
   farm_df['Fecha Autorizacion Receta'], errors='coerce'
)

# Coonvierte 'Periodo','Cantidad' e 'Importe' a formato numérico
farm_df['Periodo'] = pd.to_numeric(farm_df['Periodo'], errors='coerce')
farm_df['Cantidad Envases Renglón'] = pd.to_numeric(farm_df['Cantidad Envases Renglón'], errors='coerce')
farm_df['Importe Obra Social Renglón'] = pd.to_numeric(farm_df['Importe Obra Social Renglón'], errors='coerce')

# Renombrar las columnas
df_rename_farm = farm_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Autorizacion Receta': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro': 'Rubro',
    'Sistema Origen Receta': 'Origen',
    'Cantidad Envases Renglón': 'Cantidad',
    'Importe Obra Social Renglón': 'Importe'
})

# Autorizaciones VACUNAS ('Periodo' >= 202410)
vac_df = Report(id='D48C0FC538464DB761602D931765F4E1', connection=conn).to_dataframe()

# Convierte 'Fecha Autorizacion Receta' a formato de fecha
vac_df['Fecha Autorizacion Receta'] = pd.to_datetime(
   vac_df['Fecha Autorizacion Receta'], errors='coerce'
)

# Coonvierte 'Periodo','Cantidad' e 'Importe' a formato numérico
vac_df['Periodo'] = pd.to_numeric(vac_df['Periodo'], errors='coerce')
vac_df['Cantidad Envases Renglón'] = pd.to_numeric(vac_df['Cantidad Envases Renglón'], errors='coerce')
vac_df['Importe Obra Social Renglón'] = pd.to_numeric(vac_df['Importe Obra Social Renglón'], errors='coerce')

# Renombrar las columnas
df_rename_vac = vac_df.rename(columns={
    'Periodo': 'Periodo',
    'Fecha Autorizacion Receta': 'Fecha',
    'Zona Direccion Comercial Asociado': 'Zona',
    'Subzona Direccion Comercial Asociado': 'Subzona',
    'Rubro': 'Rubro',
    'Sistema Origen Receta': 'Origen',
    'Cantidad Envases Renglón': 'Cantidad',
    'Importe Obra Social Renglón': 'Importe'
})

# PROVISION -> tabla 'provision'

# Autorizaciones PROVISION ('Periodo' >= 202410)
prov_df = Report(id='FCBB48079E4A086C55DFECB0691349DB', connection=conn).to_dataframe()

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

# DISCAPACIDAD -> tabla 'discapacidad'

# Autorizaciones DISCAPACIDAD ('Periodo' >= 202410)
disc_df = Report(id='FD63C01AB840B77D7CE7E198A8441644', connection=conn).to_dataframe()

# Convierte 'Periodo','Tipo Orden' y 'Cantidad Prestaciones Aceptadas' a formato numérico
disc_df['Periodo'] = pd.to_numeric(disc_df['Periodo'], errors='coerce')
disc_df['Tipo Orden'] = pd.to_numeric(disc_df['Tipo Orden'], errors='coerce')
disc_df['Cantidad Prestaciones Aceptadas'] = pd.to_numeric(disc_df['Cantidad Prestaciones Aceptadas'], errors='coerce')

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

# PROTESIS -> tabla 'protesis'

# Autorizaciones PROTESIS ('Periodo' >= 202410)
prot_df = Report(id='6302B6E83346C3B12CC4AFA1E58A39AF', connection=conn).to_dataframe()

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

# ---INSERTAR DATOS EN SQLITE---
# Insertar los datos a la tabla 'autorizaciones'
print(f'Insertando datos de Autorizaciones AMBULATORIO F57 a la tabla ambulatorio... Total filas: {len(df_rename_f57)}')
df_rename_f57.to_sql('ambulatorio', conn_sql, if_exists='append', index=False)

print(f'Insertando datos de Autorizaciones AMBULATORIO F4 a la tabla ambulatorio... Total filas: {len(df_rename_f4)}')
df_rename_f4.to_sql('ambulatorio', conn_sql, if_exists='append', index=False)

print('🆗 Datos insertados correctamente en la tabla ambulatorio.')
print(f'Cantidad de registros en la tabla ambulatorio: {cursor.execute("SELECT COUNT(*) FROM ambulatorio").fetchone()[0]}')

# Insertar los datos a la tabla 'farmvac'
print(f'Insertando datos de Autorizaciones FARMACIA a la tabla farmvac... Total filas: {len(df_rename_farm)}')
df_rename_farm.to_sql('farmvac', conn_sql, if_exists='append', index=False)

print(f'Insertando datos de Autorizaciones VACUNAS a la tabla farmvac... Total filas: {len(df_rename_vac)}')
df_rename_vac.to_sql('farmvac', conn_sql, if_exists='append', index=False)

print('🆗 Datos insertados correctamente en la tabla farmacia.')
print(f'Cantidad de registros en la tabla farmacia: {cursor.execute("SELECT COUNT(*) FROM farmvac").fetchone()[0]}')

# Insertar los datos a la tabla 'provision'
print(f'Insertando datos de Autorizaciones PROVISION a la tabla provision... Total filas: {len(df_rename_prov)}')
df_rename_prov.to_sql('provision', conn_sql, if_exists='append', index=False)

print('🆗 Datos insertados correctamente en la tabla provision.')
print(f'Cantidad de registros en la tabla provision: {cursor.execute("SELECT COUNT(*) FROM provision").fetchone()[0]}')

# Insertar los datos a la tabla 'discapacidad'
print(f'Insertando datos de Autorizaciones DISCAPACIDAD a la tabla discapacidad... Total filas: {len(df_rename_disc)}')
df_rename_disc.to_sql('discapacidad', conn_sql, if_exists='append', index=False)

print('🆗 Datos insertados correctamente en la tabla discapacidad.')
print(f'Cantidad de registros en la tabla discapacidad: {cursor.execute("SELECT COUNT(*) FROM discapacidad").fetchone()[0]}')

# Insertar los datos a la tabla 'protesis'
print(f'Insertando datos de Autorizaciones PROTESIS a la tabla protesis... Total filas: {len(df_rename_prot)}')
df_rename_prot.to_sql('protesis', conn_sql, if_exists='append', index=False)

print('🆗 Datos insertados correctamente en la tabla protesis.')
print(f'Cantidad de registros en la tabla protesis: {cursor.execute("SELECT COUNT(*) FROM protesis").fetchone()[0]}')

# Confirmar los cambios y cerrar la conexión
conn_sql.commit()
cursor.close()
conn_sql.close()
conn.close()
