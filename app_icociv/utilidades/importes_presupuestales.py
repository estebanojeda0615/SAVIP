"""Interpretación declarada de importes; nunca modifica el registro económico."""
import math

MODALIDADES = {'heredado':'Sin clasificar (comportamiento anterior)', 'unitario':'Valores unitarios', 'total':'Valores totales'}
OPCIONES_INGRESO = {'heredado':'Seleccionar interpretación','unitario':'Unitario','total':'Total'}
PREGUNTA_INGRESO = '¿P y A están ingresados por unidad o por el valor total de la actividad?'
AVISO_INTERPRETACION = 'Cambiar Unitario/Total reinterpreta P y A; no convierte sus importes. Para el mismo presupuesto, P y A totales son sus importes unitarios × Cantidad. Siempre se muestran ambos resultados. En acero se interpreta P0; Cantidad es distinta de q.'

def validar_modalidad(registro):
    modo = registro.get('modalidad_importe','heredado')
    if not isinstance(modo,str) or modo not in MODALIDADES:
        raise ValueError('Modalidad de importe inválida: use heredado, unitario o total.')
    return modo

def _finito(v):
    try:return type(v) in (int,float) and math.isfinite(v)
    except OverflowError:return False


def cantidad_presupuestal_valida(cantidad):
    return _finito(cantidad) and cantidad>0

def desglose_importe(registro, valor, *, base=False):
    modo = validar_modalidad(registro)
    d = {'modalidad':modo,'unitario':None,'total':None,'estado':''}
    if modo=='heredado':
        d['estado']='No clasificado';return d
    if not _finito(valor):
        d['estado']='No disponible: importe no finito';return d
    if registro.get('tipo_calculo')=='Cálculo especial acero' and not (
        _finito(registro.get('p0')) and registro['p0']==registro.get('base_ajustable')
        and (valor==registro['p0'] if base else _finito(registro.get('r_total')) and valor==registro['p0']+registro['r_total'])):
        d['estado']='No disponible: no se identifica la base P0 o el importe P0 + R del acero';return d
    d['unitario' if modo=='unitario' else 'total'] = valor
    cantidad = registro.get('cantidad')
    if not cantidad_presupuestal_valida(cantidad):
        d['estado']='No disponible: cantidad no válida';return d
    try:derivado = valor*cantidad if modo=='unitario' else valor/cantidad
    except OverflowError:derivado = None
    if not _finito(derivado) or derivado==0 and valor!=0:
        d['estado']='No disponible: conversión fuera del rango numérico';return d
    d['total' if modo=='unitario' else 'unitario'] = derivado
    return d

def texto_desglose(registro, valor, origen):
    d = desglose_importe(registro,valor)
    b = desglose_importe(registro,registro.get('base_ajustable'),base=True)
    def numero(v):
        if not _finito(v):return '—'
        if v!=0 and (abs(v)<0.0001 or abs(v)>=1e12):return f'{v:.6g}'
        return f'{v:,.4f}'.rstrip('0').rstrip('.')
    def pesos(v):
        # Fase 4I: importes en pesos enteros (presentación; redondeo al peso, mitad hacia arriba).
        if not _finito(v):return '—'
        if v!=0 and (abs(v)<0.5 or abs(v)>=1e12):return f'{v:.6g}'  # no inventar ceros ni perder magnitudes extremas
        from decimal import Decimal, ROUND_HALF_UP
        return f"{int(Decimal(repr(float(v))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)):,}"
    significado = ('Importe original sin clasificar' if d['modalidad']=='heredado' else
        'Lado declarado: '+('unitario' if d['modalidad']=='unitario' else 'total')+'; contraparte derivada de Cantidad')
    estados = ' · '.join(dict.fromkeys(x['estado'] for x in (b,d) if x['estado']))
    return (f"{origen} · ID {registro.get('calculo_id') or 'registro anterior sin ID'}\n"
        f"Interpretación de P y A: {MODALIDADES[d['modalidad']]} · Cantidad: {numero(registro.get('cantidad'))}\n"
        f"{significado} · Base original: {pesos(registro.get('base_ajustable'))} · Valor principal: {pesos(valor)}\n"
        f"Base ajustable unitaria: {pesos(b['unitario'])} · Base ajustable total: {pesos(b['total'])}\n"
        f"Valor ajustado unitario: {pesos(d['unitario'])} · Valor ajustado total: {pesos(d['total'])}"
        + (f" · {estados}" if estados else ''))


def desglose_presupuestal(registro, valor):
    base = desglose_importe(registro,registro.get('base_ajustable'),base=True)
    ajustado = desglose_importe(registro,valor)
    return {'base_unitaria':base['unitario'],'base_total':base['total'],
            'valor_unitario':ajustado['unitario'],'valor_total':ajustado['total']}
