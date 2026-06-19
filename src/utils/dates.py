import pandas as pd

# Fecha de hoy
fecha_hoy = pd.Timestamp.today()

# Periodo actual
periodo_actual = fecha_hoy.strftime('%Y-%m')
p_actual = periodo_actual.replace('-', '')

# Periodo de prestación cerrado en formato 'YYYY-MM' (en Ambulatorio es menos 5 meses porque el desfasaje es 3 y el delay de consumo es 2)
periodo_prestacion_cerrado = (fecha_hoy - pd.DateOffset(months=5)).strftime('%Y-%m')
pp_cerrado = periodo_prestacion_cerrado.replace('-', '')

# Periodo anterior en formato 'YYYY-MM'
periodo_anterior = (fecha_hoy - pd.DateOffset(months=1)).strftime('%Y-%m')
p_anterior = periodo_anterior.replace('-', '')
