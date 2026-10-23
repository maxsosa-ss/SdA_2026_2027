import json
import re
import socket

import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_fixed

_service = None


def _get_service():
    global _service
    if _service is None:
        from .connections import get_google_creds
        _service = build('sheets', 'v4', credentials=get_google_creds())
    return _service


def _es_error_transitorio(exc: BaseException) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, HttpError):
        return exc.resp.status in (429, 500, 502, 503, 504)
    return False


@retry(
    retry=retry_if_exception(_es_error_transitorio),
    stop=stop_after_attempt(3),
    wait=wait_fixed(5),
    reraise=True,
)
def _execute(request):
    return request.execute()


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
        resultado = _execute(
            _get_service().spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=rango
            )
        )

        valores = resultado.get('values', [])

        if not valores:
            print(f"[leer_tabla_df] WARN: rango '{rango}' devolvió vacío")
            return pd.DataFrame()

        print(f"[leer_tabla_df] rango '{rango}': {len(valores) - 1} filas leídas")
        return pd.DataFrame(valores[1:], columns=valores[0])

    except Exception as e:
        raise RuntimeError(f"Error leyendo GSheets ({rango}): {e}") from e
    
def _col_a_letra(n):
    """1 -> 'A', 26 -> 'Z', 27 -> 'AA'."""
    letra = ''
    while n:
        n, resto = divmod(n - 1, 26)
        letra = chr(65 + resto) + letra
    return letra


def _letra_a_col(letra):
    n = 0
    for c in letra:
        n = n * 26 + ord(c) - 64
    return n


def _rango_a_limpiar(rango, n_columnas):
    """
    Si `rango` es una sola celda de inicio (ej. 'Hoja!A1'), devuelve las columnas completas que
    ocupa la tabla (ej. 'Hoja!A:K') para que clear_first borre también las filas sobrantes de una
    escritura anterior más larga. Si ya es una hoja entera o un rango, lo devuelve tal cual.
    """
    if '!' not in rango or ':' in rango:
        return rango
    hoja, celda = rango.rsplit('!', 1)
    m = re.fullmatch(r'([A-Za-z]+)\d+', celda)
    if not m:
        return rango
    col_ini = _letra_a_col(m.group(1).upper())
    return f"{hoja}!{_col_a_letra(col_ini)}:{_col_a_letra(col_ini + n_columnas - 1)}"


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

        # Validar que los valores se serializan ANTES de borrar: si falla
        # después del clear, la hoja queda vacía y se pierde el historial.
        json.dumps(valores)

        if clear_first:
            _execute(
                _get_service().spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id,
                    range=_rango_a_limpiar(rango, len(df_limpio.columns)),
                )
            )

        resultado = _execute(
            _get_service().spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=rango,
                valueInputOption='USER_ENTERED',
                body={'values': valores},
            )
        )

        return True

    except Exception as e:
        raise RuntimeError(f"Error escribiendo GSheets ({rango}): {e}") from e
