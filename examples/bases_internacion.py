from mstrio.project_objects import Report
import pandas as pd
from login import conn

# --- QUIRURGICAS ---

# Cantidades & Autorizaciones Valorizadas
r_id_1 = '9893BB69E24DAAE8C6814681ADE6931A'
q_qty_val = Report(id=r_id_1, connection=conn, progress_bar=False).to_dataframe()

q_qty_val.rename(columns={
	'Periodo Cirugía': 'Periodo'}, inplace=True)

# Niveles Esperados & Presupuesto

r_id_2 = '7372D310AB471232EF5C7EAB8D787F24'
q_ne_p = Report(id=r_id_2, connection=conn, progress_bar=False).to_dataframe()


quirurgicas = pd.merge(q_qty_val, q_ne_p,
					   on='Periodo', how='outer')
quirurgicas['Periodo'] = quirurgicas['Periodo'].astype(int)
order_q = ['Periodo', 'Eventos totales','Aut. Valorizadas', 'NE', 'PTTO']
quirurgicas = quirurgicas[order_q]

# --- SANATORIALES ---

# Cantidades
r_id_3 = 'BE1E34836C4AEB490E0B33B7B016945E'
s_qty = Report(id=r_id_3, connection=conn, progress_bar=False).to_dataframe()

s_qty.rename(columns={
	'Periodo ID': 'Periodo'}, inplace=True)

# Niveles Esperados
r_id_4 = '1994C345F8494B6D7313339B24BB6CF6'
s_ne = Report(id=r_id_4, connection=conn, progress_bar=False).to_dataframe()

s_ne.rename(columns={
	'Periodo ID': 'Periodo'}, inplace=True)

sanatoriales = pd.merge(s_qty, s_ne,
						on='Periodo', how='outer')

sanatoriales['Periodo'] = sanatoriales['Periodo'].astype(int)
order_s = ['Periodo', 'Dias Internación', 'Cantidad Internaciones', 'Nivel Esperado Días','Nivel Esperados Internación']
sanatoriales = sanatoriales[order_s]