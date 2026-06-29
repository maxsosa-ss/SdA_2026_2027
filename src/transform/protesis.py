import pandas as pd

from src.utils.dates import p_actual, p_anterior


def protesis_gral(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla general de Prótesis por Zona, Subzona, Origen y Periodo,
    con promedios de los últimos 6 y 12 meses (excluyendo el periodo actual)
    tanto en Cantidad como en Importe.

    Retorna DataFrame con columnas:
        Rubro General, Zona, Subzona, Periodo, Origen,
        Cantidad, Importe,
        Promedio_ultimos_6M, Promedio_ultimos_12M,
        Promedio_ultimos_6M_importe, Promedio_ultimos_12M_importe
    """
    df = df.copy()
    df['Periodo'] = df['Periodo'].astype(str).str.strip()
    df['Rubro General'] = 'Prótesis'

    agrupado = (
        df.groupby(['Rubro General', 'Zona', 'Subzona', 'Periodo', 'Origen'], as_index=False)
        [['Cantidad', 'Importe']].sum()
    )

    df_sin_actual = agrupado[agrupado['Periodo'] != p_actual].copy()

    prom6  = _promedio_n_periodos(df_sin_actual, 6,  p_anterior)
    prom12 = _promedio_n_periodos(df_sin_actual, 12, p_anterior)

    result = (
        agrupado
        .merge(prom6,  on=['Zona', 'Subzona', 'Origen', 'Periodo'], how='left')
        .merge(prom12, on=['Zona', 'Subzona', 'Origen', 'Periodo'], how='left')
    )

    cols = [
        'Rubro General', 'Zona', 'Subzona', 'Periodo', 'Origen',
        'Cantidad', 'Importe',
        'Promedio_ultimos_6M', 'Promedio_ultimos_12M',
        'Promedio_ultimos_6M_importe', 'Promedio_ultimos_12M_importe',
    ]
    return result[cols]


def _promedio_n_periodos(df: pd.DataFrame, n: int, periodo_resultado: str) -> pd.DataFrame:
    df = df.copy()
    df['Periodo'] = df['Periodo'].astype(str)

    col_cant = f'Promedio_ultimos_{n}M'
    col_imp  = f'Promedio_ultimos_{n}M_importe'

    resultados = []
    for (zona, subzona, origen), grupo in df.groupby(['Zona', 'Subzona', 'Origen']):
        ultimos_n = grupo['Periodo'].drop_duplicates().sort_values(ascending=False).head(n)
        filtrado  = grupo[grupo['Periodo'].isin(ultimos_n)]

        prom_cant = filtrado['Cantidad'].mean()
        prom_imp  = filtrado['Importe'].mean()

        resultados.append({
            'Zona':    zona,
            'Subzona': subzona,
            'Origen':  origen,
            col_cant:  round(prom_cant) if pd.notnull(prom_cant) else pd.NA,
            col_imp:   round(prom_imp)  if pd.notnull(prom_imp)  else pd.NA,
        })

    resultado_df = pd.DataFrame(resultados)
    resultado_df[col_cant] = resultado_df[col_cant].astype('Int64')
    resultado_df[col_imp]  = resultado_df[col_imp].astype('Int64')
    resultado_df['Periodo'] = periodo_resultado
    return resultado_df
