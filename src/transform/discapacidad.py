import pandas as pd

from src.utils.dates import p_actual, p_anterior


def disca_gral(df: pd.DataFrame, aux_mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla general de Discapacidad por Categoria, Zona, Subzona y Periodo,
    con promedios de los últimos 6 y 12 meses (excluyendo el periodo actual).

    Retorna DataFrame con columnas:
        Rubro, Categoria, Zona, Subzona, Periodo, Cantidad,
        Promedio_ultimos_6M, Promedio_ultimos_12M
    """
    df = df.copy()
    df['Periodo'] = df['Periodo'].astype(str).str.strip()

    # Mapear Prestacion_id -> Categoria (columna 'Rubro PPTO' en el aux)
    aux = aux_mapping.copy()
    aux['Prestacion_id'] = aux['Prestacion_id'].astype(str).str.strip()

    merged = df.merge(aux[['Prestacion_id', 'Rubro PPTO']], on='Prestacion_id', how='left')
    merged = merged.rename(columns={'Rubro PPTO': 'Categoria'})

    agrupado = (
        merged.groupby(['Categoria', 'Zona', 'Subzona', 'Periodo'], as_index=False)
        ['Cantidad'].sum()
    )
    agrupado.insert(0, 'Rubro', 'Discapacidad')

    df_sin_actual = agrupado[agrupado['Periodo'] != p_actual].copy()

    prom6  = _promedio_n_periodos(df_sin_actual, 6,  p_anterior)
    prom12 = _promedio_n_periodos(df_sin_actual, 12, p_anterior)

    result = (
        agrupado
        .merge(prom6,  on=['Categoria', 'Zona', 'Subzona', 'Periodo'], how='left')
        .merge(prom12, on=['Categoria', 'Zona', 'Subzona', 'Periodo'], how='left')
    )

    cols = [
        'Rubro', 'Categoria', 'Zona', 'Subzona', 'Periodo',
        'Cantidad', 'Promedio_ultimos_6M', 'Promedio_ultimos_12M',
    ]
    return result[cols]


def _promedio_n_periodos(df: pd.DataFrame, n: int, periodo_resultado: str) -> pd.DataFrame:
    """
    Para cada (Categoria, Zona, Subzona), toma los N periodos más recientes
    y calcula la media de Cantidad. Devuelve un DataFrame con columna Periodo
    fijada en `periodo_resultado` para poder hacer merge con la tabla principal.
    """
    df = df.copy()
    df['Periodo'] = df['Periodo'].astype(str)

    resultados = []
    col_prom = f'Promedio_ultimos_{n}M'

    for (cat, zona, subzona), grupo in df.groupby(['Categoria', 'Zona', 'Subzona']):
        ultimos_n = grupo['Periodo'].drop_duplicates().sort_values(ascending=False).head(n)
        filtrado  = grupo[grupo['Periodo'].isin(ultimos_n)]
        promedio  = filtrado['Cantidad'].mean()
        resultados.append({
            'Categoria': cat,
            'Zona':      zona,
            'Subzona':   subzona,
            col_prom:    round(promedio) if pd.notnull(promedio) else pd.NA,
        })

    resultado_df = pd.DataFrame(resultados)
    resultado_df[col_prom] = resultado_df[col_prom].astype('Int64')
    resultado_df['Periodo'] = periodo_resultado
    return resultado_df
