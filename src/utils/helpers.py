import pandas as pd

from src.utils.gc_functions import leer_tabla_df

STOCK_PARQUET = 'data/processed/stock.parquet'


def construir_pivot_qamb(spreadsheet_presupuesto):
    """
    Lee TU_AMB y el stock unificado (data/processed/stock.parquet), calcula Q_AMB = TU x STOCK
    y devuelve el DataFrame melteado por Periodo (Rubro PPTO, Subrubro PPTO, Zona DCA, Subzona DCA, Periodo, Q_AMB).
    """
    df_tu_amb = leer_tabla_df(spreadsheet_presupuesto, 'TU_AMB!A1:Y2269')

    stock_long = pd.read_parquet(STOCK_PARQUET)
    stock = stock_long.pivot_table(index=['ZONA', 'SUBZONA'], columns='Periodo', values='Stock').reset_index()
    stock.columns.name = None

    periodos = [col for col in df_tu_amb.columns if str(col).isnumeric()]

    for col in periodos:
        if df_tu_amb[col].dtype == 'object':
            df_tu_amb[col] = df_tu_amb[col].astype(str).str.replace(',', '.').astype(float)

    cols_stock = ['ZONA', 'SUBZONA'] + periodos
    df_merged = pd.merge(
        df_tu_amb,
        stock[cols_stock],
        on=['ZONA', 'SUBZONA'],
        how='left',
        suffixes=('_tu', '_stock')
    )

    df_q_amb = df_tu_amb[['RUBRO', 'SUBRUBRO', 'ZONA', 'SUBZONA']].copy()
    for col in periodos:
        df_q_amb[col] = df_merged[f'{col}_tu'] * df_merged[f'{col}_stock']
    df_q_amb.rename(columns={'RUBRO': 'Rubro PPTO', 'SUBRUBRO': 'Subrubro PPTO', 'ZONA': 'Zona DCA', 'SUBZONA': 'Subzona DCA'}, inplace=True)

    df_pivot_qamb = pd.melt(
        df_q_amb,
        id_vars=['Rubro PPTO', 'Subrubro PPTO', 'Zona DCA', 'Subzona DCA'],
        value_vars=periodos,
        var_name='Periodo',
        value_name='Q_AMB'
    )
    df_pivot_qamb = df_pivot_qamb.sort_values(['Rubro PPTO', 'Subrubro PPTO', 'Zona DCA', 'Subzona DCA', 'Periodo']).reset_index(drop=True)

    return df_pivot_qamb


def estructura_base(df_base, inicio_periodo, fin_periodo):
    """
    Toma un DataFrame base y realiza un cross merge con un rango de periodos mensuales.
    
    Parámetros:
    -----------
    df_base : pandas.DataFrame
        El DataFrame original que se va a expandir (ej. aux_comb_amb).
    inicio_periodo : str o datetime
        Fecha de inicio del rango (ej. '2023-01-01').
    fin_periodo : str o datetime
        Fecha de fin del rango (ej. '2023-12-31').
        
    Retorna:
    --------
    pandas.DataFrame
        Un nuevo DataFrame con la combinación cruzada y la columna 'Periodo' en formato 'YYYYMM'.
    """
    
    # 1. Generar el rango de fechas con frecuencia de inicio de mes ("MS")
    rango_fechas = pd.date_range(start=inicio_periodo, end=fin_periodo, freq="MS")
    
    # 2. Convertir las fechas a formato texto "YYYY-MM" y pasarlo a lista
    lista_periodos = rango_fechas.strftime("%Y-%m").tolist()
    
    # 3. Crear el DataFrame de periodos
    df_periodos = pd.DataFrame({'Periodo': lista_periodos})
    
    # 4. Realizar el merge cruzado (producto cartesiano)
    df_resultado = df_base.merge(df_periodos, how='cross')
    
    # 5. Eliminar los guiones para que el formato quede como "YYYYMM"
    df_resultado['Periodo'] = df_resultado['Periodo'].str.replace('-', '')
    
    return df_resultado