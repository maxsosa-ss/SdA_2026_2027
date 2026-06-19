import pandas as pd
from .connections import creds
from googleapiclient.discovery import build

_service = build('sheets', 'v4', credentials=creds)

# Función para leer un rango de Google Sheets y devolver un DataFrame
def leer_tabla_df(spreadsheet_id, rango):
    """
    Lee un rango de Google Sheets y devuelve un DataFrame.
    La primera fila se usa como cabecera. Retorna un DataFrame vacío si no hay datos.

    :param spreadsheet_id: str - ID del documento de Google Sheets.
    :param rango: str - Hoja y rango de celdas (ej. 'Hoja1!A1:D10').
    :return: pd.DataFrame
    """
    try:
        print(f"Consultando datos en el rango: {rango}...")
        resultado = _service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=rango
        ).execute()

        valores = resultado.get('values', [])

        if not valores:
            print('No se encontraron datos en el rango especificado.')
            return pd.DataFrame()

        return pd.DataFrame(valores[1:], columns=valores[0])

    except Exception as e:
        print(f"Ha ocurrido un error al conectarse a la API: {e}")
        return pd.DataFrame()
    
# Función para escribir un DataFrame en Google Sheets    
def escribir_tabla_df(spreadsheet_id, rango, df, incluir_cabecera=True, clear_first=False):
    """
    Escribe un DataFrame de Pandas en un rango de Google Sheets.

    :param spreadsheet_id: str - ID del documento de Google Sheets.
    :param rango: str - Hoja y celda de inicio o rango completo (ej. 'Hoja1!A1').
    :param df: pd.DataFrame - El DataFrame con los datos a escribir.
    :param incluir_cabecera: bool - Si es True, escribe los nombres de las columnas en la primera fila.
    :param clear_first: bool - Si es True, borra el contenido del rango antes de escribir.
    :return: bool - True si se escribió con éxito, False en caso contrario.
    """
    try:
        # 1. Preparar los datos convirtiendo el DataFrame a una lista de listas
        # Reemplazamos los valores NaN/None por cadenas vacías para evitar errores en la API
        df_limpio = df.fillna('')
        
        valores = []
        if incluir_cabecera:
            valores.append(df_limpio.columns.tolist())
        
        # Convertimos cada fila a elementos nativos de Python (strings, ints, floats)
        valores.extend(df_limpio.values.tolist())

        # 2. Opcional: Limpiar el rango antes de escribir nuevos datos
        if clear_first:
            print(f"Limpiando datos previos en el rango: {rango}...")
            _service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id, range=rango
            ).execute()

        # 3. Configurar el cuerpo de la solicitud
        cuerpo = {
            'values': valores
        }

        # 4. Ejecutar la escritura
        # 'USER_ENTERED' hace que Sheets interprete strings con fechas o números como tales
        print(f"Escribiendo datos en el rango: {rango}...")
        resultado = _service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=rango,
            valueInputOption='USER_ENTERED',
            body=cuerpo
        ).execute()

        print(f"Éxito: Se actualizaron {resultado.get('updatedCells')} celdas.")
        return True

    except Exception as e:
        print(f"Ha ocurrido un error al escribir en la API: {e}")
        return False    
