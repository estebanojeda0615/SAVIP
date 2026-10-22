"""Edición Qt de los seis campos y conservación del contrato numérico original."""
import os, sys, types
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionSpinBox, QScrollArea
from app_icociv.interfaz.tema import hoja_estilos
from app_icociv.interfaz.widgets.empalme_iccp_icociv import WidgetEmpalmeICCPICOCIV, NumeroEmpalme, _tooltip
app=QApplication.instance() or QApplication([])
for filename in ('segoeui.ttf','segoeuib.ttf','seguisb.ttf'):
    QFontDatabase.addApplicationFont(str(Path('C:/Windows/Fonts')/filename))
app.setFont(QFont('Segoe UI',10))
NAMES=('cantidad','precio_base','anticipo','p0','ix','q')

def baseline_module():
    module=types.ModuleType('app_icociv.interfaz.widgets.empalme_baseline_4a')
    path=ROOT/'docs/fase_4a/respaldo_inicio/app_icociv__interfaz__widgets__empalme_iccp_icociv.py.bak'
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module

def test_formato_edicion_copiar_pegar_deshacer_y_limites():
    for theme in ('claro','oscuro'):
        w=WidgetEmpalmeICCPICOCIV();w.setStyleSheet(hoja_estilos(theme));w.resize(900,700)
        w.chk_acero.setChecked(True);w.show();app.processEvents()
        try:
            for name in NAMES:
                b=getattr(w,name);w.findChild(QScrollArea).ensureWidgetVisible(b)
                b.setFocus();app.processEvents();e=b.lineEdit()
                for raw,text in (('1000','1,000'),('1000000','1,000,000'),('1.00','1'),('0.00','0'),('999999.50','999,999.5')):
                    b.selectAll();QTest.keyClicks(e,raw)
                    assert b.value()==float(raw),(name,raw,b.value())
                    QTest.keyClick(e,Qt.Key.Key_Return)
                    assert b.text()==text,(name,raw,b.text())
                    b.clearFocus();app.processEvents()
                    assert b.text()==text,(name,raw,b.text())
                    b.setFocus()
                b.setValue(1234567);e.setCursorPosition(3);QTest.keyClicks(e,'9')
                assert b.text()=='12,934,567' and e.cursorPosition()==4
                QTest.keyClick(e,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
                assert b.value()==1234567
                QTest.keyClick(e,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier)
                assert b.value()==12934567
                b.setValue(1234567);e.setSelection(2,3);QTest.keyClicks(e,'9')
                assert b.text()=='19,567' and b.value()==19567
                QTest.keyClick(e,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
                assert b.value()==1234567 and e.selectionStart()==2 and len(e.selectedText())==3
                b.selectAll();QTest.keyClick(e,Qt.Key.Key_Backspace);QTest.keyClicks(e,'1250.5')
                assert b.text()=='1,250.5' and b.value()==1250.5
                b.selectAll();QTest.keyClick(e,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier)
                assert app.clipboard().text()=='1,250.5'
                for raw,expected in (('1,000',1000),('1,250.5',1250.5),('999999.50',999999.5)):
                    b.selectAll();app.clipboard().setText(raw)
                    QTest.keyClick(e,Qt.Key.Key_V,Qt.KeyboardModifier.ControlModifier)
                    assert b.value()==expected,(name,raw,b.text(),b.value())
                if b.decimals()==4:
                    b.selectAll();QTest.keyClicks(e,'152.094');assert b.value()==152.094
                    b.selectAll();e.copy();e.paste();assert b.value()==152.094
                b.setValue(b.maximum());b.stepUp();assert b.value()==b.maximum()
                b.setValue(b.minimum());b.stepDown();assert b.value()==b.minimum()
                b.setValue(42);b.selectAll();app.clipboard().setText(str(int(b.maximum())+1))
                e.paste();assert b.value()==42
                b.selectAll();app.clipboard().setText('12,34.56');e.paste();assert b.value()==42
                b.selectAll();app.clipboard().setText('1.'+'1'*(b.decimals()+1));e.paste();assert b.value()==42
        finally:w.close()

def test_contrato_original_flechas_geometria_y_float():
    old=baseline_module().WidgetEmpalmeICCPICOCIV();new=WidgetEmpalmeICCPICOCIV()
    try:
        old.chk_acero.setChecked(True);new.chk_acero.setChecked(True)
        for theme in ('claro','oscuro'):
            for widget in (old,new):widget.setStyleSheet(hoja_estilos(theme));widget.resize(900,700);widget.show()
            app.processEvents()
            for name in NAMES:
                a,b=getattr(old,name),getattr(new,name)
                assert isinstance(b,NumeroEmpalme)
                for key in ('minimum','maximum','decimals','singleStep','buttonSymbols','isGroupSeparatorShown'):
                    assert getattr(a,key)()==getattr(b,key)(),(name,key)
                for value in (0,1,1234.5678,999999.5,b.maximum()-1,b.maximum(),1e14+.12):
                    a.setValue(value);b.setValue(value);assert a.value()==b.value(),(name,value)
                for raw in ('1234.56',f'{b.maximum()-1:.{b.decimals()}f}'):
                    for spin in (a,b):
                        spin.selectAll();QTest.keyClicks(spin.lineEdit(),raw);spin.interpretText()
                    assert a.value()==b.value(),(name,raw,a.value(),b.value())
                for widget in (old,new):widget.findChild(QScrollArea).ensureWidgetVisible(getattr(widget,name))
                app.processEvents()
                rects=[]
                for spin in (a,b):
                    option=QStyleOptionSpinBox();spin.initStyleOption(option)
                    rects.append(spin.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,QStyle.SubControl.SC_SpinBoxUp,spin))
                assert rects[1].width()>=rects[0].width() and rects[1].height()>=rects[0].height()
                b.setValue(1000)
                QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=rects[1].center());assert b.value()==1001
                b.setEnabled(False);QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=rects[1].center());assert b.value()==1001
                b.setEnabled(True)
                QTest.keyClick(b,Qt.Key.Key_Down);assert b.value()==1000
                option=QStyleOptionSpinBox();b.initStyleOption(option)
                down=b.style().subControlRect(QStyle.ComplexControl.CC_SpinBox,option,QStyle.SubControl.SC_SpinBoxDown,b)
                QTest.mouseClick(b,Qt.MouseButton.LeftButton,pos=down.center());assert b.value()==999
    finally:old.close();new.close()

def test_tooltips_completos_escapados_y_recursos_empaquetados():
    from app_icociv.interfaz.widgets.empalme_iccp_icociv import AYUDAS
    from PySide6.QtGui import QTextDocument, QImageReader
    for text in (*AYUDAS.values(),'Aviso <dato> & rango\nsegunda línea'):
        doc=QTextDocument();doc.setHtml(_tooltip(text))
        assert doc.toPlainText().strip()==text
        assert 'width="360"' in _tooltip(text)
    spec=(ROOT/'packaging/SAVIP.spec').read_text(encoding='utf-8')
    for filename in ('spin_arriba_oscuro.svg','spin_abajo_oscuro.svg'):
        assert filename in spec
        assert not QImageReader(str(ROOT/'app_icociv/interfaz/recursos'/filename)).read().isNull()

if __name__=='__main__':
    for name,fn in sorted(list(globals().items())):
        if name.startswith('test_') and callable(fn):fn();print('PASS '+name,flush=True)
