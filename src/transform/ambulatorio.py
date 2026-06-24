import numpy as np
import pandas as pd

from src.utils.dates import fecha_hoy, p_actual
from src.utils.mapping import amb_rubros_subrubros


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns={
        'Rubro Prestacion Gerencia Estrategica':    'Rubro GE',
        'Subrubro Prestacion Gerencia Estrategica': 'Subrubro GE',
        'Zona Direccion Comercial Asociado':        'Zona DCA',
        'Subzona Direccion Comercial Asociado':     'Subzona DCA',
        'Fecha Proceso Autorización':               'Fecha',
        'Cantidad Prestaciones Aceptadas':          'Q',
    }, inplace=True)
    amb_rubros_subrubros(df)
    return df

_VENTANA_DIAS = 30
_FACTOR_FERIADO_PURO = 0.10
_FACTOR_NO_LABORABLE = 0.50
_FACTOR_FIESTA = 0.25


def _to_dt_index(fechas) -> pd.DatetimeIndex:
    """Convierte listas de strings de fechas a DatetimeIndex (evita FutureWarning de isin)."""
    if isinstance(fechas, pd.DatetimeIndex):
        return fechas
    return pd.DatetimeIndex(pd.to_datetime(list(fechas)))


def _acumulado_proyectado_grupo(g: pd.DataFrame) -> pd.Series:
    """
    Vectoriza el acumulado proyectado por grupo (Subrubro):
    - Mientras hay Nivel Real: usa Acumulado Real.
    - A partir del día siguiente al último real: acumula Nivel Proyectado.
    """
    tiene_real = g['Nivel Real'] > 0
    if not tiene_real.any():
        return g['Nivel Proyectado'].cumsum()

    ultimo_pos = tiene_real.values.nonzero()[0][-1]
    ultimo_real_val = g['Acumulado Real'].iloc[ultimo_pos]

    # Acumular Nivel Proyectado solo desde el día posterior al último real
    es_post_real = pd.Series(False, index=g.index)
    es_post_real.iloc[ultimo_pos + 1:] = True
    proy_cumsum = g['Nivel Proyectado'].where(es_post_real, 0).cumsum()

    return g['Acumulado Real'].where(tiene_real, ultimo_real_val + proy_cumsum)


def proyeccion_diaria(
    df: pd.DataFrame,
    feriado,
    no_laborable,
    turistico,
    ne_amb: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Proyección diaria de ambulatorio para el mes en curso.

    Parámetros
    ----------
    df : DataFrame ambulatorio ya mapeado (post amb_rubros_subrubros), con columnas:
         Fecha (datetime), Rubro PPTO, Subrubro PPTO, Periodo, {col_qty}
    feriado      : DatetimeIndex — feriados con actividad ~10 %
    no_laborable : DatetimeIndex — días no laborables con actividad ~50 %
    turistico    : DatetimeIndex — días turísticos con actividad ~25 %
    ne_amb : DataFrame con columnas Subrubro, Periodo, Nivel Esperado (desde GSheets)
    hoy : fecha de referencia; default = fecha_hoy de utils.dates
    periodo_actual : str 'YYYYMM'; default = p_actual de utils.dates
    col_qty : nombre de la columna de cantidades en df

    Retorna
    -------
    DataFrame con columnas:
        Fecha, Rubro, Subrubro, Nivel Real, Nivel Proyectado,
        Acumulado Real, Acumulado Proyectado, Nivel Esperado
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual

    feriado_dt      = _to_dt_index(feriado)
    no_laborable_dt = _to_dt_index(no_laborable)
    turistico_dt    = _to_dt_index(turistico)
    feriados_excl   = feriado_dt.union(no_laborable_dt).union(turistico_dt)

    fecha_inicio_ventana = hoy - pd.Timedelta(days=_VENTANA_DIAS)

    # --- Datos históricos de la ventana ---
    hist = (
        df.loc[df['Fecha'] >= fecha_inicio_ventana, ['Fecha', 'Rubro PPTO', 'Subrubro PPTO', col_qty]]
        .groupby(['Fecha', 'Rubro PPTO', 'Subrubro PPTO'], as_index=False)
        .agg({col_qty: 'sum'})
        .rename(columns={col_qty: 'Prestaciones'})
    )
    hist['Dia_Semana'] = hist['Fecha'].dt.day_name()
    hist['Es_Feriado'] = hist['Fecha'].isin(feriados_excl)

    # --- Promedio por día de la semana (excluyendo feriados y hoy) ---
    # Se excluye hoy para evitar que datos parciales distorsionen el promedio del weekday
    prom_semana = (
        hist.loc[~hist['Es_Feriado'] & (hist['Fecha'] < hoy)]
        .groupby(['Rubro PPTO', 'Subrubro PPTO', 'Dia_Semana'], as_index=False)
        .agg({'Prestaciones': 'mean'})
        .rename(columns={'Prestaciones': 'Promedio_Semanal'})
        .round()
    )

    # --- Calendario del mes actual ---
    ultima_fecha = hist['Fecha'].max()
    inicio_mes = ultima_fecha.replace(day=1)
    fin_mes = ultima_fecha + pd.offsets.MonthEnd(0)

    cal = pd.DataFrame({'Fecha': pd.date_range(inicio_mes, fin_mes)})
    cal['Dia_Semana'] = cal['Fecha'].dt.day_name()
    cal['Es_Feriado'] = cal['Fecha'].isin(feriados_excl)

    # --- Producto cartesiano: calendario × combinaciones únicas ---
    combinaciones = hist[['Rubro PPTO', 'Subrubro PPTO']].drop_duplicates()
    base = cal.assign(_k=1).merge(combinaciones.assign(_k=1), on='_k').drop(columns='_k')

    # Unir datos reales
    base = base.merge(
        hist[['Fecha', 'Rubro PPTO', 'Subrubro PPTO', 'Prestaciones']],
        on=['Fecha', 'Rubro PPTO', 'Subrubro PPTO'],
        how='left',
    )

    # Unir promedios semanales
    base = base.merge(prom_semana, on=['Rubro PPTO', 'Subrubro PPTO', 'Dia_Semana'], how='left')

    # --- Nivel Proyectado con ajustes por tipo de día ---
    base['Nivel Proyectado'] = base['Promedio_Semanal']
    base['Nivel Proyectado'] = np.where(
        base['Fecha'].isin(feriado_dt),
        (base['Nivel Proyectado'] * _FACTOR_FERIADO_PURO).round(),
        base['Nivel Proyectado'],
    )
    base['Nivel Proyectado'] = np.where(
        base['Fecha'].isin(no_laborable_dt),
        (base['Nivel Proyectado'] * _FACTOR_NO_LABORABLE).round(),
        base['Nivel Proyectado'],
    )
    base['Nivel Proyectado'] = np.where(
        base['Fecha'].isin(turistico_dt),
        (base['Nivel Proyectado'] * _FACTOR_FIESTA).round(),
        base['Nivel Proyectado'],
    )

    # --- Agregación final ---
    result = (
        base
        .groupby(['Fecha', 'Rubro PPTO', 'Subrubro PPTO'], as_index=False)
        .agg({'Prestaciones': 'sum', 'Nivel Proyectado': 'sum'})
        .sort_values(['Rubro PPTO', 'Fecha'])
        .reset_index(drop=True)
        .fillna(0)
        .infer_objects(copy=False)
    )
    result = result.astype({'Nivel Proyectado': int, 'Prestaciones': int})

    # --- Nivel Esperado ---
    ne = (
        ne_amb.loc[ne_amb['Periodo'].astype(str) == str(periodo_actual)]
        .groupby('Subrubro', as_index=False)
        .agg({'Nivel Esperado': 'sum'})
        .astype({'Nivel Esperado': int})
    )

    result = (
        result
        .merge(ne, left_on='Subrubro PPTO', right_on='Subrubro', how='left')
        .drop(columns='Subrubro')
        .rename(columns={
            'Rubro PPTO': 'Rubro',
            'Subrubro PPTO': 'Subrubro',
            'Prestaciones': 'Nivel Real',
        })
    )

    # --- Acumulados ---
    result['Acumulado Real'] = result.groupby('Subrubro')['Nivel Real'].cumsum()

    result['Acumulado Proyectado'] = (
        result.groupby('Subrubro', group_keys=False)
        .apply(_acumulado_proyectado_grupo)
    )

    # Acumulado Real: sólo hasta ayer inclusive
    result['Acumulado Real'] = result['Acumulado Real'].where(result['Fecha'] < hoy, 0)
    # Acumulado Proyectado: sólo desde hoy en adelante
    result['Acumulado Proyectado'] = result['Acumulado Proyectado'].where(result['Fecha'] >= hoy, 0)
    result['Acumulado Proyectado'] = result['Acumulado Proyectado'].fillna(0).astype(int)

    cols = ['Fecha', 'Rubro', 'Subrubro', 'Nivel Real', 'Nivel Proyectado',
            'Acumulado Real', 'Acumulado Proyectado', 'Nivel Esperado']
    return result[cols]


def proyeccion_ejercicio(
    df: pd.DataFrame,
    proyamb_dia: pd.DataFrame,
    ne_amb: pd.DataFrame,
    val_amb: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Proyección del ejercicio (todos los periodos) de ambulatorio.

    Parámetros
    ----------
    df : DataFrame ambulatorio ya mapeado, con columnas:
         Fecha, Rubro PPTO, Subrubro PPTO, Zona DCA, Subzona DCA, Periodo, {col_qty}
    proyamb_dia : salida de proyeccion_diaria() — se usa el último Acumulado Proyectado por Subrubro
    ne_amb : DataFrame con columnas Rubro, Subrubro, Zona DCA, Subzona DCA, Periodo, Nivel Esperado
    val_amb : DataFrame con columnas Rubro, Subrubro, Zona DCA, Subzona DCA, Periodo, Conversor, VU, M2
    hoy : fecha de referencia; default = fecha_hoy de utils.dates
    periodo_actual : str 'YYYYMM'; default = p_actual de utils.dates
    col_qty : nombre de la columna de cantidades en df

    Retorna
    -------
    DataFrame con columnas:
        Rubro, Subrubro, Zona DCA, Subzona DCA, Periodo, Nivel Esperado,
        Prestaciones, Aut. Proyectadas, Faltante, Dif. valorizada
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual

    # --- Prestaciones reales agrupadas ---
    prestaciones = (
        df.groupby(['Rubro PPTO', 'Subrubro PPTO', 'Zona DCA', 'Subzona DCA', 'Periodo'], as_index=False)
        [col_qty].sum()
        .rename(columns={
            'Rubro PPTO': 'Rubro',
            'Subrubro PPTO': 'Subrubro',
            col_qty: 'Prestaciones',
        })
    )

    # --- Base: ne_amb + prestaciones reales ---
    result = ne_amb.merge(
        prestaciones,
        on=['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo'],
        how='left',
    )
    result['Nivel Esperado'] = result['Nivel Esperado'].fillna(0)
    result['Prestaciones'] = result['Prestaciones'].fillna(0).infer_objects(copy=False).astype(int)

    # --- Incidencia por zona/subzona (periodos anteriores al actual) ---
    hist_prev = df.loc[df['Periodo'].astype(str) < str(periodo_actual)]
    inc = (
        hist_prev.groupby(['Rubro PPTO', 'Subrubro PPTO', 'Zona DCA', 'Subzona DCA'], as_index=False)
        [col_qty].sum()
        .rename(columns={'Rubro PPTO': 'Rubro', 'Subrubro PPTO': 'Subrubro', col_qty: 'Prest_hist'})
    )
    inc['Total Subrubro'] = inc.groupby('Subrubro')['Prest_hist'].transform('sum')
    inc['Incidencia'] = inc['Prest_hist'] / inc['Total Subrubro']

    # --- Último Acumulado Proyectado por Subrubro ---
    ultimos_proy = proyamb_dia.groupby('Subrubro')['Acumulado Proyectado'].last().to_dict()
    result['Aut. Proyectadas'] = result['Subrubro'].map(ultimos_proy)

    # --- Merge de incidencia ---
    result = result.merge(
        inc[['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Incidencia', 'Total Subrubro']],
        on=['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA'],
        how='left',
    )
    result['Incidencia'] = pd.to_numeric(result['Incidencia'], errors='coerce').fillna(0)
    result['Aut. Proyectadas'] = pd.to_numeric(result['Aut. Proyectadas'], errors='coerce').fillna(0)

    # --- Distribuir proyectadas para el periodo actual según incidencia ---
    mask_actual = result['Periodo'].astype(str) == str(periodo_actual)

    if hoy.day > 10:
        result.loc[mask_actual, 'Aut. Proyectadas'] = (
            (result.loc[mask_actual, 'Aut. Proyectadas'] * result.loc[mask_actual, 'Incidencia'])
            .round()
            .astype(int)
        )
        result.loc[~mask_actual, 'Aut. Proyectadas'] = result.loc[~mask_actual, 'Prestaciones']
    else:
        result['Aut. Proyectadas'] = 0
        result.loc[~mask_actual, 'Aut. Proyectadas'] = result.loc[~mask_actual, 'Prestaciones']

    result['Aut. Proyectadas'] = result['Aut. Proyectadas'].fillna(0).infer_objects(copy=False).astype(int)

    # --- Desvío y valorización ---
    desvio = (
        result.groupby(['Periodo', 'Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA'], as_index=False)
        [['Nivel Esperado', 'Aut. Proyectadas', 'Prestaciones']].sum()
    )
    desvio['Desvio Proyectado'] = (
        (desvio['Aut. Proyectadas'] / desvio['Nivel Esperado']) - 1
    ).round(6)

    desvio['Faltante'] = desvio['Aut. Proyectadas'] - desvio['Prestaciones']

    if val_amb is not None:
        valorizado = desvio.merge(
            val_amb,
            on=['Periodo', 'Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA'],
            how='left',
        )
        valorizado['Dif. valorizada Periodo Prestación'] = (
            valorizado['Conversor'] * valorizado['VU']
            * (valorizado['Aut. Proyectadas'] - valorizado['Nivel Esperado'])
        )
        valorizado['Dif. valorizada'] = (
            valorizado['M2'] * valorizado['Dif. valorizada Periodo Prestación']
        ).fillna(0)
    else:
        valorizado = desvio.copy()
        valorizado['Dif. valorizada'] = 0.0

    cols_out = [
        'Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo',
        'Nivel Esperado', 'Prestaciones', 'Aut. Proyectadas', 'Faltante', 'Dif. valorizada',
    ]
    return valorizado[cols_out]
