import pandas as pd
from googleapiclient.discovery import build

_service = None


def _get_service():
    global _service
    if _service is None:
        from .connections import get_google_creds
        _service = build('sheets', 'v4', credentials=get_google_creds())
    return _service

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
        resultado = _get_service().spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=rango
        ).execute()

        valores = resultado.get('values', [])

        if not valores:
            print(f"[leer_tabla_df] WARN: rango '{rango}' devolvió vacío")
            return pd.DataFrame()

        print(f"[leer_tabla_df] rango '{rango}': {len(valores) - 1} filas leídas")
        return pd.DataFrame(valores[1:], columns=valores[0])

    except Exception as e:
        raise RuntimeError(f"Error leyendo GSheets ({rango}): {e}") from e
    
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
        df_limpio = df.fillna('')
        valores = []
        if incluir_cabecera:
            valores.append(df_limpio.columns.tolist())
        valores.extend(df_limpio.values.tolist())

        if clear_first:
            _get_service().spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id, range=rango
            ).execute()

        resultado = _get_service().spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=rango,
            valueInputOption='USER_ENTERED',
            body={'values': valores},
        ).execute()

        return True

    except Exception as e:
        raise RuntimeError(f"Error escribiendo GSheets ({rango}): {e}") from e
