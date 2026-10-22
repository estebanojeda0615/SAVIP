"""Geometría y eventos Qt de A/B/C; preferencias y datos de prueba aislados."""
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, Mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/fase_3c_a'
RUNTIME = OUT / 'temporal'
RUNTIME.mkdir(parents=True, exist_ok=True)
os.environ.update(QT_QPA_PLATFORM='offscreen', MPLCONFIGDIR=str(RUNTIME/'matplotlib'))
sys.path.insert(0, str(ROOT))
from PySide6.QtCore import QSettings, QPoint, Qt
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
for scope in (QSettings.Scope.UserScope, QSettings.Scope.SystemScope):
    QSettings.setPath(QSettings.Format.IniFormat, scope, str(RUNTIME/'settings'))
from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest, QSignalSpy
from matplotlib.figure import Figure
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.interfaz.widgets.visor_grafica import VisorGraficaDialog
from app_icociv.interfaz.tema import hoja_estilos
from app_icociv.interfaz.animaciones import establecer_movimiento_reducido
app = QApplication.instance() or QApplication([])
for name in ('segoeui.ttf','segoeuib.ttf','seguisb.ttf'):
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/'+name)
SIZES = ((1100,700),(1366,768),(1920,1080))

def settle(v):
    v.show()
    v.activateWindow()
    app.processEvents()
    QTest.qWait(20)

def measure(b, parent):
    pos=b.mapTo(parent,QPoint())
    r=b.contentsRect()
    return {'texto':b.text(),'icono':not b.icon().isNull(),'geometry':[pos.x(),pos.y(),b.width(),b.height()],
            'contentsRect':[r.x(),r.y(),r.width(),r.height()],
            'sizeHint':[b.sizeHint().width(),b.sizeHint().height()],
            'accesible':b.accessibleName(),'tooltip':b.toolTip(),'dpr':b.devicePixelRatioF()}

def shot(v,name):
    dest=OUT/'capturas'
    dest.mkdir(exist_ok=True)
    assert v.grab().save(str(dest/(name+'.png')))

def figure(horizon=3):
    fig=Figure()
    ax=fig.add_subplot()
    x=list(range(36+horizon))
    ax.plot(x,[100+i*.2 for i in x],label='Serie sintética; no pronóstico')
    return fig

def registrar_geometria(etapa):
    rows=[]
    v=VentanaPrincipal()
    establecer_movimiento_reducido(True)
    try:
        for theme in ('claro','oscuro'):
            v._aplicar_tema(theme,persistir=False)
            for size in SIZES:
                v.resize(*size)
                v._cambiar_seccion(0)
                for collapsed in (False,True):
                    v.navegacion.establecer_contraccion(collapsed)
                    settle(v)
                    actions=[v.boton_cargar,v.boton_abrir_sesion,v.boton_guardar_sesion]
                    rows.append({'etapa':etapa,'tema':theme,'size':size,'area':'A','contraida':collapsed,
                        'panel':[v.navegacion.width(),v.navegacion.height()],
                        'botones':[measure(b,v.navegacion) for b in actions]})
                    shot(v,f'{etapa}_{theme}_{size[0]}x{size[1]}_nav_{collapsed}')
                v.navegacion.establecer_contraccion(False)
                v._cambiar_seccion(2)
                settle(v)
                w=v.widget_empalme
                buttons=w.findChildren(QPushButton,'boton_incremento')
                rows.append({'etapa':etapa,'tema':theme,'size':size,'area':'B',
                    'scroll_horizontal':w.findChild(QScrollArea).horizontalScrollBar().maximum(),
                    'botones':[measure(b,w) for b in buttons]})
                shot(v,f'{etapa}_{theme}_{size[0]}x{size[1]}_empalme')
                viewer=VisorGraficaDialog(v,figure(),'Gráfica sintética',hoja_estilos(theme))
                viewer.resize(*size)
                settle(viewer)
                rows.append({'etapa':etapa,'tema':theme,'size':size,'area':'C',
                    'botones':[measure(b,viewer) for b in (viewer.boton_alejar,viewer.boton_acercar,viewer.boton_restablecer)]})
                shot(viewer,f'{etapa}_{theme}_{size[0]}x{size[1]}_grafica')
                viewer.close()
    finally:
        v.close()
    (OUT/(etapa+'_MEDIDAS.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')

def test_a_acciones_geometria_click_teclado_y_senales():
    load,abrir,guardar=Mock(),Mock(),Mock()
    with patch.object(VentanaPrincipal,'seleccionar_archivo',lambda self:load()), patch.object(VentanaPrincipal,'abrir_sesion',lambda self:abrir()), patch.object(VentanaPrincipal,'guardar_sesion_actual',lambda self:guardar()):
        v=VentanaPrincipal()
        establecer_movimiento_reducido(True)
        try:
            actions=((v.boton_cargar,load),(v.boton_abrir_sesion,abrir),(v.boton_guardar_sesion,guardar))
            original=[b.text() for b,_ in actions]
            for theme in ('claro','oscuro'):
                v._aplicar_tema(theme,persistir=False)
                for size in SIZES:
                    v.resize(*size)
                    for _ in range(3):
                        v.navegacion.establecer_contraccion(True)
                        settle(v)
                        for b,method in actions:
                            b.setEnabled(True)  # Precondición de sesión disponible; acción instrumentada.
                            assert b.isVisible() and b.toolTip() and b.accessibleName()
                            assert b.text() or not b.icon().isNull()
                            rect=b.geometry()
                            point=b.mapTo(v.navegacion,QPoint())
                            assert point.x()>=0 and point.x()+rect.width()<=v.navegacion.width(), measure(b,v.navegacion)
                            assert b.width()>=32 and b.contentsRect().width()>=b.iconSize().width()
                            old=method.call_count
                            QTest.mouseClick(b,Qt.MouseButton.LeftButton)
                            assert method.call_count==old+1, (b.accessibleName(),b.isEnabled(),b.isVisible(),method.call_count,old)
                            b.setFocus()
                            app.processEvents()
                            assert b.hasFocus()
                            QTest.keyClick(b,Qt.Key.Key_Space)
                            assert method.call_count==old+2
                            b.setEnabled(False)
                            QTest.mouseClick(b,Qt.MouseButton.LeftButton)
                            assert method.call_count==old+2
                            b.setEnabled(True)
                        nav_spy=QSignalSpy(v.navegacion.seleccion_cambiada)
                        QTest.mouseClick(v.navegacion.botones[1],Qt.MouseButton.LeftButton)
                        assert nav_spy.count()==1 and v.tabs_principales.currentIndex()==1
                        toggle_spy=QSignalSpy(v.navegacion.contraccion_cambiada)
                        QTest.mouseClick(v.navegacion.boton_contraer,Qt.MouseButton.LeftButton)
                        app.processEvents()
                        assert toggle_spy.count()==1 and not v.navegacion.esta_contraida()
                        assert [b.text() for b,_ in actions]==original
                        assert v.navegacion.height()==v.centralWidget().height()
                        assert v.cabecera_app.mapTo(v.centralWidget(),QPoint()).x()==v.navegacion.width()
        finally:
            v.close()

def test_b_empalme_paso_limites_disabled_teclado():
    v=VentanaPrincipal()
    establecer_movimiento_reducido(True)
    try:
        w=v.widget_empalme
        for theme in ('claro','oscuro'):
            v._aplicar_tema(theme,persistir=False)
            for size in SIZES:
                v.resize(*size)
                v._cambiar_seccion(2)
                settle(v)
                for spin in (w.fecha_inicial_anio,w.fecha_inicial_mes,w.fecha_final_anio,w.fecha_final_mes):
                    w.findChild(QScrollArea).ensureWidgetVisible(spin)
                    buttons=spin.parentWidget().findChildren(QPushButton,'boton_incremento')
                    assert len(buttons)==2
                    minus,plus=buttons
                    assert all(38<=b.width()<=40 for b in buttons)
                    middle=(spin.minimum()+spin.maximum())//2
                    spin.setValue(middle)
                    spy=QSignalSpy(spin.valueChanged)
                    QTest.mouseClick(plus,Qt.MouseButton.LeftButton)
                    assert spin.value()==middle+1 and spy.count()==1
                    QTest.mouseClick(minus,Qt.MouseButton.LeftButton)
                    assert spin.value()==middle and spy.count()==2
                    plus.setFocus()
                    QTest.keyClick(plus,Qt.Key.Key_Space)
                    assert spin.value()==middle+1 and spy.count()==3
                    for b,value in ((minus,spin.minimum()),(plus,spin.maximum())):
                        spin.setValue(value)
                        count=spy.count()
                        QTest.mouseClick(b,Qt.MouseButton.LeftButton)
                        assert spin.value()==value and spy.count()==count
                    spin.setValue(middle)
                    parent=spin.parentWidget()
                    parent.setEnabled(False)
                    QTest.mouseClick(plus,Qt.MouseButton.LeftButton)
                    assert spin.value()==middle
                    parent.setEnabled(True)
    finally:
        v.close()

def test_c_zoom_pan_reset_preservan_datos():
    for theme in ('claro','oscuro'):
        for horizon in (1,3,24):
            fig=figure(horizon)
            d=VisorGraficaDialog(None,fig,'Prueba gráfica',hoja_estilos(theme))
            settle(d)
            try:
                ax=d.eje
                line=ax.lines[0]
                before=line.get_xydata().copy()
                base=d._leer_limites()
                for button in (d.boton_alejar,d.boton_acercar,d.boton_restablecer):
                    assert button.width()>=32 and button.height()>=32
                    assert button.toolTip() and button.accessibleName()
                spy=QSignalSpy(d.boton_acercar.clicked)
                QTest.mouseClick(d.boton_acercar,Qt.MouseButton.LeftButton)
                assert spy.count()==1
                assert abs((ax.get_xlim()[1]-ax.get_xlim()[0])-(base[0][1]-base[0][0])/1.25)<1e-9
                app.processEvents()
                px,py=ax.transData.transform((sum(ax.get_xlim())/2,sum(ax.get_ylim())/2))
                d._al_presionar(SimpleNamespace(inaxes=ax,button=1,x=px,y=py))
                zoom=d._leer_limites()
                d._al_mover(SimpleNamespace(key=None,x=px+30,y=py))
                d._al_soltar(SimpleNamespace())
                assert d._leer_limites()!=zoom and not d._panorama_activo
                d.boton_restablecer.setFocus()
                QTest.keyClick(d.boton_restablecer,Qt.Key.Key_Space)
                assert d._leer_limites()==base
                assert (line.get_xydata()==before).all()
                d.boton_acercar.setEnabled(False)
                QTest.mouseClick(d.boton_acercar,Qt.MouseButton.LeftButton)
                assert d._leer_limites()==base
            finally:
                d.close()

def test_a_alternancia_con_movimiento():
    v=VentanaPrincipal()
    try:
        establecer_movimiento_reducido(False)
        settle(v)
        for _ in range(3):
            for collapsed in (True,False):
                v.navegacion.establecer_contraccion(collapsed)
                QTest.qWait(280)
                assert v.navegacion.width()==(60 if collapsed else 244)
        for collapsed in (True,False,True):
            v.navegacion.establecer_contraccion(collapsed)
            QTest.qWait(40)
        QTest.qWait(300)
        assert v.navegacion.width()==60
        for b in (v.boton_cargar,v.boton_abrir_sesion,v.boton_guardar_sesion):
            assert b.mapTo(v.navegacion,QPoint()).x()+b.width()<=60
    finally:
        establecer_movimiento_reducido(True)
        v.close()

if __name__=='__main__':
    if '--antes' in sys.argv:
        import types
        import app_icociv.interfaz.ventana_principal as ui
        import app_icociv.interfaz.tema.estilos as styles
        baseline=[]
        for name in ('componentes/navegacion','widgets/empalme_iccp_icociv','widgets/visor_grafica'):
            p=OUT/'respaldo_inicio'/('app_icociv__interfaz__'+name.replace('/','__')+'.py.bak')
            module=types.ModuleType('baseline_'+name.replace('/','_'))
            exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),module.__dict__)
            baseline.append(module)
        VisorGraficaDialog=baseline[2].VisorGraficaDialog
        with patch.object(ui,'NavegacionLateral',baseline[0].NavegacionLateral), patch.object(ui,'WidgetEmpalmeICCPICOCIV',baseline[1].WidgetEmpalmeICCPICOCIV), patch.object(styles,'RUTA_PLANTILLA',OUT/'respaldo_inicio/app_icociv__interfaz__tema__plantilla.qss.bak'):
            styles.limpiar_cache()
            registrar_geometria('ANTES')
    else:
        for name,fn in sorted(list(globals().items())):
            if name.startswith('test_') and callable(fn):
                try:
                    fn()
                except Exception:
                    import traceback
                    traceback.print_exc()
                    raise SystemExit(1)
                print('PASS '+name,flush=True)
        registrar_geometria('DESPUES')
