"""Estados y legibilidad de widgets reales; preferencias y datos sintéticos aislados."""
import os,sys,json,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/fase_3c_b'
RUNTIME=OUT/'temporal'
RUNTIME.mkdir(parents=True,exist_ok=True)
os.environ.update(QT_QPA_PLATFORM='offscreen',TEMP=str(RUNTIME),TMP=str(RUNTIME),MPLCONFIGDIR=str(RUNTIME/'matplotlib'))
tempfile.tempdir=str(RUNTIME)
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import QSettings,QPoint,Qt
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
for scope in (QSettings.Scope.UserScope,QSettings.Scope.SystemScope):
    QSettings.setPath(QSettings.Format.IniFormat,scope,str(RUNTIME/'settings'))
from PySide6.QtWidgets import QApplication,QScrollArea,QDoubleSpinBox,QLineEdit,QComboBox,QStyleOptionSpinBox,QStyle
from PySide6.QtTest import QTest,QSignalSpy
from matplotlib.figure import Figure
from tests.test_proyecciones_fase_3 import abrir,guardar,anexo_sintetico,esperar
from tests import test_numericos_icociv
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.interfaz.widgets.visor_grafica import VisorGraficaDialog
from app_icociv.interfaz.tema.colores import contraste
from app_icociv.interfaz.animaciones import establecer_movimiento_reducido
import app_icociv.interfaz.ventana_principal as ui
def reducir_movimiento():
    establecer_movimiento_reducido(True)
    return True
_preferencia_fixture=patch.object(ui,'aplicar_preferencia_sistema',reducir_movimiento)
_preferencia_fixture.start()
app=QApplication.instance()
SIZES=((1100,700),(1366,768),(1920,1080))

def settle(v):
    v.show();v.activateWindow();app.processEvents();QTest.qWait(30)

def shot(v,name):
    if hasattr(v,'notificaciones'):v.notificaciones.cerrar_todas()
    (OUT/'capturas').mkdir(exist_ok=True)
    assert v.grab().save(str(OUT/'capturas'/(name+'.png')))

def parameters(b):
    return {'valor':b.value(),'min':b.minimum(),'max':b.maximum(),'decimales':b.decimals(),
            'step':b.singleStep(),'locale':b.locale().name(),'group':b.isGroupSeparatorShown(),
            'botones':int(b.buttonSymbols().value),'texto':b.lineEdit().text()}

def pixels(b,parent):
    im=b.grab().toImage()
    border=im.pixelColor(im.width()//2,0).name()
    field=im.pixelColor(im.width()//2,4).name()
    pos=b.mapTo(parent,QPoint())
    outer=parent.grab().toImage()
    outside=outer.pixelColor(max(0,pos.x()-3),max(0,min(outer.height()-1,pos.y()+b.height()//2))).name()
    return {'borde':border,'campo':field,'exterior':outside,'ratio_campo':contraste(border,field),
            'ratio_exterior':contraste(border,outside),'alto':b.height(),'ancho':b.width()}

def capture_evidence(stage):
    rows=[];colors=[]
    for loaded in (False,True):
        v=VentanaPrincipal()
        w=v.widget_empalme
        v._cambiar_seccion(2)
        if loaded:
            source=RUNTIME/'anexo.xlsx'
            if not source.exists():anexo_sintetico(source)
            v._cargar_archivo(str(source))
            esperar(v,lambda:v.combo_grupo.count()==3 and v.combo_grupo.isEnabled())
            w.combo_grupo_icociv.setCurrentIndex(1)
        try:
            for theme in ('claro','oscuro'):
                v._aplicar_tema(theme,persistir=False)
                for size in SIZES:
                    v.resize(*size);settle(v)
                    scroll=w.findChild(QScrollArea)
                    scroll.verticalScrollBar().setValue(0)
                    app.processEvents()
                    rows.append({'tema':theme,'size':size,'datos':loaded,'scroll_horizontal':scroll.horizontalScrollBar().maximum(),
                        'viewport':scroll.viewport().width(),'contenido':scroll.widget().width(),
                        'minimo_contenido':scroll.widget().minimumSizeHint().width()})
                    shot(v,f'{stage}_{theme}_{size[0]}x{size[1]}_empalme_{loaded}')
                    if size==(1100,700):
                        scroll.ensureWidgetVisible(w.precio_base)
                        shot(v,f'{stage}_{theme}_numericos_{loaded}')
                for name,b in (('cantidad',w.cantidad),('P',w.precio_base),('A',w.anticipo),('contrato',w.contrato),('serie',w.combo_grupo_icociv),('objeto',w.objeto)):
                    v.resize(1100,700)
                    b.setEnabled(True)
                    scroll.ensureWidgetVisible(b)
                    for state in ('normal','hover','foco','disabled'):
                        b.setEnabled(state!='disabled')
                        v.navegacion.botones[0].setFocus()
                        QTest.mouseMove(v,QPoint(5,5))
                        if state=='foco':b.setFocus()
                        if state=='hover':QTest.mouseMove(b,QPoint(2,b.height()//2))
                        app.processEvents();QTest.qWait(20)
                        colors.append({'tema':theme,'datos':loaded,'widget':name,'estado':state,
                                       'foco_real':b.hasFocus(),'hover_real':b.underMouse(),'habilitado':b.isEnabled(),**pixels(b,w)})
                        if name=='cantidad':shot(v,f'{stage}_{theme}_{name}_{state}_{loaded}')
                    b.setEnabled(True)
        finally:v.close()
    (OUT/(stage+'_SCROLL.json')).write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (OUT/(stage+'_COLORES.json')).write_text(json.dumps(colors,indent=2),encoding='utf-8')

def capture_shared(stage):
    v=VentanaPrincipal();w=v.widget_proyecciones;rows=[]
    try:
        v._cambiar_seccion(1);v.resize(1100,700);settle(v)
        scroll=w.findChild(QScrollArea)
        for theme in ('claro','oscuro'):
            v._aplicar_tema(theme,persistir=False)
            for name,b in (('cantidad_ICOCIV',w.cantidad),('P_ICOCIV',w.precio_base),('A_ICOCIV',w.anticipo),('anio_ICOCIV',v.spin_anio),('horizonte_ICOCIV',v.spin_horizonte_personalizado)):
                scroll.ensureWidgetVisible(b);b.setEnabled(True)
                for state in ('normal','foco','disabled'):
                    v.navegacion.botones[0].setFocus();QTest.mouseMove(v,QPoint(5,5))
                    b.setEnabled(state!='disabled')
                    if state=='foco':b.setFocus()
                    app.processEvents()
                    rows.append({'tema':theme,'widget':name,'estado':state,'foco_real':b.hasFocus(),**pixels(b,w)})
                b.setEnabled(True)
            shot(v,f'{stage}_{theme}_controles_compartidos')
    finally:v.close()
    (OUT/(stage+'_COMPARTIDOS.json')).write_text(json.dumps(rows,indent=2),encoding='utf-8')

def graph_metrics(d):
    d.canvas.draw()
    renderer=d.canvas.get_renderer()
    labels=[x for x in d.eje.get_xticklabels() if x.get_visible() and x.get_text()]
    boxes=[x.get_window_extent(renderer) for x in labels]
    overlaps=[(labels[i].get_text(),labels[i+1].get_text()) for i in range(len(boxes)-1) if boxes[i].overlaps(boxes[i+1])]
    return {'etiquetas':[x.get_text() for x in labels],'solapamientos':overlaps,
            'cajas':[list(x.bounds) for x in boxes],'canvas':[d.canvas.width(),d.canvas.height()]}

def capture_graphs(stage):
    v=VentanaPrincipal()
    records=[]
    try:
        with patch.object(v.controlador,'ejecutar_analisis',side_effect=AssertionError('Recalcular al consultar')):
            abrir(v,ROOT/'docs/auditoria_better_ui_v11/temporal/sesion_auditoria.json')
            for index,horizon in ((0,1),(1,3)):
                ident=v.widget_proyecciones.historial[index]['id']
                v.selector_resultados_icociv.setCurrentIndex(v.selector_resultados_icociv.findData(ident))
                capture_result(v,horizon,stage,records)
        source=RUNTIME/'sesion_H24.json'
        if source.exists():
            abrir(v,source)
        else:
            xlsx=RUNTIME/'anexo_H24.xlsx';anexo_sintetico(xlsx)
            v._cargar_archivo(str(xlsx));esperar(v,lambda:v.combo_grupo.count()==3 and v.combo_grupo.isEnabled())
            v.combo_grupo.setCurrentIndex(1)
            v.combo_horizonte.setCurrentIndex(v.combo_horizonte.count()-1)
            v.spin_horizonte_personalizado.setValue(24)
            v.ejecutar_proyeccion()
            count=len(v.widget_proyecciones.historial)
            esperar(v,lambda:v.resultado_ui_actual['proyeccion']['horizonte_solicitado']==24)
            guardar(v,source)
        capture_result(v,24,stage,records)
    finally:v.close()
    (OUT/(stage+'_GRAFICAS.json')).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')

def capture_result(v,horizon,stage,records):
    for theme in ('claro','oscuro'):
        v._aplicar_tema(theme,persistir=False)
        v._cambiar_seccion(3);v.resize(1366,768);settle(v)
        shot(v,f'{stage}_{theme}_resultados_H{horizon}')
        (OUT/f'{stage}_{theme}_RESULTADOS_H{horizon}.txt').write_text(v.texto_resultados.toPlainText(),encoding='utf-8')
        for size in ((560,420),(900,640)):
            fig=Figure()
            dates=v._dibujar_grafica(fig,v.resultado_ui_actual['serie_df'],v.resultado_ui_actual['proyeccion'])
            d=VisorGraficaDialog(v,fig,'Gráfica',v.styleSheet())
            d.resize(*size);settle(d)
            rec={'tema':theme,'H':horizon,'size':size,'fechas':dates,
                 'curvas':[x.get_xydata().tolist() for x in d.eje.lines],
                 'intervalos':[p.vertices.tolist() for c in d.eje.collections for p in c.get_paths()],
                 'limites':d._leer_limites(),**graph_metrics(d)}
            records.append(rec)
            shot(d,f'{stage}_{theme}_{size[0]}x{size[1]}_grafica_H{horizon}')
            d.close()

def baseline_module(name):
    import types
    p=OUT/'respaldo_inicio'/(name.replace('/','__')+'.bak')
    module=types.ModuleType('baseline_'+p.stem.replace('.','_'))
    exec(compile(p.read_text(encoding='utf-8-sig'),str(p),'exec'),module.__dict__)
    return module

def test_a_numericos_empalme_conservan_valores_edicion_y_flechas():
    from app_icociv.interfaz.widgets.empalme_iccp_icociv import WidgetEmpalmeICCPICOCIV
    from app_icociv.interfaz.tema import hoja_estilos
    from PySide6.QtGui import QImageReader
    spec=(ROOT/'packaging/SAVIP.spec').read_text(encoding='utf-8')
    for filename in ('spin_arriba.svg','spin_abajo.svg'):
        assert not QImageReader(str(ROOT/'app_icociv/interfaz/recursos'/filename)).read().isNull()
        assert filename in spec
    old=baseline_module('app_icociv/interfaz/widgets/empalme_iccp_icociv.py').WidgetEmpalmeICCPICOCIV()
    new=WidgetEmpalmeICCPICOCIV()
    try:
        for theme in ('claro','oscuro'):
            new.setStyleSheet(hoja_estilos(theme));new.resize(850,700);settle(new)
            for name,value in (('cantidad',1234.5678),('precio_base',1234567890.12),('anticipo',12345.67),('p0',9876543.21),('ix',1234.5678),('q',9876.5432)):
                a,b=getattr(old,name),getattr(new,name)
                a.setValue(value);b.setValue(value)
                # 4A cambia editor/locale/formato; el contrato numérico de 3C-B sigue vigente.
                assert all(parameters(a)[key]==parameters(b)[key]
                           for key in ('valor','min','max','decimales','step','group','botones'))
                if name in ('p0','ix','q'):new.chk_acero.setChecked(True)
                new.findChild(QScrollArea).ensureWidgetVisible(b)
                app.processEvents()
                assert b.height()>=38
                assert b.lineEdit().fontMetrics().horizontalAdvance(b.lineEdit().text())<=b.lineEdit().contentsRect().width()
                option=QStyleOptionSpinBox();b.initStyleOption(option)
                edit=b.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,QStyle.SubControl.SC_SpinBoxEditField,b)
                up=b.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,QStyle.SubControl.SC_SpinBoxUp,b)
                assert not edit.intersects(up)
                before=b.value();spy=QSignalSpy(b.valueChanged)
                QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=up.center())
                assert b.value()==before+b.singleStep() and spy.count()==1
                b.setValue(value)
                b.setFocus();b.lineEdit().setCursorPosition(len(b.lineEdit().text()));app.processEvents()
                assert b.lineEdit().cursorPosition()==len(b.lineEdit().text())
                b.setEnabled(False);QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=up.center())
                assert b.value()==value
                b.setEnabled(True)
    finally:old.close();new.close()

def test_b_contraste_efectivo_estados_y_paleta_documental():
    rows=json.loads((OUT/'DESPUES_COLORES.json').read_text())
    rows+=json.loads((OUT/'DESPUES_COMPARTIDOS.json').read_text())
    for r in rows:
        if r['estado']!='disabled':
            assert r['ratio_campo']>=3 and r['ratio_exterior']>=3,r
    from app_icociv.reportes.modelo import PALETA
    from app_icociv.interfaz.tema.colores import CLARO,OSCURO
    old=baseline_module('app_icociv/interfaz/tema/colores.py')
    for key,value in PALETA.items():
        assert value in old.CLARO.values(),(key,value)
    # Fase 4F (renovación visual autorizada): la paleta de interfaz ya no está congelada en
    # 3C-B. Se conserva el contrato documental (PALETA de informes idéntica, arriba) y que
    # ningún token previo desaparezca; la única clave nueva es 'seleccion_inactiva'.
    for theme,new,previous in (('claro',CLARO,old.CLARO),('oscuro',OSCURO,old.OSCURO)):
        assert set(new)-set(previous)=={'seleccion_inactiva'} and not set(previous)-set(new)

def test_c_scroll_empalme_tab_senales_y_datos():
    v=VentanaPrincipal();w=v.widget_empalme
    try:
        for loaded in (False,True):
            if loaded:
                v._cargar_archivo(str(RUNTIME/'anexo.xlsx'))
                esperar(v,lambda:v.combo_grupo.isEnabled() and v.combo_grupo.count()==3)
                w.combo_grupo_icociv.setCurrentIndex(1)
                for b in (w.combo_nivel2,w.combo_nivel3,w.combo_nivel4,w.combo_nivel5,w.combo_nivel6):
                    if b.isEnabled() and b.count()>1:b.setCurrentIndex(1)
            for theme in ('claro','oscuro'):
                v._aplicar_tema(theme,persistir=False)
                for size in SIZES:
                    v.resize(*size);v._cambiar_seccion(2);settle(v)
                    scroll=w.findChild(QScrollArea)
                    assert scroll.horizontalScrollBar().maximum()==0
                    for b in (w.contrato,w.responsable,w.cantidad,w.precio_base,w.anticipo,w.boton_calcular,w.boton_exportar):
                        scroll.ensureWidgetVisible(b);app.processEvents()
                        p=b.mapTo(scroll.viewport(),QPoint())
                        assert p.x()>=0 and p.x()+b.width()<=scroll.viewport().width()
                    scroll.ensureWidgetVisible(w.cantidad)
                    w.cantidad.setFocus();QTest.keyClick(w.cantidad,Qt.Key.Key_Tab)
                    assert w.modalidad_importe.hasFocus()  # 4E incorpora este control entre Cantidad y P.
                    QTest.keyClick(w.modalidad_importe,Qt.Key.Key_Tab)
                    assert w.precio_base.hasFocus()
                    QTest.keyClick(w.precio_base,Qt.Key.Key_Tab)
                    assert w.anticipo.hasFocus()
                    spin=w.fecha_inicial_mes
                    buttons=spin.parentWidget().findChildren(__import__('PySide6.QtWidgets',fromlist=['QPushButton']).QPushButton,'boton_incremento')
                    assert all(b.width()==40 for b in buttons)
    finally:v.close()

def test_d_texto_resultados_separado_sin_alterar_contenido():
    import re
    for theme in ('claro','oscuro'):
        for horizon in (1,3,24):
            a=(OUT/f'ANTES_{theme}_RESULTADOS_H{horizon}.txt').read_text(encoding='utf-8')
            b=(OUT/f'DESPUES_{theme}_RESULTADOS_H{horizon}.txt').read_text(encoding='utf-8')
            assert re.sub(r'\s','',a)==re.sub(r'\s','',b)
            assert 'técnica Nivel de confianza:' in b and 'técnicaNivel' not in b

def test_e_fechas_sin_superposicion_datos_y_zoom_pan_reset():
    from app_icociv.interfaz.widgets.visor_grafica import configurar_ejes_dinamicos
    from app_icociv.interfaz.tema import hoja_estilos
    from types import SimpleNamespace
    before=json.loads((OUT/'ANTES_GRAFICAS.json').read_text())
    after=json.loads((OUT/'DESPUES_GRAFICAS.json').read_text())
    for a,b in zip(before,after):
        assert a['fechas']==b['fechas'] and a['curvas']==b['curvas'] and a['limites']==b['limites']
        assert a['intervalos']==b['intervalos']
        assert not b['solapamientos']
        assert all(x>=0 and y>=0 and x+w<=b['canvas'][0] and y+h<=b['canvas'][1] for x,y,w,h in b['cajas'])
    for n in (36,120):
        for horizon in (1,3,24):
            for width,height in ((560,420),(900,640)):
                fig=Figure();ax=fig.add_subplot()
                x=list(range(n+horizon));y=[100+i*.1 for i in x]
                dates=[f'{2020+i//12:04d}-{i%12+1:02d}' for i in x]
                ax.plot(x,y);configurar_ejes_dinamicos(ax,dates)
                d=VisorGraficaDialog(None,fig,'Fechas',hoja_estilos('claro'));d.resize(width,height);settle(d)
                original=ax.lines[0].get_xydata().copy();base=d._leer_limites()
                try:
                    for _ in range(6):
                        assert not graph_metrics(d)['solapamientos']
                        QTest.mouseClick(d.boton_acercar,Qt.MouseButton.LeftButton)
                    d.canvas.draw()
                    px,py=ax.transData.transform((sum(ax.get_xlim())/2,sum(ax.get_ylim())/2))
                    d._al_presionar(SimpleNamespace(inaxes=ax,button=1,x=px,y=py))
                    d._al_mover(SimpleNamespace(key=None,x=px+25,y=py))
                    d._al_soltar(SimpleNamespace())
                    assert not graph_metrics(d)['solapamientos']
                    QTest.mouseClick(d.boton_restablecer,Qt.MouseButton.LeftButton)
                    assert d._leer_limites()==base and (ax.lines[0].get_xydata()==original).all()
                    assert not graph_metrics(d)['solapamientos']
                finally:d.close()

if __name__=='__main__':
    try:
        if '--capturar' in sys.argv:
            stage=sys.argv[-1]
            capture_evidence(stage)
            capture_shared(stage)
            capture_graphs(stage)
        else:
            for name,fn in sorted(list(globals().items())):
                if name.startswith('test_') and callable(fn):fn();print('PASS '+name,flush=True)
    except Exception:
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
