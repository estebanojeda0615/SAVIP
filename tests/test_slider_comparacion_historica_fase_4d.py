import json,math,os,types
from pathlib import Path
from copy import deepcopy
from functools import lru_cache
from unittest.mock import patch
import pandas as pd
from PySide6.QtCore import QCoreApplication  # Fase 4I-G: la apertura de sesiones termina en el bucle de eventos
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest,QSignalSpy
from PySide6.QtGui import QFontDatabase,QFont
from PySide6.QtWidgets import QApplication,QScrollArea,QMessageBox,QFileDialog
from openpyxl import load_workbook
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV,COLUMNAS_VALORES,COLUMNAS_PROYECCIONES,COLUMNAS_VALORES_TECNICAS,_extraer_contexto
from app_icociv.interfaz.widgets.comparacion_historica import historico_observado,periodo_mensual
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.persistencia.historial_icociv import serializar_resultado,recuperar_resultado
from app_icociv.persistencia.gestor_sesiones import cargar_sesion
from tests.test_historial_empalme_fase_4b import guardar,abrir
from tests.fixtures.fase0.generadores import anexo_slider_4d
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs/fase_4d_slider'
APP=QApplication.instance() or QApplication([])

@lru_cache(maxsize=1)
def _reales():return json.loads((OUT/'fixtures/TRES_ANALISIS_REALES.json').read_text(encoding='utf-8'))
def reales():return deepcopy(_reales())
def cargar(v):
    v.sesion_pendiente={'proyecciones_icociv':reales()};v._restaurar_sesion_pendiente();return v.widget_proyecciones
def originales(w):
    d=deepcopy(w.datos_sesion());d.pop('comparacion_historica',None);return d
def sin_motor():return patch('app_icociv.interfaz.controladores.controlador_principal.ControladorPrincipal.ejecutar_analisis',side_effect=AssertionError('Motor al consultar'))

def sintetico():
    w=WidgetProyeccionesICOCIV();base=reales()['historial_analisis'][0]
    resultado=recuperar_resultado(base['resultado'])
    puntos=[('2020_1',100.),('2024_2',104.7619047619),('2024_4',120.),('2024_5',110.),('2026_12',100.)]
    resultado['serie_df']=pd.DataFrame(puntos,columns=['Periodo','Indice'])
    resultado['fila']=pd.DataFrame([dict(puntos)])
    resultado['proyeccion']['resultado_horizonte_solicitado']['indice_proyectado']=110.
    w.actualizar_contexto(resultado);w.registrar_analisis(resultado,base['seleccion'],base['parametros'],'FUENTE_SINTETICA_NO_OFICIAL.xlsx')
    w.unidad.setCurrentIndex(1);w.cantidad.setValue(2);w.precio_base.setValue(1000);w.anticipo.setValue(100);w.modalidad_importe.setCurrentIndex(w.modalidad_importe.findData('unitario'));w.boton_calcular.click()
    # Fixture de sesión anterior: metadato ausente intencionadamente.
    w.valores[0].pop('modalidad_importe');w.modalidad_importe.setCurrentIndex(0);w._refrescar_tabla_valores()
    assert len(w.valores)==1 and w.valores[0]['i0_icociv']==100 and w.valores[0]['i_icociv']==110
    return w

def test_dos_porcentajes_independientes_slider_manual_y_teclas():
    # El contrato informativo 4D se revocó explícitamente: ahora se comprueba economía efectiva.
    from tests.test_referencia_economica_fase_4d_b import test_inicializacion_movimiento_real_y_retorno_sin_drift
    test_inicializacion_movimiento_real_y_retorno_sin_drift()
    w=sintetico()
    try:
        w.seleccionar_referencia_historica('2024-05');antes=deepcopy(w._periodo_por_analisis);spy=QSignalSpy(w.comparacion_cambiada)
        w.selector_referencia.setEditText('2024-03');QTest.keyClick(w.selector_referencia.lineEdit(),Qt.Key_Return)
        assert w._periodo_por_analisis==antes and spy.count()==1 and 'no está observado' in w.lbl_estado_comparacion.text()
        assert w.seleccionar_referencia_historica('2020-01') and len(COLUMNAS_VALORES)==17
    finally:w.close()


def test_tres_analisis_dos_series_selecciones_propias_y_ambos_selectores():
    v=VentanaPrincipal();w=cargar(v)
    try:
        ids=[a['id'] for a in w.historial];antes=deepcopy(w.valores);snapshots=deepcopy(w.historial)
        assert w.historial[0]['contexto']['ruta_texto']==w.historial[1]['contexto']['ruta_texto']!=w.historial[2]['contexto']['ruta_texto']
        with sin_motor() as motor,patch.object(v.controlador,'cargar_archivo',side_effect=AssertionError('Lectura DANE')) as lectura:
            antes_comparaciones=[w.comparacion_registro(r) for r in w.valores]
            w.selector_analisis.setCurrentIndex(w.selector_analisis.findData(ids[0]));w.seleccionar_referencia_historica(w._periodos_slider[0])
            despues=[w.comparacion_registro(r) for r in w.valores]
            assert despues[0]!=antes_comparaciones[0] and despues[1:]==antes_comparaciones[1:]
            v.selector_resultados_icociv.setCurrentIndex(v.selector_resultados_icociv.findData(ids[1]));w.seleccionar_referencia_historica(w._periodos_slider[10])
            v.selector_resultados_icociv.setCurrentIndex(v.selector_resultados_icociv.findData(ids[2]));w.seleccionar_referencia_historica(w._periodos_slider[20])
            referencias=deepcopy(w._periodo_por_analisis)
            for i in (0,2,1,0):
                w.selector_analisis.setCurrentIndex(w.selector_analisis.findData(ids[i]))
                assert w.selector_referencia.currentData()==referencias[ids[i]]
                assert referencias[ids[i]] in v.lbl_comparacion_resultados.text()
            assert motor.call_count==lectura.call_count==0
        assert w.valores==antes
        assert [a['resultado'] for a in w.historial]==[a['resultado'] for a in snapshots]
        assert [a['fila_tecnica'] for a in w.historial]==[a['fila_tecnica'] for a in snapshots]
    finally:v.close()

def test_meses_discontinuos_invalidos_legados_y_series_incompatibles():
    w=sintetico()
    try:
        a=w.historial[0];resultado=recuperar_resultado(a['resultado'])
        resultado['serie_df']=pd.DataFrame([('2020_1',100.),('2024_1',0.),('2024_2',None),('2024_3',float('nan')),('2024_4',float('inf')),('2024_5',90.),('2024_6','115 (Proyectado)'),('2026_12',100.)],columns=['Periodo','Indice'])
        resultado['fila']=pd.DataFrame([dict(resultado['serie_df'].itertuples(index=False,name=None))])
        a['resultado']=serializar_resultado(resultado);w._preparar_comparacion_historica();w._actualizar_controles_comparacion()
        assert w._periodos_slider==['2020-01','2024-05','2026-12']
        assert not w.seleccionar_referencia_historica('2024-01') and not w.seleccionar_referencia_historica('2024-02')
        r=deepcopy(w.valores[0]);r.pop('analisis_id');assert w.comparacion_registro(r)[:3]==('',None,None)
        r=deepcopy(w.valores[0]);r['ruta_icociv']='Otra serie';assert w.comparacion_registro(r)[:3]==('',None,None)
        r=deepcopy(w.valores[0]);r['i_icociv']=float('nan');assert w.comparacion_registro(r)[:3]==('',None,None)
        resultado['serie_df']=pd.concat([resultado['serie_df'],resultado['serie_df'].iloc[:1]],ignore_index=True)
        a['resultado']=serializar_resultado(resultado);assert not historico_observado(a)[0]
        a['resultado']['fila']=serializar_resultado(pd.DataFrame())
        w._preparar_comparacion_historica();w._actualizar_controles_comparacion();assert not w.slider_comparacion.isEnabled()
        assert 'no disponible' in w.lbl_estado_comparacion.text().lower()
        assert periodo_mensual('2024-13') is None and periodo_mensual('0000-01') is None
        legacy=WidgetProyeccionesICOCIV()
        try:
            r.pop('analisis_id',None)
            legacy.restaurar_datos_sesion({'valores':[r]});assert legacy.modelo_valores.columnCount()==17
            assert not legacy.slider_comparacion.isEnabled() and legacy.comparacion_registro(r)[:3]==('',None,None)
        finally:legacy.close()
    finally:w.close()

def test_sesion_mixta_reabierta_sin_fuente_sin_motor_y_empalme_intacto(tmp_path):
    v=VentanaPrincipal();w=cargar(v);otro=None
    try:
        fuente=anexo_slider_4d(tmp_path/'anexo.xlsx')  # Fase 1A (AS-007): regenerado idéntico; antes se copiaba de docs/
        for a in w.historial:a['archivo_excel']=str(fuente)
        v.controlador.ruta_archivo=fuente
        emp=json.loads((ROOT/'docs/fase_4c/FIXTURE_DATOS.json').read_text(encoding='utf-8'))['empalme_iccp_icociv']
        v.widget_empalme.restaurar_datos_sesion(emp)
        for i,a in enumerate(w.historial):
            v._activar_analisis(a['id']);w.seleccionar_referencia_historica(w._periodos_slider[i*5])
        antes=deepcopy(w.datos_sesion());emp_antes=deepcopy(v.widget_empalme.datos_sesion())
        p=tmp_path/'mixta.json';guardar(v,p)
        guardado=cargar_sesion(p)['proyecciones_icociv']
        assert all(guardado[k]==valor for k,valor in antes.items())
        antes=guardado
        fuente.rename(tmp_path/'anexo_retirado.xlsx');assert not fuente.exists()
        v.close();otro=VentanaPrincipal()
        with sin_motor() as motor,patch.object(otro.controlador,'cargar_archivo',side_effect=AssertionError('DANE ausente')) as carga:
            abrir(otro,p);nuevo=otro.widget_proyecciones
            assert nuevo.datos_sesion()==antes and otro.widget_empalme.datos_sesion()==emp_antes
            # Fase 4G: referencias y objetivos distintos por análisis → 19 columnas (fecha junto a I0 y a I).
            assert nuevo.slider_comparacion.isEnabled() and nuevo.modelo_valores.columnCount()==19
            for a in nuevo.historial:
                otro._activar_analisis(a['id']);assert nuevo.selector_referencia.currentData()==antes['comparacion_historica']['selecciones'][a['id']]['periodo']
            assert motor.call_count==carga.call_count==0
        assert nuevo.valores==antes['valores'] and nuevo.proyecciones==antes['proyecciones']
    finally:
        if otro:otro.close()
        v.close()

def test_metadatos_corruptos_rechazo_no_destructivo(tmp_path):
    v=VentanaPrincipal();w=cargar(v)
    try:
        antes=deepcopy(w.datos_sesion());identificador=w.historial[0]['id']
        corruptos=[None,[],{'version':True,'periodo_por_analisis':{}},{'version':2,'periodo_por_analisis':{}},
            {'version':1,'periodo_por_analisis':[]},{'version':1,'periodo_por_analisis':{'inexistente':'2024-01'}},
            {'version':1,'periodo_por_analisis':{identificador:'2024-13'}},{'version':1,'periodo_por_analisis':{identificador:'2024_1'}},
            {'version':1,'periodo_por_analisis':{identificador:'1900-01'}}]
        for bloque in corruptos:
            d=deepcopy(antes);d['comparacion_historica']=bloque
            try:w.restaurar_datos_sesion(d)
            except ValueError:pass
            else:raise AssertionError('Se aceptó bloque corrupto')
            assert w.datos_sesion()==antes
        p=tmp_path/'corrupta.json';p.write_text(json.dumps({'proyecciones_icociv':d},ensure_ascii=False),encoding='utf-8')
        with patch.object(type(v),'_corte_dane_cargado',return_value='9999-12'),patch.object(QFileDialog,'getOpenFileName',return_value=(str(p),'')),patch.object(type(v),'_decidir_cierre',return_value='descartar'),patch.object(QMessageBox,'warning') as aviso,sin_motor() as motor:
            v.abrir_sesion()
            while v._operacion_sesion: QCoreApplication.processEvents()
            assert aviso.called and 'Excel del DANE' not in aviso.call_args[0][2] and motor.call_count==0
        assert w.datos_sesion()==antes
    finally:v.close()

def test_filtro_seleccion_detalle_y_borrados_con_historial_conservado():
    v=VentanaPrincipal();w=cargar(v)
    try:
        v._activar_analisis(w.historial[0]['id']);w.tabla_valores.selectRow(0);calculo=w.valores[0]['calculo_id']
        w.seleccionar_referencia_historica(w._periodos_slider[3]);assert w._valores_visibles[w.tabla_valores.selectedIndexes()[0].row()]['calculo_id']==calculo
        w.solo_analisis_activo.setChecked(True);assert len(w._valores_visibles)==1 and w.tabla_valores.selectedIndexes()
        with patch.object(w,'_mostrar_resultado') as detalle:
            w._detalle_valor();assert detalle.call_count==1 and detalle.call_args.args[0]['calculo_id']==calculo
        w._eliminar_valor();assert len(w.valores)==2 and len(w.historial)==3
        with patch.object(w,'_confirmar_eliminar_todo',return_value=False):w._eliminar_todos_valores();assert len(w.valores)==2
        with patch.object(w,'_confirmar_eliminar_todo',return_value=True):w._eliminar_todos_valores();assert not w.valores and len(w.historial)==3
        assert w.modelo_valores.rowCount()==0 and len(w._periodo_por_analisis)==3
    finally:v.close()

def test_excel_18_columnas_formulas_comparativas_y_originales_iguales(tmp_path):
    # Las 18 columnas informativas y las hojas extra fueron sustituidas por el contrato 4D-B.
    from tests.test_referencia_economica_fase_4d_b import test_excel_cinco_hojas_formulas_y_trazabilidad
    test_excel_cinco_hojas_formulas_y_trazabilidad(tmp_path)


def test_informes_tecnicos_y_constructor_empalme_intactos():
    from dataclasses import asdict
    from datetime import datetime
    from app_icociv.reportes import sesion_modulos as actuales
    source=OUT/'respaldo_inicio/app_icociv__reportes__sesion_modulos.py.bak'
    m=types.ModuleType('reportes_anteriores');m.__package__='app_icociv.reportes';exec(compile(source.read_text(encoding='utf-8'),str(source),'exec'),m.__dict__)
    w=WidgetProyeccionesICOCIV()
    try:
        w.restaurar_datos_sesion(reales());momento=datetime(2026,10,11,12)
        with patch.object(m,'datetime') as c1,patch.object(actuales,'datetime') as c2:
            c1.now.return_value=c2.now.return_value=momento
            antes=asdict(m.construir_proyecciones(w));despues=asdict(actuales.construir_proyecciones(w))
        # Toda sección técnica sigue idéntica; solo cambia la presentación económica autorizada.
        antes['secciones']=[s for s in antes['secciones'] if s['clave']!='valores']
        despues['secciones']=[s for s in despues['secciones'] if s['clave']!='valores']
        assert antes==despues
        # 4E autoriza sólo los párrafos presupuestales; tablas y contenido económico previo siguen idénticos.
        fixture=json.loads((ROOT/'docs/fase_4c/FIXTURE_DATOS.json').read_text(encoding='utf-8'))['empalme_iccp_icociv']
        with patch('app_icociv.reportes.contenido_empalme.datetime') as reloj:
            reloj.now.return_value=momento
            antes=asdict(m.construir_empalme(fixture['calculos'],fixture['generales'],historial=fixture['historial_empalme']))
            despues=asdict(actuales.construir_empalme(fixture['calculos'],fixture['generales'],historial=fixture['historial_empalme']))
        for s in despues['secciones']:
            s['bloques']=[b for b in s['bloques'] if not str(b.get('texto','')).startswith(('Desglose presupuestal complementario','Los agregados anteriores conservan'))]
        assert antes==despues
    finally:w.close()

def test_temas_resoluciones_foco_y_controles_sin_scroll_externo_horizontal():
    for f in ('segoeui.ttf','segoeuib.ttf','seguisb.ttf'):QFontDatabase.addApplicationFont('C:/Windows/Fonts/'+f)
    APP.setFont(QFont('Segoe UI',10));v=VentanaPrincipal();w=cargar(v)
    try:
        v._cambiar_seccion(1)
        for tema in ('claro','oscuro'):
            v._aplicar_tema(tema,persistir=False)
            for ancho,alto in ((1100,700),(1366,768),(1920,1080)):
                v.resize(ancho,alto);v.show();APP.processEvents();scroll=w.findChild(QScrollArea);scroll.ensureWidgetVisible(w.slider_comparacion);APP.processEvents()
                assert scroll.horizontalScrollBar().maximum()==0 and w.slider_comparacion.width()>=120 and w.selector_referencia.width()>=150
                w.slider_comparacion.setFocus();APP.processEvents();assert APP.focusWidget() is w.slider_comparacion
                QTest.keyClick(w.slider_comparacion,Qt.Key_Tab);assert APP.focusWidget() in (w.selector_referencia,w.selector_referencia.lineEdit())
                assert w.tabla_valores.horizontalScrollBar().maximum()>0
    finally:v.close()
