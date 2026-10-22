"""Referencias auténticas y escenarios de presentación; originales intactos."""
import re
import math
import pandas as pd
from app_icociv.persistencia.historial_icociv import recuperar_resultado
from app_icociv.interfaz.widgets.tabla_numerica import numero_original, variacion_indice
from app_icociv.servicios import fecha_objetivo as fo


def periodo_mensual(valor):
    m = re.fullmatch(r'(\d{4})[-_](\d{1,2})', valor) if isinstance(valor, str) else None
    if not m or not 1 <= int(m[1]) <= 9999 or not 1 <= int(m[2]) <= 12:
        return None
    return f'{int(m[1]):04d}-{int(m[2]):02d}'


def historico_observado(analisis):
    try:
        snapshot = analisis['resultado']
        serie = recuperar_resultado(snapshot.get('serie_df'))
        fuente = recuperar_resultado(snapshot.get('fila'))
        if (not isinstance(serie, pd.DataFrame) or not {'Periodo','Indice'}.issubset(serie.columns)
                or not isinstance(fuente, pd.DataFrame) or len(fuente) != 1
                or analisis['contexto'].get('ruta') != snapshot.get('ruta_jerarquica')):
            return {}, 'Referencia no disponible: falta una serie histórica con origen verificable.'
        originales = {}
        for col in fuente.columns:
            periodo = periodo_mensual(col)
            if periodo:
                if periodo in originales:
                    return {}, 'Referencia no disponible: meses duplicados en la fila de origen.'
                originales[periodo] = numero_original(pd.to_numeric(fuente[col].iloc[0], errors='coerce'))
        observados = {}; vistos = set()
        for fecha, valor in serie[['Periodo','Indice']].itertuples(index=False, name=None):
            periodo = periodo_mensual(fecha)
            if not periodo or periodo in vistos:
                return {}, 'Referencia no disponible: períodos históricos inválidos o duplicados.'
            vistos.add(periodo); indice = numero_original(pd.to_numeric(valor, errors='coerce'))
            if indice is not None and indice > 0 and originales.get(periodo) == indice:
                observados[periodo] = indice
        return dict(sorted(observados.items())), ('' if observados else
            'Sin meses históricos válidos: se requieren índices observados finitos, positivos y verificados en la fila de origen.')
    except (KeyError, TypeError, ValueError, IndexError, AttributeError):
        return {}, 'Referencia no disponible: la instantánea histórica no permite verificar las observaciones.'


def historico_efectivo(analisis, externas=None):
    """Meses observados del snapshot más referencias DANE aplicadas expresamente.

    Devuelve (meses fusionados, último mes del snapshot, motivo). El último mes
    del snapshot es la referencia predeterminada aunque una fuente posterior
    aporte meses nuevos: cargar otro anexo nunca la desplaza.
    """
    observados, razon = historico_observado(analisis)
    original = next(reversed(observados)) if observados else None
    if observados and externas:
        observados = dict(sorted({**observados, **{p: v['indice'] for p, v in externas.items()}}.items()))
    return observados, original, razon


def validar_externas(externas, analisis):
    """Referencias DANE posteriores guardadas: valor exacto, origen y fecha."""
    if not isinstance(externas, dict):
        raise ValueError('Referencias DANE posteriores inválidas; no se reemplazará la sesión.')
    snapshot = historico_observado(analisis)[0]
    objetivo = periodo_mensual(analisis['contexto'].get('periodo_proyectado'))
    for periodo, dato in externas.items():
        indice = numero_original(dato.get('indice')) if isinstance(dato, dict) else None
        if (not isinstance(periodo, str) or periodo_mensual(periodo) != periodo or periodo in snapshot
                or not snapshot or periodo <= next(reversed(snapshot)) or not objetivo or periodo >= objetivo
                or indice is None or indice <= 0 or type(dato.get('indice')) is not float
                or any(not isinstance(dato.get(k), str) or not dato.get(k) for k in ('archivo', 'tabla', 'huella_fuente', 'aplicado'))):
            raise ValueError('Referencia DANE posterior inválida o incompatible con el objetivo; no se reemplazará la sesión.')


def indice_vinculado(analisis, periodo):
    """Fase 4I-P2: I del análisis para `periodo` (AAAA-MM). Para el objetivo original, el índice registrado
    en su contexto; para otra fecha, el punto guardado de su trayectoria de 24 meses (sin motor). None si
    esa fecha no es consultable en el análisis."""
    contexto = analisis['contexto']
    if periodo == periodo_mensual(contexto.get('periodo_proyectado')):
        return numero_original(contexto.get('indice_proyectado'))
    try:
        return numero_original(fo.consultar(analisis, periodo)['indice'])
    except (KeyError, TypeError, ValueError):
        return None


def comparar_registro(registro, analisis, historico, periodo):
    vacio = ('', None, None)
    if not analisis or registro.get('analisis_id') != analisis['id']:
        return (*vacio, 'Sin modificación / vínculo no demostrable: registro anterior sin análisis.')
    contexto = analisis['contexto']; indice = numero_original(registro.get('i_icociv'))
    objetivo = periodo_mensual(registro.get('periodo_proyectado'))
    # Fase 4I-P2: la actividad es demostrable si su I es EXACTAMENTE el del análisis para su propia fecha:
    # el objetivo original o un punto consultado de la trayectoria guardada (fecha objetivo aplicada).
    if (not contexto.get('ruta_texto') or registro.get('ruta_icociv') != contexto['ruta_texto']
            or not objetivo or indice is None or indice != indice_vinculado(analisis, objetivo)):
        return (*vacio, 'Sin modificación / vínculo no demostrable: índice, serie u objetivo incompatible.')
    if periodo and periodo >= objetivo:
        # Fase 4I-P2: con una fecha consultada anterior, una referencia DANE posterior aplicada puede no ser
        # anterior al objetivo de la actividad; igual que al aplicarla, no se compara (se conserva el registro).
        return (*vacio, f'Sin modificación: la referencia {periodo} no es anterior al objetivo {objetivo} de la actividad.')
    referencia = historico.get(periodo)
    variacion = variacion_indice(referencia, indice)
    if variacion is None:
        return (*vacio, 'Referencia no disponible: mes no observado o índice histórico no válido.')
    return periodo, referencia, variacion, ''


def escenario_registro(registro, analisis, historico, periodo, override=False):
    fecha, referencia, porcentaje, razon = comparar_registro(registro, analisis, historico, periodo)
    if razon:
        if override and razon.startswith('Referencia no disponible'):
            raise ValueError(razon + ' Se conserva el escenario anterior.')
        return dict(registro), razon
    if not override:
        discrepancia = registro.get('i0_icociv') != referencia
        return dict(registro), ('I0 original distinto del último observado; sin intervención se conserva el resultado registrado.' if discrepancia else 'Referencia predeterminada')
    # Siempre partir del registro, conservando el orden Base + Base * (Factor - 1).
    p, a, indice = (numero_original(registro.get(k)) for k in ('precio_base','anticipo_amortizado','i_icociv'))
    if p is None or a is None or indice is None or p <= 0 or a < 0 or p <= a:
        raise ValueError('Entradas económicas originales inválidas; se conserva el escenario anterior.')
    # Fase 4I-C: el escenario usa el MISMO factor aplicado (porcentaje redondeado a 2 decimales).
    from app_icociv.servicios.actualizacion_icociv import CRITERIO_FACTOR, aplicar_factor
    base = p - a; aplicado = aplicar_factor(base, indice, referencia)
    factor, ajuste, valor, porcentaje = aplicado['factor'], aplicado['r'], aplicado['valor'], aplicado['porcentaje']
    if not all(math.isfinite(v) for v in (base, factor, ajuste, valor, porcentaje)):
        raise ValueError('El escenario no es finito; se conserva el escenario anterior.')
    if periodo == next(reversed(historico)) and registro.get('i0_icociv') == referencia:
        return dict(registro), 'Referencia predeterminada'
    resultado = dict(registro)
    resultado.update(i0_icociv=referencia, periodo_base=fecha, base_ajustable=base,
        factor_icociv=factor, r_total=ajuste, diferencia_absoluta=ajuste,
        valor_proyectado=valor, diferencia_porcentual=porcentaje, criterio_factor=CRITERIO_FACTOR,
        factor_icociv_indices=aplicado['factor_indices'],
        trazabilidad_formula=f'Base = P - A = {base!r}\nVariación aplicada = ROUND(((I/I0) - 1) × 100; 2) = ROUND((({indice!r}/{referencia!r}) - 1) × 100; 2) = {porcentaje:.2f} %\nFactor aplicado F = {factor:.4f}\nR = Base × (F - 1) = {base!r} × ({factor:.4f} - 1) = {ajuste!r}\nValor proyectado = Base + R = {base!r} + {ajuste!r} = {valor!r}')
    return resultado, 'Referencia modificada (escenario)'


def validar_comparacion(datos, historial):
    if 'comparacion_historica' not in datos:
        return
    bloque = datos['comparacion_historica']; analisis = {a['id']:a for a in historial}
    if not isinstance(bloque, dict) or type(bloque.get('version')) is not int or bloque['version'] not in (1,2,3):
        raise ValueError('Estado de referencia no válido; no se reemplazará la sesión.')
    # Versión 3 (Fase 4G) = versión 2 + referencias DANE posteriores aplicadas expresamente.
    externas = bloque.get('referencias_externas', {}) if bloque['version'] == 3 else {}
    if not isinstance(externas, dict) or any(i not in analisis for i in externas):
        raise ValueError('Referencias DANE posteriores ajenas al historial; no se reemplazará la sesión.')
    for identificador, mapa in externas.items():validar_externas(mapa, analisis[identificador])
    def efectivo(identificador):return historico_efectivo(analisis[identificador], externas.get(identificador))
    def validar_periodos(mapa):
        if not isinstance(mapa, dict):raise ValueError('Referencias guardadas inválidas.')
        for identificador, periodo in mapa.items():
            if (not isinstance(identificador,str) or identificador not in analisis
                    or not isinstance(periodo,str) or periodo_mensual(periodo) != periodo
                    or periodo not in efectivo(identificador)[0]):
                raise ValueError('Referencia histórica inválida o ajena al análisis; no se reemplazará la sesión.')
    if bloque['version'] == 1:
        validar_periodos(bloque.get('periodo_por_analisis'));return
    selecciones = bloque.get('selecciones')
    if not isinstance(selecciones,dict) or type(bloque.get('global')) is not bool:
        raise ValueError('Estado económico de referencia inválido.')
    validar_periodos({k:v.get('periodo') if isinstance(v,dict) else None for k,v in selecciones.items()})
    for identificador, seleccion in selecciones.items():
        h, original, _ = efectivo(identificador)
        if type(seleccion.get('override')) is not bool or (not seleccion['override'] and seleccion['periodo'] != original):
            raise ValueError('Intervención económica guardada inválida.')
        if seleccion['override']:
            for r in datos.get('valores',[]):
                if r.get('analisis_id') == identificador:
                    escenario_registro(r,analisis[identificador],h,seleccion['periodo'],True)
    validar_periodos(bloque.get('consulta_v1',{}))
    if bloque['global']:
        historicos = [efectivo(a['id'])[0] for a in historial]
        if not historicos or not all(historicos) or not set.intersection(*(set(h) for h in historicos)):
            raise ValueError('Modo global guardado sin intersección verificable.')
