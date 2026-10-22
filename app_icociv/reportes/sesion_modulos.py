"""Informes de los módulos: mismas plantillas y snapshots, sin ejecutar el motor."""
from datetime import datetime
from dataclasses import replace
from pathlib import Path
from app_icociv.utilidades.importes_presupuestales import texto_desglose
from app_icociv.exportables.archivo_atomico import guardar_atomico
from app_icociv.persistencia.historial_icociv import recuperar_resultado
from app_icociv.reportes.modelo import Informe,Portada,Seccion,Tabla,Parrafo,ConfiguracionInforme,identificador_informe,NOMBRE_COMPLETO
from app_icociv.reportes.contenido import DatosProyeccion,construir_informe_proyeccion
from app_icociv.reportes.contenido_empalme import construir_informe_empalme,_insumo
from app_icociv.interfaz.widgets.tabla_numerica import numero_original,texto_numero,variacion_indice


def guardar(informe,ruta,formato):
    from app_icociv.reportes import docx_render,pdf_render
    if formato not in ('docx','pdf'):raise ValueError('Formato de informe no válido.')
    if Path(ruta).suffix.lower()!=f'.{formato}':raise ValueError('La extensión del archivo debe coincidir con el formato seleccionado.')
    renderer=pdf_render if formato=='pdf' else docx_render
    return guardar_atomico(ruta,lambda temporal:renderer.guardar(informe,temporal))


def _numero(valor,decimales=4):
    return texto_numero(numero_original(valor),decimales)


def _factor(r):
    from app_icociv.servicios.actualizacion_icociv import es_factor_legado
    # Fase 4I-D: celda solo numérica; el criterio anterior se informa en un párrafo aparte.
    return _numero(r.get('factor_icociv'),6) if es_factor_legado(r) else _numero(r.get('factor_icociv'),4)


def _tabla_registros(valores):
    bloques=[Tabla(['N.º','Ítem','Unidad','Cantidad','P (COP)','A (COP)','Base (COP)'],
        [[str(i),str(r.get('item','')),str(r.get('unidad','')),_numero(r.get('cantidad')),_numero(r.get('precio_base'),0),
          _numero(r.get('anticipo_amortizado'),0),_numero(r.get('base_ajustable'),0)] for i,r in enumerate(valores,1)],columnas_numericas=(0,3,4,5,6)),
        Tabla(['N.º','ID análisis','I0 ICOCIV','I ICOCIV','Factor','Valor (COP)','Diferencia (%)'],
        [[str(i),str(r.get('analisis_id') or 'Registro anterior sin vínculo'),_numero(r.get('i0_icociv')),_numero(r.get('i_icociv')),
          _factor(r),_numero(r.get('valor_proyectado'),0),_numero(r.get('diferencia_porcentual'),2)] for i,r in enumerate(valores,1)],columnas_numericas=(0,2,3,4,5,6))]
    for i,r in enumerate(valores,1):
        bloques.extend([Parrafo(f"Registro {i} · ID {r.get('calculo_id','')} · {r.get('fecha_calculo','')} · Modelo {r.get('modelo_proyeccion','')} · Horizonte {r.get('horizonte','')} meses"),
            Parrafo(f"Proyecto {r.get('proyecto','')} · Componente {r.get('tipo_componente','')} {r.get('nombre_componente','')} · Ruta {r.get('ruta_icociv','')}"),
            Parrafo(str(r.get('observacion_tecnica') or 'Sin observación técnica registrada.')),
            Parrafo(str(r.get('trazabilidad_formula') or 'Sin desarrollo matemático guardado.'))])
    return bloques


def construir_proyecciones(widget,config=None):
    config=config or ConfiguracionInforme.desde_tipo('tecnico')
    momento=datetime.now();identificador=identificador_informe(momento);proyecto=widget.datos_proyecto()
    secciones=[Seccion('sesion','Alcance de la sesión',[
        Parrafo(getattr(widget,'_descripcion_alcance',None) or 'Se incluyen todos los análisis guardados y registros acumulados del módulo. El filtro de la pantalla no reduce el conjunto exportado. Las proyecciones son estimaciones de SAVIP y no índices oficiales del DANE.'),
        Parrafo(f"Análisis activo: {widget.analisis_activo_id or 'sin análisis activo'}. Proyecciones visibles guardadas: {len(widget.proyecciones)}. Registros calculados: {len(widget.valores)}."),
        Tabla(['Dato del proyecto','Valor'],[[k,str(v)] for k,v in proyecto.items()])])]
    if widget.historial:
        secciones.append(Seccion('historial','Historial de análisis',[
            Tabla(['ID','Análisis','Creado','Modelo','Horizonte (meses)'],
                [[a['id'],a['nombre'],a['creado'],str(a['contexto'].get('modelo','')),str(a['parametros'].get('horizonte',''))] for a in widget.historial])]))
    for i,a in enumerate(widget.historial,1):
        snapshot=recuperar_resultado(a['resultado']);serie=snapshot['serie_df']
        datos=DatosProyeccion(snapshot['proyeccion'],serie,fuente_label=str(snapshot.get('fuente_visible') or snapshot.get('fuente','')),
            archivo_excel=a.get('archivo_excel',''),ruta_jerarquica=snapshot.get('ruta_jerarquica'),fila=snapshot.get('fila'),
            year_month=list(serie['Periodo'].astype(str)) if 'Periodo' in serie else [],
            usuario=proyecto.get('responsable_tecnico',''),nombre_sesion=a['nombre'])
        original=construir_informe_proyeccion(datos,config,momento)
        secciones.append(Seccion(f'analisis_{i}',f'Análisis {i} {a["nombre"]}',[
            Parrafo(f"ID {a['id']} · Creado {a['creado']} · Proyecto al ejecutar {a['proyecto'].get('nombre_proyecto','')}"),
            Parrafo('Las tablas técnicas siguientes proceden de la instantánea conservada; no se recalcula el modelo.')]))
        secciones.extend(replace(s,clave=f'analisis_{i}_{s.clave}',titulo=f'Análisis {i} {s.titulo}') for s in original.secciones)
    if not widget.historial:
        secciones.append(Seccion('anterior','Información de la sesión anterior',[
            Parrafo('Esta sesión no contiene instantáneas técnicas del historial. Se conserva la información disponible sin reconstruir modelos ni inventar datos.'),
            Tabla(['Campo del contexto','Valor'],[[k,str(v)] for k,v in (widget.contexto or {}).items()])]))
    for i,r in enumerate(widget._filas_proyecciones_numericas(),1):
        secciones.append(Seccion(f'fila_{i}',f'Registro técnico acumulado {i}',[
            Tabla(['Campo','Valor guardado'],[[k,_numero(v) if k in ('indice_base','indice_proyectado','mae','rmse','mape','smape','mase') else str(v)] for k,v in r.items()])]))
    if widget.valores:
        efectivos = [widget.escenario_registro(r)[0] for r in widget.valores]
        bloques = _tabla_registros(efectivos)
        bloques.insert(0,Parrafo('Escenario económico vigente. Cambiar la referencia no modifica los pronósticos ni los registros originales. Cantidad es informativa. Alcance de la próxima selección: ' + ('global ICOCIV' if widget.aplicar_global.isChecked() else 'análisis activo') + '.'))
        bloques.append(Tabla(['N.º','Ajuste R (COP)','Estado'],
            [[str(i),_numero(e.get('r_total'),0),widget.escenario_registro(r)[1]]
                for i,(r,e) in enumerate(zip(widget.valores,efectivos),1)],columnas_numericas=(0,1)))
        for i,r in enumerate(widget.valores,1):
            referencia,objetivo = widget.fechas_registro(r)
            # Las fechas acompañan al párrafo existente de identidad, sin nuevas columnas.
            posicion = 3+(i-1)*4
            bloques[posicion] = replace(bloques[posicion],texto=bloques[posicion].texto + f' · Referencia efectiva: {referencia or "No disponible"} · Objetivo: {objetivo or "No disponible"}')
            bloques[posicion+1] = replace(bloques[posicion+1],texto=bloques[posicion+1].texto+'\nDesglose presupuestal complementario · Escenario vigente del slider\n'+texto_desglose(r,efectivos[i-1].get('valor_proyectado'),'').split('\n',1)[1])
        from app_icociv.servicios.actualizacion_icociv import TEXTO_CRITERIO_FACTOR, TEXTO_FACTOR_LEGADO
        from app_icociv.servicios.actualizacion_icociv import es_factor_legado
        legados=[str(i) for i,e in enumerate(efectivos,1) if es_factor_legado(e)]
        bloques.append(Parrafo(f'Metodología del factor presupuestal: {TEXTO_CRITERIO_FACTOR}'
            + (f' Registros N.º {", ".join(legados)}: {TEXTO_FACTOR_LEGADO}; su factor y sus importes no siguen la regla vigente.' if legados
               else ' Todos los registros siguen la regla vigente.')))
        for i,(r,e) in enumerate(zip(widget.valores,efectivos),1):
            if e != r:
                bloques.append(Parrafo(f"Auditoría registro {i} · ID {r.get('calculo_id','')} · ID análisis {r.get('analisis_id','')} · Original: I0 {_numero(r.get('i0_icociv'))} ({r.get('periodo_base','')}), factor {_numero(r.get('factor_icociv'),6)}, R {_numero(r.get('r_total'),3)}, valor {_numero(r.get('valor_proyectado'),3)}, diferencia {_numero(r.get('diferencia_porcentual'),3)} %. Registro y snapshot íntegros en sesión JSON."))
        secciones.append(Seccion('valores','Valores económicos vigentes y trazabilidad',bloques))
    return Informe(Portada('Proyecciones ICOCIV de la sesión','Análisis técnicos y valores calculados',[(k,str(v)) for k,v in proyecto.items()]),
        secciones,identificador,'tecnico',momento,pie=f'{NOMBRE_COMPLETO} · {identificador}')


def construir_empalme(calculos,generales,config=None,historial=None,operativos=None):
    informe=construir_informe_empalme(calculos,generales,config)
    resumen_original = next((s for s in informe.secciones if s.clave=='resumen'),None)
    if resumen_original is not None:
        resumen_original.bloques.append(Parrafo('Los agregados anteriores conservan los importes originales del servicio. No representan un total presupuestal cuando hay modalidades distintas o sin clasificar. Consulte los importes unitarios y totales por ID en el desglose complementario.'))
    operativos = calculos if operativos is None else operativos
    if operativos:
        from app_icociv.interfaz.widgets.empalme_iccp_icociv import _fila_operativa
        datos = [_fila_operativa(r) for r in operativos]
        resumen = Seccion('resumen_operativo_empalme','Resumen operativo de Empalme',[
            Parrafo('Registros económicos vigentes. La variación del valor es 100 × R / Base ajustable; es distinta de la variación del índice. Cantidad convierte los pares unitario/total según la modalidad declarada, sin modificar el valor principal.'),
            Tabla(['N.º','Componente','Ítem / insumo','Base (COP)','Ajuste R (COP)','Valor ajustado (COP)','Variación del valor (%)'],
                [[str(r.get('numero_calculo') or ''),str(r.get('nombre_componente') or ''),str(r.get('item') or '')]
                    + [_numero(r.get(k),3 if k=='variacion_valor' else 2) for k in ('base_ajustable','r_total','valor_actualizado','variacion_valor')] for r in datos],
                columnas_numericas=(0,3,4,5,6),anchos=(0.7,3.2,3.2,2.1,2.1,2.3,2.3))])
        indice = next((i for i,s in enumerate(informe.secciones) if s.clave=='indices'),0)
        resumen.bloques.extend(Parrafo(texto_desglose(r,r.get('valor_actualizado'),'Desglose presupuestal complementario · registro económico original')) for r in operativos)
        informe.secciones.insert(indice,resumen)
    for s in informe.secciones:
        if s.clave=='resultados':
            original=s.bloques[0]
            s.bloques=[replace(original,encabezados=['Ítem','Unidad','Base (COP)','R1 (COP)','R2 (COP)','Ajuste R (COP)','Valor actualizado (COP)','Diferencia (%)'],
                filas=[[_insumo(r),str(r.get('unidad',''))]+[_numero(r.get(k),3 if k=='diferencia_porcentual' else 2) for k in ('base_ajustable','r1','r2','r_total','valor_actualizado','diferencia_porcentual')] for r in calculos])]
    informe.secciones.extend([
        Seccion('equivalencias_modulo','Equivalencias ICCP ICOCIV',[Tabla(['Insumo contractual','Serie ICCP','Ruta ICOCIV'],
            [[_insumo(r),str(r.get('serie_iccp') or r.get('ruta_iccp') or ''),str(r.get('ruta_icociv') or '')] for r in calculos])]),
        Seccion('variacion_indice','Variación informativa del índice ICOCIV',[Tabla(['Insumo','I0 ICOCIV','I ICOCIV','Variación (%)','Estado','Periodo final'],
            [[_insumo(r),_numero(r.get('i0_icociv')),_numero(r.get('i_icociv')),_numero(variacion_indice(r.get('i0_icociv'),r.get('i_icociv')),3),
              'Proyectado' if r.get('icociv_final_es_proyectado') else 'Histórico',str(r.get('fecha_final',''))] for r in calculos],
            nota='Variación = 100 × (I / I0 − 1). Es informativa y no se aplica como factor adicional. Vacío indica dato no disponible o I0 inválido.',columnas_numericas=(1,2,3))])])
    if historial:
        informe.secciones.append(Seccion('historial_empalme','Historial independiente de Empalme',[
            Tabla(['N.º','Análisis','ID análisis','ID cálculo','Creado','Estado'],
                  [[str(a['numero']),a['nombre'],a['id'],a['calculo_id'],a['creado'],
                    'Instantánea original archivada' if 'resultado_archivado' in a else 'Registro operativo vinculado'] for a in historial])]))
        from app_icociv.persistencia.historial_empalme import campos_componente, resultado_analisis
        for a in historial:
            campos = campos_componente(resultado_analisis(a, calculos))
            if campos:
                informe.secciones[-1].bloques.append(Parrafo(f"Análisis {a['numero']} · ID {a['id']} · " + ' · '.join(f"{k}: {v}" for k, v in campos)))
            if 'resultado_archivado' in a:
                r = a['resultado_archivado']
                informe.secciones[-1].bloques.append(Parrafo(texto_desglose(r,r.get('valor_actualizado'),'Desglose presupuestal complementario · instantánea archivada · ID análisis '+a['id'])))
    return informe
