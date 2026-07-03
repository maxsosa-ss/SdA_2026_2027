import numpy as np
import pandas as pd

from src.utils.dates import fecha_hoy, p_actual

_VENTANA_DIAS        = 30
_FACTOR_FERIADO_PURO = 0.10
_FACTOR_NO_LABORABLE = 0.50
_FACTOR_TURISTICO    = 0.25

_DIAS_ES = {
    'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
    'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo',
}


def _to_dt_index(fechas) -> pd.DatetimeIndex:
    if isinstance(fechas, pd.DatetimeIndex):
        return fechas
    return pd.DatetimeIndex(pd.to_datetime(list(fechas)))


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.rename(columns={
        'Rubro PPTO':                             'Rubro',
        'Subrubro PPTO':                          'Subrubro',
        'Fecha Autorizacion Receta':              'Fecha',
        'Zona Direccion Comercial Asociado':      'Zona DCA',
        'Subzona Direccion Comercial Asociado':   'Subzona DCA',
        'Cantidad Envases Renglón':               'Q',
        'Importe Obra Social Renglón':            'Importe',
    }, inplace=True)
    df['Q']       = pd.to_numeric(df['Q'],       errors='coerce').fillna(0)
    df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce').fillna(0)
    return df


def proyeccion_diaria(
    df: pd.DataFrame,
    feriado,
    no_laborable,
    turistico,
    ne_q: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Proyección diaria de Farmacia para el mes en curso.
    Farmacia se identifica por Subrubro == 'Farmacia' (Rubro siempre es 'Farmacia').

    Retorna DataFrame con columnas:
        Fecha, Rubro, Subrubro, Nivel Real, Nivel Proyectado,
        Acumulado Real, Acumulado Proyectado, Nivel Esperado
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual

    feriado_dt      = _to_dt_index(feriado)
    no_laborable_dt = _to_dt_index(no_laborable)
    turistico_dt    = _to_dt_index(turistico)
    todos_no_hab    = feriado_dt.union(no_laborable_dt).union(turistico_dt)

    fecha_inicio_ventana = hoy - pd.Timedelta(days=_VENTANA_DIAS)

    # --- Histórico de Farmacia para promedios (excluye hoy) ---
    hist = (
        df.loc[
            (df['Subrubro'] == 'Farmacia') &
            (df['Fecha'] < hoy) &
            (df['Fecha'] >= fecha_inicio_ventana),
            ['Fecha', col_qty]
        ]
        .groupby('Fecha', as_index=False)
        .agg({col_qty: 'sum'})
        .rename(columns={col_qty: 'Cantidad'})
    )
    hist['Dia'] = hist['Fecha'].dt.day_name().map(_DIAS_ES)

    # --- Promedio por día de la semana (excluye feriados/no laborables/turísticos) ---
    promedios = (
        hist.loc[~hist['Fecha'].isin(todos_no_hab)]
        .groupby('Dia')['Cantidad'].mean().round()
    )

    # --- Calendario del mes ---
    ultima_fecha = hist['Fecha'].max()
    inicio_mes = ultima_fecha.replace(day=1)
    fin_mes    = ultima_fecha + pd.offsets.MonthEnd(0)

    cal = pd.DataFrame({'Fecha': pd.date_range(inicio_mes, fin_mes)})
    cal['Dia'] = cal['Fecha'].dt.day_name().map(_DIAS_ES)

    # --- Nivel Real: Farmacia del mes, hasta ayer ---
    farm_mes = (
        df.loc[
            (df['Subrubro'] == 'Farmacia') &
            (df['Fecha'] >= inicio_mes) &
            (df['Fecha'] < hoy),
            ['Fecha', col_qty]
        ]
        .groupby('Fecha', as_index=False)
        .agg({col_qty: 'sum'})
        .rename(columns={col_qty: 'Nivel Real'})
    )
    cal = cal.merge(farm_mes, on='Fecha', how='left')
    cal['Nivel Real'] = cal['Nivel Real'].fillna(0).astype(int)

    # --- Nivel Proyectado con ajustes por tipo de día ---
    cal['Nivel Proyectado'] = cal['Dia'].map(promedios)
    cal['Nivel Proyectado'] = np.where(
        cal['Fecha'].isin(feriado_dt),
        (cal['Nivel Proyectado'] * _FACTOR_FERIADO_PURO).round(),
        cal['Nivel Proyectado'],
    )
    cal['Nivel Proyectado'] = np.where(
        cal['Fecha'].isin(no_laborable_dt),
        (cal['Nivel Proyectado'] * _FACTOR_NO_LABORABLE).round(),
        cal['Nivel Proyectado'],
    )
    cal['Nivel Proyectado'] = np.where(
        cal['Fecha'].isin(turistico_dt),
        (cal['Nivel Proyectado'] * _FACTOR_TURISTICO).round(),
        cal['Nivel Proyectado'],
    )
    cal['Nivel Proyectado'] = (
        cal['Nivel Proyectado'].fillna(0).infer_objects(copy=False).astype(int)
    )

    # --- Acumulado Real (hasta ayer, 0 desde hoy) ---
    cal['Acumulado Real'] = cal['Nivel Real'].cumsum()
    cal['Acumulado Real'] = cal['Acumulado Real'].where(cal['Fecha'] < hoy, 0)

    # --- Acumulado Proyectado (desde hoy, continúa donde terminó el real) ---
    real_antes_hoy = cal.loc[cal['Fecha'] < hoy, 'Acumulado Real']
    ultimo_real = int(real_antes_hoy.iloc[-1]) if not real_antes_hoy.empty else 0

    es_post     = cal['Fecha'] >= hoy
    proy_cumsum = cal['Nivel Proyectado'].where(es_post, 0).cumsum()
    cal['Acumulado Proyectado'] = np.where(
        es_post, (ultimo_real + proy_cumsum).astype(int), 0
    )

    # --- Nivel Esperado (suma sobre Subrubros del NE para Farmacia) ---
    ne_val = (
        ne_q.loc[
            (ne_q['Subrubro'] == 'Farmacia') &
            (ne_q['Periodo'].astype(str) == str(periodo_actual)),
            'Nivel Esperado',
        ].sum()
    )
    cal['Nivel Esperado'] = int(ne_val)
    cal['Rubro']    = 'Farmacia'
    cal['Subrubro'] = 'Farmacia'

    cols = [
        'Fecha', 'Rubro', 'Subrubro', 'Nivel Real', 'Nivel Proyectado',
        'Acumulado Real', 'Acumulado Proyectado', 'Nivel Esperado',
    ]
    return cal[cols]


def proyeccion_ejercicio(
    df: pd.DataFrame,
    proy_dia: pd.DataFrame,
    ne_q: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Proyección del ejercicio para Farmacia y Vacunas (todos los periodos).
    Se mergea por Rubro + Subrubro + Zona DCA + Subzona DCA + Periodo.

    Retorna DataFrame con columnas:
        Rubro, Subrubro, Zona DCA, Subzona DCA, Periodo,
        Nivel Esperado, Cantidad, Aut. Proyectadas
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual

    # --- Real agrupado por Rubro, Subrubro, Zona, Subzona, Periodo ---
    real = (
        df.groupby(['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo'], as_index=False)
        [col_qty].sum()
        .rename(columns={col_qty: 'Cantidad'})
    )
    real['Periodo'] = real['Periodo'].astype(str)

    # --- Base: ne_q + real (merge a nivel Subrubro) ---
    result = ne_q.merge(
        real,
        on=['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo'],
        how='left',
    )
    result['Nivel Esperado'] = result['Nivel Esperado'].fillna(0)
    result['Cantidad'] = result['Cantidad'].fillna(0).infer_objects(copy=False).astype(int)

    # --- Incidencia: Farmacia histórica (todos los periodos hasta ayer) por Zona/Subzona ---
    hist_farm = (
        df.loc[(df['Subrubro'] == 'Farmacia') & (df['Fecha'] < hoy)]
        .groupby(['Zona DCA', 'Subzona DCA'], as_index=False)
        [col_qty].sum()
        .rename(columns={col_qty: 'Q_hist'})
    )
    total_hist = hist_farm['Q_hist'].sum()
    hist_farm['Incidencia'] = (
        hist_farm['Q_hist'] / total_hist if total_hist > 0 else 0.0
    )

    # --- Último Acumulado Proyectado de Farmacia (fin de mes) ---
    ultimo_proy = int(proy_dia['Acumulado Proyectado'].iloc[-1])

    # --- Merge de incidencia ---
    result = result.merge(
        hist_farm[['Zona DCA', 'Subzona DCA', 'Incidencia']],
        on=['Zona DCA', 'Subzona DCA'],
        how='left',
    )
    result['Incidencia'] = pd.to_numeric(result['Incidencia'], errors='coerce').fillna(0)
    result['Aut. Proyectadas'] = 0

    cond_farmacia = result['Subrubro'] == 'Farmacia'
    mask_actual   = result['Periodo'].astype(str) == str(periodo_actual)

    if hoy.day > 10:
        # Farmacia, periodo actual → distribuir proyectadas por incidencia
        result.loc[mask_actual & cond_farmacia, 'Aut. Proyectadas'] = (
            (ultimo_proy * result.loc[mask_actual & cond_farmacia, 'Incidencia'])
            .round()
            .astype(int)
        )
        # Periodos anteriores → usar real
        result.loc[~mask_actual, 'Aut. Proyectadas'] = result.loc[~mask_actual, 'Cantidad']
    else:
        # Primeros 10 días: sin proyección en el periodo actual
        result.loc[~mask_actual, 'Aut. Proyectadas'] = result.loc[~mask_actual, 'Cantidad']

    # Vacunas siempre en 0 (sin proyección)
    result.loc[~cond_farmacia, 'Aut. Proyectadas'] = 0
    result['Aut. Proyectadas'] = (
        result['Aut. Proyectadas'].fillna(0).infer_objects(copy=False).astype(int)
    )

    cols = [
        'Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo',
        'Nivel Esperado', 'Cantidad', 'Aut. Proyectadas',
    ]
    return result[cols]


def seg_proy_importe(
    df: pd.DataFrame,
    proy_dia: pd.DataFrame,
    ne_imp: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Fila diaria de seguimiento del importe proyectado de Farmacia.
    Columnas: Fecha | Real | Importe Proyectado | Nivel Esperado
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual
    ayer = hoy - pd.Timedelta(days=1)

    farm_period = (
        df.loc[
            (df['Subrubro'] == 'Farmacia') &
            (df['Periodo'].astype(str) == str(periodo_actual)) &
            (df['Fecha'] < hoy),
            ['Fecha', col_qty, 'Importe']
        ]
        .groupby('Fecha', as_index=False)
        .agg({col_qty: 'sum', 'Importe': 'sum'})
    )

    total_importe_real = farm_period['Importe'].sum()
    promedio_costo = 0.0
    if not farm_period.empty and farm_period[col_qty].sum() > 0:
        promedio_costo = (
            farm_period['Importe'] / farm_period[col_qty].replace(0, np.nan)
        ).mean()
        if pd.isna(promedio_costo):
            promedio_costo = 0.0

    acum_proy_fin  = int(proy_dia['Acumulado Proyectado'].iloc[-1])
    ayer_real_s    = proy_dia.loc[proy_dia['Fecha'] == ayer, 'Acumulado Real']
    acum_real_ayer = int(ayer_real_s.iloc[0]) if not ayer_real_s.empty else 0
    q_faltantes    = max(acum_proy_fin - acum_real_ayer, 0)

    proy_imp_valor = round(promedio_costo * q_faltantes + total_importe_real, 2)

    nivel_esperado = round(
        ne_imp.loc[
            (ne_imp['Subrubro'] == 'Farmacia') &
            (ne_imp['Periodo'].astype(str) == str(periodo_actual)),
            'Nivel Esperado $',
        ].sum(),
        2,
    )

    return pd.DataFrame([{
        'Fecha':              hoy,
        'Real':               round(total_importe_real, 2),
        'Importe Proyectado': proy_imp_valor,
        'Nivel Esperado':     nivel_esperado,
    }])


def proyeccion_importe(
    df: pd.DataFrame,
    proy_dia: pd.DataFrame,
    ne_imp: pd.DataFrame,
    hoy: pd.Timestamp = None,
    periodo_actual: str = None,
    col_qty: str = 'Q',
) -> pd.DataFrame:
    """
    Proyección de importe para Farmacia y Vacunas.
    Se mergea por Rubro + Subrubro + Zona DCA + Subzona DCA + Periodo.

    Retorna DataFrame con columnas:
        Rubro, Subrubro, Zona DCA, Subzona DCA, Periodo,
        Nivel Esperado $, Importe, Proyección Importe
    """
    hoy = hoy or fecha_hoy.normalize()
    periodo_actual = periodo_actual or p_actual
    ayer = hoy - pd.Timedelta(days=1)

    # --- Importe real agrupado (Farmacia y Vacunas) ---
    real_imp = (
        df.groupby(['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo'], as_index=False)
        ['Importe'].sum()
    )
    real_imp['Periodo'] = real_imp['Periodo'].astype(str)

    # --- Base: ne_imp + importe real (merge a nivel Subrubro) ---
    result = ne_imp.merge(
        real_imp,
        on=['Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo'],
        how='left',
    )
    result['Importe'] = result['Importe'].fillna(0)

    # --- Proyección de importe para Farmacia del periodo actual ---
    farm_period = (
        df.loc[
            (df['Subrubro'] == 'Farmacia') &
            (df['Periodo'].astype(str) == str(periodo_actual)) &
            (df['Fecha'] < hoy),
            ['Fecha', col_qty, 'Importe']
        ]
        .groupby('Fecha', as_index=False)
        .agg({col_qty: 'sum', 'Importe': 'sum'})
    )

    total_importe_real = farm_period['Importe'].sum()
    promedio_costo = 0.0
    if not farm_period.empty and farm_period[col_qty].sum() > 0:
        promedio_costo = (
            farm_period['Importe'] / farm_period[col_qty].replace(0, np.nan)
        ).mean()
        if pd.isna(promedio_costo):
            promedio_costo = 0.0

    # Cantidades faltantes = proyectado al fin de mes − acumulado real de ayer
    acum_proy_fin  = int(proy_dia['Acumulado Proyectado'].iloc[-1])
    ayer_real_s    = proy_dia.loc[proy_dia['Fecha'] == ayer, 'Acumulado Real']
    acum_real_ayer = int(ayer_real_s.iloc[0]) if not ayer_real_s.empty else 0
    q_faltantes    = max(acum_proy_fin - acum_real_ayer, 0)

    proy_imp_valor = round(promedio_costo * q_faltantes + total_importe_real, 2)

    # Asignar el valor proyectado a todas las filas de Farmacia del periodo actual
    result['Proyección Importe'] = 0.0
    mask = (
        (result['Subrubro'] == 'Farmacia') &
        (result['Periodo'].astype(str) == str(periodo_actual))
    )
    result.loc[mask, 'Proyección Importe'] = proy_imp_valor

    cols = [
        'Rubro', 'Subrubro', 'Zona DCA', 'Subzona DCA', 'Periodo',
        'Nivel Esperado $', 'Importe', 'Proyección Importe',
    ]
    return result[cols]
