import numpy as np
import pandas as pd

from src.utils.dates import fecha_hoy, p_actual

_ACREEDOR_ALIMENTOS = [
    '785833', '719848', '108077', '616554', '203401', '192794',
    '169179', '47359',  '644229', '20005',  '781897', '115355',
    '68378',  '46433',
]


def prov_gral(df: pd.DataFrame, ne_provision: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla general de Provisión por categoría (DROGUERIA / ALIMENTOS / OTRAS),
    Origen y Periodo, con Nivel Esperado en importe.

    Retorna DataFrame con columnas:
        Rubro, Provision AC, Origen, Periodo,
        $ Nivel Esperado, Autorizaciones $, Autorizaciones QTY
    """
    df = df.copy()
    df['Provision']   = df['Provision'].astype(str).str.strip()
    df['Origen']      = df['Origen'].astype(str).str.strip()
    df['Acreedor_id'] = df['Acreedor_id'].astype(str).str.strip()
    df['Periodo']     = df['Periodo'].astype(str).str.strip()

    condiciones = [
        df['Provision'] == 'MEDICAMENTOS ESPECIALES',
        df['Acreedor_id'].isin(_ACREEDOR_ALIMENTOS),
    ]
    df['NR'] = np.select(condiciones, ['DROGUERIA', 'ALIMENTOS'], default='OTRAS')

    agrupado = (
        df.groupby(['Periodo', 'NR', 'Origen'], as_index=False)
        [['Importe', 'Cantidad']].sum()
    )

    ne = ne_provision.copy()
    ne['Provision AC'] = ne['Provision AC'].astype(str).str.strip()
    ne['Origen']       = ne['Origen'].astype(str).str.strip()
    ne['Periodo']      = ne['Periodo'].astype(str).str.strip()

    result = ne.merge(
        agrupado,
        left_on=['Provision AC', 'Origen', 'Periodo'],
        right_on=['NR', 'Origen', 'Periodo'],
        how='left',
    )
    result = result.drop(columns=['NR'], errors='ignore')
    result = result.rename(columns={
        'Cantidad': 'Autorizaciones QTY',
        'Importe':  'Autorizaciones $',
    })
    result['Rubro'] = 'Provisión'
    result = result.fillna(0)

    cols = [
        'Rubro', 'Provision AC', 'Origen', 'Periodo',
        '$ Nivel Esperado', 'Autorizaciones $', 'Autorizaciones QTY',
    ]
    return result[cols]


def prov_diario(
    df: pd.DataFrame,
    hoy: pd.Timestamp = None,
    feriados: dict = None,
    ne_gral: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Detalle diario de Droguería con proyección lineal para los días hábiles
    restantes del mes. Se calcula por separado para Ambulatorio e Internación.

    Proyección diaria = acumulado_real / días_hábiles_con_datos

    `ne_gral`, si se pasa, es el resultado de `prov_gral()` (columnas
    'Periodo', 'Origen', '$ Nivel Esperado') usado para completar la
    columna 'Nivel Esperado' del período corriente.

    Retorna DataFrame con columnas:
        Fecha, Origen Autorización, Autorizaciones $, Autorizaciones QTY,
        Proyección, Acumulado Aut. $, Acumulado Proy. $, Nivel Esperado,
        Proyección Importe
    """
    hoy = hoy or fecha_hoy.normalize()

    df = df.copy()
    df['Origen Autorización'] = df['Origen Autorización'].astype(str).str.strip()
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

    agrupado = (
        df.groupby(['Fecha', 'Origen Autorización'], as_index=False)
        [['Autorizaciones $', 'Autorizaciones QTY']].sum()
        .sort_values('Fecha')
        .reset_index(drop=True)
    )

    # --- Calendario completo del mes ---
    if agrupado.empty:
        anio, mes = hoy.year, hoy.month
    else:
        anio = agrupado['Fecha'].dt.year.iloc[0]
        mes  = agrupado['Fecha'].dt.month.iloc[0]

    inicio_mes = pd.Timestamp(year=anio, month=mes, day=1)
    fin_mes    = inicio_mes + pd.offsets.MonthEnd(1)
    rango      = pd.date_range(start=inicio_mes, end=fin_mes)

    if feriados:
        feriados_ar = (
            feriados.get('feriado', pd.DatetimeIndex([]))
            .union(feriados.get('no_laborable', pd.DatetimeIndex([])))
            .union(feriados.get('turistico', pd.DatetimeIndex([])))
        )
    else:
        feriados_ar = pd.DatetimeIndex([])

    df_cal = pd.DataFrame({'Fecha': rango})
    es_habil = (df_cal['Fecha'].dt.dayofweek < 5) & (~df_cal['Fecha'].isin(feriados_ar))
    df_cal['Dia_Habil_Mes'] = es_habil.cumsum()
    df_cal.loc[~es_habil, 'Dia_Habil_Mes'] = np.nan

    total_dias_habiles = df_cal['Dia_Habil_Mes'].max()

    # Cruzar calendario con datos reales (left join por Fecha)
    merged = df_cal.merge(agrupado, on='Fecha', how='left')

    dia_habil_actual = merged.dropna(subset=['Autorizaciones $'])['Dia_Habil_Mes'].max()
    if pd.isna(dia_habil_actual):
        dia_habil_actual = 0
    dias_restantes = total_dias_habiles - dia_habil_actual

    print(f'📅 Total días hábiles: {total_dias_habiles} | Día hábil actual: {dia_habil_actual} | Restantes: {dias_restantes}')

    # --- Proyección diaria por Origen ---
    total_amb = agrupado.loc[agrupado['Origen Autorización'] == 'Ambulatorio', 'Autorizaciones $'].sum()
    total_int = agrupado.loc[agrupado['Origen Autorización'] == 'Internación',  'Autorizaciones $'].sum()
    p_dia_amb = total_amb / dia_habil_actual if dia_habil_actual > 0 else 0.0
    p_dia_int = total_int / dia_habil_actual if dia_habil_actual > 0 else 0.0

    # --- Columna Proyección (inicialmente NaN) ---
    merged['Proyección'] = np.nan

    # Días sin datos (Origen NaN = fines de semana / feriados sin datos)
    dias_vacios = (
        merged[merged['Origen Autorización'].isna()][['Fecha', 'Dia_Habil_Mes']]
        .drop_duplicates()
    )
    merged = merged.dropna(subset=['Origen Autorización'])

    nuevas_filas = []
    for _, row in dias_vacios.iterrows():
        proy_amb = p_dia_amb if row['Fecha'] >= hoy else 0.0
        proy_int = p_dia_int if row['Fecha'] >= hoy else 0.0
        nuevas_filas.append({
            'Fecha': row['Fecha'],
            'Dia_Habil_Mes': row['Dia_Habil_Mes'],
            'Origen Autorización': 'Ambulatorio',
            'Proyección': proy_amb,
        })
        nuevas_filas.append({
            'Fecha': row['Fecha'],
            'Dia_Habil_Mes': row['Dia_Habil_Mes'],
            'Origen Autorización': 'Internación',
            'Proyección': proy_int,
        })

    if nuevas_filas:
        merged = pd.concat([merged, pd.DataFrame(nuevas_filas)], ignore_index=True)

    # Días con datos reales que son >= hoy → asignar proyección
    merged.loc[
        (merged['Origen Autorización'] == 'Ambulatorio') & (merged['Fecha'] >= hoy),
        'Proyección',
    ] = p_dia_amb
    merged.loc[
        (merged['Origen Autorización'] == 'Internación') & (merged['Fecha'] >= hoy),
        'Proyección',
    ] = p_dia_int

    merged = merged.fillna(0)
    merged = (
        merged.drop(columns=['Dia_Habil_Mes'])
        .sort_values(['Origen Autorización', 'Fecha'])
        .reset_index(drop=True)
    )

    # --- Proyección corregida (excluye fines de semana Y feriados) ---
    es_no_habil = (merged['Fecha'].dt.dayofweek >= 5) | (merged['Fecha'].isin(feriados_ar))
    proy_corr = merged['Proyección'].where(~es_no_habil, 0.0)

    # --- Acumulados por Origen ---
    cum_real = merged.groupby('Origen Autorización')['Autorizaciones $'].cumsum()
    cum_proy = proy_corr.groupby(merged['Origen Autorización']).cumsum()

    es_futuro = merged['Fecha'] >= hoy
    merged['Acumulado Aut. $']  = cum_real.where(~es_futuro)
    merged['Acumulado Proy. $'] = (cum_real + cum_proy).where(es_futuro)

    # --- Proyección Importe: total de fin de mes por Origen (real + corregida) ---
    totales_mes = (merged['Autorizaciones $'] + proy_corr).groupby(merged['Origen Autorización']).transform('sum')
    merged['Proyección Importe'] = totales_mes

    # --- Nivel Esperado del período corriente, tomado de prov_gral ---
    if ne_gral is not None and not ne_gral.empty:
        ne_actual = (
            ne_gral.loc[ne_gral['Periodo'] == p_actual]
            .drop_duplicates('Origen')
            .set_index('Origen')['$ Nivel Esperado']
        )
        merged['Nivel Esperado'] = merged['Origen Autorización'].map(ne_actual)
    else:
        merged['Nivel Esperado'] = np.nan

    merged = merged.sort_values(['Fecha', 'Origen Autorización']).reset_index(drop=True)

    cols = [
        'Fecha', 'Origen Autorización', 'Autorizaciones $', 'Autorizaciones QTY', 'Proyección',
        'Acumulado Aut. $', 'Acumulado Proy. $', 'Nivel Esperado', 'Proyección Importe',
    ]
    return merged[cols]


def prov_drogueria(
    gral: pd.DataFrame,
    df_nc: pd.DataFrame,
    ne_nc: pd.DataFrame,
) -> pd.DataFrame:
    """
    Resumen de Provisión Droguería por Periodo (Ambulatorio + Internación
    combinados), con Nivel Esperado, Proyección Importe, e Importe
    Recepcionado / Nivel Esperado de Notas de Crédito.

    `gral` es el resultado de `prov_gral()` ya enriquecido con la columna
    'Proyección Importe' (ver `_run_tl()` en el pipeline). `df_nc` es el
    detalle crudo de NC (ya scopeado a Droguerías en el report de origen).
    `ne_nc` es el resultado de `extract_ne_provision_nc()`.

    Retorna DataFrame con columnas:
        Periodo, Autorizaciones QTY, Autorizaciones $, Proyección Importe,
        $ Nivel Esperado, Importe Recepcionado NC, Nivel Esperado NC
    """
    drogueria = gral[gral['Provision AC'] == 'DROGUERIA']
    agg = (
        drogueria.groupby('Periodo', as_index=False)
        [['Autorizaciones QTY', 'Autorizaciones $', 'Proyección Importe', '$ Nivel Esperado']]
        .sum()
    )

    nc_periodo = (
        df_nc.groupby('Periodo', as_index=False)['Importe Recepcionado'].sum()
        .rename(columns={'Importe Recepcionado': 'Importe Recepcionado NC'})
    )

    result = agg.merge(nc_periodo, on='Periodo', how='left')
    ne_nc = ne_nc[['Periodo', '$ Nivel Esperado NC']].rename(
        columns={'$ Nivel Esperado NC': 'Nivel Esperado NC'}
    )
    result = result.merge(ne_nc, on='Periodo', how='left')
    result = result.fillna(0)

    cols = [
        'Periodo', 'Autorizaciones QTY', 'Autorizaciones $', 'Proyección Importe',
        '$ Nivel Esperado', 'Importe Recepcionado NC', 'Nivel Esperado NC',
    ]
    return result[cols]
