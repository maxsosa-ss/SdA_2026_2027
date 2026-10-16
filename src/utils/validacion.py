import pandas as pd

from src.utils.discord import notify_warning

_ZONA = ['Zona DCA', 'Subzona DCA']
_MAX_LINEAS = 10


def zonas_sin_referencia(real: pd.DataFrame, ref: pd.DataFrame, col_qty: str = 'Q') -> pd.DataFrame:
    """(Zona, Subzona) con datos reales que no existen en `ref`; esos datos se pierden al cruzar."""
    reales = real.groupby(_ZONA, as_index=False)[col_qty].sum()
    existentes = ref[_ZONA].drop_duplicates().assign(_ok=True)
    cruce = reales.merge(existentes, on=_ZONA, how='left')
    return cruce.loc[cruce['_ok'].isna(), _ZONA + [col_qty]]


def filas_sin_valor(base: pd.DataFrame, ref: pd.DataFrame, claves: list[str], col_valor: str) -> pd.DataFrame:
    """Filas de `base` sin match en `ref` por `claves`, o cuyo `col_valor` en `ref` es nulo."""
    cruce = base[claves].drop_duplicates().merge(ref[claves + [col_valor]], on=claves, how='left')
    return cruce.loc[cruce[col_valor].isna(), claves]


def validar_zonas(
    real: pd.DataFrame,
    referencias: dict[str, pd.DataFrame],
    titulo: str,
    col_qty: str = 'Q',
) -> None:
    """
    Avisa por Discord (sin cortar el pipeline) si hay zonas/subzonas con datos reales que no están
    en alguna de las tablas de referencia (NE, VU, ...). Pasa, por ejemplo, cuando cambia la
    estructura de zonas en MicroStrategy y los Sheets auxiliares no se actualizaron.
    """
    campos = []
    for nombre, ref in referencias.items():
        faltantes = zonas_sin_referencia(real, ref, col_qty)
        if faltantes.empty:
            continue
        lineas = [f'{r["Zona DCA"]} / {r["Subzona DCA"]}: {r[col_qty]:,.0f}' for _, r in faltantes.head(_MAX_LINEAS).iterrows()]
        if len(faltantes) > _MAX_LINEAS:
            lineas.append(f'... y {len(faltantes) - _MAX_LINEAS} más')
        print(f'⚠️ {titulo}: {len(faltantes)} zona/subzona con datos reales sin {nombre}')
        campos.append({'name': f'Sin {nombre} ({len(faltantes)})', 'value': '\n'.join(lineas)})
    if campos:
        notify_warning(f'{titulo}: zonas con datos reales sin referencia', fields=campos)


def validar_valores(
    base: pd.DataFrame,
    ref: pd.DataFrame,
    claves: list[str],
    col_valor: str,
    titulo: str,
    nombre_ref: str,
) -> None:
    """Avisa por Discord (sin cortar el pipeline) si hay filas de `base` sin `col_valor` en `ref`."""
    faltantes = filas_sin_valor(base, ref, claves, col_valor)
    if faltantes.empty:
        return
    lineas = [' | '.join(str(v) for v in fila) for fila in faltantes.head(_MAX_LINEAS).itertuples(index=False)]
    if len(faltantes) > _MAX_LINEAS:
        lineas.append(f'... y {len(faltantes) - _MAX_LINEAS} más')
    print(f'⚠️ {titulo}: {len(faltantes)} filas sin {col_valor} en {nombre_ref}')
    notify_warning(
        f'{titulo}: filas sin {col_valor} en {nombre_ref}',
        fields=[{'name': ' | '.join(claves), 'value': '\n'.join(lineas)}],
    )
