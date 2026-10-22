"""Validación de consultas económicas guardadas; no ejecuta servicios de cálculo."""
from datetime import datetime
import json
import math
import re
from uuid import UUID
from app_icociv.utilidades.importes_presupuestales import validar_modalidad


def resultado_analisis(analisis, calculos):
    if 'resultado_archivado' in analisis:
        return analisis['resultado_archivado']
    r = next(r for r in calculos if r.get('calculo_id') == analisis['calculo_id'])
    return {**r, 'numero_calculo': analisis['numero_calculo_original']}


def campos_componente(registro):
    tipo = registro.get('tipo_componente')
    nombre = registro.get('nombre_componente', '')
    visible = {'Grupo de obra': 'Grupo', 'Subclase de obra': 'Subclase'}.get(tipo, tipo)
    etiqueta = {'Subclase': 'Nombre de la subclase', 'Tipología': 'Nombre de la tipología',
                'Actividad': 'Nombre de la actividad', 'Otro': 'Nombre del componente'}.get(visible,
                f"Nombre del {visible.lower()}" if visible else 'Nombre del componente')
    return ([('Tipo de componente', visible)] if tipo else []) + ([(etiqueta, nombre)] if nombre else [])


def validar_componente(registro):
    validar_modalidad(registro)
    if registro.get('tipo_componente') not in (None, 'Grupo de obra', 'Subclase de obra', 'Tipología', 'Capítulo', 'Actividad', 'Ítem', 'Insumo', 'Otro'):
        raise ValueError('Tipo de componente inválido.')
    if not isinstance(registro.get('nombre_componente', ''), str):
        raise ValueError('Nombre del componente inválido.')


def validar_sesion_empalme(datos):
    if datos is None:
        return
    if not isinstance(datos, dict):
        raise ValueError('El bloque Empalme no es válido.')
    try:
        json.dumps(datos, allow_nan=False)
        calculos = datos.get('calculos', [])
        borrador = datos.get('borrador_formulario')  # Fase 4I-I: opcional; entradas literales sin registrar
        if borrador is not None:
            if not isinstance(borrador, dict):
                raise ValueError('Borrador de Empalme inválido.')
            for k in ('cantidad', 'precio_base', 'anticipo_amortizado', 'p0', 'ix', 'q'):
                v = borrador.get(k)
                if v is not None and (type(v) not in (int, float) or not math.isfinite(v)):
                    raise ValueError('Borrador de Empalme con importe no numérico.')
            for k in ('item', 'codigo_item', 'nombre_componente', 'observacion_tecnica', 'fecha_inicial', 'fecha_final', 'tipo_calculo'):
                if not isinstance(borrador.get(k, ''), str):
                    raise ValueError('Borrador de Empalme con texto inválido.')
            if not isinstance(borrador.get('seleccion_icociv', {}), dict):
                raise ValueError('Borrador de Empalme con ruta ICOCIV inválida.')
            validar_modalidad(borrador)
        historial = datos.get('historial_empalme', [])
        if not isinstance(calculos, list) or not isinstance(historial, list) or any(not isinstance(r, dict) for r in calculos + historial):
            raise ValueError('Registros de Empalme inválidos.')
        for registro in calculos:
            validar_componente(registro)
        ids_calculos = [r['calculo_id'] for r in calculos if r.get('calculo_id')]
        if len(set(ids_calculos)) != len(ids_calculos):
            raise ValueError('IDs de cálculo duplicados.')
        ids = set();vinculos = set()
        for numero, a in enumerate(historial, 1):
            if str(UUID(a['id'])) != a['id']:raise ValueError('UUID histórico no canónico.')
            datetime.fromisoformat(a['creado'])
            if a['id'] in ids or a['calculo_id'] in vinculos or a['numero'] != numero or not isinstance(a['nombre'], str) or not a['nombre']:
                raise ValueError('IDs, secuencias o vínculos históricos inválidos.')
            ids.add(a['id']);vinculos.add(a['calculo_id'])
            if not isinstance(a['archivo_excel'], str) or '\0' in a['archivo_excel']:
                raise ValueError('Referencia de archivo inválida.')
            original = a.get('formulario_original', {})
            if not isinstance(original, dict) or any(k not in ('item','codigo_item','unidad','cantidad','precio_base','anticipo_amortizado','fecha_inicial','fecha_final','tipo_serie_iccp','serie_iccp','ruta_icociv','observacion_tecnica','calculo_acero','p0','ix','q','modalidad_importe') for k in original):
                raise ValueError('Formulario original inválido.')
            validar_modalidad(original)
            for k, v in original.items():
                if k in ('cantidad','precio_base','anticipo_amortizado','p0','ix','q') and v is not None and (type(v) not in (int,float) or not math.isfinite(v)):
                    raise ValueError('Entrada original no numérica.')
                if k in ('item','codigo_item','unidad','fecha_inicial','fecha_final','tipo_serie_iccp','serie_iccp','ruta_icociv','observacion_tecnica') and not isinstance(v,str):
                    raise ValueError('Texto de formulario original inválido.')
            r = resultado_analisis(a, calculos)
            validar_componente(r)
            if r.get('calculo_id') != a['calculo_id'] or r.get('analisis_empalme_id') != a['id']:
                raise ValueError('Referencia histórica incoherente.')
            periodos = []
            for clave in ('fecha_inicial', 'fecha_final'):
                match = re.fullmatch(r'(20\d{2}|2100)[_-](\d{1,2})', r[clave])
                if not match or not 1 <= int(match[2]) <= 12:
                    raise ValueError('Periodo histórico inválido.')
                periodos.append((int(match[1]), int(match[2])))
            if periodos[0] > periodos[1]:
                raise ValueError('Periodo inicial posterior al final.')
            for i, k in enumerate(('fecha_inicial','fecha_final')):
                if k in original:
                    match = re.fullmatch(r'(20\d{2}|2100)[_-](\d{1,2})', original[k])
                    if not match or (int(match[1]), int(match[2])) != periodos[i]:
                        raise ValueError('Periodo del formulario original incoherente.')
            caso = 'solo_iccp' if periodos[1] <= (2021, 12) else 'solo_icociv' if periodos[0] > (2021, 12) else 'empalme_completo'
            if r['caso'] != caso:
                raise ValueError('Escenario incompatible con los periodos.')
            if r.get('tipo_calculo') not in ('general','Cálculo especial acero'):
                raise ValueError('Tipo de cálculo histórico inválido.')
            for clave in ('item', 'unidad', 'ruta_iccp', 'ruta_icociv'):
                if not isinstance(r.get(clave), str):
                    raise ValueError('Ruta o descripción histórica inválida.')
            seleccion = r.get('seleccion_icociv', {})
            if not isinstance(seleccion, dict) or any(v is not None and (type(v) is not bool if k.startswith('chk_') else type(v) is not int or v < 0) for k, v in seleccion.items()):
                raise ValueError('Selección histórica inválida.')
            claves = ['precio_base', 'anticipo_amortizado', 'base_ajustable', 'r1', 'r2', 'r_total', 'valor_actualizado']
            if caso != 'solo_icociv':claves += ['i0_iccp', 'i_iccp']
            if caso != 'solo_iccp':claves += ['i0_icociv', 'i_icociv']
            for clave in claves:
                if type(r.get(clave)) not in (int, float) or not math.isfinite(r[clave]):
                    raise ValueError('Cifra histórica inválida.')
            if r['base_ajustable'] <= 0 or any(r[k] == 0 for k in claves if k.startswith('i0_')):
                raise ValueError('Base o índice inicial inválido.')
            if r['r_total'] != r['r1'] + r['r2'] or r['valor_actualizado'] != r['base_ajustable'] + r['r_total']:
                raise ValueError('Resultados históricos inconsistentes.')
        if datos.get('analisis_empalme_activo_id') is not None and datos['analisis_empalme_activo_id'] not in ids:
            raise ValueError('Análisis Empalme activo inexistente.')
        for r in calculos:
            if r.get('analisis_empalme_id') and not any(a['id'] == r['analisis_empalme_id'] and a['calculo_id'] == r.get('calculo_id') for a in historial):
                raise ValueError('Registro operativo con vínculo huérfano.')
        if not isinstance(datos.get('generales', {}), dict) or any(not isinstance(v,str) for v in datos.get('generales', {}).values()):
            raise ValueError('Datos generales de Empalme inválidos.')
    except (KeyError, TypeError, StopIteration, OverflowError) as error:
        raise ValueError('Instantánea de Empalme incompleta o inválida.') from error
