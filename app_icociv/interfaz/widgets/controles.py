"""Controles Qt compartidos que evitan cambios accidentales con la rueda del mouse."""

from __future__ import annotations

import re
from PySide6.QtCore import QEvent, Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QValidator
from PySide6.QtWidgets import QApplication, QComboBox, QDoubleSpinBox, QSpinBox, QStyle, QStyleOptionSpinBox


class ComboBoxSinRueda(QComboBox):
    """QComboBox que evita cambios accidentales de selección con la rueda del mouse."""

    def wheelEvent(self, event) -> None:  # noqa: N802 - firma Qt
        event.ignore()


def confirmar_ingreso_presupuestal(parent, selector, cantidad):
    """Declara la entrada antes de crear registros, sin reentradas del botón."""
    from PySide6.QtWidgets import QMessageBox
    from app_icociv.utilidades.importes_presupuestales import cantidad_presupuestal_valida, PREGUNTA_INGRESO
    if getattr(parent,'_confirmando_ingreso',False):return False
    parent._confirmando_ingreso=True
    habilitado=parent.boton_calcular.isEnabled();parent.boton_calcular.setEnabled(False)
    try:
        if not cantidad_presupuestal_valida(cantidad):
            QMessageBox.warning(parent,'Cantidad presupuestal','Ingrese una Cantidad numérica, finita y mayor que cero para obtener los cuatro importes antes de guardar.')
            parent.cantidad.setFocus();return False
        if selector.currentData() in ('unitario','total'):return True
        dialogo=QMessageBox(parent);dialogo.setWindowTitle('Interpretación de la entrada')
        dialogo.setIcon(QMessageBox.Question);dialogo.setText(PREGUNTA_INGRESO)
        dialogo.setInformativeText('Elija para calcular y guardar las cuatro cifras, o cancele sin crear un registro. P y A conservarán los importes digitados.')
        unitario=dialogo.addButton('Unitario',QMessageBox.AcceptRole)
        total=dialogo.addButton('Total',QMessageBox.AcceptRole)
        cancelar=dialogo.addButton('Cancelar',QMessageBox.RejectRole);dialogo.setDefaultButton(cancelar)
        dialogo.exec();elegido=dialogo.clickedButton()
        if elegido not in (unitario,total):return False
        selector.setCurrentIndex(selector.findData('unitario' if elegido is unitario else 'total'))
        return True
    finally:
        parent._confirmando_ingreso=False;parent.boton_calcular.setEnabled(habilitado)


class SpinSinRueda(QDoubleSpinBox):
    """Evita cambios accidentales en campos numéricos con la rueda."""

    def wheelEvent(self, event) -> None:  # noqa: N802 - firma Qt
        event.ignore()


class SpinEnteroSinRueda(QSpinBox):
    """Evita cambios accidentales en campos enteros con la rueda."""

    def wheelEvent(self, event) -> None:  # noqa: N802 - firma Qt
        event.ignore()


class SpinHorizonte(SpinEnteroSinRueda):
    """Detecta intentos de superar el máximo sin ampliar el rango efectivo."""
    maximo_intentado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._valor_antes_edicion = self.value()
        self._aviso_pendiente = False
        self.lineEdit().installEventFilter(self)

    def validate(self, texto, posicion):
        resultado = super().validate(texto, posicion)
        # El menú Pegar llega directamente al validador nativo, sin KeyPress.
        if resultado[0] == QValidator.Invalid and re.fullmatch(r'\+?\d+', texto.strip()) and int(texto.strip()) > self.maximum() and not getattr(self, '_aviso_pendiente', False):
            self._valor_antes_edicion = self.value()
            self._aviso_pendiente = True
            def avisar():
                self._aviso_pendiente = False
                self._rechazar()
            QTimer.singleShot(0, avisar)
        return resultado

    def _rechazar(self):
        self.setValue(self._valor_antes_edicion)
        self.lineEdit().setText(self.textFromValue(self.value()))
        self.maximo_intentado.emit()

    def eventFilter(self, obj, event):
        if obj is self.lineEdit():
            if event.type() == QEvent.FocusIn:
                self._valor_antes_edicion = self.value()
            elif event.type() == QEvent.KeyPress:
                if event.key() == Qt.Key_Up and self.value() == self.maximum():
                    self.maximo_intentado.emit()
                    return True
                editor = self.lineEdit()
                texto = QApplication.clipboard().text().strip() if event.matches(QKeySequence.Paste) else event.text()
                if texto and (event.matches(QKeySequence.Paste) or not event.modifiers() & (Qt.ControlModifier | Qt.AltModifier)):
                    if editor.hasSelectedText():
                        self._valor_antes_edicion = self.value()
                    start = editor.selectionStart() if editor.hasSelectedText() else editor.cursorPosition()
                    fin = start + len(editor.selectedText())
                    candidato = editor.text()[:start] + texto + editor.text()[fin:]
                    if re.fullmatch(r'\+?\d+', candidato.strip()) and int(candidato.strip()) > self.maximum():
                        self._rechazar()
                        return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        arriba = self.style().subControlRect(QStyle.CC_SpinBox, option, QStyle.SC_SpinBoxUp, self)
        if self.isEnabled() and event.button() == Qt.LeftButton and self.value() == self.maximum() and arriba.contains(event.position().toPoint()):
            self.maximo_intentado.emit()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up and self.value() == self.maximum():
            self.maximo_intentado.emit()
            event.accept()
            return
        super().keyPressEvent(event)
