"""Columna derivada: índices originales, contratos de tabla y acciones por fila."""
import os,sys,types
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication,QMessageBox
import app_icociv.interfaz.widgets.empalme_iccp_icociv as actual
from app_icociv.servicios.empalme_iccp_icociv import calcular_empalme_general,calcular_empalme_acero
app=QApplication.instance() or QApplication([])

def baseline_module():
    name='app_icociv.interfaz.widgets.empalme_baseline_variacion'
    module=types.ModuleType(name)
    path=ROOT/'docs/fase_4a_variacion_indice/respaldo_inicio/app_icociv__interfaz__widgets__empalme_iccp_icociv.py.bak'
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module

def registros():
    iccp={'Total ICCP':{'2021_1':100,'2021_6':105,'2021_12':110}}
    icociv={'2021_12':95.816,'2022_1':122.67,'2022_2':95.816}
    base={'item':'Cemento','unidad':'m3','precio_base':123456.78,'cantidad':12.3456,
          'anticipo_amortizado':1234.56,'fecha_inicial':'2021-01','fecha_final':'2022-01',
          'tipo_serie_iccp':'total_iccp','serie_iccp':'Total ICCP','ruta_icociv':'Ruta > Cemento'}
    rows=[calcular_empalme_general(base,icociv,iccp),
          calcular_empalme_general({**base,'item':'Arena','fecha_inicial':'2022-01','fecha_final':'2022-02','ruta_icociv':'Ruta > Arena'},icociv,iccp),
          calcular_empalme_acero({**base,'item':'Acero','p0':500000,'ix':4200.1234,'q':125.5,'calculo_acero':True,'ruta_icociv':'Ruta > Acero'},icociv,iccp),
          calcular_empalme_general({**base,'item':'Solo ICCP','fecha_final':'2021-06'},icociv,iccp)]
    for i,row in enumerate(rows):row.update(calculo_id='fixture-'+str(i),numero_calculo=i+1)
    return rows

def test_porcentajes_extremos_precision_y_datos_invalidos():
    f=actual._fmt_variacion_indice
    assert f(95.8160,122.6700)=='28.027 %'
    assert f(100,100)=='0 %' and f(100,95)=='-5 %'
    assert f(1,123.45678)=='12,245.678 %'
    for initial,final in ((0,100),(None,100),(100,None),('abc',100),(float('nan'),100),
                          (100,float('inf')),(float('-inf'),100),(True,100),(1e-308,1e308)):
        assert f(initial,final)=='N/D',(initial,final)
    assert f(100,100.0001)=='0 < Δ < 0.001 %'
    assert f(100,99.9999)=='-0.001 % < Δ < 0 %'
    # Las dos celdas de índice se muestran iguales; la variación usa sus originales distintos.
    assert actual._fmt_indice(100.00001)==actual._fmt_indice(100.00002)
    assert f(100.00001,100.00002)!='0 %'
    assert f(100,100.001)=='0.001 %'

def test_columna_solo_visible_orden_alineacion_y_actualizacion():
    old=baseline_module().WidgetEmpalmeICCPICOCIV();new=actual.WidgetEmpalmeICCPICOCIV()
    rows=registros();before=deepcopy(rows)
    try:
        for w in (old,new):w.calculos=deepcopy(rows);w._actualizar_tabla()
        frame=new.modelo_valor_ajustado._dataframe
        column=actual.COLUMNA_VARIACION_INDICE
        pos=frame.columns.get_loc(column)
        assert frame.columns[pos-1].startswith('ÍNDICE ICOCIV FINAL (I)') and frame.columns[pos+1]=='R2'
        # 4A C conserva los valores originales como números; las unidades van al encabezado.
        for i,r in enumerate(rows):
            assert frame.iloc[i,pos]==actual.variacion_indice(r.get('i0_icociv'),r.get('i_icociv'))
        assert new.modelo_valor_ajustado.data(new.modelo_valor_ajustado.index(0,pos))=='28.027'
        assert new.calculos==old.calculos==before
        assert new._dataframe_valor_ajustado().equals(old._dataframe_valor_ajustado())
        assert new._dataframe_detalle_exportacion().equals(old._dataframe_detalle_exportacion())
        assert new._columnas_valor_ajustado()==old._columnas_valor_ajustado()
        index=new.modelo_valor_ajustado.index(0,pos)
        assert new.modelo_valor_ajustado.data(index,Qt.TextAlignmentRole)==Qt.AlignRight|Qt.AlignVCenter
        new.calculos[0]['i_icociv']=95.816
        new._actualizar_tabla()
        assert new.modelo_valor_ajustado._dataframe.iloc[0,pos]==0
        new.calculos=[];new._actualizar_tabla()
        assert column in new.modelo_valor_ajustado._dataframe and new.modelo_valor_ajustado.rowCount()==0
    finally:old.close();new.close()

def test_seleccion_detalle_edicion_y_eliminacion():
    w=actual.WidgetEmpalmeICCPICOCIV();w.calculos=registros();w._actualizar_tabla()
    try:
        for row in range(4):
            w.tabla.selectRow(row)
            assert w._fila_seleccionada()==row
            with patch.object(w,'_dialogo_detalle'),patch.object(w,'_mostrar_resultado') as detail:w.boton_detalle.click()
            assert detail.call_args.args[0] is w.calculos[row]
            w.accion_editar.trigger()
            assert w.indice_edicion==row and w.item.text()==w.calculos[row]['item']
            assert w.chk_acero.isChecked()==(row==2)
        w.tabla.selectRow(1);w.boton_eliminar.click()
        assert [r['item'] for r in w.calculos]==['Cemento','Acero','Solo ICCP']
        assert w.modelo_valor_ajustado.rowCount()==3
        with patch.object(QMessageBox,'exec',lambda box:0),patch.object(QMessageBox,'clickedButton',
                lambda box:next(b for b in box.buttons() if b.text()=='Eliminar')):
            w.boton_eliminar_todo.click()
        assert not w.calculos and w.modelo_valor_ajustado.rowCount()==0
    finally:w.close()

def test_edicion_recalcula_sin_cambiar_resultados_ni_identificadores():
    import app_icociv.servicios.empalme_iccp_icociv as service
    from datetime import datetime
    old=baseline_module().WidgetEmpalmeICCPICOCIV();new=actual.WidgetEmpalmeICCPICOCIV()
    rows=registros()
    option={'indices':{'2021_12':95.816,'2022_1':130.1234567},'seleccion':{},'ruta_estructurada':[]}
    try:
        for w in (old,new):
            w.calculos=deepcopy(rows);w._actualizar_tabla();w.tabla.selectRow(0)
            w.accion_editar.trigger() if hasattr(w,'accion_editar') else w.boton_editar.click()
            with patch.object(service,'datetime') as clock:
                clock.now.return_value=datetime(2026,10,10,12,0)
                w._finalizar_calculo(deepcopy(rows[0]),deepcopy(option))
            assert len(w.calculos)==4 and w.calculos[0]['calculo_id']=='fixture-0' and w.indice_edicion is None
        assert new.calculos[0]['tipo_componente'] is None and new.calculos[0]['nombre_componente']==''
        # Fase 4B-A añade sólo metadatos opcionales al registro actualizado.
        assert old.calculos==[{k:v for k,v in r.items() if k not in ('tipo_componente','nombre_componente')} for r in new.calculos]
        frame=new.modelo_valor_ajustado._dataframe
        assert frame.iloc[0][actual.COLUMNA_VARIACION_INDICE]==actual.variacion_indice(95.816,130.1234567)
        assert new._dataframe_valor_ajustado().equals(old._dataframe_valor_ajustado())
    finally:old.close();new.close()

if __name__=='__main__':
    for name,fn in sorted(list(globals().items())):
        if name.startswith('test_') and callable(fn):fn();print('PASS '+name,flush=True)
