"""Edición localizada exclusiva de Cantidad, P y A; el valor sigue siendo float Qt."""

from decimal import Decimal, InvalidOperation
import re

from PySide6.QtCore import QLocale, Qt, Signal
from PySide6.QtGui import QKeySequence, QValidator
from PySide6.QtWidgets import QApplication, QLineEdit, QMenu, QToolTip

from app_icociv.interfaz.widgets.controles import SpinSinRueda


def _agrupar(texto: str) -> str:
    entero, punto, fraccion = texto.replace(",", "").partition(".")
    signo = entero[:1] if entero.startswith(("-", "+")) else ""
    digitos = entero[len(signo):]
    grupos = [digitos[max(0, i - 3):i] for i in range(len(digitos), 0, -3)]
    return signo + ",".join(reversed(grupos)) + punto + fraccion


def normalizar_numero(texto: str) -> str:
    """Función común (Fase 4I-A V4) de calculadora y celdas: devuelve el número canónico «1234.5».

    Convenio del producto para un único separador seguido de tres cifras: la COMA agrupa miles
    («1,250» → 1250; «4,559» → 4559) y el PUNTO es decimal («1.250» → 1.25). Con varios
    separadores el formato es inequívoco («1.250.000,50», «$ 6,561,232.00»). «0,250» y «12,5»
    son decimales porque no pueden ser grupos de miles.
    """
    if "\t" in texto.strip("\r\n") or "\n" in texto.strip("\r\n"):
        raise ValueError("Se recibió un rango de varias celdas; pegue un solo valor.")
    return _pegado(texto)


def _pegado(texto: str) -> str:
    # Fase 4I: admite «$», «COP» y espacios (incluido el no separable) como separadores de miles.
    texto = re.sub(r"(?i)\bCOP\b|\$", "", texto).replace("\u00a0", " ").strip()
    if re.fullmatch(r"[+-]?\d{1,3}( \d{3})+([.,]\d+)?", texto):
        texto = texto.replace(" ", "")
    texto = texto.strip()
    if not re.fullmatch(r"[+-]?\d[\d.,]*", texto):
        raise ValueError("Pegue solamente un número; formato principal: 1,234.56.")
    cuerpo = texto.lstrip("+-")
    if "." in cuerpo and "," in cuerpo:
        decimal = "," if cuerpo.rfind(",") > cuerpo.rfind(".") else "."
        miles = "." if decimal == "," else ","
        entero, fraccion = cuerpo.rsplit(decimal, 1)
        if not re.fullmatch(r"\d{1,3}(" + re.escape(miles) + r"\d{3})+", entero) or not fraccion.isdigit():
            raise ValueError("Los separadores del número pegado no son consistentes.")
        cuerpo = entero.replace(miles, "") + "." + fraccion
    elif "." in cuerpo or "," in cuerpo:
        separador = "." if "." in cuerpo else ","
        partes = cuerpo.split(separador)
        if len(partes) == 2:
            if not partes[0].isdigit() or (partes[1] and not partes[1].isdigit()):
                raise ValueError("Número pegado no válido.")
            # V4: «1,250» (coma + tres cifras, parte entera 1-999) agrupa miles; «1.250» es decimal.
            miles = separador == "," and 1 <= len(partes[0]) <= 3 and len(partes[1]) == 3 and int(partes[0]) > 0
            cuerpo = partes[0] + ("" if miles else ".") + partes[1]
        else:
            if not re.fullmatch(r"\d{1,3}(" + re.escape(separador) + r"\d{3})+", cuerpo):
                raise ValueError("La agrupación de miles del número pegado no es válida.")
            cuerpo = cuerpo.replace(separador, "")
    return (texto[0] if texto.startswith(("-", "+")) else "") + cuerpo


class _EditorNumero(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self._anteriores = []
        self._siguientes = []

    def _estado(self):
        return self.text(), self.cursorPosition(), self.selectionStart(), len(self.selectedText()), self.parentWidget().value()

    def _registrar(self, antes):
        if self.text() != antes[0]:
            if not self._anteriores or self._anteriores[-1] != antes:
                self._anteriores.append(antes)
            self._siguientes.clear()

    def paste(self) -> None:
        if self.isReadOnly():
            return
        control = self.parentWidget()
        inicio = self.selectionStart() if self.hasSelectedText() else self.cursorPosition()
        rango = (self.text(), inicio, inicio + len(self.selectedText()))
        try:
            self._insertar(control.normalizar_pegado(QApplication.clipboard().text()), rango)
        except ValueError as error:
            control._avisar(str(error))

    def _insertar(self, texto, rango) -> None:
        """Sustituye la selección guardada por ``texto`` (ya normalizado) si el validador lo admite."""
        control = self.parentWidget()
        base, inicio, fin = rango
        candidato = base[:inicio] + texto + base[fin:]
        if control.validate(candidato, inicio + len(texto))[0] == QValidator.State.Invalid:
            raise ValueError(f"Número fuera del rango permitido, con más de {control.decimals()} decimales o no representable a esa magnitud por el float original. Corrija la entrada; no se redondeará al pegar.")
        antes = self._estado()
        if self.text() != base:
            self.setText(base)
        self.setSelection(inicio, fin - inicio) if fin > inicio else self.setCursorPosition(inicio)
        self.insert(texto)
        self._registrar(antes)

    def keyPressEvent(self, event) -> None:
        if event.matches(QKeySequence.StandardKey.Undo) or event.matches(QKeySequence.StandardKey.Redo):
            origen, destino = (self._anteriores, self._siguientes) if event.matches(QKeySequence.StandardKey.Undo) else (self._siguientes, self._anteriores)
            if origen:
                destino.append(self._estado())
                texto, cursor, inicio, longitud, valor = origen.pop()
                # Restaurar el estado de edición sin volver a redondear ni borrar la pila de edición.
                SpinSinRueda.setValue(self.parentWidget(), valor)
                self.setText(texto)
                self.setSelection(inicio, longitud) if inicio >= 0 else self.setCursorPosition(cursor)
            return
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste()
            return
        antes = self._estado()
        # Borrar un separador automático debe borrar el dígito adyacente, no restaurar el mismo texto.
        if not self.hasSelectedText() and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            pos = self.cursorPosition()
            if event.key() == Qt.Key.Key_Backspace and pos > 0 and self.text()[pos - 1] == ",":
                self.setCursorPosition(pos - 1)
            elif event.key() == Qt.Key.Key_Delete and pos < len(self.text()) and self.text()[pos] == ",":
                self.setCursorPosition(pos + 1)
        super().keyPressEvent(event)
        self._registrar(antes)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        for titulo, funcion, habilitada in (
            ("Deshacer", lambda: self._atajo(Qt.Key.Key_Z), bool(self._anteriores)),
            ("Rehacer", lambda: self._atajo(Qt.Key.Key_Y), bool(self._siguientes)),
            ("Cortar", lambda: self._atajo(Qt.Key.Key_X), self.hasSelectedText() and not self.isReadOnly()),
            ("Copiar", self.copy, self.hasSelectedText()),
            ("Pegar", self.paste, not self.isReadOnly()),
            ("Seleccionar todo", self.selectAll, bool(self.text())),
        ):
            accion = menu.addAction(titulo)
            accion.setEnabled(habilitada)
            accion.triggered.connect(funcion)
        menu.exec(event.globalPos())

    def _atajo(self, tecla):
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        self.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, tecla, Qt.KeyboardModifier.ControlModifier))


class NumeroICOCIV(SpinSinRueda):
    entradaRechazada = Signal(str)

    def normalizar_pegado(self, texto: str) -> str:
        return normalizar_numero(texto)

    def __init__(self, minimo: float, maximo: float, decimales: int) -> None:
        super().__init__()
        self.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.setRange(minimo, maximo)
        self.setDecimals(decimales)
        self.setSingleStep(1)
        self.setGroupSeparatorShown(True)
        self.setButtonSymbols(self.ButtonSymbols.NoButtons)
        self.setLineEdit(_EditorNumero(self))
        self.lineEdit().setAcceptDrops(False)
        self.lineEdit().textEdited.connect(self._formatear_edicion)
        self.lineEdit().inputRejected.connect(self._explicar_rechazo)

    def setValue(self, valor: float) -> None:
        super().setValue(valor)
        editor = self.lineEdit()
        if isinstance(editor, _EditorNumero):
            editor._anteriores.clear()
            editor._siguientes.clear()

    def _avisar(self, mensaje: str) -> None:
        self.entradaRechazada.emit(mensaje)
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), mensaje, self)

    def _explicar_rechazo(self) -> None:
        self._avisar(f"Use punto decimal, un valor entre {self.textFromValue(self.minimum())} y {self.textFromValue(self.maximum())} y hasta {self.decimals()} decimales. A magnitudes elevadas el float original puede no representar todos los decimales; reduzca la magnitud o la precisión de la entrada.")

    def textFromValue(self, valor: float) -> str:
        texto = f"{valor:.{self.decimals()}f}"
        if "." in texto:
            texto = texto.rstrip("0").rstrip(".")
        return _agrupar(texto)

    def valueFromText(self, texto: str) -> float:
        try:
            return float(Decimal(texto.replace(",", "")))
        except InvalidOperation:
            return self.value()

    def validate(self, texto: str, pos: int):
        plano = texto.replace(",", "")
        estado = QValidator.State.Invalid
        if plano in ("", "+") or (plano == "-" and self.minimum() < 0):
            estado = QValidator.State.Intermediate
        elif re.fullmatch(r"[+-]?\d+(\.\d*)?", plano):
            fraccion = plano.partition(".")[2]
            valor = Decimal(plano)
            # Representabilidad a la precisión escrita (no a la máxima), para no volver más estricto
            # el campo al ampliar sus decimales (P y A admiten 4 desde la Fase 4I-A).
            if (len(fraccion) <= self.decimals()
                    and Decimal(str(self.minimum())) <= valor <= Decimal(str(self.maximum()))
                    and Decimal(f"{float(valor):.{len(fraccion)}f}") == valor):
                estado = QValidator.State.Acceptable
        return estado, texto, pos

    def _formatear_edicion(self, texto: str) -> None:
        editor = self.lineEdit()
        pos = editor.cursorPosition()
        logica = len(texto[:pos].replace(",", ""))
        formateado = _agrupar(texto)
        if formateado == texto:
            return
        editor.setText(formateado)
        contador = 0
        destino = 0
        while destino < len(formateado) and contador < logica:
            contador += formateado[destino] != ","
            destino += 1
        editor.setCursorPosition(destino)
