"""Contratos 4A C por etapas: datos, tabla activa y archivos auténticos."""
import os,sys
import json
from copy import deepcopy
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QDialog,QMessageBox
from unittest.mock import patch
from PySide6.QtTest import QTest
from app_icociv.interfaz.widgets.tabla_numerica import numero_original,variacion_indice
from app_icociv.interfaz.widgets.empalme_iccp_icociv import WidgetEmpalmeICCPICOCIV,COLUMNA_VARIACION_INDICE
from tests.test_variacion_indice_empalme import registros
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV
from app_icociv.exportables.archivo_atomico import guardar_atomico
from tests.fixtures.sesiones import cargar as cargar_sesion_sintetica, ruta_temporal as ruta_sesion_sintetica  # Fase 1A (AS-007)
app=QApplication.instance() or QApplication([])

def test_a_valor_original_display_y_copia_numericos():
    w=WidgetEmpalmeICCPICOCIV();rows=registros();rows[0].update(i0_icociv=105.969,i_icociv=151.2643,icociv_final_es_proyectado=True,fecha_final='2027_3')
    before=deepcopy(rows);w.calculos=rows;w._actualizar_tabla();w.show();app.processEvents()
    try:
        model=w.modelo_valor_ajustado;frame=model._dataframe
        pos=frame.columns.get_loc(COLUMNA_VARIACION_INDICE);index=model.index(0,pos)
        assert isinstance(frame.iat[0,pos],float)
        assert model.data(index,Qt.UserRole)==((151.2643/105.969)-1)*100
        assert '%' not in model.data(index) and '<' not in model.data(index)
        final=next(i for i,c in enumerate(frame.columns) if c.startswith('ÍNDICE ICOCIV FINAL'))
        cell=model.index(0,final)
        assert model.data(cell)=='151.2643' and model.data(cell,Qt.UserRole)==151.2643
        assert 'Proyectado' in model.data(cell,Qt.ToolTipRole) and '2027_3' in model.data(cell,Qt.ToolTipRole)
        w.tabla.setCurrentIndex(cell);QTest.keyClick(w.tabla,Qt.Key.Key_C,Qt.ControlModifier)
        QTest.keyRelease(w.tabla,Qt.Key.Key_Control)  # Ctrl queda activo en QTest offscreen si no se libera.
        assert app.clipboard().text()=='151.2643'
        assert rows==before
        w._mostrar_resultado(rows[0]);html=w.resultado.toHtml()
        assert '151.2643' in html and '(proyectado)' not in html
        assert variacion_indice(95.816,122.67)==((122.67/95.816)-1)*100
        for value in (None,float('nan'),float('inf'),'texto',True):assert numero_original(value) is None
        assert numero_original('151,2643 (proyectado)')==151.2643
        assert numero_original('1.234,5678')==1234.5678
        assert numero_original('151,2643 basura') is None
        assert variacion_indice(0,100) is None
    finally:w.close()

def proyecciones_guardadas():
    data=cargar_sesion_sintetica('SESION_AUDITORIA_UI')['proyecciones_icociv']
    w=WidgetProyeccionesICOCIV();w.restaurar_datos_sesion(data)
    return w

def test_b_barra_unica_destinos_filtro_borrado_y_edicion():
    w=proyecciones_guardadas()
    try:
        # Fase 4G-B: ICOCIV añade «Editar actividad» (5 botones); Empalme conserva 4.
        assert len(w.barra.findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton))==5
        assert w.barra.activa is None and not w.barra.boton_eliminar.isEnabled()
        w.tabla_proyecciones.selectRow(1);w.tabla_valores.selectRow(0)
        assert w.barra.activa==1
        before=deepcopy(w.historial);selected=w._valores_visibles[0]
        with patch.object(w,'_mostrar_resultado') as show:w.barra.boton_detalle.click()
        assert show.call_args.args[0] is selected
        w.barra.boton_eliminar.click();assert selected not in w.valores and len(w.proyecciones)==3
        w.show();w.tabla_proyecciones.setFocus();app.processEvents()
        w.tabla_proyecciones.selectRow(1);w.barra.boton_eliminar.click()
        assert len(w.proyecciones)==2 and len(w.historial)==3
        assert [a['resultado'] for a in before]==[a['resultado'] for a in w.historial]
        w.tabla_valores.selectRow(0);w.solo_analisis_activo.setChecked(True)
        assert w.barra.activa==1 and 'Valores proyectados' in w.barra.etiqueta.text()
        with patch.object(w,'_confirmar_eliminar_todo',return_value=False):w.barra.boton_todo.click()
        assert w.valores
        with patch.object(w,'_confirmar_eliminar_todo',return_value=True):w.barra.boton_todo.click()
        assert not w.valores and len(w.proyecciones)==2 and len(w.historial)==3
        assert not w.barra.boton_detalle.isEnabled()
    finally:w.close()
    e=WidgetEmpalmeICCPICOCIV();e.calculos=registros();e._actualizar_tabla()
    try:
        e.tabla.selectRow(0);e.tabla_equivalencias.selectRow(2)
        assert e.barra.activa==0
        with patch.object(e,'_dialogo_detalle'),patch.object(e,'_mostrar_resultado') as show:e.boton_detalle.click()
        assert show.call_args.args[0] is e.calculos[2]
        e.accion_editar.trigger();assert e.indice_edicion==2 and e.chk_acero.isChecked()
        from PySide6.QtCore import QItemSelectionModel
        e.tabla_equivalencias.selectionModel().select(e.modelo_equivalencias.index(0,0),QItemSelectionModel.Select)
        assert e.barra.indice() is None and not e.boton_detalle.isEnabled() and not e.boton_eliminar.isEnabled()
        e.tabla_equivalencias.clearSelection();e.tabla_equivalencias.selectRow(2)
        original=deepcopy(e.calculos)
        with patch.object(QDialog,'exec',return_value=0):e.boton_detalle.click()
        assert e.calculos==original
        e.boton_eliminar.click();assert len(e.calculos)==3 and all(r['item']!='Acero' for r in e.calculos)
        with patch.object(QMessageBox,'exec',lambda box:0),patch.object(QMessageBox,'clickedButton',lambda box:next(b for b in box.buttons() if b.text()=='Cancelar')):e.boton_eliminar_todo.click()
        assert len(e.calculos)==3
    finally:e.close()

def test_c_guardado_cancelacion_fallo_y_archivo_previo(tmp_path):
    from PySide6.QtWidgets import QFileDialog
    destino=tmp_path/'previo.xlsx';destino.write_bytes(b'original')
    def fallar(temporal):
        temporal.write_bytes(b'incompleto');raise OSError('Disco lleno simulado')
    try:guardar_atomico(destino,fallar)
    except OSError:pass
    else:raise AssertionError('Se ocultó el fallo')
    assert destino.read_bytes()==b'original' and list(tmp_path.iterdir())==[destino]
    w=proyecciones_guardadas();antes=w.datos_sesion()
    try:
        with patch.object(QFileDialog,'getSaveFileName',return_value=('','')),patch.object(w,'_generar_informe') as generar:
            w._exportar_informe('pdf');w._exportar_informe('docx');assert generar.call_count==0
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(tmp_path/'bad.pdf'),'')),patch.object(w,'_generar_informe',side_effect=PermissionError('Ruta sin permiso')),patch.object(QMessageBox,'critical') as error,patch.object(QMessageBox,'information') as exito:
            w._exportar_informe('pdf');assert error.call_count==1 and exito.call_count==0
        assert w.datos_sesion()==antes
    finally:w.close()

def test_d_tres_formatos_por_modulo_cancelacion_empalme_y_snapshot():
    from PySide6.QtWidgets import QFileDialog
    from app_icociv.reportes.modelo import ConfiguracionInforme
    p=proyecciones_guardadas();e=WidgetEmpalmeICCPICOCIV();e.calculos=registros();e._actualizar_tabla()
    try:
        for w,excel,informe in ((p,'_exportar_excel','_exportar_informe'),(e,'exportar_excel','generar_informe')):
            menu=w.barra.menu;actions=menu.actions()
            assert [a.text() for a in actions]==['Archivo Excel (.xlsx)','Informe PDF (.pdf)','Informe Word (.docx)']
            from contextlib import ExitStack
            with ExitStack() as pila,patch.object(w,excel) as x,patch.object(w,informe) as d:
                if w is p:  # Fase 4G-B: ICOCIV pregunta el alcance (aquí, toda la sesión) antes de exportar.
                    pila.enter_context(patch.object(p,'_elegir_alcance_exportacion',return_value=p.alcance_exportacion('sesion')))
                    pila.enter_context(patch.object(p,'_confirmar_avisos_alcance',return_value=True))
                for a in actions:a.trigger()
            assert x.call_count==1 and [c.args[0] for c in d.call_args_list]==['pdf','docx']
        antes=deepcopy(e.calculos)
        with patch('app_icociv.interfaz.widgets.dialogo_informe.pedir_configuracion',return_value=ConfiguracionInforme.desde_tipo('empalme')),patch.object(QFileDialog,'getSaveFileName',return_value=('','')),patch.object(e,'_generar_informe') as generar:
            e.generar_informe('docx');assert generar.call_count==0
        assert e.calculos==antes
        with patch('app_icociv.proyeccion.servicio_proyeccion.ejecutar_proyeccion',side_effect=AssertionError('No recalcular')):
            from app_icociv.reportes.sesion_modulos import construir_proyecciones
            reporte=construir_proyecciones(p)
        assert sum(s.clave.startswith('analisis_') and s.clave.count('_')==1 for s in reporte.secciones)==3
    finally:p.close();e.close()

if __name__=='__main__':
    import inspect,tempfile
    for name,fn in sorted(list(globals().items())):
        if name.startswith('test_') and callable(fn):
            if 'tmp_path' in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as folder:fn(Path(folder))
            else:fn()
            print('PASS '+name,flush=True)
