"""Módulo ICOCIV: tabla acumulativa de proyecciones y calculadora de actualización.

Reutiliza el estilo, formato y exportación del módulo de empalme, pero trabaja
únicamente con índices ICOCIV (sin ICCP).
"""

from __future__ import annotations

from datetime import datetime
from copy import deepcopy
from html import escape
import json
import math
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from PySide6.QtCore import QEvent, Qt, QTimer, Signal, QSignalBlocker
from app_icociv.servicios import fecha_objetivo as fo
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QKeySequence, QPalette, QPen, QShortcut, QUndoCommand, QUndoStack
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QInputDialog,
    QMenu,
    QBoxLayout,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QStyle,
    QStylePainter,
    QStyleOptionComboBox,
    QComboBox,
    QRadioButton,
    QStyledItemDelegate,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QToolTip,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app_icociv.utilidades.importes_presupuestales import MODALIDADES, OPCIONES_INGRESO, PREGUNTA_INGRESO, AVISO_INTERPRETACION, validar_modalidad, desglose_importe, desglose_presupuestal, texto_desglose
from app_icociv.interfaz.tema import tokens
from app_icociv.interfaz.formato_numerico import numero_ui, detalle_ui, formula_ui, numero_tecnico_ui, pesos_ui, porcentaje_ui
from app_icociv.interfaz.widgets.modelo_tabla import ModeloTablaPandas
from app_icociv.interfaz.widgets.tabla_numerica import ModeloTablaNumerica,TablaCopiable,numero_original
from app_icociv.interfaz.widgets.acciones_tablas import BarraAccionesTablas
from app_icociv.interfaz.widgets.controles import ComboBoxSinRueda
from app_icociv.interfaz.widgets.numerico_icociv import NumeroICOCIV, normalizar_numero
from app_icociv.config.rutas import ruta_recurso
from app_icociv.interfaz.tema.colores import paleta
from app_icociv.interfaz.widgets.empalme_iccp_icociv import (
    FORMATO_INDICE_EXCEL,
    FORMATO_MONEDA_EXCEL,
    UNIDADES_INGENIERIA,
    _activar_recalculo_excel,
    _ajustar_hoja_excel,
    _ayuda,
    _escribir_pares_excel,
    _escribir_tabla_excel,
    _etiqueta_ayuda,
    _fmt_factor,
    _fmt_indice,
    _fmt_moneda,
    _fmt_porcentaje,
    _numero_excel,
    _periodo_visible,
)
from app_icociv.servicios.actualizacion_icociv import (calcular_actualizacion_icociv, es_factor_legado, CRITERIO_FACTOR,
                                                        TEXTO_CRITERIO_FACTOR, TEXTO_FACTOR_LEGADO)
from app_icociv.persistencia.historial_icociv import serializar_resultado, recuperar_resultado
from app_icociv.exportables.archivo_atomico import guardar_atomico
from app_icociv.interfaz.widgets.comparacion_historica import historico_observado, comparar_registro, validar_comparacion, escenario_registro, periodo_mensual, historico_efectivo
from app_icociv.interfaz.widgets.historial_series import (agrupar_historial, localizar_en_fuente, fichas_historial,
    ambitos_disponibles, analisis_en_ambito, resolver_alcance, etiqueta_proyeccion)
from contextlib import contextmanager


HOJA_RESUMEN = "Resumen"
HOJA_PROYECCIONES = "Proyecciones ICOCIV"
HOJA_VALORES = "Valores proyectados"
HOJA_DETALLE_VALORES = "Detalle valores V1.0"
HOJA_TRAZABILIDAD = "Trazabilidad"
HOJA_METODOLOGIA = "Metodología y fórmulas"

# Columnas visibles de la tabla acumulativa de proyecciones.
# Se prioriza la ventana de proyección (periodo proyectado), no solo el horizonte.
COLUMNAS_PROYECCIONES = [
    ("numero", "N°"),
    ("item", "Ítem / insumo"),
    ("item_ruta", "Ruta ICOCIV resumida"),
    ("tabla_icociv", "Tabla ICOCIV"),
    ("fecha_final_serie", "Fecha final de serie histórica"),
    ("fecha_inicial_proyeccion", "Fecha inicial de proyección"),
    ("fecha_final_proyeccion", "Fecha final de proyección"),
    ("horizonte_solicitado", "Horizonte solicitado"),
    ("maximo_recomendado", "Alcance máximo de proyección"),
    ("modelo", "Modelo seleccionado"),
    ("indice_base", "Índice base"),
    ("indice_proyectado", "Índice proyectado"),
    ("estado", "Estado del horizonte"),
    # P0-C / C2: la columna entregaba la pareja [inferior, superior].
    ("ic95", "Intervalo de predicción"),
    ("mae", "MAE"),
    ("rmse", "RMSE"),
    ("mape", "MAPE"),
    ("smape", "sMAPE"),
    ("mase", "MASE"),
    ("advertencia", "Advertencia"),
    ("fecha_calculo", "Fecha de cálculo"),
]

# Columnas visibles de la tabla acumulativa de valores proyectados (calculadora).
COLUMNAS_VALORES_TECNICAS = [
    ("numero", "N°"),
    ("item", "Ítem / insumo"),
    ("unidad", "Unidad"),
    ("cantidad", "Cantidad"),
    ("precio_base", "P"),
    ("anticipo", "A"),
    ("base_ajustable", "Base ajustable"),
    ("ruta_icociv", "Ruta ICOCIV"),
    ("i0_icociv", "I0 ICOCIV"),
    ("i_icociv", "I ICOCIV proyectado"),
    ("factor", "Factor"),
    ("r_total", "R"),
    ("valor_proyectado", "Valor proyectado"),
    ("diferencia", "Diferencia %"),
    ("modelo", "Modelo usado"),
    ("horizonte", "Horizonte"),
    ("fecha_calculo", "Fecha de cálculo"),
    ("observacion", "Observación técnica"),
]


COLUMNAS_VALORES = [
    ("numero", "N.º"), ("proyecto", "Proyecto"), ("componente", "Componente del proyecto"),
    ("item", "Ítem / insumo"), ("unidad", "Unidad"), ("cantidad", "Cantidad"),
    ("precio_base", "P"), ("anticipo", "A"),
    ("base_unitaria", "Base ajustable unitaria (COP)"), ("base_total", "Base ajustable total (COP)"),
    ("i0_icociv", "I0 ICOCIV"), ("i_icociv", "I ICOCIV proyectado"), ("factor", "Factor"),
    ("valor_unitario", "Valor proyectado unitario (COP)"), ("valor_total", "Valor proyectado total (COP)"), ("diferencia", "Diferencia %"),
    ("observacion", "Observación técnica"),
]

# Fase 4G: columnas auxiliares de fecha, solo cuando la fecha de ese índice no es
# única entre las filas incluidas. Van inmediatamente a la derecha de su índice.
COLUMNA_FECHA_I0 = ("fecha_i0", "Fecha I0 (AAAA-MM)")
COLUMNA_FECHA_I = ("fecha_i", "Fecha de I proyectado (AAAA-MM)")
IMPORTES_TIPIFICADOS = ("base_unitaria", "base_total", "valor_unitario", "valor_total")


def plan_columnas_valores(fechas):
    """Columnas físicas y títulos de índices para las filas dadas.

    ``fechas`` es una lista de pares (fecha I0 efectivo, fecha I proyectado) en
    AAAA-MM ('' si falta). Cada índice se evalúa por separado: con fecha única
    y completa, la fecha va en su encabezado; si difiere o falta en alguna
    fila, se añade su columna auxiliar. Sin filas no se fabrica ninguna fecha.
    Devuelve (columnas, {clave: título}) con 17, 18 o 19 columnas.
    """
    columnas = list(COLUMNAS_VALORES)
    titulos = {}
    for posicion, clave, auxiliar, titulo in ((0, "i0_icociv", COLUMNA_FECHA_I0, "I0 ICOCIV"),
                                              (1, "i_icociv", COLUMNA_FECHA_I, "I ICOCIV proyectado")):
        valores = {par[posicion] for par in fechas}
        if not fechas:
            titulos[clave] = titulo
        elif len(valores) == 1 and next(iter(valores)):
            titulos[clave] = f"{titulo}\n{next(iter(valores))}"
        else:
            titulos[clave] = titulo
            columnas.insert([c for c, _ in columnas].index(clave) + 1, auxiliar)
    return columnas, titulos


TIPOS_COMPONENTE = {
    "Capítulo": "Nombre del capítulo", "Grupo de obra": "Nombre del grupo",
    "Subclase de obra": "Nombre de la subclase", "Tipología": "Nombre de la tipología",
    "Actividad": "Nombre de la actividad", "Otro": "Nombre del componente",
    "Ítem": "Nombre del ítem", "Insumo": "Nombre del insumo",
}
NOMBRES_COMPONENTE = {"Grupo de obra": "Grupo", "Subclase de obra": "Subclase"}


class _SliderSinRueda(QSlider):
    def wheelEvent(self, event):  # noqa: N802 - firma Qt
        event.ignore()
        contenedor = self.parentWidget()
        while contenedor is not None:
            if isinstance(contenedor,QScrollArea):
                # Qt no propaga la rueda ignorada hasta el viewport de esta jerarquía.
                QApplication.sendEvent(contenedor.viewport(),event)
                return
            contenedor = contenedor.parentWidget()


class _SelectorAnalisisCompacto(ComboBoxSinRueda):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(360)
        self.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Fixed)
        self.currentTextChanged.connect(self.setToolTip)
        self.setView(QListView())
        self.view().setTextElideMode(Qt.ElideNone)
        self.view().setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def sizeHint(self):  # noqa: N802 - firma Qt
        tamano = super().sizeHint();tamano.setWidth(320)
        return tamano

    def paintEvent(self, event):  # noqa: N802 - firma Qt
        opcion = QStyleOptionComboBox();self.initStyleOption(opcion)
        pintor = QStylePainter(self);pintor.drawComplexControl(QStyle.CC_ComboBox,opcion)
        ancho = self.style().subControlRect(QStyle.CC_ComboBox,opcion,QStyle.SC_ComboBoxEditField,self).width()
        opcion.currentText = self.fontMetrics().elidedText(opcion.currentText,Qt.ElideRight,ancho)
        pintor.drawControl(QStyle.CE_ComboBoxLabel,opcion)

    def showPopup(self):  # noqa: N802 - firma Qt
        ancho = max((self.fontMetrics().horizontalAdvance(self.itemText(i)) for i in range(self.count())),default=0)+48
        pantalla = self.screen().availableGeometry()
        self.view().setMinimumWidth(min(max(self.width(),ancho),pantalla.width()-40))
        super().showPopup()
        popup = self.view().window();popup.setMaximumWidth(pantalla.width()-20);rect = popup.frameGeometry()
        x = max(pantalla.left(),min(rect.left(),pantalla.right()-rect.width()+1))
        y = max(pantalla.top(),min(rect.top(),pantalla.bottom()-rect.height()+1))
        popup.move(popup.x()+x-rect.left(),popup.y()+y-rect.top())


class _SelectorComponente(ComboBoxSinRueda):
    def setCurrentText(self, texto):  # noqa: N802 - acepta nombres guardados anteriores
        indice = self.findData(texto)
        if indice >= 0:
            self.setCurrentIndex(indice)
        else:
            super().setCurrentText(texto)



_CLAVES_NUMERICAS = {"numero", "cantidad", "precio_base", "anticipo", "base_unitaria", "base_total", "i0_icociv",
                     "i_icociv", "factor", "valor_unitario", "valor_total", "diferencia"}


class _DelegadoTablaICOCIV(QStyledItemDelegate):
    """Alinea cifras y permite leer el texto completo sin cambiar el modelo."""

    def __init__(self, columnas_numericas: set[int], parent: QWidget) -> None:
        super().__init__(parent)
        self.columnas_numericas = columnas_numericas

    def initStyleOption(self, option, index) -> None:  # noqa: N802 - firma Qt
        super().initStyleOption(option, index)
        claves = getattr(index.model(), 'claves', None)
        if claves is not None:
            numerica = index.column() < len(claves) and claves[index.column()] in _CLAVES_NUMERICAS
        else:
            numerica = index.column() in self.columnas_numericas
        if numerica:
            option.displayAlignment = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

    def paint(self, painter, option, index) -> None:
        super().paint(painter, option, index)
        # Fase 4I-A: resaltado temporal de la fila completa movida/editada, por calculo_id.
        w = getattr(self, 'widget_icociv', None)
        if w is None or w._resaltado_id is None or index.row() >= len(w._valores_visibles) \
                or w._valores_visibles[index.row()].get('calculo_id') != w._resaltado_id:
            return
        color = QColor(paleta('oscuro' if option.palette.color(QPalette.Base).lightness() < 128 else 'claro')['exito'])
        painter.save()
        relleno = QColor(color);relleno.setAlpha(46)
        painter.fillRect(option.rect, relleno)
        painter.setPen(QPen(color, 2))
        painter.drawLine(option.rect.topLeft(), option.rect.topRight())
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()

    def helpEvent(self, event, view, option, index) -> bool:
        if event.type() == QEvent.Type.ToolTip and index.isValid():
            texto = str(index.data() or '')
            claves = getattr(index.model(), 'claves', [])
            clave = claves[index.column()] if index.column() < len(claves) else None
            enriquecida = clave in (*IMPORTES_TIPIFICADOS, 'i0_icociv', 'i_icociv')
            if hasattr(self, 'widget_icociv') and (self.widget_icociv.historial or enriquecida):
                w = self.widget_icociv
                r = w._valores_visibles[index.row()]
                if enriquecida:texto = str(index.data(Qt.ToolTipRole) or texto)
                a = next((a for a in w.historial if a['id']==r.get('analisis_id')),None)
                texto += f"\nAnálisis: {a['nombre']}" if a else '\nRegistro anterior sin vínculo con el historial.'  # ID completo: «Ver detalle»
            QToolTip.showText(event.globalPos(),f"<qt>{escape(texto).replace(chr(10),'<br>')}</qt>",view)
            return True
        return super().helpEvent(event,view,option,index)


class _CambioPresupuesto(QUndoCommand):
    """Acción atómica y reversible sobre la lista canónica ``valores`` (mover o editar una celda).

    Guarda las dos listas completas (referencias a registros que no se mutan tras crearse), de
    modo que deshacer/rehacer restaura exactamente el orden y los registros, sin recalcular.
    """

    def __init__(self, widget, texto, antes, despues, calculo_id) -> None:
        super().__init__(texto)
        self.widget, self.antes, self.despues, self.calculo_id = widget, list(antes), list(despues), calculo_id

    def redo(self) -> None:
        self.widget._aplicar_estado(self.despues, self.calculo_id)

    def undo(self) -> None:
        self.widget._aplicar_estado(self.antes, self.calculo_id)


class _CambioFechaObjetivo(_CambioPresupuesto):
    """Fase 4I-J: fecha objetivo + consultas de los análisis + actividades recalculadas, en UN solo paso."""

    def __init__(self, widget, texto, antes, despues, fechas_antes, fechas_despues) -> None:
        super().__init__(widget, texto, antes, despues, None)
        self.fechas_antes, self.fechas_despues = fechas_antes, fechas_despues

    def redo(self) -> None:
        self.widget._aplicar_fechas(self.fechas_despues);super().redo()

    def undo(self) -> None:
        self.widget._aplicar_fechas(self.fechas_antes);super().undo()


COLUMNAS_EDITABLES = {"proyecto": "proyecto", "componente": "nombre_componente", "item": "item", "unidad": "unidad",
                      "cantidad": "cantidad", "precio_base": "precio_base", "anticipo": "anticipo_amortizado"}


class _ModeloValoresICOCIV(ModeloTablaNumerica):
    editar_celda = None  # la ventana ICOCIV asigna el callback de edición validada
    fechas_indices = {}
    fechas_filas = []
    registros = []
    # Claves de las columnas físicas actuales (17, 18 o 19; Fase 4G).
    claves = [clave for clave, _ in COLUMNAS_VALORES]

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.EditRole and index.isValid() and index.row() < len(self.registros):
            clave = self.claves[index.column()] if index.column() < len(self.claves) else None
            if clave in COLUMNAS_EDITABLES:
                v = self.registros[index.row()].get(COLUMNAS_EDITABLES[clave])
                return repr(v) if isinstance(v, float) else str(v if v is not None else '')
        valor = super().data(index,role)
        if not index.isValid():return valor
        clave = self.claves[index.column()] if index.column() < len(self.claves) else None
        if clave in IMPORTES_TIPIFICADOS and index.row()<len(self.registros):
            r = self.registros[index.row()];modo = validar_modalidad(r)
            declarado = clave in (('base_unitaria','valor_unitario') if modo=='unitario' else ('base_total','valor_total')) and modo!='heredado'
            if role==Qt.DisplayRole and super().data(index,Qt.UserRole) is None:return '—'
            if role==Qt.FontRole and declarado:
                fuente=QFont();fuente.setBold(True);return fuente
            if role==Qt.ToolTipRole:
                # Ayuda breve; el detalle completo sigue en «Ver detalle».
                importe = super().data(index,Qt.UserRole)
                if modo=='heredado':
                    return 'Importe sin clasificar (modalidad no declarada). Detalle completo en «Ver detalle».'
                return (f"{'Importe declarado' if declarado else 'Conversión por Cantidad'}: "
                        f"{'$' + pesos_ui(importe) if importe is not None else 'no disponible'}\n"
                        f"Modalidad: {'Unitario' if modo == 'unitario' else 'Total'}")
        if (role == Qt.DisplayRole and clave in ('factor', 'diferencia') and index.row() < len(self.registros)
                and not es_factor_legado(self.registros[index.row()])):
            # Fase 4I-D: posiciones uniformes (1.0000 · 2.00) para el factor aplicado y su variación.
            v = self.registros[index.row()].get('factor_icociv' if clave == 'factor' else 'diferencia_porcentual')
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return f"{v:.4f}" if clave == 'factor' else f"{v:,.2f}"
        if clave == 'factor' and index.row() < len(self.registros) and es_factor_legado(self.registros[index.row()]):
            # Fase 4I-C: registro histórico con factor I/I0 original; no se presenta como factor redondeado.
            f = self.registros[index.row()].get('factor_icociv')
            if role == Qt.DisplayRole and isinstance(f, (int, float)):
                # Fase 4I-D: solo el número (precisión original, no se disfraza de factor redondeado);
                # el estado «criterio anterior» va en el aviso sobre la tabla y en el detalle.
                return f"{f:.6f}"
            if role == Qt.ToolTipRole:
                return f"{TEXTO_FACTOR_LEGADO}. Factor original: {f!r}. Use «Actualizar al factor redondeado…» para recalcularlo expresamente."
        if role==Qt.ToolTipRole and clave in ('i0_icociv','factor','diferencia') and isinstance(valor,str):
            valor=valor.replace('Valor original:','Valor vigente:',1)
        if role==Qt.ToolTipRole and clave in ('i0_icociv','i_icociv','fecha_i0','fecha_i') and index.row()<len(self.fechas_filas):
            referencia,objetivo=self.fechas_filas[index.row()]
            valor=(valor or '')+f'\nReferencia efectiva: {referencia or "No disponible"} · Objetivo: {objetivo or "No disponible"}'
        return valor

    def flags(self, index):
        base = super().flags(index)
        clave = self.claves[index.column()] if index.isValid() and index.column() < len(self.claves) else None
        if clave in COLUMNAS_EDITABLES and self.editar_celda is not None and index.row() < len(self.registros):
            return base | Qt.ItemIsEditable
        return base  # I0, I, factor, importes y fechas: solo lectura

    def setData(self, index, valor, role=Qt.EditRole):
        if role != Qt.EditRole or not (self.flags(index) & Qt.ItemIsEditable):
            return False
        return bool(self.editar_celda(index.row(), self.claves[index.column()], valor))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        clave = self.claves[section] if orientation == Qt.Horizontal and 0 <= section < len(self.claves) else None
        if role == Qt.DisplayRole and clave in IMPORTES_TIPIFICADOS:
            return dict(COLUMNAS_VALORES)[clave].replace(' unitaria','\nunitaria').replace(' unitario','\nunitario').replace(' total','\ntotal')
        if role == Qt.DisplayRole and clave in self.fechas_indices:
            return self.fechas_indices[clave]
        return super().headerData(section,orientation,role)


class WidgetProyeccionesICOCIV(QWidget):
    """Calculadora ICOCIV y tablas acumulativas de la sesión."""

    analisis_solicitado = Signal(str)
    comparacion_cambiada = Signal(str)
    # Fase 4G: el usuario eligió «Sin análisis activo» en cualquier selector.
    analisis_desactivado = Signal()
    modo_compacto = False  # lo fija la ventana principal en pantalla dividida
    # Fase 4I-A V4: abrir en Resultados la gráfica GUARDADA de este analisis_id (sin recalcular).
    grafica_solicitada = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.contexto: dict[str, Any] | None = None
        # Fase 4I-J: fecha objetivo común del presupuesto (AAAA-MM) y traza de excepciones individuales.
        self.fecha_objetivo_presupuesto = ""
        self.excepciones_fecha: list[dict[str, Any]] = []
        self.proyecciones: list[dict[str, Any]] = []
        self.valores: list[dict[str, Any]] = []
        self.historial: list[dict[str, Any]] = []
        self.analisis_activo_id: str | None = None
        self._valores_visibles: list[dict[str, Any]] = []
        self._item_editado = False  # el usuario escribió un nombre propio
        self._datos_sesion_adicionales: dict[str, Any] = {}
        self._historicos_comparacion = {}
        self._analisis_comparacion = {}
        self._razones_comparacion = {}
        self._periodo_por_analisis = {}
        self._periodos_slider = []
        self._overrides = {}
        self._consultas_v1 = {}
        # Fase 4G: referencias DANE posteriores aplicadas expresamente, por análisis:
        # {id: {periodo: {indice, archivo, tabla, huella_fuente, aplicado}}}.
        self._referencias_externas = {}
        self._periodo_original = {}
        # Fase 4G-B: cuatro estados separados. Consulta (ámbito + proyección) solo
        # filtra la vista; ``analisis_activo_id`` es el ÚNICO vínculo de los cálculos
        # nuevos; ``_edicion_calculo_id`` existe solo tras «Editar» explícito.
        self._ambito_consulta = None
        self._proyeccion_consulta = None
        self._fichas = []
        self._ambitos = []
        self._edicion_calculo_id = None
        self._formulario_guardado = None
        self._insercion = None  # (calculo_id de referencia, después?) para la próxima actividad
        self._alcance_pendiente = None
        # La ventana principal asigna un proveedor del anexo cargado (tablas, periodos, ruta).
        self.fuente_dane = None
        self.modelo_proyecciones = ModeloTablaNumerica({dict(COLUMNAS_PROYECCIONES)[k]:4 for k in ('indice_base','indice_proyectado','mae','rmse','mape','smape','mase')})
        self.modelo_proyecciones.decimales.update({dict(COLUMNAS_PROYECCIONES)[k]:0 for k in ('numero','horizonte_solicitado','maximo_recomendado')})
        # Fase 4I: importes en pesos enteros (presentación) y variación con 2 decimales.
        self.modelo_valores = _ModeloValoresICOCIV({dict(COLUMNAS_VALORES)[k]:4 if k in ('i0_icociv','i_icociv') else 6 if k=='factor'
            else 4 if k=='factor' else 0 if k in ('numero','precio_base','anticipo','base_unitaria','base_total','valor_unitario','valor_total')
            else 2 if k=='diferencia' else 3 for k in ('numero','cantidad','precio_base','anticipo','base_unitaria','base_total','i0_icociv','i_icociv','factor','valor_unitario','valor_total','diferencia')})
        self.modelo_valores.editar_celda = self._editar_celda
        # Fase 4I-A: pila de Deshacer/Rehacer del presupuesto y resaltado temporal por calculo_id.
        self.pila_deshacer = QUndoStack(self)
        self._estado_pila = None  # lista canónica que la pila considera vigente
        self._resaltado_id = None
        self._temporizador_resaltado = QTimer(self)
        self._temporizador_resaltado.setSingleShot(True)
        self._temporizador_resaltado.setInterval(3500)
        self._temporizador_resaltado.timeout.connect(self._quitar_resaltado)
        self._crear_interfaz()
        self._actualizar_estado_calculadora()

    def datos_proyecto(self) -> dict[str, str]:
        return {
            "nombre_proyecto": self.nombre_proyecto.text(), "objeto": self.objeto_proyecto.toPlainText(),
            "responsable_tecnico": self.responsable_tecnico.text(),
            "observacion_general": self.observacion_general.toPlainText(),
        }

    def datos_sesion(self) -> dict[str, Any]:
        self.sincronizar_analisis_activo()
        datos = deepcopy(self._datos_sesion_adicionales)
        datos.update({
            "proyecto": self.datos_proyecto(), "proyecciones": deepcopy(self.proyecciones),
            "valores": deepcopy(self.valores), "contexto": deepcopy(self.contexto),
            "calculadora": self._datos_calculadora(),
        })
        if self.historial:
            datos.update(historial_analisis=deepcopy(self.historial), analisis_activo_id=self.analisis_activo_id,
                         filtrar_analisis=self.solo_analisis_activo.isChecked())
            datos['comparacion_historica'] = {'version':2, 'selecciones':{i:{'periodo':p,'override':self._overrides.get(i,False)} for i,p in self._periodo_por_analisis.items()}, 'global':self.aplicar_global.isChecked(), 'consulta_v1':dict(self._consultas_v1)}
            externas = {i:deepcopy(m) for i,m in self._referencias_externas.items() if m}
            if externas:
                # Versión 3 (Fase 4G): índice exacto, archivo y huella de cada referencia DANE posterior.
                datos['comparacion_historica'].update(version=3, referencias_externas=externas)
        datos.pop("fecha_objetivo_presupuesto", None);datos.pop("excepciones_fecha", None)
        if self.fecha_objetivo_presupuesto:
            datos["fecha_objetivo_presupuesto"] = self.fecha_objetivo_presupuesto
        if self.excepciones_fecha:
            datos["excepciones_fecha"] = deepcopy(self.excepciones_fecha)
        return datos

    def analisis_activo(self) -> dict[str, Any] | None:
        return next((a for a in self.historial if a["id"] == self.analisis_activo_id), None)

    def sincronizar_analisis_activo(self) -> None:
        # Fase 4G-B: el borrador de la calculadora ya no se copia en el análisis activo
        # (navegar no guarda silenciosamente el formulario); vive solo en la sesión.
        for a in self.historial:
            a["registros_ids"] = [r["calculo_id"] for r in self.valores if r.get("analisis_id") == a["id"]]

    def _datos_calculadora(self) -> dict[str, Any]:
        return {**({"modalidad_importe":self.modalidad_importe.currentData()} if self.modalidad_importe.currentData()!='heredado' else {}),
                "tipo_componente": self.tipo_componente.currentData(),
                "nombre_componente": self.nombre_componente.text(), "item": self.item.text(),
                "unidad": self.unidad.currentData(), "cantidad": self.cantidad.value(),
                "precio_base": self.precio_base.value(), "anticipo": self.anticipo.value(),
                "observacion": self.observacion.toPlainText()}

    def registrar_analisis(self, resultado, seleccion, parametros, archivo) -> None:
        self._preseleccionar_componente()
        identificador = uuid4().hex
        contexto = deepcopy(self.contexto)
        numero = len(self.historial) + 1
        horizonte = contexto["horizonte_solicitado"]
        nombre = f"{numero}. {contexto['serie_final']} · {contexto['periodo_proyectado']} · {horizonte} {'mes' if horizonte == 1 else 'meses'}"
        analisis = {"id": identificador, "nombre": nombre, "creado": datetime.now().isoformat(timespec="seconds"),
                    "archivo_excel": str(archivo or ""), "seleccion": deepcopy(seleccion),
                    "parametros": deepcopy(parametros), "contexto": contexto,
                    "resultado": serializar_resultado(resultado), "proyecto": self.datos_proyecto(),
                    "calculadora": self._datos_calculadora(), "registros_ids": [],
                    "fila_tecnica": deepcopy(self.proyecciones[-1])}
        self.proyecciones[-1]["analisis_id"] = identificador
        analisis["fila_tecnica"]["analisis_id"] = identificador
        self.historial.append(analisis)
        self._preparar_comparacion_historica()
        self.establecer_analisis_activo(identificador)

    def establecer_analisis_activo(self, identificador) -> None:
        self.analisis_activo_id = identificador
        self._aplicar_consulta_al_contexto()
        # La consulta acompaña al análisis activo solo si pertenece al ámbito consultado.
        if identificador and identificador in self.ids_ambito():
            self._proyeccion_consulta = identificador
        self._refrescar_historial()
        self._refrescar_tabla_valores()
        self._mostrar_resumen_activo()

    def _aplicar_consulta_al_contexto(self) -> None:
        """Fase 4I-J: los NUEVOS cálculos usan la fecha consultada del análisis activo (punto guardado de su
        trayectoria). El contexto original del análisis y las actividades ya guardadas no cambian."""
        a = self.analisis_activo()
        consulta = (a or {}).get("consulta_horizonte")
        if a is not None and consulta and self.contexto is not None:
            self.contexto = fo.contexto_consultado(deepcopy(a["contexto"]), consulta)

    def resumen_fechas(self) -> str:
        """Fecha común del presupuesto y análisis vigentes fuera de ella (para mostrar en la interfaz)."""
        if not self.fecha_objetivo_presupuesto:
            return ""
        fuera = [f"«{a['contexto'].get('serie_final', a['nombre'])}» ({fo.periodo_visible(fo.fecha_vigente(a))})"
                 for a in fo.vigentes(self.historial) if fo.fecha_vigente(a) != self.fecha_objetivo_presupuesto]
        texto = f"Fecha objetivo del presupuesto: {fo.periodo_visible(self.fecha_objetivo_presupuesto)}"
        return texto + (" · Fuera de la fecha común: " + ", ".join(fuera) if fuera else "")

    def actividades_en_otra_fecha(self) -> int:
        return sum(1 for r in self.valores if self.fecha_objetivo_presupuesto
                   and fo.periodo_iso(r.get("periodo_proyectado")) != self.fecha_objetivo_presupuesto)

    def aplicar_fecha_objetivo(self, periodo: str, solo_id: str | None = None, confirmar: bool = True,
                               actualizar_actividades: bool = True) -> bool:
        """Consulta la fecha objetivo en las trayectorias GUARDADAS (sin motor, sin historial nuevo). Sin
        `solo_id`: todas las revisiones vigentes y fija la fecha común; con `solo_id`: solo ese análisis.
        Fase 4I-J (ajuste): si hay actividades del alcance que cambiarían, muestra antes una vista previa
        («Aceptar y actualizar» / «Cancelar») y, si se acepta, recalcula TODAS con el punto guardado de su
        análisis (misma regla económica) en un solo paso de Deshacer. Si una falla, no cambia nada."""
        periodo = fo.periodo_iso(periodo)
        vigentes = fo.vigentes(self.historial)
        objetivos = [a for a in vigentes if solo_id is None or a["id"] == solo_id]
        if not objetivos:
            QMessageBox.information(self, "Fecha objetivo", "Seleccione un análisis vigente para aplicar el cambio solo a él."
                                    if solo_id else "Todavía no hay análisis guardados en el presupuesto.")
            return False
        consultas, problemas = {}, []
        for a in objetivos:
            try:
                consultas[a["id"]] = fo.consultar(a, periodo)
            except ValueError as error:
                problemas.append(f"• «{a['nombre']}»: {error}.")
        if problemas:
            QMessageBox.warning(self, "Fecha objetivo no aplicada",
                                f"No se cambió ninguna serie: {fo.periodo_visible(periodo)} no puede consultarse en todas las "
                                "trayectorias guardadas.\n\n" + "\n".join(problemas))
            return False
        excepcion, divergencia = None, ""
        if solo_id:
            a = objetivos[0]
            otras = {fo.fecha_vigente(x) for x in vigentes if x["id"] != solo_id} - {""}
            comun = self.fecha_objetivo_presupuesto or (next(iter(otras)) if len(otras) == 1 else "")
            if (comun and periodo != comun) or any(f != periodo for f in otras):
                serie = a["contexto"].get("serie_final") or a["nombre"]
                divergencia = (f"Atención: la serie «{serie}» quedará en {fo.periodo_visible(periodo)}"
                               + (f", mientras el presupuesto se analiza principalmente para {fo.periodo_visible(comun)}." if comun else
                                  ", con fecha distinta de otras series."))
                excepcion = {"analisis_id": a["id"], "serie": serie, "periodo": periodo, "fecha_comun": comun,
                             "confirmado": datetime.now().isoformat(timespec="seconds")}
        # Vista previa SIN mutar nada: actividades del alcance recalculadas con el punto guardado de SU análisis.
        pares, fallos, afectadas = [], [], []
        if actualizar_actividades:
            por_id = {x["id"]: x for x in self.historial}
            afectadas = [r for r in self.valores if solo_id is None or r.get("analisis_id") == solo_id]
            for r in afectadas:
                nombre = f"N.º {r.get('numero_fila', '?')} «{r.get('item', '')}»"
                analisis = por_id.get(r.get("analisis_id"))
                if analisis is None:
                    fallos.append(f"• {nombre}: no tiene un análisis vinculado verificable.");continue
                try:
                    c = consultas.get(analisis["id"]) or fo.consultar(analisis, periodo)
                    if fo.periodo_iso(r.get("periodo_proyectado")) == periodo and r.get("i_icociv") == c["indice"]:
                        continue  # ya corresponde a esta fecha
                    nuevo = self._recalcular_registro(r, {"i_icociv": c["indice"], "periodo_proyectado": periodo, "horizonte": c["horizonte"]})
                except ValueError as error:
                    fallos.append(f"• {nombre}: {error}.");continue
                nuevo["historial_ediciones"][-1].update(
                    antes={k: r.get(k) for k in self._CLAVES_ARCHIVO}, despues={k: nuevo.get(k) for k in self._CLAVES_ARCHIVO},
                    motivo=f"actualización expresa de la fecha objetivo a {periodo} con la trayectoria guardada "
                           f"(H{c['horizonte']} desde {c['origen']}); sin ejecutar el motor")
                pares.append((r, nuevo))
        if fallos:
            QMessageBox.warning(self, "Fecha objetivo no aplicada", "No se modificó ninguna actividad ni la fecha del presupuesto: "
                                "estas actividades no pueden actualizarse con garantías. Elija otra fecha o actualice su análisis "
                                "con el flujo existente.\n\n" + "\n".join(fallos))
            return False
        if pares:
            antes = sum(r.get("valor_proyectado") or 0 for r, _ in pares);despues = sum(x.get("valor_proyectado") or 0 for _, x in pares)
            anteriores = sorted({fo.periodo_visible(r.get("periodo_proyectado")) for r, _ in pares})
            fuera = [r for r in self.valores if solo_id and r.get("analisis_id") != solo_id
                     and fo.periodo_iso(r.get("periodo_proyectado")) != periodo]
            introduccion = (f"Se actualizarán {len(pares)} actividades al periodo {periodo} utilizando las proyecciones ya guardadas. "
                            "No se realizará un nuevo análisis estadístico. Se conservarán los datos originales y la trazabilidad; "
                            f"podrá deshacer la operación.\n\nFecha anterior: {', '.join(anteriores)} → nueva: {fo.periodo_visible(periodo)} · "
                            f"Análisis: {len({r.get('analisis_id') for r, _ in pares})} · Valor principal: {pesos_ui(antes)} → "
                            f"{pesos_ui(despues)} (diferencia {pesos_ui(despues - antes)}).")
            if divergencia:
                introduccion += f"\n\n{divergencia} {len(fuera)} actividades de otras series quedarán con otra fecha."
            if confirmar and not self._confirmar_actualizacion(pares, titulo="Actualizar fecha objetivo del presupuesto",
                                                              introduccion=introduccion, boton="Aceptar y actualizar", con_fechas=True):
                return False
        elif divergencia and confirmar and not self._confirmar_fecha_individual(excepcion["serie"], periodo, excepcion["fecha_comun"]):
            return False
        marca = datetime.now().isoformat(timespec="seconds")
        fechas_antes = self._estado_fechas()
        nuevas = {aid: ({**consultas[aid], "alcance": "individual" if solo_id else "todas", "aplicado": marca} if aid in consultas
                        else fechas_antes["consultas"][aid]) for aid in fechas_antes["consultas"]}
        fechas_despues = {"fecha": fechas_antes["fecha"] if solo_id else periodo, "consultas": nuevas,
                          "excepciones": fechas_antes["excepciones"] + ([excepcion] if excepcion else [])}
        if pares:  # una sola operación deshacible: fechas + consultas + todas las actividades
            reemplazo = {id(r): n for r, n in pares}
            self.pila_deshacer.push(_CambioFechaObjetivo(self, f"actualizar {len(pares)} actividades a {periodo}",
                                                         self.valores, [reemplazo.get(id(r), r) for r in self.valores],
                                                         fechas_antes, fechas_despues))
            self._avisar_edicion(f"{len(pares)} actividades actualizadas a {fo.periodo_visible(periodo)} con las proyecciones "
                                 "guardadas (sin ejecutar el motor). Puede deshacerlo con Ctrl+Z.")
            return True
        self._aplicar_fechas(fechas_despues)
        if afectadas:
            self._avisar_edicion("Las actividades ya corresponden a esta fecha.")
        else:
            pendientes = self.actividades_en_otra_fecha()
            if pendientes:
                self._avisar_edicion(f"{pendientes} actividades guardadas siguen calculadas con otra fecha objetivo; sus valores no se "
                                     "modificaron. Use «Aplicar fecha objetivo a análisis guardados» para actualizarlas.")
        return True

    def _estado_fechas(self) -> dict:
        return {"fecha": self.fecha_objetivo_presupuesto, "excepciones": deepcopy(self.excepciones_fecha),
                "consultas": {a["id"]: deepcopy(a.get("consulta_horizonte")) for a in self.historial}}

    def _aplicar_fechas(self, estado: dict) -> None:
        """Restaura/aplica fecha común, excepciones y consultas (sin tocar contextos ni instantáneas)."""
        self.fecha_objetivo_presupuesto = estado["fecha"];self.excepciones_fecha = deepcopy(estado["excepciones"])
        for a in self.historial:
            consulta = estado["consultas"].get(a["id"])
            if consulta:
                a["consulta_horizonte"] = deepcopy(consulta)
            else:
                a.pop("consulta_horizonte", None)
        activo = self.analisis_activo()
        if activo is not None and self.contexto is not None and not activo.get("consulta_horizonte"):
            self.contexto = deepcopy(activo["contexto"])
        self._aplicar_consulta_al_contexto()
        self._refrescar_historial();self._mostrar_resumen_activo()

    def _confirmar_fecha_individual(self, serie: str, periodo: str, comun: str) -> bool:
        """«Atención: diferentes fechas de proyección» con [Aplicar solo a esta serie] [Cancelar]."""
        caja = QMessageBox(QMessageBox.Icon.Warning, "Atención: diferentes fechas de proyección",
                           (f"El presupuesto se está analizando principalmente para {fo.periodo_visible(comun)}. " if comun else "")
                           + f"La serie «{serie}» quedaría en {fo.periodo_visible(periodo)}"
                           + (f", mientras las demás mantienen {fo.periodo_visible(comun)}." if comun else ", con fecha distinta de otras series.")
                           + "\n\nEsta combinación puede dificultar la comparación y la interpretación de los resultados "
                           "presupuestales. ¿Desea aplicarla únicamente a esta serie?", QMessageBox.StandardButton.NoButton, self)
        aplicar = caja.addButton("Aplicar solo a esta serie", QMessageBox.ButtonRole.AcceptRole)
        cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(cancelar);caja.setEscapeButton(cancelar);caja.exec()
        return caja.clickedButton() is aplicar

    def confirmar_exportacion(self, registros) -> bool:
        """Fase 4I-J: comprobación central antes de exportar (Excel, PDF, Word) sobre los registros incluidos."""
        texto = fo.advertencia_fechas(list(registros), self.fecha_objetivo_presupuesto)
        return not texto or self._dialogo_exportacion(texto)

    def _dialogo_exportacion(self, texto: str) -> bool:
        """«Advertencia antes de exportar» con [Continuar exportación] [Cancelar]."""
        caja = QMessageBox(QMessageBox.Icon.Warning, "Advertencia antes de exportar",
                           texto + "\n\nCompruebe que esta combinación es intencional. Los valores guardados no serán modificados.",
                           QMessageBox.StandardButton.NoButton, self)
        continuar = caja.addButton("Continuar exportación", QMessageBox.ButtonRole.AcceptRole)
        cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(cancelar);caja.setEscapeButton(cancelar);caja.exec()
        return caja.clickedButton() is continuar

    def _mostrar_resumen_activo(self) -> None:
        """Panel de resultado sin elegir ninguna actividad (4G-B: nunca la «última»)."""
        a = self.analisis_activo()
        if a is None:
            self.resultado.setHtml("<p>Ninguna proyección activa para nuevos cálculos. Seleccione una fila y use "
                                   "«Ver detalle» para consultar una actividad guardada.</p>")
            return
        n = sum(1 for r in self.valores if r.get("analisis_id") == a["id"])
        consulta = a.get("consulta_horizonte")
        fechas = (f"<p>Fecha consultada: <b>{escape(fo.periodo_visible(consulta['periodo']))}</b> (H{consulta['horizonte']} de su trayectoria "
                  f"guardada desde {escape(fo.periodo_visible(consulta['origen']))}) · Índice proyectado {numero_ui(consulta['indice'])}</p>"
                  if consulta else "")
        if self.resumen_fechas():
            fechas += f"<p>{escape(self.resumen_fechas())}</p>"
        self.resultado.setHtml(f"<p><b>Para nuevos cálculos:</b> {escape(fo.nombre_vigente(a))}</p>{fechas}<p>{n} actividades vinculadas. "
                               "Seleccione una fila y use «Ver detalle» para consultarla o «Editar actividad» para modificarla; "
                               "ninguna se carga en la calculadora automáticamente.</p>")

    # ------------------------------------------------------------ consulta 4G-B
    def ids_ambito(self) -> list[str]:
        return analisis_en_ambito(self._fichas, self._ambito_consulta)

    def _ficha(self, identificador):
        return next((f for f in self._fichas if f['id'] == identificador), None)

    def etiqueta_activo(self) -> str:
        a = self.analisis_activo();f = self._ficha(self.analisis_activo_id)
        if a is None:return "Ninguna proyección activa"
        return f"{f['serie_final']} · {etiqueta_proyeccion(f)}" if f else a['nombre']

    def _refrescar_controles_consulta(self) -> None:
        with QSignalBlocker(self.selector_ambito):
            self.selector_ambito.clear()
            self.selector_ambito.addItem("Toda la sesión", None)
            for ambito in self._ambitos:
                self.selector_ambito.addItem(ambito['etiqueta'], ambito['clave'])
                self.selector_ambito.setItemData(self.selector_ambito.count()-1, f"{ambito['etiqueta']}\n{ambito['contexto']}", Qt.ToolTipRole)
            clave = self._ambito_consulta['clave'] if self._ambito_consulta else None
            self.selector_ambito.setCurrentIndex(max(0, self.selector_ambito.findData(clave)))
        ids = self.ids_ambito();fichas = [f for f in self._fichas if f['id'] in ids]
        varias = len({f['serie'] or f['id'] for f in fichas}) > 1
        if self._proyeccion_consulta not in ids:self._proyeccion_consulta = None
        with QSignalBlocker(self.selector_analisis_valores):
            self.selector_analisis_valores.clear()
            self.selector_analisis_valores.addItem("Todas las proyecciones de esta selección" if self.historial
                                                   else "Sin análisis guardados en esta sesión", None)
            for f in fichas:self.selector_analisis_valores.addItem(etiqueta_proyeccion(f, varias), f['id'])
            self.selector_analisis_valores.setCurrentIndex(max(0, self.selector_analisis_valores.findData(self._proyeccion_consulta)))
        for i in range(self.selector_analisis_valores.count()):
            self.selector_analisis_valores.setItemData(i, self.selector_analisis_valores.itemText(i), Qt.ToolTipRole)
        # Fase 4I-A: el historial inferior es otra vista del MISMO estado (sin estado propio).
        for origen, destino in ((self.selector_ambito, self.selector_ambito_inferior),
                                (self.selector_analisis_valores, self.selector_proyeccion_inferior)):
            with QSignalBlocker(destino):
                destino.clear()
                for i in range(origen.count()):
                    destino.addItem(origen.itemText(i), origen.itemData(i))
                    destino.setItemData(i, origen.itemData(i, Qt.ToolTipRole), Qt.ToolTipRole)
                destino.setCurrentIndex(origen.currentIndex())
        self._actualizar_botones_grafica()
        ambito = self._ambito_consulta
        self.lbl_contexto_ambito.setText(f"{ambito['contexto']}" + (f" · {ambito.get('tabla')}" if ambito.get('tabla') else "")
                                         if ambito else "Todas las series y proyecciones de la sesión")
        texto = f"Para nuevos cálculos: {self.etiqueta_activo()}"
        if ambito and self.analisis_activo_id and self.analisis_activo_id not in ids:
            texto += f" · Estás consultando {ambito['etiqueta']}; los nuevos cálculos usarán otra serie."
        self.lbl_calculo_activo.setText(texto)

    def _cambiar_ambito(self, _indice=None) -> None:
        """Cambia solo la consulta: ni análisis activo, ni slider, ni calculadora."""
        clave = self.selector_ambito.currentData()
        self._ambito_consulta = next((x for x in self._ambitos if x['clave'] == clave), None)
        self._refrescar_controles_consulta()
        self._refrescar_tabla_valores()

    def _cambiar_proyeccion_consulta(self) -> None:
        identificador = self.selector_analisis_valores.currentData()
        self._proyeccion_consulta = identificador
        self._refrescar_controles_consulta()
        self._refrescar_tabla_valores()
        if identificador and identificador != self.analisis_activo_id:
            # Elegir una proyección concreta la activa para cálculos NUEVOS (sin cargar actividades).
            self.analisis_solicitado.emit(identificador)

    def _refrescar_historial(self) -> None:
        with QSignalBlocker(self.selector_analisis):
            self.selector_analisis.clear()
            self.selector_analisis.addItem("Sin análisis activo" if self.historial else "Sin análisis guardados en esta sesión",None)
            # Fase 4I-P: se rotula la consulta vigente (fecha y H aplicados); el `nombre` guardado no cambia.
            for a in self.historial:
                self.selector_analisis.addItem(fo.nombre_vigente(a),a['id'])
                if fo.detalle_vigente(a):
                    self.selector_analisis.setItemData(self.selector_analisis.count()-1, fo.detalle_vigente(a), Qt.ToolTipRole)
            self.selector_analisis.setCurrentIndex(max(0,self.selector_analisis.findData(self.analisis_activo_id)))
        if not self._fichas and self.historial:
            self._fichas = fichas_historial(self.historial);self._ambitos = ambitos_disponibles(self._fichas)
        self._actualizar_fichas_vigentes()
        self._refrescar_controles_consulta()
        self.selector_analisis_valores.setToolTip(self.selector_analisis_valores.currentText())
        a = self.analisis_activo()
        self.lbl_analisis.setText(
            f"Activo: {fo.nombre_vigente(a)} · Creado: {a['creado']} · Proyecto al ejecutar: {a['proyecto'].get('nombre_proyecto', '')}"
            if a else ("No hay análisis seleccionado. El historial y los registros se conservan." if self.historial else
                       "Ejecute una proyección válida para conservar un nuevo análisis. Recuperar uno guardado no recalcula."))
        self._refrescar_arbol_historial()
        self._actualizar_controles_comparacion()

    def _actualizar_fichas_vigentes(self) -> None:
        """Fase 4I-P: las fichas en caché toman el objetivo y el H de la consulta vigente de su análisis."""
        por_id = {a['id']: a for a in self.historial}
        for f in self._fichas:
            a = por_id.get(f['id'])
            if a is None:
                continue
            vigente = fo.consulta_vigente(a)
            contexto = a.get('contexto') or {}
            f['objetivo'] = vigente['periodo'] if vigente else (fo.periodo_iso(contexto.get('periodo_proyectado')) or f['objetivo'])
            f['horizonte'] = vigente['horizonte'] if vigente else (a.get('parametros') or {}).get('horizonte')

    def grupos_historial(self) -> list[dict]:
        """Estructura Serie → Análisis → Actividades (solo lectura, por IDs)."""
        return agrupar_historial(self.historial, self.valores)

    def _refrescar_arbol_historial(self) -> None:
        if not hasattr(self, 'arbol_historial'):return
        arbol = self.arbol_historial
        with QSignalBlocker(arbol):
            arbol.clear()
            for grupo in self.grupos_historial():
                serie = QTreeWidgetItem([grupo['etiqueta'], f"{grupo['tabla']} · {len(grupo['analisis'])} análisis"])
                serie.setData(0, Qt.UserRole, ('serie', grupo['clave']))
                serie.setToolTip(0, grupo['etiqueta'] if grupo['verificable'] else f"{grupo['etiqueta']}\n{grupo['motivo']} Se muestra sin agrupar.")
                arbol.addTopLevelItem(serie)
                for a in grupo['analisis']:
                    nodo = QTreeWidgetItem([a['etiqueta'], f"Último observado {a['ultimo_observado'] or 's/d'} · {len(a['actividades'])} actividades"])
                    nodo.setData(0, Qt.UserRole, ('analisis', a['id']))
                    nodo.setToolTip(0, f"ID análisis: {a['id']}\nCreado: {a['creado']}\nHuella de datos DANE: {a['huella_datos'] or 'no verificable'}"
                                    + (f"\n{a['detalle_consulta']}" if a.get('detalle_consulta') else ""))
                    serie.addChild(nodo)
                    for act in a['actividades']:
                        hijo = QTreeWidgetItem([act['item'] or act['componente'] or act['calculo_id'],
                                                f"{MODALIDADES.get(act['modalidad'], act['modalidad'])} · Cantidad {numero_ui(act['cantidad'])} · Valor {numero_ui(act['valor'])}"])
                        hijo.setData(0, Qt.UserRole, ('actividad', act['calculo_id'], a['id']))
                        hijo.setToolTip(0, f"ID cálculo: {act['calculo_id']}\nID análisis: {a['id']}")
                        nodo.addChild(hijo)
                    if a['id'] == self.analisis_activo_id:
                        arbol.setCurrentItem(nodo);serie.setExpanded(True);nodo.setExpanded(True)
            arbol.resizeColumnToContents(0)

    def _activar_nodo_historial(self, item, _columna=0) -> None:
        dato = item.data(0, Qt.UserRole) or ()
        if not dato or dato[0] == 'serie':return
        identificador = dato[1] if dato[0] == 'analisis' else dato[2]
        if identificador != self.analisis_activo_id:
            self.analisis_solicitado.emit(identificador)
        if dato[0] == 'actividad':self.localizar_actividad(dato[1])

    def _seleccionar_fila_valores(self, fila, columna=0) -> None:
        """Selecciona una fila completa sin depender de modificadores de teclado activos."""
        from PySide6.QtCore import QItemSelectionModel
        indice = self.modelo_valores.index(fila, columna)
        self.tabla_valores.selectionModel().setCurrentIndex(
            indice, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)

    def localizar_actividad(self, calculo_id) -> bool:
        """Selecciona en la tabla operativa la fila con ese ID (no por nombre ni posición)."""
        fila = next((i for i,r in enumerate(self._valores_visibles) if r.get('calculo_id') == calculo_id), None)
        if fila is None and self.solo_analisis_activo.isChecked():
            self.solo_analisis_activo.setChecked(False)
            fila = next((i for i,r in enumerate(self._valores_visibles) if r.get('calculo_id') == calculo_id), None)
        if fila is None:return False
        self._seleccionar_fila_valores(fila);self.tabla_valores.scrollTo(self.modelo_valores.index(fila,0))
        self._mostrar_resultado(self._valores_visibles[fila])
        return True

    def _solicitar_analisis(self) -> None:
        if self.sender() is self.selector_analisis_valores:
            self._cambiar_proyeccion_consulta();return
        identificador = self.sender().currentData() if isinstance(self.sender(),QComboBox) else self.selector_analisis.currentData()
        if identificador:
            self.analisis_solicitado.emit(identificador)
        elif self.analisis_activo_id is not None:
            # «Sin análisis activo» deselecciona de verdad (antes restauraba el ID previo).
            self.desactivar_analisis()
        else:
            self._refrescar_historial()

    def desactivar_analisis(self) -> None:
        """Deja ``analisis_activo_id = None`` sin borrar historial, registros ni sesión.

        La calculadora queda deshabilitada hasta elegir un análisis. Si estaba
        marcado «Solo registros del análisis activo», se desmarca con aviso para
        que la tabla siga mostrando todos los registros.
        """
        self.sincronizar_analisis_activo()
        self.analisis_activo_id = None
        self.contexto = None
        # 4G-B: la consulta (ámbito, proyección y casilla) es independiente y se conserva.
        self._refrescar_historial()
        self._actualizar_estado_calculadora()
        self._refrescar_tabla_valores()
        self.resultado.setHtml("<p>Ninguna proyección activa para nuevos cálculos. El historial, los registros y los "
                               "datos digitados en la calculadora se conservan; seleccione un análisis para calcular.</p>")
        self.analisis_desactivado.emit()
        self.comparacion_cambiada.emit(self.resumen_comparacion_historica())

    def validar_datos_sesion(self, datos: dict[str, Any] | None) -> None:
        if datos is None:
            return
        if not isinstance(datos, dict):
            raise ValueError("El bloque Proyecciones ICOCIV de la sesión no es válido.")
        proyecto = datos.get("proyecto", {})
        if not isinstance(proyecto, dict) or any(not isinstance(v, str) for v in proyecto.values()):
            raise ValueError("Los metadatos del proyecto deben ser textos.")
        for clave in ("proyecciones", "valores"):
            filas = datos.get(clave, [])
            if not isinstance(filas, list) or any(not isinstance(fila, dict) for fila in filas):
                raise ValueError(f"Los registros de {clave} no son válidos; no se reemplazará la sesión.")
        if not isinstance(datos.get("calculadora", {}), dict):
            raise ValueError("El formulario de calculadora guardado no es válido.")
        for registro in datos.get("valores", []):validar_modalidad(registro)
        formulario = datos.get("calculadora", {})
        validar_modalidad(formulario)
        for clave in ("item", "nombre_componente", "observacion", "tipo_componente"):
            if clave in formulario and not isinstance(formulario[clave], str):
                raise ValueError(f"El campo {clave} guardado debe ser texto.")
        if formulario.get("tipo_componente", "Capítulo") not in TIPOS_COMPONENTE:
            raise ValueError("El tipo de componente del formulario guardado no es reconocido.")
        for clave, campo in (("cantidad", self.cantidad), ("precio_base", self.precio_base), ("anticipo", self.anticipo)):
            valor = formulario.get(clave, 0)
            if not isinstance(valor, (int, float)) or not math.isfinite(valor):
                raise ValueError(f"El campo {clave} guardado no es un número válido.")
            if not campo.minimum() <= valor <= campo.maximum():
                raise ValueError(f"El campo {clave} está fuera del rango del control actual; no se reinterpretará.")
        if datos.get("contexto") is not None and not isinstance(datos["contexto"], dict):
            raise ValueError("El contexto ICOCIV guardado no es válido.")
        historial = datos.get("historial_analisis", [])
        if not isinstance(historial, list) or any(not isinstance(a, dict) for a in historial):
            raise ValueError("El historial guardado no es válido.")
        ids = set()
        try:
            for a in historial:
                if not isinstance(a["id"], str) or not a["id"] or a["id"] in ids:
                    raise ValueError("Identificadores de análisis vacíos o repetidos.")
                ids.add(a["id"])
                if any(not isinstance(a[k], str) for k in ("nombre", "creado", "archivo_excel")):
                    raise ValueError("La identificación del análisis debe ser texto.")
                if not isinstance(a["seleccion"], dict) or not isinstance(a["parametros"], dict):
                    raise ValueError("Selección o parámetros del análisis inválidos.")
                for k, v in a["seleccion"].items():
                    if k.startswith("idx_") and v is not None and (type(v) is not int or v < 0):
                        raise ValueError("Índice jerárquico guardado inválido.")
                    if k.startswith("chk_") and type(v) is not bool:
                        raise ValueError("Estado de ruta alternativa guardado inválido.")
                for k, minimo, maximo in (("horizonte", 1, 24), ("mes", 1, 12), ("anio", 1900, 9999)):
                    if type(a["parametros"].get(k)) is not int or not minimo <= a["parametros"][k] <= maximo:
                        raise ValueError("Parámetros del historial fuera de rango.")
                if not isinstance(a["fila_tecnica"], dict) or not isinstance(a["registros_ids"], list):
                    raise ValueError("La trazabilidad del análisis no es válida.")
                consulta = a.get("consulta_horizonte")
                if consulta is not None and (not isinstance(consulta, dict) or not fo.periodo_iso(consulta.get("periodo"))
                        or type(consulta.get("horizonte")) is not int or not 1 <= consulta["horizonte"] <= 24
                        or type(consulta.get("indice")) not in (int, float) or not math.isfinite(consulta["indice"])):
                    raise ValueError("La fecha consultada de un análisis no es válida.")
                self.validar_datos_sesion({k: a[k] for k in ("proyecto", "calculadora", "contexto")})
                resultado = recuperar_resultado(a["resultado"])
                if (not isinstance(resultado, dict) or not isinstance(resultado.get("fila"), pd.DataFrame)
                        or not isinstance(resultado.get("fuente"), str)
                        or not isinstance(resultado.get("ruta_jerarquica"), list)
                        or not isinstance(resultado.get("proyeccion"), dict)
                        or not isinstance(resultado.get("serie_df"), pd.DataFrame)
                        or not {"Periodo", "Indice"}.issubset(resultado["serie_df"].columns)
                        or _extraer_contexto(resultado) != a["contexto"]):
                    raise ValueError("El resultado guardado no corresponde al contexto del análisis.")
                vinculados = [r.get("calculo_id") for r in datos.get("valores", []) if r.get("analisis_id") == a["id"]]
                if a["registros_ids"] != vinculados or any(not isinstance(i, str) for i in vinculados):
                    raise ValueError("Los vínculos de registros del historial no coinciden.")
            if datos.get("analisis_activo_id") is not None and datos["analisis_activo_id"] not in ids:
                raise ValueError("El análisis activo no existe en el historial.")
            if any(r.get("analisis_id") is not None and r["analisis_id"] not in ids for r in datos.get("valores", [])):
                raise ValueError("Un registro está vinculado a un análisis inexistente.")
            if type(datos.get("filtrar_analisis", False)) is not bool:
                raise ValueError("El filtro de historial guardado no es válido.")
            if "resultado_visible" in datos:
                visible = recuperar_resultado(datos["resultado_visible"])
                if (not isinstance(visible, dict) or not isinstance(visible.get("fuente"), str)
                        or not isinstance(visible.get("serie_df"), pd.DataFrame)
                        or not isinstance(visible.get("fila"), pd.DataFrame)
                        or not isinstance(visible.get("proyeccion"), dict)):
                    raise ValueError("El resultado visible guardado no es válido.")
        except (KeyError, TypeError, IndexError, AttributeError) as error:
            raise ValueError("El historial contiene una instantánea incompleta o inválida.") from error
        validar_comparacion(datos, historial)

    def restaurar_datos_sesion(self, datos: dict[str, Any] | None) -> None:
        self.validar_datos_sesion(datos)
        datos = deepcopy(datos or {})
        self.pila_deshacer.clear();self._estado_pila = None;self._resaltado_id = None  # nada de la sesión anterior se deshace aquí
        self._datos_sesion_adicionales = datos
        proyecto = datos.get("proyecto", {})
        self.nombre_proyecto.setText(proyecto.get("nombre_proyecto", ""))
        self.objeto_proyecto.setPlainText(proyecto.get("objeto", ""))
        self.responsable_tecnico.setText(proyecto.get("responsable_tecnico", ""))
        self.observacion_general.setPlainText(proyecto.get("observacion_general", ""))
        self.proyecciones = datos.get("proyecciones", [])
        self.valores = datos.get("valores", [])
        self.historial = datos.get("historial_analisis", [])
        self.fecha_objetivo_presupuesto = fo.periodo_iso(datos.get("fecha_objetivo_presupuesto"))
        self.excepciones_fecha = list(datos.get("excepciones_fecha") or [])
        bloque = datos.get('comparacion_historica',{})
        self._periodo_por_analisis = {};self._overrides = {};self._consultas_v1 = {}
        self._referencias_externas = deepcopy(bloque.get('referencias_externas', {})) if bloque.get('version') == 3 else {}
        if bloque.get('version') in (2, 3):
            self._periodo_por_analisis = {i:v['periodo'] for i,v in bloque['selecciones'].items()}
            self._overrides = {i:v['override'] for i,v in bloque['selecciones'].items()}
            self._consultas_v1 = dict(bloque.get('consulta_v1',{}))
        elif bloque.get('version') == 1:self._consultas_v1 = dict(bloque['periodo_por_analisis'])
        with QSignalBlocker(self.aplicar_global):self.aplicar_global.setChecked(bloque.get('global',False))
        self._preparar_comparacion_historica()
        self.analisis_activo_id = datos.get("analisis_activo_id")
        self.solo_analisis_activo.blockSignals(True)
        self.solo_analisis_activo.setChecked(datos.get("filtrar_analisis", False))
        self.solo_analisis_activo.blockSignals(False)
        self._refrescar_historial()
        self.contexto = datos.get("contexto")
        self._actualizar_estado_calculadora()
        self.restaurar_calculadora(datos.get("calculadora", {}))
        self._refrescar_tabla_proyecciones()
        self._refrescar_tabla_valores()
        self._salir_edicion();self._formulario_guardado = self._datos_calculadora()
        if self.valores:
            self._mostrar_resumen_activo()
        else:
            self.resultado.setHtml("<p>Sin cálculos de actualización en esta sesión.</p>")

    def restaurar_calculadora(self, formulario) -> None:
        self.tipo_componente.setCurrentText(formulario.get("tipo_componente", "Capítulo"))
        self.nombre_componente.setText(formulario.get("nombre_componente", ""))
        self.item.setText(formulario.get("item", ""))
        self._item_editado = bool(self.item.text())
        self.unidad.setCurrentIndex(max(0, self.unidad.findData(formulario.get("unidad"))))
        self.modalidad_importe.setCurrentIndex(self.modalidad_importe.findData(validar_modalidad(formulario)))
        self.cantidad.setValue(formulario.get("cantidad", 0))
        self.precio_base.setValue(formulario.get("precio_base", 0))
        self.anticipo.setValue(formulario.get("anticipo", 0))
        self.observacion.setPlainText(formulario.get("observacion", ""))

    # ------------------------------------------------------------------ API
    def montar_controles_seleccion(self, grupo_seleccion, grupo_parametros, boton_ejecutar) -> None:
        """Recibe el selector jerárquico, los parámetros y el botón de ejecución
        creados por la ventana principal y los ubica al inicio del módulo."""
        encabezado = QLabel("1. Selección ICOCIV y parámetros de proyección")
        encabezado.setObjectName("icociv_titulo_seccion")
        ayuda = QLabel(
            "Seleccione la serie siguiendo las opciones que aparecen en cada nivel y defina el periodo objetivo."
        )
        ayuda.setWordWrap(True)
        ayuda.setObjectName("ruta_dashboard")
        self._layout_seleccion.addWidget(encabezado)
        self._layout_seleccion.addWidget(ayuda)
        for grupo in (grupo_seleccion, grupo_parametros):
            formulario = grupo.layout()
            if isinstance(formulario, QFormLayout):
                formulario.setVerticalSpacing(tokens.ESPACIO_2)
                formulario.setHorizontalSpacing(tokens.ESPACIO_4)
        grupo_parametros.layout().setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        grupo_parametros.layout().setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.fila_seleccion = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.fila_seleccion.setSpacing(tokens.ESPACIO_5)
        self.fila_seleccion.addWidget(grupo_seleccion, 3, Qt.AlignmentFlag.AlignTop)
        parametros = QWidget()
        layout_parametros = QVBoxLayout(parametros)
        layout_parametros.setContentsMargins(0, 0, 0, 0)
        layout_parametros.setSpacing(tokens.ESPACIO_3)
        layout_parametros.addWidget(grupo_parametros)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(boton_ejecutar)
        layout_parametros.addLayout(fila)
        layout_parametros.addStretch()
        self.fila_seleccion.addWidget(parametros, 2)
        self._layout_seleccion.addLayout(self.fila_seleccion)
        self._ajustar_distribucion()

    def actualizar_contexto(self, resultado_ui: dict[str, Any] | None, registrar: bool = True) -> None:
        """Recibe el resultado actual; acumula una fila si ``registrar`` y es válida."""
        contexto = _extraer_contexto(resultado_ui) if resultado_ui else None
        self.contexto = contexto
        self.analisis_activo_id = None
        self._refrescar_historial()
        self._actualizar_estado_calculadora()
        if registrar and contexto and contexto.get("proyeccion_generada"):
            self._registrar_proyeccion(contexto)

    # ---------------------------------------------------------------- UI
    def _crear_interfaz(self) -> None:
        self.setObjectName("proyecciones_icociv")
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(tokens.ESPACIO_5, tokens.ESPACIO_5, tokens.ESPACIO_5, tokens.ESPACIO_5)
        layout.setSpacing(tokens.ESPACIO_4)

        titulo = QLabel("Proyecciones ICOCIV y actualización de valores")
        titulo.setObjectName("titulo_dashboard")
        subtitulo = QLabel(
            "Cada proyección válida se acumula abajo. La calculadora usa el índice base "
            "(último observado) y el índice proyectado por la aplicación; no usa ICCP."
        )
        subtitulo.setWordWrap(True)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        (self.aviso_legados_superior, self.lbl_legados_superior,
         self.boton_actualizar_legados_superior, self.boton_detalle_legados_superior) = self._crear_aviso_legados()
        layout.addWidget(self.aviso_legados_superior)
        layout.addWidget(self._grupo_proyecto())
        historial = QGroupBox("Historial de análisis de la sesión")
        historial_layout = QVBoxLayout(historial)
        self.selector_analisis = ComboBoxSinRueda()
        self.selector_analisis.setMinimumContentsLength(16)
        self.selector_analisis.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.selector_analisis.setAccessibleName("Análisis activo del historial")
        self.selector_analisis.currentIndexChanged.connect(self._solicitar_analisis)
        self.lbl_analisis = QLabel()
        self.lbl_analisis.setWordWrap(True)
        self.lbl_analisis.setObjectName("ruta_dashboard")
        historial_layout.addWidget(self.selector_analisis)
        historial_layout.addWidget(self.lbl_analisis)
        # Fase 4G: navegación Serie → Análisis (revisiones) → Actividades, por IDs.
        self.arbol_historial = QTreeWidget()
        self.arbol_historial.setHeaderLabels(["Serie / análisis / actividad", "Detalle"])
        self.arbol_historial.setAccessibleName("Historial agrupado por serie, análisis y actividades")
        self.arbol_historial.setRootIsDecorated(True)
        self.arbol_historial.setUniformRowHeights(True)
        self.arbol_historial.setMinimumHeight(tokens.ESPACIO_8 * 3)
        self.arbol_historial.setMaximumHeight(tokens.ESPACIO_8 * 6)
        self.arbol_historial.header().setStretchLastSection(True)
        self.arbol_historial.itemActivated.connect(self._activar_nodo_historial)
        self.arbol_historial.itemClicked.connect(self._activar_nodo_historial)
        # Entrega 1.1: el árbol de dos columnas se retira de la presentación; el
        # historial se navega con los dos desplegables (se montan al final de _crear_interfaz).
        self.arbol_historial.setVisible(False)
        self.selector_analisis.setVisible(False)
        self._layout_historial = historial_layout
        layout.addWidget(historial)

        # Contenedor donde la ventana principal monta el selector jerárquico,
        # los parámetros y el botón de ejecución (sección 1 del módulo).
        self.contenedor_seleccion = QWidget()
        self._layout_seleccion = QVBoxLayout(self.contenedor_seleccion)
        self._layout_seleccion.setContentsMargins(0, 0, 0, 0)
        self._layout_seleccion.setSpacing(tokens.ESPACIO_3)
        layout.addWidget(self.contenedor_seleccion)

        self.lbl_contexto = QLabel()
        self.lbl_contexto.setWordWrap(True)
        self.lbl_contexto.setObjectName("ruta_dashboard")
        contexto = QFrame()
        contexto.setObjectName("icociv_contexto")
        layout_contexto = QVBoxLayout(contexto)
        layout_contexto.setContentsMargins(tokens.ESPACIO_4, tokens.ESPACIO_3, tokens.ESPACIO_4, tokens.ESPACIO_3)
        etiqueta_contexto = QLabel("Contexto de la proyección")
        etiqueta_contexto.setObjectName("icociv_titulo_seccion")
        layout_contexto.addWidget(etiqueta_contexto)
        layout_contexto.addWidget(self.lbl_contexto)
        layout.addWidget(contexto)

        self.fila_calculo = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        self.fila_calculo.setSpacing(tokens.ESPACIO_4)
        self.fila_calculo.addWidget(self._grupo_calculadora(), 3)
        self.fila_calculo.addWidget(self._grupo_resultado(), 2)
        layout.addLayout(self.fila_calculo)
        layout.addWidget(self._grupo_tablas())
        layout.addStretch()

        # Historial superior: Ámbito ICOCIV → Proyección guardada (mismos controles 4G-B).
        for texto, control in (("Ámbito ICOCIV", self.selector_ambito), (None, self.lbl_contexto_ambito),
                               ("Proyección guardada", self.selector_analisis_valores), (None, self.lbl_filtro_valores)):
            if texto:
                rotulo = QLabel(texto);rotulo.setObjectName("icociv_titulo_seccion");rotulo.setBuddy(control)
                if control is self.selector_analisis_valores:
                    # Fase 4I-B: «Ver gráfica» a la derecha del rótulo, en su misma fila.
                    fila = QHBoxLayout();fila.addWidget(rotulo);fila.addStretch();fila.addWidget(self.boton_grafica_superior)
                    self._layout_historial.insertLayout(self._layout_historial.count()-1, fila)
                else:
                    self._layout_historial.insertWidget(self._layout_historial.count()-1, rotulo)
            self._layout_historial.insertWidget(self._layout_historial.count()-1, control)
        for control in (self.selector_ambito, self.selector_analisis_valores):
            control.setMaximumWidth(16777215);control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenido)
        layout_principal.addWidget(scroll)
        self._refrescar_historial()

    def _grupo_proyecto(self) -> QGroupBox:
        grupo = QGroupBox()
        layout = QVBoxLayout(grupo)
        boton = QPushButton("Datos generales del proyecto")
        boton.setObjectName("boton_secundario")
        boton.setToolTip("Plegar o desplegar los datos comunes del proyecto sin borrarlos.")
        boton.setCheckable(True)
        contenido = QWidget()
        grid = QGridLayout(contenido)
        self.nombre_proyecto = QLineEdit()
        self.responsable_tecnico = QLineEdit()
        self.objeto_proyecto = QTextEdit()
        self.observacion_general = QTextEdit()
        for texto in (self.objeto_proyecto, self.observacion_general):
            texto.setMaximumHeight(tokens.ESPACIO_8 + tokens.ESPACIO_6)
        campos = (("Nombre del proyecto", self.nombre_proyecto), ("Responsable técnico", self.responsable_tecnico),
                  ("Objeto / descripción", self.objeto_proyecto), ("Observación general", self.observacion_general))
        for i, (nombre, campo) in enumerate(campos):
            etiqueta = QLabel(nombre)
            etiqueta.setBuddy(campo)
            grid.addWidget(etiqueta, (i // 2) * 2, i % 2)
            grid.addWidget(campo, (i // 2) * 2 + 1, i % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        boton.toggled.connect(contenido.setVisible)
        boton.setChecked(True)
        layout.addWidget(boton)
        layout.addWidget(contenido)
        return grupo

    def resizeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        super().resizeEvent(event)
        self._ajustar_distribucion()

    def _ajustar_distribucion(self) -> None:
        if hasattr(self,'fila_filtro'):
            disponible = self.fila_filtro.parentWidget().width()-2*tokens.ESPACIO_5
            necesario = self.selector_ambito_inferior.sizeHint().width()+self.selector_proyeccion_inferior.sizeHint().width()+self.fila_filtro.spacing()
            self.fila_filtro.setDirection(QBoxLayout.LeftToRight if disponible>=necesario else QBoxLayout.TopToBottom)
        # Umbral aprobado (856 px) intacto; en el modo compacto de la ventana (pantalla dividida) la
        # selección y la calculadora van siempre en una columna para no desbordar en horizontal.
        ancho_doble = tokens.VENTANA_MIN_WIDTH - tokens.NAVEGACION_ANCHO_EXPANDIDO
        direccion = (
            QBoxLayout.Direction.LeftToRight
            if self.width() >= ancho_doble and not self.modo_compacto
            else QBoxLayout.Direction.TopToBottom
        )
        for nombre in ("fila_seleccion", "fila_calculo"):
            fila = getattr(self, nombre, None)
            if fila is not None:
                fila.setDirection(direccion)
        self._evaluar_columnas_calculadora()

    def _grupo_calculadora(self) -> QGroupBox:
        grupo = QGroupBox("Calculadora de actualización con proyección ICOCIV")
        grid = QGridLayout(grupo)
        grid.setHorizontalSpacing(tokens.ESPACIO_4)
        grid.setVerticalSpacing(tokens.ESPACIO_2)
        self.tipo_componente = _SelectorComponente()
        for tipo in TIPOS_COMPONENTE:
            self.tipo_componente.addItem(NOMBRES_COMPONENTE.get(tipo, tipo), tipo)
        self.nombre_componente = QLineEdit()
        self.lbl_nombre_componente = QLabel(TIPOS_COMPONENTE["Capítulo"])
        self.lbl_nombre_componente.setBuddy(self.nombre_componente)
        self.nombre_componente.setToolTip("Nombre presupuestal libre; no modifica ni selecciona series ICOCIV.")
        self.tipo_componente.currentTextChanged.connect(self._actualizar_etiqueta_componente)
        # Fase 4I-I: cada celda se registra con su posición a dos columnas para poder pasarla a una sola
        # columna en media pantalla reutilizando los MISMOS widgets (sin recrear ni reconectar nada).
        self._grid_calculadora = grid;self._celdas_calculadora = []
        celda = lambda w, fila, col, ancho=1: self._celdas_calculadora.append((w, fila, col, ancho))
        celda(QLabel("Tipo de componente"), 0, 0)
        celda(self.tipo_componente, 1, 0)
        celda(self.lbl_nombre_componente, 0, 1)
        celda(self.nombre_componente, 1, 1)
        self.item = QLineEdit()
        self.item.textEdited.connect(self._marcar_item_editado)
        self.unidad = ComboBoxSinRueda()
        self.unidad.addItem("Sin selección", None)
        for unidad in UNIDADES_INGENIERIA:
            self.unidad.addItem(unidad, unidad)
        self.modalidad_importe = ComboBoxSinRueda()
        for modo,titulo in OPCIONES_INGRESO.items():self.modalidad_importe.addItem(titulo,modo)
        self.modalidad_importe.setAccessibleName("Interpretación de P y A")
        self.modalidad_importe.setToolTip(AVISO_INTERPRETACION)
        self.modalidad_importe.setMinimumContentsLength(16)
        self.modalidad_importe.setMaximumWidth(360)
        self.modalidad_importe.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cantidad = NumeroICOCIV(0, 1_000_000_000, 4)
        # Fase 4I-A: P y A conservan hasta 4 decimales internos (la vista sigue al peso).
        self.precio_base = NumeroICOCIV(0, 1_000_000_000_000_000, 4)
        self.anticipo = NumeroICOCIV(0, 1_000_000_000_000_000, 4)
        self.precio_base.lineEdit().setPlaceholderText("Ej.: 423,467.54")
        self.anticipo.lineEdit().setPlaceholderText("Ej.: 0")
        self.observacion = QTextEdit()
        self.observacion.setMaximumHeight(64)
        campos = [
            ("Nombre del ítem o insumo", self.item, "Insumo, actividad, APU o componente contractual."),
            ("Unidad", self.unidad, "Unidad de medida del ítem."),
            ("Cantidad", self.cantidad, "Cantidad presupuestal positiva; necesaria para mostrar importes unitarios y totales."),
            ("Precio o valor base P", self.precio_base, "Valor actual que se desea proyectar. Al pegar, la coma agrupa miles («1,250» = 1250) y el punto es decimal («1.250» = 1.25)."),
            ("Anticipo amortizado A", self.anticipo, "Anticipo ya amortizado; si no aplica, deje en cero."),
            ("Observación técnica", self.observacion, "Justificación o criterio técnico del cálculo."),
        ]
        pregunta=QLabel(PREGUNTA_INGRESO);pregunta.setWordWrap(True)
        self.aviso_interpretacion=QLabel(AVISO_INTERPRETACION);self.aviso_interpretacion.setWordWrap(True)
        posiciones = ((2, 0, 2), (4, 0, 1), (4, 1, 1), (6, 0, 1), (6, 1, 1), (11, 0, 2))
        for (etiqueta, widget, ayuda), (fila, columna, ancho) in zip(campos, posiciones):
            celda(_etiqueta_ayuda(etiqueta, ayuda), fila, columna, ancho)
            celda(_ayuda(widget, ayuda), fila + 1, columna, ancho)
        celda(pregunta, 8, 0, 2);celda(self.modalidad_importe, 9, 0, 2);celda(self.aviso_interpretacion, 10, 0, 2)
        for widget in (self.cantidad, self.precio_base, self.anticipo):
            widget.setAlignment(Qt.AlignmentFlag.AlignRight)
            widget.setMaximumWidth(tokens.PANEL_MAX_WIDTH)
        self.unidad.setMaximumWidth(tokens.PANEL_MAX_WIDTH)
        for widget in (self.unidad, self.cantidad, self.precio_base, self.anticipo):
            fila = widget.parentWidget().layout()  # crece hasta su máximo y queda alineado a la izquierda
            fila.setStretch(0, 100);fila.addStretch(1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        contenedor_acciones = QWidget();acciones = QHBoxLayout(contenedor_acciones)
        acciones.setContentsMargins(0, 0, 0, 0);acciones.setSpacing(tokens.ESPACIO_2)
        acciones.addStretch()
        self.boton_limpiar = QPushButton("Limpiar")
        self.boton_limpiar.setObjectName("boton_secundario")
        self.boton_limpiar.clicked.connect(self._limpiar_calculadora)
        self.boton_calcular = QPushButton("Calcular y agregar a la tabla")
        self.boton_calcular.clicked.connect(self._calcular)
        acciones.addWidget(self.boton_limpiar)
        acciones.addWidget(self.boton_calcular)
        celda(contenedor_acciones, 13, 0, 2)
        self.lbl_calculo_activo = QLabel("Para nuevos cálculos: Ninguna proyección activa")
        self.lbl_calculo_activo.setObjectName("estado_dashboard");self.lbl_calculo_activo.setWordWrap(True)
        self.lbl_calculo_activo.setAccessibleName("Proyección activa para nuevos cálculos")
        celda(self.lbl_calculo_activo, 14, 0, 2)
        self._calculadora_una_columna = None
        self._colocar_calculadora(False)
        self._grupo_calc = grupo;grupo.installEventFilter(self)
        return grupo

    def _ancho_columna_calculadora(self) -> int:
        """Ancho cómodo de una columna: la etiqueta más ancha de una celda emparejada o un importe P/A
        completo con separadores y 4 decimales. Se mide con la fuente real (sigue DPI y tema)."""
        pares = [w for w, _f, _c, ancho in self._celdas_calculadora if ancho == 1]
        importe = self.precio_base.fontMetrics().horizontalAdvance("999,999,999,999,999.9999") + 2 * tokens.ESPACIO_5
        return max(importe, *(w.sizeHint().width() for w in pares))

    def _colocar_calculadora(self, una_columna: bool) -> None:
        """Dos columnas (diseño aprobado) o una sola columna en orden de lectura. Mueve los widgets existentes."""
        if una_columna == self._calculadora_una_columna:
            return
        self._calculadora_una_columna = una_columna
        grid = self._grid_calculadora
        for w, *_ in self._celdas_calculadora:
            grid.removeWidget(w)
        if una_columna:
            # Orden de lectura: cada par (etiqueta, campo) de la izquierda y luego el de la derecha, banda a banda.
            orden = sorted(self._celdas_calculadora, key=lambda c: (c[1] - c[1] % 2 if c[1] < 8 else c[1], c[2], c[1]))
            for fila, (w, *_r) in enumerate(orden):
                grid.addWidget(w, fila, 0, 1, 2)
        else:
            for w, fila, col, ancho in self._celdas_calculadora:
                grid.addWidget(w, fila, col, 1, ancho)

    def _evaluar_columnas_calculadora(self) -> None:
        """Una columna en pantalla dividida (modo compacto de la ventana, con su histéresis 1180/1260 px) o
        cuando dos columnas no caben con la medida real de la fuente; si no, el diseño aprobado de dos."""
        grupo = getattr(self, "_grupo_calc", None)
        if grupo is None:
            return
        disponible = grupo.contentsRect().width() - self._grid_calculadora.horizontalSpacing()
        necesario = 2 * self._ancho_columna_calculadora()
        holgura = 24 if self._calculadora_una_columna else 0  # sin parpadeo cerca del límite
        self._colocar_calculadora(self.modo_compacto or disponible < necesario + holgura)

    def eventFilter(self, objeto, evento):  # noqa: N802 - firma Qt
        if objeto is getattr(self, "_grupo_calc", None) and evento.type() == QEvent.Type.Resize:
            self._evaluar_columnas_calculadora()
        return super().eventFilter(objeto, evento)

    def _preseleccionar_componente(self) -> None:
        ruta = [r for r in (self.contexto or {}).get("ruta", []) if r.get("nivel") != "Tabla ICOCIV"]
        nivel = ruta[-1].get("nivel", "").lower() if ruta else ""
        tipo = "Otro"
        for fragmento, opcion in (("insumo", "Insumo"), ("ítem", "Ítem"), ("item", "Ítem"),
                                 ("capít", "Capítulo"), ("capit", "Capítulo"), ("tipolog", "Tipología"),
                                 ("subclas", "Subclase de obra"), ("grupo", "Grupo de obra")):
            if fragmento in nivel:
                tipo = opcion
                break
        self.tipo_componente.setCurrentText(tipo)

    def _actualizar_etiqueta_componente(self, tipo: str) -> None:
        self.lbl_nombre_componente.setText(TIPOS_COMPONENTE.get(self.tipo_componente.currentData(), "Nombre del componente"))

    def _grupo_resultado(self) -> QGroupBox:
        grupo = QGroupBox("Resultado de actualización ICOCIV proyectada")
        layout = QVBoxLayout(grupo)
        self.resultado = QTextBrowser()
        self.resultado.setOpenLinks(False)
        self.resultado.anchorClicked.connect(self._editar_interpretacion)
        self.resultado.setMinimumHeight(180)
        self.resultado.setHtml(
            "<p>Ejecute una proyección y calcule para ver P, A, base, I0, I, factor, R y el valor proyectado.</p>"
        )
        layout.addWidget(self.resultado)
        return grupo

    def _grupo_tablas(self) -> QGroupBox:
        grupo = QGroupBox("Tablas acumulativas de la sesión")
        layout = QVBoxLayout(grupo)

        layout.addWidget(QLabel("1. Proyecciones ICOCIV realizadas"))
        self.tabla_proyecciones = TablaCopiable()
        self.tabla_proyecciones.setModel(self.modelo_proyecciones)
        self.tabla_proyecciones.setAlternatingRowColors(True)
        self.tabla_proyecciones.setMinimumHeight(150)
        self._configurar_tabla(self.tabla_proyecciones, COLUMNAS_PROYECCIONES)
        layout.addWidget(self.tabla_proyecciones, 1)
        self.sin_proyecciones = QLabel("Sin proyecciones registradas. Seleccione una serie y ejecute la proyección.")
        self.sin_proyecciones.setWordWrap(True)
        layout.addWidget(self.sin_proyecciones)
        ayuda_tabla = QLabel("Desplace la tabla horizontalmente para consultar todas las columnas. Ver detalle muestra el registro completo.")
        ayuda_tabla.setWordWrap(True)
        ayuda_tabla.setObjectName("ruta_dashboard")
        layout.addWidget(ayuda_tabla)

        layout.addWidget(self._grupo_comparacion_historica())
        layout.addWidget(QLabel("2. Valores proyectados ICOCIV (calculadora)"))
        # Fase 4G-B: Ámbito ICOCIV → Proyección (consulta) y casilla de filtro.
        self.selector_ambito = _SelectorAnalisisCompacto()
        self.selector_ambito.setAccessibleName('Ámbito ICOCIV consultado')
        self.selector_ambito.setToolTip('Categoría jerárquica real o serie exacta. Solo cambia la consulta; no activa análisis ni modifica la calculadora.')
        self.selector_ambito.setMinimumContentsLength(16)
        self.selector_ambito.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.selector_ambito.currentIndexChanged.connect(self._cambiar_ambito)
        self.lbl_contexto_ambito = QLabel();self.lbl_contexto_ambito.setObjectName("ruta_dashboard");self.lbl_contexto_ambito.setWordWrap(True)
        self.solo_analisis_activo = QCheckBox("Mostrar solo registros de la selección")
        self.solo_analisis_activo.toggled.connect(self._refrescar_tabla_valores)
        self.lbl_filtro_valores = QLabel()
        self.lbl_filtro_valores.setWordWrap(True)
        self.lbl_filtro_valores.setObjectName("ruta_dashboard")
        self.selector_analisis_valores = _SelectorAnalisisCompacto()
        self.selector_analisis_valores.setAccessibleName('Proyección consultada del ámbito')
        self.selector_analisis_valores.setMinimumContentsLength(16)
        self.selector_analisis_valores.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.selector_analisis_valores.currentIndexChanged.connect(self._solicitar_analisis)
        layout.addWidget(self.lbl_contexto_ambito)  # se traslada al historial superior al final de _crear_interfaz
        layout.addWidget(self.lbl_filtro_valores)
        # Fase 4I-A: historial INFERIOR junto a la tabla; dos instancias visuales de la misma consulta.
        # Cada cambio se delega al control superior (fuente única) y _refrescar_controles_consulta
        # vuelve a copiar opciones y selección con QSignalBlocker, sin ciclos.
        self.selector_ambito_inferior = _SelectorAnalisisCompacto()
        self.selector_ambito_inferior.setAccessibleName('Ámbito ICOCIV consultado (junto a la tabla)')
        self.selector_proyeccion_inferior = _SelectorAnalisisCompacto()
        self.selector_proyeccion_inferior.setAccessibleName('Proyección consultada del ámbito (junto a la tabla)')
        self.selector_ambito_inferior.currentIndexChanged.connect(self.selector_ambito.setCurrentIndex)
        self.selector_proyeccion_inferior.currentIndexChanged.connect(self.selector_analisis_valores.setCurrentIndex)
        # Fase 4I-A V4: «Ver gráfica de la proyección» bajo ambos selectores de proyección.
        self.boton_grafica_superior = QPushButton("Ver gráfica")
        self.boton_grafica_inferior = QPushButton("Ver gráfica")
        for boton in (self.boton_grafica_superior, self.boton_grafica_inferior):
            boton.setObjectName("boton_compacto")
            boton.setAccessibleName("Ver en Resultados la gráfica guardada de la proyección seleccionada")
            boton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
            boton.clicked.connect(self._solicitar_grafica)
        self._colorear_icono_grafica()
        rotulo_historial = QLabel("Historial de proyecciones (acceso rápido a la misma selección)")
        rotulo_historial.setObjectName("ruta_dashboard");layout.addWidget(rotulo_historial)
        self.fila_filtro = QBoxLayout(QBoxLayout.LeftToRight)
        for texto, control in (("Ámbito ICOCIV", self.selector_ambito_inferior), ("Proyección guardada", self.selector_proyeccion_inferior)):
            control.setMinimumContentsLength(16)
            control.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            control.setMaximumWidth(16777215);control.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            caja = QWidget();columna = QVBoxLayout(caja);columna.setContentsMargins(0, 0, 0, 0);columna.setSpacing(2)
            rotulo = QLabel(texto);rotulo.setObjectName("icociv_titulo_seccion");rotulo.setBuddy(control)
            columna.addWidget(rotulo);columna.addWidget(control);self.fila_filtro.addWidget(caja, 1, Qt.AlignTop)
        layout.addLayout(self.fila_filtro)
        self.lbl_filtro_inferior = QLabel();self.lbl_filtro_inferior.setWordWrap(True);self.lbl_filtro_inferior.setObjectName("ruta_dashboard")
        fila_casilla = QHBoxLayout();fila_casilla.addWidget(self.solo_analisis_activo);fila_casilla.addWidget(self.lbl_filtro_inferior,1)
        layout.addLayout(fila_casilla)
        # Fase 4I-D: aviso persistente de registros con el criterio anterior + conversión por lote.
        self.aviso_legados, self.lbl_legados, self.boton_actualizar_legados, self.boton_detalle_legados = self._crear_aviso_legados()
        layout.addWidget(self.aviso_legados)
        # Fase 4I-A: Deshacer/Rehacer visibles sobre la tabla (mover y editar celdas).
        self.boton_deshacer = QPushButton("↶ Deshacer");self.boton_rehacer = QPushButton("↷ Rehacer")
        for boton, nombre, accion in ((self.boton_deshacer, "Deshacer la última acción del presupuesto", self.pila_deshacer.undo),
                                      (self.boton_rehacer, "Rehacer la acción deshecha del presupuesto", self.pila_deshacer.redo)):
            boton.setObjectName("boton_compacto");boton.setAccessibleName(nombre);boton.clicked.connect(accion)
            boton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        self.aviso_tabla = QLabel();self.aviso_tabla.setObjectName("estado_dashboard");self.aviso_tabla.setWordWrap(True)
        self.aviso_tabla.setAccessibleName("Aviso de edición de la tabla");self.aviso_tabla.hide()
        fila_deshacer = QHBoxLayout();fila_deshacer.addWidget(self.boton_deshacer);fila_deshacer.addWidget(self.boton_rehacer)
        # Fase 4I-B: una sola barra: Deshacer/Rehacer a la izquierda y «Ver gráfica» a la derecha.
        fila_deshacer.addWidget(self.aviso_tabla, 1);fila_deshacer.addStretch();fila_deshacer.addWidget(self.boton_grafica_inferior);layout.addLayout(fila_deshacer)
        # Atajos limitados al bloque de tablas: un editor de texto abierto conserva su propio Ctrl+Z.
        for secuencia, accion in ((QKeySequence.StandardKey.Undo, self.pila_deshacer.undo),
                                  (QKeySequence.StandardKey.Redo, self.pila_deshacer.redo),
                                  ("Ctrl+Shift+Z", self.pila_deshacer.redo)):
            atajo = QShortcut(QKeySequence(secuencia), grupo);atajo.setContext(Qt.WidgetWithChildrenShortcut)
            atajo.activated.connect(accion)
        for senal in (self.pila_deshacer.indexChanged, self.pila_deshacer.canUndoChanged, self.pila_deshacer.canRedoChanged):
            senal.connect(self._actualizar_botones_deshacer)
        self._actualizar_botones_deshacer()
        self.tabla_valores = TablaCopiable()
        self.tabla_valores.setModel(self.modelo_valores)
        self.tabla_valores.setAlternatingRowColors(True)
        self.tabla_valores.setMinimumHeight(150)
        self._configurar_tabla(self.tabla_valores, COLUMNAS_VALORES)
        self.tabla_valores.itemDelegate().widget_icociv = self
        self.tabla_valores.horizontalHeader().setMinimumHeight(54)
        # Fase 4I: doble clic / F2 editan entradas; arrastrar el número de fila reordena el presupuesto.
        self.tabla_valores.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        cabecera_filas = self.tabla_valores.verticalHeader()
        cabecera_filas.setSectionsMovable(True)
        cabecera_filas.setToolTip("Arrastre el número de fila para reordenar el presupuesto.")
        cabecera_filas.sectionMoved.connect(self._fila_arrastrada)
        cabecera_filas.sectionPressed.connect(self._quitar_resaltado)
        self.tabla_valores.pressed.connect(self._quitar_resaltado)
        self.tabla_valores.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabla_valores.customContextMenuRequested.connect(self._menu_tabla_valores)
        layout.addWidget(self.tabla_valores, 1)
        self.lbl_insercion = QLabel();self.lbl_insercion.setObjectName("estado_dashboard");self.lbl_insercion.setWordWrap(True)
        self.boton_cancelar_insercion = QPushButton("Cancelar inserción");self.boton_cancelar_insercion.setObjectName("boton_secundario")
        self.boton_cancelar_insercion.clicked.connect(self.cancelar_insercion)
        fila_insercion = QHBoxLayout();fila_insercion.addWidget(self.lbl_insercion,1);fila_insercion.addWidget(self.boton_cancelar_insercion)
        layout.addLayout(fila_insercion);self.lbl_insercion.hide();self.boton_cancelar_insercion.hide()
        self.sin_valores = QLabel("Sin valores proyectados. Complete la calculadora y agregue un registro.")
        self.sin_valores.setWordWrap(True)
        layout.addWidget(self.sin_valores)
        self.barra=BarraAccionesTablas(self,[(self.tabla_proyecciones,'Proyecciones ICOCIV realizadas'),(self.tabla_valores,'Valores proyectados ICOCIV (calculadora)')],
            lambda i:len(self.proyecciones if i==0 else self.valores),lambda:bool(self.proyecciones or self.valores or self.historial),
            lambda:self._accion_tabla('detalle'),lambda:self._accion_tabla('eliminar'),lambda:self._accion_tabla('todo'),self._exportar_formato,
            editar=lambda:self._accion_tabla('editar'))
        self.boton_exportar=self.barra.boton_exportar;layout.addWidget(self.barra)
        self.resumen_presupuestal = QLabel("Seleccione una sola fila para consultar su desglose presupuestal.")
        self.resumen_presupuestal.setTextFormat(Qt.PlainText)
        self.resumen_presupuestal.setWordWrap(True)
        layout.addWidget(self.resumen_presupuestal)
        self.tabla_valores.selectionModel().selectionChanged.connect(self._actualizar_resumen_presupuestal)
        self._actualizar_presentacion_tablas()
        return grupo

    def _grupo_comparacion_historica(self):
        grupo = QGroupBox('Referencia económica histórica');layout = QVBoxLayout(grupo)
        nota = QLabel('Cambiar la fecha de referencia recalcula los valores económicos mostrados; la proyección y el registro original de SAVIP se conservan.');nota.setWordWrap(True)
        layout.addWidget(nota)
        controles = QHBoxLayout()
        self.slider_comparacion = _SliderSinRueda(Qt.Horizontal)
        self.slider_comparacion.setAccessibleName('Mes histórico de referencia económica')
        self.slider_comparacion.setFocusPolicy(Qt.StrongFocus);self.slider_comparacion.setMinimumWidth(120)
        self.selector_referencia = ComboBoxSinRueda();self.selector_referencia.setEditable(True)
        self.selector_referencia.setInsertPolicy(QComboBox.NoInsert);self.selector_referencia.setMinimumWidth(150)
        self.selector_referencia.setAccessibleName('Periodo de referencia YYYY-MM')
        controles.addWidget(self.slider_comparacion,1);controles.addWidget(self.selector_referencia)
        layout.addLayout(controles)
        self.aplicar_global = QCheckBox('Aplicar fecha de referencia a todos los análisis ICOCIV')
        self.aplicar_global.setToolTip('Usará el mismo mes observado cuando exista en todas las series. No afecta Empalme. Marcar configura la próxima selección; desmarcar conserva las referencias ya aplicadas.')
        layout.addWidget(self.aplicar_global)
        self.lbl_ayuda_global = QLabel('El alcance global se aplica solo con la próxima selección explícita de un mes común. No afecta Empalme.')
        self.lbl_ayuda_global.setWordWrap(True);layout.addWidget(self.lbl_ayuda_global)
        # Fase 4G: acciones deliberadas; cargar un anexo nuevo nunca cambia la referencia por sí solo.
        fila_dane = QHBoxLayout()
        self.boton_ultimo_dane = QPushButton('Usar último índice DANE disponible')
        self.boton_ultimo_dane.setObjectName('boton_secundario')
        self.boton_ultimo_dane.setToolTip('Actualiza solo la referencia económica (I0 efectivo, factor y valores) con el último mes '
            'del anexo cargado para esta misma serie. No ejecuta una nueva proyección: el índice pronosticado queda congelado.')
        self.boton_ultimo_dane.clicked.connect(self.usar_ultimo_indice_dane)
        self.boton_restaurar_referencia = QPushButton('Restaurar referencia del análisis')
        self.boton_restaurar_referencia.setObjectName('boton_secundario')
        self.boton_restaurar_referencia.setToolTip('Vuelve exactamente al mes y al I0 originales del análisis guardado.')
        self.boton_restaurar_referencia.clicked.connect(self.restaurar_referencia_analisis)
        fila_dane.addWidget(self.boton_ultimo_dane);fila_dane.addWidget(self.boton_restaurar_referencia);fila_dane.addStretch()
        layout.addLayout(fila_dane)
        self.boton_aplicar_consulta = QPushButton('Aplicar explícitamente la fecha informativa de la sesión 4D')
        self.boton_aplicar_consulta.clicked.connect(lambda:self.seleccionar_referencia_historica(self._consultas_v1.get(self.analisis_activo_id)))
        layout.addWidget(self.boton_aplicar_consulta)
        self.lbl_referencia_comparacion = QLabel();self.lbl_objetivo_comparacion = QLabel();self.lbl_estado_comparacion = QLabel()
        for etiqueta in (self.lbl_referencia_comparacion,self.lbl_objetivo_comparacion,self.lbl_estado_comparacion):
            etiqueta.setWordWrap(True);etiqueta.setTextFormat(Qt.PlainText);layout.addWidget(etiqueta)
        # actionTriggered/sliderMoved representan interacción; setValue no autoriza repricing.
        self.slider_comparacion.actionTriggered.connect(lambda _:self._mover_comparacion(self.slider_comparacion.sliderPosition()))
        self.slider_comparacion.sliderPressed.connect(lambda:self._mover_comparacion(self.slider_comparacion.sliderPosition()))
        self.slider_comparacion.sliderMoved.connect(self._mover_comparacion)
        self.selector_referencia.activated.connect(lambda _:self._seleccionar_comparacion_manual())
        self.selector_referencia.lineEdit().editingFinished.connect(self._seleccionar_comparacion_manual)
        self.aplicar_global.toggled.connect(self._cambiar_alcance_global)
        return grupo

    def _preparar_comparacion_historica(self):
        self._fichas = fichas_historial(self.historial)
        self._ambitos = ambitos_disponibles(self._fichas)
        if self._ambito_consulta and not any(x['clave'] == self._ambito_consulta['clave'] for x in self._ambitos):
            self._ambito_consulta = None
        if self._proyeccion_consulta and not any(f['id'] == self._proyeccion_consulta for f in self._fichas):
            self._proyeccion_consulta = None
        self._analisis_comparacion = {a['id']:a for a in self.historial}
        self._historicos_comparacion = {};self._razones_comparacion = {}
        self._periodo_por_analisis = {k:v for k,v in self._periodo_por_analisis.items() if k in self._analisis_comparacion}
        self._overrides = {k:v for k,v in self._overrides.items() if k in self._analisis_comparacion}
        self._consultas_v1 = {k:v for k,v in self._consultas_v1.items() if k in self._analisis_comparacion}
        self._referencias_externas = {k:v for k,v in self._referencias_externas.items() if k in self._analisis_comparacion}
        self._periodo_original = {}
        for identificador, analisis in self._analisis_comparacion.items():
            # El mes predeterminado es siempre el último del snapshot; un anexo nuevo no lo desplaza.
            observados, original, razon = historico_efectivo(analisis, self._referencias_externas.get(identificador))
            self._historicos_comparacion[identificador] = observados;self._razones_comparacion[identificador] = razon
            self._periodo_original[identificador] = original
            if observados and identificador not in self._periodo_por_analisis:
                self._periodo_por_analisis[identificador] = original;self._overrides[identificador] = False
        if self.aplicar_global.isChecked() and not self._periodos_globales():
            with QSignalBlocker(self.aplicar_global):self.aplicar_global.setChecked(False)
            self.lbl_ayuda_global.setText('Modo global desactivado: la sesión cambió y no existe intersección verificable. Las referencias anteriores se conservan. ' + self._motivo_global())

    def _periodos_globales(self):
        historicos = list(self._historicos_comparacion.values())
        return sorted(set.intersection(*(set(h) for h in historicos))) if historicos and all(historicos) else []

    def _motivo_global(self):
        faltantes = [f"{a['nombre']} (ID {i})" for i,a in self._analisis_comparacion.items() if not self._historicos_comparacion.get(i)]
        return 'Análisis sin fuente verificable: ' + '; '.join(faltantes) if faltantes else 'Las series no comparten meses observados válidos.'

    def _cambiar_alcance_global(self, marcado):
        if marcado and not self._periodos_globales():
            with QSignalBlocker(self.aplicar_global):self.aplicar_global.setChecked(False)
            self._actualizar_controles_comparacion(False)
            self.lbl_estado_comparacion.setText('No puede aplicarse globalmente: falta fuente verificable o no hay meses comunes. Ningún escenario cambió.')
            self.lbl_ayuda_global.setText(self._motivo_global())
        else:
            self.lbl_ayuda_global.setText('El alcance global se aplica solo con la próxima selección explícita de un mes común. Desmarcar conserva las referencias aplicadas. No afecta Empalme.')
            self._actualizar_controles_comparacion(False)
        self.comparacion_cambiada.emit(self.resumen_comparacion_historica())

    def comparacion_registro(self, registro):
        identificador = registro.get('analisis_id')
        return comparar_registro(registro,self._analisis_comparacion.get(identificador),
            self._historicos_comparacion.get(identificador,{}),self._periodo_por_analisis.get(identificador))

    def escenario_registro(self, registro):
        identificador = registro.get('analisis_id')
        return escenario_registro(registro,self._analisis_comparacion.get(identificador),
            self._historicos_comparacion.get(identificador,{}),self._periodo_por_analisis.get(identificador),self._overrides.get(identificador,False))

    def fechas_registro(self, registro):
        efectivo, _ = self.escenario_registro(registro)
        return periodo_mensual(efectivo.get('periodo_base')) or '', periodo_mensual(registro.get('periodo_proyectado')) or ''

    def _actualizar_controles_comparacion(self, avisar=True):
        analisis = self.analisis_activo();identificador = self.analisis_activo_id
        historico = self._historicos_comparacion.get(identificador,{})
        self._periodos_slider = self._periodos_globales() if self.aplicar_global.isChecked() else list(historico)
        periodo = self._periodo_por_analisis.get(identificador)
        with QSignalBlocker(self.slider_comparacion), QSignalBlocker(self.selector_referencia):
            self.slider_comparacion.setRange(0,max(0,len(self._periodos_slider)-1));self.selector_referencia.clear()
            for fecha in self._periodos_slider:self.selector_referencia.addItem(fecha,fecha)
            pos = self._periodos_slider.index(periodo) if periodo in self._periodos_slider else -1
            self.slider_comparacion.setValue(max(0,pos));self.selector_referencia.setCurrentIndex(pos)
            self.slider_comparacion.setEnabled(bool(analisis and self._periodos_slider));self.selector_referencia.setEnabled(bool(analisis and self._periodos_slider))
        if hasattr(self, 'boton_ultimo_dane'):
            self.boton_ultimo_dane.setEnabled(bool(analisis and historico))
            self.boton_restaurar_referencia.setEnabled(bool(analisis and historico and (
                periodo != self._periodo_original.get(identificador) or self._overrides.get(identificador))))
        consulta = self._consultas_v1.get(identificador)
        self.boton_aplicar_consulta.setVisible(bool(consulta))
        self.boton_aplicar_consulta.setText(f'Aplicar explícitamente consulta 4D: {consulta}' if consulta else '')
        if not analisis or not historico:
            self.lbl_referencia_comparacion.setText('Referencia no disponible');self.lbl_objetivo_comparacion.setText('')
            self.lbl_estado_comparacion.setText('Sin análisis' if not analisis else self._razones_comparacion.get(identificador,''))
        else:
            contexto = analisis['contexto']; indice = numero_original(contexto.get('indice_proyectado'))
            vigente = fo.consulta_vigente(analisis)  # Fase 4I-P2: el panel muestra la consulta vigente
            estado = 'Referencia modificada' if self._overrides.get(identificador) else 'Referencia predeterminada'
            externa = self._referencias_externas.get(identificador, {}).get(periodo)
            origen = f" · Origen: anexo posterior {Path(externa['archivo']).name} (aplicado {externa['aplicado']})" if externa else ''
            self.lbl_referencia_comparacion.setText(f'{estado}: {periodo} · Índice observado: {numero_ui(historico.get(periodo))}{origen}')
            if vigente:
                self.lbl_objetivo_comparacion.setText(
                    f"Objetivo consultado: {vigente['periodo']} · H{vigente['horizonte']} · Índice proyectado: {numero_ui(vigente['indice'])}"
                    f" (ejecución original: {periodo_mensual(contexto.get('periodo_proyectado'))} · H{contexto.get('horizonte_solicitado')}"
                    f" · {numero_ui(indice)})")
            else:
                self.lbl_objetivo_comparacion.setText(f"Objetivo guardado: {periodo_mensual(contexto.get('periodo_proyectado'))} · Índice proyectado: {numero_ui(indice)}")
            avisos = []
            if not self._overrides.get(identificador) and contexto.get('indice_base') != historico.get(periodo):
                avisos.append('I0 original distinto del último observado: cifras registradas conservadas hasta intervención explícita.')
            if consulta:avisos.append(f'Consulta 4D anterior {consulta}: aún no aplicada a la economía.')
            if self.aplicar_global.isChecked() and periodo not in self._periodos_slider:avisos.append('Seleccione un mes común; la fecha actual no se aplicó globalmente.')
            self.lbl_estado_comparacion.setText(f"Análisis: {fo.nombre_vigente(analisis)} · ID {identificador}" + ('\n'+' '.join(avisos) if avisos else ''))
        if avisar:self.comparacion_cambiada.emit(self.resumen_comparacion_historica())

    def resumen_comparacion_historica(self):
        filas = []
        for r in self.valores:
            if r.get('analisis_id') == self.analisis_activo_id:
                e, estado = self.escenario_registro(r)
                filas.append(f"{r.get('item','')} · I0 efectivo {numero_ui(e.get('i0_icociv'))} · Factor {numero_ui(e.get('factor_icociv'))} · R {numero_ui(e.get('r_total'))} · Valor {numero_ui(e.get('valor_proyectado'))} · Diferencia {numero_ui(e.get('diferencia_porcentual'))}% · {estado}")
                filas.append(texto_desglose(r,e.get('valor_proyectado'),'Registro del análisis activo · escenario vigente'))
        return '\n'.join([e.text() for e in (self.lbl_referencia_comparacion,self.lbl_objetivo_comparacion,self.lbl_estado_comparacion) if e.text()] + filas)

    def _mover_comparacion(self, posicion):
        if 0 <= posicion < len(self._periodos_slider):self.seleccionar_referencia_historica(self._periodos_slider[posicion])

    def _seleccionar_comparacion_manual(self):
        self.seleccionar_referencia_historica(self.selector_referencia.currentText().strip())

    def seleccionar_referencia_historica(self, periodo):
        ids = list(self._analisis_comparacion) if self.aplicar_global.isChecked() else [self.analisis_activo_id]
        validos = self._periodos_globales() if self.aplicar_global.isChecked() else self._historicos_comparacion.get(self.analisis_activo_id,{})
        if periodo not in validos:
            self._actualizar_controles_comparacion(False)
            self.lbl_estado_comparacion.setText('Referencia no disponible: ese mes no está observado en todas las series afectadas. Se conserva el escenario anterior.')
            self.comparacion_cambiada.emit(self.resumen_comparacion_historica());return False
        nuevos = {}
        try:
            for identificador in ids:
                h = self._historicos_comparacion[identificador];a = self._analisis_comparacion[identificador]
                vigente = fo.consulta_vigente(a)  # Fase 4I-P2: índice de la consulta vigente, si existe
                indice = vigente['indice'] if vigente else numero_original(a['contexto'].get('indice_proyectado'))
                if indice is None or not math.isfinite((indice/h[periodo]-1)*100):
                    raise ValueError('La referencia produciría un factor o porcentaje no finito; ningún escenario cambió.')
                override = (periodo != self._periodo_original.get(identificador) or a['contexto'].get('indice_base') != h[periodo]
                    or any(r.get('i0_icociv') != h[periodo] for r in self.valores if r.get('analisis_id')==identificador and not comparar_registro(r,a,h,periodo)[3]))
                for r in self.valores:
                    if r.get('analisis_id') == identificador:escenario_registro(r,a,h,periodo,True)
                nuevos[identificador] = override
        except ValueError as error:
            self._actualizar_controles_comparacion(False);self.lbl_estado_comparacion.setText(str(error))
            self.comparacion_cambiada.emit(self.resumen_comparacion_historica());return False
        if all(self._periodo_por_analisis.get(i)==periodo and self._overrides.get(i,False)==o and i not in self._consultas_v1 for i,o in nuevos.items()):
            # Enter también activa el combo; la segunda señal conserva el aviso previo.
            with QSignalBlocker(self.selector_referencia):self.selector_referencia.setEditText(periodo)
            return True
        for identificador, override in nuevos.items():
            self._periodo_por_analisis[identificador] = periodo;self._overrides[identificador] = override;self._consultas_v1.pop(identificador,None)
        self._actualizar_columnas_comparativas()
        seleccion = _seleccion(self.tabla_valores)
        filas = [r for r in self.valores if r.get('analisis_id')==self.analisis_activo_id]
        if seleccion is not None:self._mostrar_resultado(self._valores_visibles[seleccion])
        elif filas:self._mostrar_resultado(filas[-1])
        self._actualizar_controles_comparacion()
        return True

    def _confirmar_actualizacion_dane(self, texto) -> bool:
        caja = QMessageBox(self);caja.setIcon(QMessageBox.Icon.Question)
        caja.setWindowTitle('Actualizar referencia económica');caja.setText(texto)
        aplicar = caja.addButton('Actualizar referencia', QMessageBox.ButtonRole.AcceptRole)
        caja.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole);caja.exec()
        return caja.clickedButton() is aplicar

    def usar_ultimo_indice_dane(self) -> bool:
        """Adopta, por acción expresa, el último índice del anexo cargado como I0 efectivo.

        Solo actualiza la referencia económica: el pronóstico, el ID y el
        snapshot no cambian. Con alcance global se verifica la correspondencia
        de TODAS las series antes de aplicar; si una falla, no cambia ninguna.
        """
        fuente = self.fuente_dane() if callable(self.fuente_dane) else None
        if not fuente:
            self.lbl_estado_comparacion.setText('No hay un anexo DANE cargado. Ningún escenario cambió.');return False
        tablas, periodos, ruta = fuente
        ids = list(self._analisis_comparacion) if self.aplicar_global.isChecked() else [self.analisis_activo_id]
        propuestas = {}
        try:
            for identificador in ids:
                a = self._analisis_comparacion[identificador]
                serie = localizar_en_fuente(a['resultado'], tablas, periodos)['serie']
                snapshot = historico_observado(a)[0]
                if not snapshot:raise ValueError(f"{a['nombre']}: el snapshot no tiene meses observados verificables.")
                original = next(reversed(snapshot));ultimo = next(reversed(serie))
                objetivo = periodo_mensual(a['contexto'].get('periodo_proyectado'))
                if ultimo < original:raise ValueError(f"{a['nombre']}: el anexo cargado termina en {ultimo}, antes que el análisis ({original}).")
                if ultimo == original:
                    revision = '' if serie[ultimo] == snapshot[original] else f' El DANE revisó {original} ({snapshot[original]!r} → {serie[ultimo]!r}); se conserva el valor original del análisis.'
                    raise ValueError(f"{a['nombre']}: no hay meses posteriores a {original}.{revision}")
                if not objetivo or ultimo >= objetivo:
                    raise ValueError(f"{a['nombre']}: el mes {ultimo} no es anterior al objetivo {objetivo}; no se compara.")
                propuestas[identificador] = (ultimo, serie[ultimo], localizar_en_fuente(a['resultado'], tablas, periodos))
            if len({p[0] for p in propuestas.values()}) != 1:
                raise ValueError('Las series terminan en meses distintos en el anexo cargado; no se aplica globalmente.')
        except (KeyError, ValueError) as error:
            self.lbl_estado_comparacion.setText(f'Referencia DANE no aplicada: {error} Ningún escenario cambió.')
            self.comparacion_cambiada.emit(self.resumen_comparacion_historica());return False
        periodo = next(iter(propuestas.values()))[0]
        lineas = []
        for identificador,(_,indice,_) in propuestas.items():
            a = self._analisis_comparacion[identificador];actual = self._periodo_por_analisis.get(identificador)
            lineas.append(f"{a['nombre']}: I0 {actual} = {numero_ui(self._historicos_comparacion[identificador].get(actual))} → {periodo} = {numero_ui(indice)}")
        texto = ('Actualizar referencia económica (no ejecuta una nueva proyección; el índice pronosticado se conserva):\n'
                 + '\n'.join(lineas) + '\nCambiarán I0 efectivo, factor, R, valores y diferencia de las actividades vinculadas.')
        if not self._confirmar_actualizacion_dane(texto):return False
        previas = deepcopy(self._referencias_externas)
        aplicado = datetime.now().isoformat(timespec='seconds')
        for identificador,(p,indice,origen) in propuestas.items():
            self._referencias_externas.setdefault(identificador,{})[p] = {
                'indice':float(indice),'archivo':str(ruta or ''),'tabla':origen['tabla'],
                'huella_fuente':origen['huella_fuente'],'aplicado':aplicado}
        self._preparar_comparacion_historica()
        if not self.seleccionar_referencia_historica(periodo):
            self._referencias_externas = previas;self._preparar_comparacion_historica();self._actualizar_controles_comparacion()
            return False
        return True

    def restaurar_referencia_analisis(self) -> None:
        """Vuelve exactamente al mes e I0 originales (sin recalcular: valores registrados)."""
        ids = list(self._analisis_comparacion) if self.aplicar_global.isChecked() else [self.analisis_activo_id]
        for identificador in ids:
            if self._periodo_original.get(identificador):
                self._periodo_por_analisis[identificador] = self._periodo_original[identificador]
                self._overrides[identificador] = False;self._consultas_v1.pop(identificador,None)
        self._actualizar_columnas_comparativas()
        filas = [r for r in self.valores if r.get('analisis_id')==self.analisis_activo_id]
        if filas:self._mostrar_resultado(filas[-1])
        self._actualizar_controles_comparacion()

    def _actualizar_columnas_comparativas(self):
        """Escenario vigente de las filas visibles y columnas de fecha (Fase 4G).

        Las fechas se evalúan sobre las filas visibles: si el filtro, el slider
        o una restauración cambian su unicidad, se reconstruye la tabla con 17,
        18 o 19 columnas y se vuelve a seleccionar la fila por su ID.
        """
        efectivos = [self.escenario_registro(r)[0] for r in self._valores_visibles]
        fechas = [self.fechas_registro(r) for r in self._valores_visibles]
        columnas, titulos = plan_columnas_valores(fechas)
        claves = [clave for clave, _ in columnas]
        df = _dataframe_valores(efectivos, columnas, fechas)
        modelo = self.modelo_valores
        seleccion = {i.row() for i in self.tabla_valores.selectionModel().selectedRows()} if self.tabla_valores.selectionModel() else set()
        previos = modelo.registros  # filas mostradas antes de este refresco
        ids = [previos[i].get('calculo_id') for i in sorted(seleccion) if i < len(previos)]
        modelo.registros = efectivos
        modelo.fechas_filas = fechas
        modelo.fechas_indices = titulos
        if claves != modelo.claves or len(df) != len(modelo._dataframe):
            modelo.claves = claves
            self._columnas_valores = columnas
            modelo.establecer_dataframe(df)
            for identificador in ids:
                fila = next((i for i, r in enumerate(self._valores_visibles) if r.get('calculo_id') == identificador), None)
                if fila is not None:self._seleccionar_fila_valores(fila)
        else:
            actual = modelo._dataframe
            for fila in range(len(df)):
                for col in range(len(claves)):actual.iat[fila,col] = df.iat[fila,col]
            if len(df):modelo.dataChanged.emit(modelo.index(0,0),modelo.index(len(df)-1,len(claves)-1))
            modelo.headerDataChanged.emit(Qt.Horizontal,0,len(claves)-1)
        self._actualizar_resumen_presupuestal()

    def _encabezados_indices(self, registros):
        """Compatibilidad: títulos de I0 e I según la regla de fechas de 4G."""
        return plan_columnas_valores([self.fechas_registro(r) for r in registros])[1]

    def _accion_tabla(self,accion):
        if self.barra.activa is None:return
        acciones={'detalle':(self._detalle_proyeccion,self._detalle_valor),
                  'editar':(lambda:None,self.editar_seleccionado),
                  'eliminar':(self._eliminar_proyeccion,self._eliminar_valor),
                  'todo':(self._eliminar_todas_proyecciones,self._eliminar_todos_valores)}
        acciones[accion][self.barra.activa]()

    def alcance_exportacion(self, tipo, serie=None, analisis_id=None):
        """Resuelve un alcance con el ámbito consultado (no con el filtro ni el activo)."""
        if tipo == 'serie' and serie is not None:
            ambito = next((x for x in self._ambitos if x['tipo'] == 'serie' and x['clave'] == serie), None)
        else:
            ambito = self._ambito_consulta
        alcance = resolver_alcance(tipo, self._fichas, self.valores, ambito, analisis_id)
        etiqueta = {'sesion': 'Toda la sesión', 'categoria': ambito['etiqueta'] if ambito else '',
                    'serie': ambito['etiqueta'] if ambito else '', 'proyeccion': ''}[tipo]
        if tipo == 'proyeccion':
            f = self._ficha(analisis_id);etiqueta = f"{f['serie_final']} · {etiqueta_proyeccion(f)}" if f else ''
        alcance['descripcion'] = etiqueta;alcance['contexto'] = ambito['contexto'] if ambito and tipo in ('categoria','serie') else ''
        return alcance

    def _elegir_alcance_exportacion(self, formato):
        """Diálogo «Alcance de exportación»: 4 opciones con recuentos reales; None = cancelar."""
        dialogo = QDialog(self);dialogo.setWindowTitle('Alcance de exportación');layout = QVBoxLayout(dialogo)
        layout.addWidget(QLabel(f"Exportar resultados ICOCIV · Formato: {formato.upper()}"))
        series = [x for x in self._ambitos if x['tipo'] == 'serie' and (not self._ambito_consulta or set(analisis_en_ambito(self._fichas, x)) & set(self.ids_ambito()))]
        combo_serie = ComboBoxSinRueda();combo_serie.setAccessibleName('Serie ICOCIV exacta')
        for x in series:combo_serie.addItem(x['etiqueta'], x['clave'])
        if self._ambito_consulta and self._ambito_consulta['tipo'] == 'serie':combo_serie.setCurrentIndex(max(0, combo_serie.findData(self._ambito_consulta['clave'])))
        combo_proy = ComboBoxSinRueda();combo_proy.setAccessibleName('Proyección específica')
        for f in self._fichas:
            if f['id'] in self.ids_ambito():combo_proy.addItem(f"{f['serie_final']} · {etiqueta_proyeccion(f)}", f['id'])
        combo_proy.setCurrentIndex(max(0, combo_proy.findData(self._proyeccion_consulta)))
        opciones = {};etiquetas = {}
        textos = {'sesion':'Toda la sesión','categoria':'Categoría jerárquica seleccionada','serie':'Serie ICOCIV específica','proyeccion':'Proyección específica'}
        for tipo in ('sesion','categoria','serie','proyeccion'):
            fila = QHBoxLayout();opciones[tipo] = QRadioButton(textos[tipo]);etiquetas[tipo] = QLabel()
            fila.addWidget(opciones[tipo]);fila.addStretch();fila.addWidget(etiquetas[tipo]);layout.addLayout(fila)
            if tipo == 'serie':layout.addWidget(combo_serie)
            if tipo == 'proyeccion':layout.addWidget(combo_proy)
        opciones['sesion'].setChecked(True)
        detalle = QLabel();detalle.setWordWrap(True);layout.addWidget(detalle)
        botones = QDialogButtonBox(QDialogButtonBox.Cancel);exportar = botones.addButton('Exportar', QDialogButtonBox.AcceptRole)
        botones.button(QDialogButtonBox.Cancel).setText('Cancelar');botones.button(QDialogButtonBox.Cancel).setObjectName('boton_secundario')
        botones.accepted.connect(dialogo.accept);botones.rejected.connect(dialogo.reject);layout.addWidget(botones)
        resultado = {}

        def calcular(tipo):
            try:
                return self.alcance_exportacion(tipo, combo_serie.currentData(), combo_proy.currentData())
            except ValueError:
                return None

        def actualizar(*_):
            for tipo in opciones:
                x = calcular(tipo)
                etiquetas[tipo].setText(f"{len(x['calculos'])} actividades · {len(x['analisis'])} análisis" if x else 'Sin selección válida')
                opciones[tipo].setEnabled(x is not None)
            tipo = next(t for t,o in opciones.items() if o.isChecked());x = calcular(tipo)
            resultado['alcance'] = x;exportar.setEnabled(x is not None)
            exportar.setText(f"Exportar {len(x['calculos'])} registros" if x else 'Exportar')
            detalle.setText(('Ámbito elegido: ' + (x['descripcion'] or 'Toda la sesión') + (f" · {x['contexto']}" if x['contexto'] else '')) if x else 'Elija una selección válida.')
        for o in opciones.values():o.toggled.connect(actualizar)
        combo_serie.currentIndexChanged.connect(actualizar);combo_proy.currentIndexChanged.connect(actualizar);actualizar()
        return resultado.get('alcance') if dialogo.exec() == QDialog.Accepted else None

    def _confirmar_avisos_alcance(self, alcance) -> bool:
        avisos = []
        if alcance['solo_tecnico']:
            avisos.append(f"0 actividades; {len(alcance['analisis'])} análisis técnicos. Se exportará solo la parte técnica, sin resultados económicos.")
        if alcance['posibles_duplicados']:
            avisos.append('Posible doble contabilización (misma actividad aparente en revisiones distintas): '
                          + '; '.join(', '.join(f"{x['calculo_id']} ({x['analisis_id']})" for x in g) for g in alcance['posibles_duplicados'])
                          + '. No se eliminará ningún registro.')
        legados = [r for r in self.valores if r.get('calculo_id') in set(alcance.get('calculos') or []) and es_factor_legado(r)]
        if legados:
            avisos.append(f"{len(legados)} actividades usan el factor anterior (I/I0 sin redondear): se exportarán fieles a su cálculo "
                          "guardado, distintas de la regla vigente. Para cifras homogéneas, cancele y use «Actualizar todas al criterio vigente».")
        if alcance['no_atribuibles']:
            avisos.append(f"{len(alcance['no_atribuibles'])} registros sin vínculo demostrable quedan fuera de este alcance (siguen en Toda la sesión): "
                          + ', '.join(str(x) for x in alcance['no_atribuibles']))
        if not avisos:return True
        caja = QMessageBox(self);caja.setIcon(QMessageBox.Icon.Warning);caja.setWindowTitle('Revisar alcance de exportación')
        caja.setText('\n\n'.join(avisos));seguir = caja.addButton('Exportar', QMessageBox.ButtonRole.AcceptRole)
        caja.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole);caja.exec()
        return caja.clickedButton() is seguir

    def _exportar_formato(self,formato):
        alcance = self._elegir_alcance_exportacion(formato)
        if alcance is None or not self._confirmar_avisos_alcance(alcance):return
        # Fase 4I-J: fechas objetivo mixtas o distintas de la del presupuesto, sobre lo que REALMENTE se exporta.
        incluidos = self.valores if not alcance or alcance['tipo'] == 'sesion' else [r for r in self.valores if r.get('calculo_id') in set(alcance['calculos'])]
        if not self.confirmar_exportacion(incluidos):return
        self._alcance_pendiente = alcance
        try:
            self._exportar_excel() if formato=='xlsx' else self._exportar_informe(formato)
        finally:
            self._alcance_pendiente = None

    @contextmanager
    def _preparando(self, texto):
        """Estado veraz junto a la tabla mientras se genera un archivo; se retira también si falla."""
        self.aviso_tabla.setText(texto + " La ventana responderá al terminar.");self.aviso_tabla.show();self.aviso_tabla.repaint()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            yield
        finally:
            QApplication.restoreOverrideCursor();self.aviso_tabla.hide()

    @contextmanager
    def _vista_exportacion(self, alcance):
        """Subconjunto por IDs para los tres exportadores; no copia ni modifica registros."""
        if not alcance or alcance['tipo'] == 'sesion':
            self._descripcion_alcance = None;yield;return
        guardado = (self.valores, self.historial, self.proyecciones)
        calculos, analisis = set(alcance['calculos']), set(alcance['analisis'])
        self.valores = [r for r in guardado[0] if r.get('calculo_id') in calculos]
        self.historial = [a for a in guardado[1] if a['id'] in analisis]
        self.proyecciones = [p for p in guardado[2] if p.get('analisis_id') in analisis]
        self._descripcion_alcance = (f"Alcance exportado: {dict(sesion='Toda la sesión',categoria='Categoría jerárquica',serie='Serie ICOCIV específica',proyeccion='Proyección específica')[alcance['tipo']]}"
            f" · {alcance['descripcion']}" + (f" ({alcance['contexto']})" if alcance.get('contexto') else '')
            + f" · {len(alcance['calculos'])} actividades · {len(alcance['analisis'])} análisis. No es el presupuesto completo de la sesión.")
        try:
            yield
        finally:
            self.valores, self.historial, self.proyecciones = guardado
            self._descripcion_alcance = None

    def _actualizar_presentacion_tablas(self) -> None:
        for tabla, estado in ((self.tabla_proyecciones, self.sin_proyecciones), (self.tabla_valores, self.sin_valores)):
            filas = tabla.model().rowCount()
            tabla.setVisible(filas > 0)
            estado.setVisible(filas == 0)
            alto = tabla.horizontalHeader().sizeHint().height() + min(max(filas, 1), 6) * tokens.ALTURA_CONTROL_COMPACTO
            tabla.setFixedHeight(alto + tabla.horizontalScrollBar().sizeHint().height() + tokens.ESPACIO_2)

    def _configurar_tabla(self, tabla: QTableView, columnas: list[tuple[str, str]]) -> None:
        numericas = {
            "numero", "cantidad", "precio_base", "anticipo", "base_ajustable", "indice_base",
            "indice_proyectado", "i0_icociv", "i_icociv", "factor", "r_total", "valor_proyectado",
            "diferencia", "horizonte", "horizonte_solicitado", "maximo_recomendado",
            "mae", "rmse", "mape", "smape", "mase",
            "indice_referencia", "variacion_comparativa", "base_unitaria", "base_total", "valor_unitario", "valor_total",
        }
        # El delegado consulta las claves físicas vigentes del modelo (17/18/19 columnas).
        tabla.setItemDelegate(_DelegadoTablaICOCIV({i for i, (clave, _) in enumerate(columnas) if clave in numericas}, tabla))
        tabla.setShowGrid(False)
        tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        tabla.verticalHeader().setDefaultSectionSize(tokens.ALTURA_CONTROL_COMPACTO)
        cabecera = tabla.horizontalHeader()
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        cabecera.setDefaultSectionSize(tokens.ESPACIO_7 * 5)
        tabla.model().modelReset.connect(lambda: self._ajustar_ancho_columnas(
            tabla, getattr(self, '_columnas_valores', columnas) if tabla is getattr(self, 'tabla_valores', None) else columnas))
        tabla.model().modelReset.connect(self._actualizar_presentacion_tablas)
        self._ajustar_ancho_columnas(tabla, columnas)

    @staticmethod
    def _ajustar_ancho_columnas(tabla: QTableView, columnas: list[tuple[str, str]]) -> None:
        cabecera = tabla.horizontalHeader()
        for i, (clave, titulo) in enumerate(columnas):
            ancho = max(tokens.ESPACIO_7 * 5, tabla.fontMetrics().horizontalAdvance(titulo) + tokens.ESPACIO_7)
            if clave in ('base_unitaria','base_total','valor_unitario','valor_total'):
                ancho = max(190,tabla.fontMetrics().horizontalAdvance(titulo.split(' unit')[0].split(' total')[0])+tokens.ESPACIO_7)
            if i == 0:
                ancho = tokens.ESPACIO_6 * 2
            elif i == 1:
                ancho = max(ancho, tokens.NAVEGACION_ANCHO_EXPANDIDO)
            cabecera.resizeSection(i, ancho)

    # ------------------------------------------------------------ acciones
    def _marcar_item_editado(self, texto: str) -> None:
        # Si el usuario borra todo el campo, se vuelve a permitir la sugerencia.
        self._item_editado = bool(texto.strip())

    def _sugerir_nombre_item(self) -> None:
        """Rellena el nombre del ítem con la serie final, sin pisar ediciones."""
        serie_final = (self.contexto or {}).get("serie_final", "") if self.contexto else ""
        self.item.setPlaceholderText(serie_final or "Nombre del ítem o insumo")
        if serie_final and not self._item_editado:
            self.item.setText(serie_final)

    def _limpiar_calculadora(self) -> None:
        # Nuevo cálculo: confirma antes de descartar datos sin guardar y sale del modo edición.
        if self._hay_borrador() and not self._confirmar_descartar_borrador('Limpiar'):return
        self._salir_edicion()
        self.tipo_componente.setCurrentIndex(0)
        self.nombre_componente.clear()
        self._item_editado = False
        self.item.clear()
        self.unidad.setCurrentIndex(0)
        self.modalidad_importe.setCurrentIndex(0)
        self.cantidad.setValue(0)
        self.precio_base.setValue(0)
        self.anticipo.setValue(0)
        self.observacion.clear()
        self._sugerir_nombre_item()
        self._formulario_guardado = self._datos_calculadora()

    def _calcular(self) -> None:
        contexto = self.contexto
        if not contexto or not contexto.get("proyeccion_generada"):
            QMessageBox.information(
                self,
                "Calculadora ICOCIV",
                "Ejecute primero una proyección válida antes de calcular la actualización.",
            )
            return
        unidad = self.unidad.currentData()
        nombre_item = self.item.text().strip() or contexto.get("serie_final", "")
        entrada = {
            "item": nombre_item,
            "unidad": str(unidad or ""),
            "cantidad": self.cantidad.value() or None,
            "precio_base": self.precio_base.value(),
            "anticipo_amortizado": self.anticipo.value(),
            "i0_icociv": contexto.get("indice_base"),
            "i_icociv": contexto.get("indice_proyectado"),
            "ruta_icociv": contexto.get("ruta_texto"),
            "modelo_proyeccion": contexto.get("modelo"),
            "horizonte": contexto.get("horizonte_solicitado"),
            "periodo_base": contexto.get("periodo_base"),
            "periodo_proyectado": contexto.get("periodo_proyectado"),
            "observacion_tecnica": self.observacion.toPlainText().strip(),
        }
        try:
            if not nombre_item:
                raise ValueError("Ingrese el nombre del ítem o insumo.")
            if not unidad:
                raise ValueError("Seleccione una unidad válida.")
            from .controles import confirmar_ingreso_presupuestal
            if (self._ambito_consulta and self.analisis_activo_id and self.analisis_activo_id not in self.ids_ambito()
                    and not self._confirmar_vinculo_fuera_de_ambito()):return
            if not confirmar_ingreso_presupuestal(self,self.modalidad_importe,entrada["cantidad"]):return
            resultado = calcular_actualizacion_icociv(entrada)
        except ValueError as exc:
            QMessageBox.warning(self, "Validación ICOCIV", str(exc))
            return
        resultado["modalidad_importe"] = self.modalidad_importe.currentData()
        if any(x is None for x in desglose_presupuestal(resultado,resultado.get("valor_proyectado")).values()):
            QMessageBox.warning(self,"Desglose no disponible","Los importes o su conversión por Cantidad exceden el rango numérico. Corrija las entradas antes de guardar.")
            return
        editado = next((r for r in self.valores if r.get('calculo_id') == self._edicion_calculo_id), None) if self._edicion_calculo_id else None
        if editado is not None and editado.get('analisis_id') != self.analisis_activo_id:
            QMessageBox.warning(self, "Editar", "La actividad en edición pertenece a otro análisis; active su proyección o use Limpiar.");return
        resultado["calculo_id"] = editado['calculo_id'] if editado is not None else uuid4().hex[:8]
        resultado["proyecto"] = self.nombre_proyecto.text()
        resultado["tipo_componente"] = self.tipo_componente.currentData()
        resultado["nombre_componente"] = self.nombre_componente.text()
        if self.analisis_activo_id:
            resultado["analisis_id"] = self.analisis_activo_id
        if editado is not None:
            # Edición expresa: reemplaza en su misma posición conservando el calculo_id.
            self.valores[self.valores.index(editado)] = resultado
            self._salir_edicion()
        else:
            posicion = self._posicion_insercion()
            if posicion is None:
                self.valores.append(resultado)
            else:
                self.valores.insert(posicion, resultado)
            self.cancelar_insercion()
        self._formulario_guardado = self._datos_calculadora()
        self._mostrar_resultado(resultado)
        self._refrescar_tabla_valores()
        fila=next((i for i,r in enumerate(self._valores_visibles) if r.get("calculo_id")==resultado["calculo_id"]),None)
        if fila is not None:
            self.tabla_valores.selectRow(fila)
            self.tabla_valores.scrollTo(self.modelo_valores.index(fila,8))

    # ------------------------------------------------------------ Fase 4I
    def _avisar_edicion(self, texto) -> None:
        # Fase 4I-A: aviso NO modal junto a la tabla (antes QMessageBox).
        self.aviso_tabla.setText(texto);self.aviso_tabla.show()
        QToolTip.showText(self.tabla_valores.mapToGlobal(self.tabla_valores.rect().topLeft()), texto, self.tabla_valores)

    def changeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        super().changeEvent(event)
        if event.type() == QEvent.Type.PaletteChange:
            self._colorear_icono_grafica()

    def _colorear_icono_grafica(self) -> None:
        """Fase 4I-B (auditoría better-ui): un solo SVG recoloreado por tema y estado.

        El SVG de navegación trae un trazo gris fijo que en tema claro casi no se veía.
        """
        from app_icociv.interfaz.tema.iconos import icono_para
        icono = icono_para(self, "nav_resultados")
        for boton in (getattr(self, "boton_grafica_superior", None), getattr(self, "boton_grafica_inferior", None)):
            if boton is not None:
                boton.setIcon(icono)

    def _actualizar_botones_grafica(self) -> None:
        """Habilitado solo con una proyección CONCRETA y con gráfica guardada; nunca elige una por su cuenta."""
        a = next((x for x in self.historial if x["id"] == self._proyeccion_consulta), None) if self._proyeccion_consulta else None
        disponible = a is not None and all(k in (a.get("resultado") or {}) for k in ("serie_df", "proyeccion"))
        if a is None:
            ayuda = ("Selecciona una proyección guardada concreta para ver su gráfica." if self.historial
                     else "No hay proyecciones guardadas en esta sesión.")
        elif not disponible:
            ayuda = "Gráfica no disponible para este registro: la sesión no guardó la serie o la proyección."
        else:
            ayuda = f"Abre en Resultados la gráfica guardada de {fo.nombre_vigente(a)} (no recalcula)."
        for boton in (getattr(self, "boton_grafica_superior", None), getattr(self, "boton_grafica_inferior", None)):
            if boton is not None:
                boton.setEnabled(disponible);boton.setToolTip(ayuda)

    def _solicitar_grafica(self) -> None:
        if self._proyeccion_consulta and any(a["id"] == self._proyeccion_consulta for a in self.historial):
            self.grafica_solicitada.emit(self._proyeccion_consulta)

    def _actualizar_botones_deshacer(self, *_):
        p = self.pila_deshacer
        self.boton_deshacer.setEnabled(p.canUndo());self.boton_rehacer.setEnabled(p.canRedo())
        self.boton_deshacer.setToolTip(f"Deshacer: {p.undoText()} (Ctrl+Z)" if p.canUndo() else "No hay acciones del presupuesto para deshacer")
        self.boton_rehacer.setToolTip(f"Rehacer: {p.redoText()} (Ctrl+Y)" if p.canRedo() else "No hay acciones del presupuesto para rehacer")

    def _registrar_cambio(self, texto, nuevos, calculo_id) -> None:
        """Una acción del usuario = un comando; ``push`` la aplica (redo)."""
        self.aviso_tabla.hide()
        self.pila_deshacer.push(_CambioPresupuesto(self, texto, self.valores, nuevos, calculo_id))

    def _aplicar_estado(self, valores, calculo_id) -> None:
        columna = max(0, self.tabla_valores.currentIndex().column())  # conserva la celda recién editada
        self.valores = list(valores)
        self._estado_pila = list(self.valores)
        self._refrescar_tabla_valores()
        self._refrescar_historial()
        self.comparacion_cambiada.emit(self.resumen_comparacion_historica())
        fila = next((i for i, r in enumerate(self._valores_visibles) if r.get("calculo_id") == calculo_id), None)
        if fila is not None:
            self._seleccionar_fila_valores(fila, columna);self.tabla_valores.scrollTo(self.modelo_valores.index(fila, columna))
        self._resaltar(calculo_id)

    def _resaltar(self, calculo_id) -> None:
        """Resalta la fila completa ~3.5 s o hasta un clic; reinicia el temporizador (uno solo)."""
        self._resaltado_id = calculo_id
        self._temporizador_resaltado.start()
        self.tabla_valores.viewport().update()

    def _quitar_resaltado(self, *_):
        if self._resaltado_id is not None:
            self._resaltado_id = None
            self.tabla_valores.viewport().update()


    def _editar_celda(self, fila, clave, valor) -> bool:
        """Edición directa de una entrada; recalcula con el servicio económico existente.

        Atómica: si la validación falla, el registro anterior queda intacto. Conserva
        calculo_id, analisis_id, posición, modalidad y componente; guarda el antes en
        ``historial_ediciones`` del propio registro.
        """
        if not 0 <= fila < len(self._valores_visibles):
            return False
        registro = self._valores_visibles[fila];campo = COLUMNAS_EDITABLES[clave]
        texto = str(valor).strip()
        try:
            if campo in ("cantidad", "precio_base", "anticipo_amortizado"):
                # Fase 4I-A: misma función y convenio que la calculadora.
                nuevo = float(normalizar_numero(texto))
                if not math.isfinite(nuevo):raise ValueError("Número no válido.")
                if campo == "cantidad" and nuevo <= 0:raise ValueError("La cantidad debe ser mayor que cero.")
            elif campo == "unidad":
                if texto not in UNIDADES_INGENIERIA:
                    raise ValueError("Unidad no reconocida. Use una de: " + ", ".join(UNIDADES_INGENIERIA))
                nuevo = texto
            else:
                if campo == "item" and not texto:raise ValueError("El nombre del ítem no puede quedar vacío.")
                nuevo = texto
            if registro.get(campo) == nuevo:
                return True
            cambios = {campo: nuevo}
            actualizado = self._recalcular_registro(registro, cambios)
        except ValueError as error:
            self._avisar_edicion(f"No se aplicó el cambio: {error} Se conserva el valor anterior.")
            return False
        titulo = dict(COLUMNAS_VALORES).get(clave, clave).split("\n")[0]
        self._registrar_cambio(f"editar {titulo} de «{registro.get('item', '')}»",
                               [actualizado if r is registro else r for r in self.valores], registro.get("calculo_id"))
        return True

    def _recalcular_registro(self, registro, cambios) -> dict:
        """Nuevo registro equivalente con ``cambios`` aplicados (servicio original)."""
        datos = {**registro, **cambios}
        # Fase 4I-C: renombrar ítem/unidad no recalcula (no cambia el criterio de un registro histórico).
        if any(k in cambios for k in ("cantidad", "precio_base", "anticipo_amortizado", "criterio_factor", "i_icociv")):
            entrada = {"item": datos.get("item",""), "unidad": datos.get("unidad",""), "cantidad": datos.get("cantidad"),
                       "precio_base": datos.get("precio_base"), "anticipo_amortizado": datos.get("anticipo_amortizado", 0),
                       "i0_icociv": registro.get("i0_icociv"), "i_icociv": datos.get("i_icociv"),
                       "ruta_icociv": registro.get("ruta_icociv"), "modelo_proyeccion": registro.get("modelo_proyeccion"),
                       "horizonte": datos.get("horizonte"), "periodo_base": registro.get("periodo_base"),
                       "periodo_proyectado": datos.get("periodo_proyectado"),
                       "observacion_tecnica": registro.get("observacion_tecnica","")}
            resultado = calcular_actualizacion_icociv(entrada)
            if any(x is None for x in desglose_presupuestal({**datos, **resultado}, resultado.get("valor_proyectado")).values()) and validar_modalidad(registro) != "heredado":
                raise ValueError("Los importes o su conversión por Cantidad no son representables.")
            datos.update(resultado)
        conservar = {k: registro[k] for k in ("calculo_id", "analisis_id", "modalidad_importe", "proyecto", "tipo_componente",
                                              "nombre_componente", "fecha_calculo") if k in registro}
        conservar.update({k: v for k, v in cambios.items() if k in ("proyecto", "nombre_componente")})
        datos.update(conservar)
        antes = {k: registro.get(k) for k in cambios}
        datos["historial_ediciones"] = list(registro.get("historial_ediciones", [])) + [
            {"fecha": datetime.now().isoformat(timespec="seconds"), "antes": antes, "despues": dict(cambios)}]
        return datos

    def reordenar_visibles(self, ids_visibles, calculo_id=None) -> None:
        """Aplica un nuevo orden de las filas visibles al presupuesto completo, por IDs.

        Las filas ocultas por el filtro conservan su posición; las visibles ocupan las
        mismas posiciones globales que antes, en el nuevo orden. Nada se recalcula.
        """
        visibles = {r.get("calculo_id") for r in self._valores_visibles}
        if set(ids_visibles) != visibles or len(ids_visibles) != len(self._valores_visibles):
            raise ValueError("El nuevo orden no corresponde a las filas visibles.")
        por_id = {r.get("calculo_id"): r for r in self._valores_visibles}
        huecos = [i for i,r in enumerate(self.valores) if r.get("calculo_id") in visibles]
        nuevos = list(self.valores)
        for posicion, identificador in zip(huecos, ids_visibles):
            nuevos[posicion] = por_id[identificador]
        if all(a is b for a, b in zip(nuevos, self.valores)):
            return
        movido = por_id.get(calculo_id)
        self._registrar_cambio(f"mover «{movido.get('item', '')}»" if movido else "reordenar actividades", nuevos, calculo_id)

    def mover_actividad(self, calculo_id, destino) -> bool:
        """Mueve una fila visible a la posición visible ``destino`` (base 0)."""
        ids = [r.get("calculo_id") for r in self._valores_visibles]
        if calculo_id not in ids or not 0 <= destino < len(ids):
            return False
        ids.insert(destino, ids.pop(ids.index(calculo_id)))
        self.reordenar_visibles(ids, calculo_id)
        return True

    def _fila_arrastrada(self, _logica, origen, destino) -> None:
        cabecera = self.tabla_valores.verticalHeader()
        with QSignalBlocker(cabecera):
            cabecera.moveSection(destino, origen)  # el modelo, no la cabecera, guarda el orden
        if 0 <= origen < len(self._valores_visibles):
            self.mover_actividad(self._valores_visibles[origen].get("calculo_id"), destino)

    def preparar_insercion(self, calculo_id, despues=False) -> bool:
        """Reserva la posición de la próxima actividad (no crea ningún registro)."""
        if not any(r.get("calculo_id") == calculo_id for r in self.valores):
            return False
        if self.analisis_activo() is None:
            QMessageBox.information(self, "Insertar actividad", "Seleccione primero la proyección guardada para la nueva "
                                    "actividad (Historial › Proyección guardada). No se hereda de la fila vecina.")
            return False
        self._insercion = (calculo_id, bool(despues))
        fila = next(i for i,r in enumerate(self.valores) if r.get("calculo_id") == calculo_id) + 1
        self.lbl_insercion.setText(f"La próxima actividad se insertará {'debajo' if despues else 'encima'} de la fila {fila} "
                                   f"(«{self.valores[fila-1].get('item','')}») con {self.etiqueta_activo()}. "
                                   "Complete la calculadora y pulse «Calcular y agregar a la tabla».")
        self.lbl_insercion.show();self.boton_cancelar_insercion.show()
        return True

    def cancelar_insercion(self) -> None:
        self._insercion = None
        if hasattr(self, "lbl_insercion"):
            self.lbl_insercion.hide();self.boton_cancelar_insercion.hide()

    def _posicion_insercion(self):
        if not self._insercion:
            return None
        referencia, despues = self._insercion
        indice = next((i for i,r in enumerate(self.valores) if r.get("calculo_id") == referencia), None)
        return None if indice is None else indice + (1 if despues else 0)

    def _menu_tabla_valores(self, punto) -> None:
        index = self.tabla_valores.indexAt(punto)
        if not index.isValid():
            return
        self._seleccionar_fila_valores(index.row())
        fila = index.row();registro = self._valores_visibles[fila];ident = registro.get("calculo_id")
        menu = QMenu(self.tabla_valores)
        editar = menu.addAction("Editar celda (F2)", lambda: self.tabla_valores.edit(index))
        editar.setEnabled(bool(self.modelo_valores.flags(index) & Qt.ItemIsEditable))
        menu.addAction("Pegar en la celda (Ctrl+V)", self.tabla_valores.pegar_en_celda).setEnabled(editar.isEnabled())
        menu.addSeparator()
        menu.addAction("Mover arriba", lambda: self.mover_actividad(ident, fila - 1)).setEnabled(fila > 0)
        menu.addAction("Mover abajo", lambda: self.mover_actividad(ident, fila + 1)).setEnabled(fila < len(self._valores_visibles) - 1)
        menu.addAction("Mover a posición…", lambda: self._pedir_posicion(ident))
        menu.addSeparator()
        menu.addAction("Insertar actividad arriba", lambda: self.preparar_insercion(ident, False))
        menu.addAction("Insertar actividad abajo", lambda: self.preparar_insercion(ident, True))
        menu.addSeparator()
        menu.addAction("Editar actividad en la calculadora", self.editar_seleccionado)
        menu.addAction("Actualizar al factor redondeado…", lambda: self.actualizar_factor_legado(ident)).setEnabled(es_factor_legado(registro))
        menu.exec(self.tabla_valores.viewport().mapToGlobal(punto))

    _CLAVES_ARCHIVO = ("factor_icociv", "diferencia_porcentual", "r_total", "diferencia_absoluta", "valor_proyectado",
                       "base_ajustable", "precio_base", "anticipo_amortizado", "cantidad", "i0_icociv", "i_icociv",
                       "periodo_base", "periodo_proyectado", "modalidad_importe", "analisis_id", "calculo_id",
                       "trazabilidad_formula", "criterio_factor")

    def _convertir_legado(self, registro) -> dict:
        """Registro equivalente con la regla vigente; archiva el estado anterior EXACTO para auditoría."""
        for clave in ("precio_base", "i0_icociv", "i_icociv"):
            if not isinstance(registro.get(clave), (int, float)) or not math.isfinite(registro[clave]) or registro[clave] <= 0:
                raise ValueError(f"falta un dato fiable ({clave})")
        nuevo = self._recalcular_registro(registro, {"criterio_factor": CRITERIO_FACTOR})
        anterior = {k: registro.get(k) for k in self._CLAVES_ARCHIVO}
        anterior.update({f"desglose_{k}": v for k, v in desglose_presupuestal(registro, registro.get("valor_proyectado")).items()})
        anterior["posicion"] = next((i for i, r in enumerate(self.valores) if r is registro), None)
        nuevo["historial_ediciones"][-1].update(antes=anterior, despues={k: nuevo.get(k) for k in self._CLAVES_ARCHIVO},
                                                motivo="actualización expresa al criterio vigente del factor")
        return nuevo

    def actualizar_legados_lote(self) -> bool:
        """Fase 4I-D: convierte TODAS las actividades con el factor anterior en una sola operación.

        Atómica: primero valida y calcula todas; si alguna no es convertible se informa y NO se aplica
        nada. Una confirmación con vista previa; un solo comando deshacible. No ejecuta el motor.
        """
        legados = [r for r in self.valores if es_factor_legado(r)]
        if not legados:
            return False
        convertidos, fallidos = {}, []
        for r in legados:
            try:
                convertidos[id(r)] = self._convertir_legado(r)
            except ValueError as error:
                fallidos.append(f"N.º {r.get('numero_fila', '?')} «{r.get('item', '')}»: {error}")
        if fallidos:
            QMessageBox.warning(self, "Actualizar al criterio vigente", "\n".join([
                "No se aplicó ningún cambio: estas actividades no tienen datos suficientes para recalcularse sin inventar información.",
                "", *fallidos, "", "Corrija P, I0 o I con «Editar» y vuelva a intentarlo."]))
            return False
        total = lambda filas: sum(x.get("valor_proyectado") or 0 for x in filas)
        nuevos = [convertidos.get(id(r), r) for r in self.valores]
        if not self._confirmar_actualizacion([(r, convertidos[id(r)]) for r in legados]):
            return False
        self._registrar_cambio(f"actualizar {len(legados)} actividades al criterio vigente", nuevos, legados[0].get("calculo_id"))
        return True

    def _confirmar_actualizacion(self, pares, titulo="Actualizar criterio vigente", introduccion=None, boton="Actualizar",
                                 con_fechas=False) -> bool:
        """Vista previa tabular (antes → después); True si el usuario pulsa el botón afirmativo.
        Fase 4I-J: también confirma el cambio de fecha objetivo (con columnas de fecha)."""
        dialogo = QDialog(self);dialogo.setWindowTitle(titulo);dialogo.resize(1060 if con_fechas else 860, 420)
        layout = QVBoxLayout(dialogo)
        n = len(pares)
        intro = QLabel(introduccion or f"{n} actividad{'es' if n != 1 else ''} se recalcular{'án' if n != 1 else 'á'} con la regla vigente: {TEXTO_CRITERIO_FACTOR}")
        intro.setWordWrap(True);layout.addWidget(intro)
        cabeceras = ["N.º", "Actividad", *(("Fecha anterior", "Fecha nueva") if con_fechas else ()), "Factor anterior",
                     "Factor actualizado", "Diferencia %", "Valor anterior", "Valor actualizado"]
        tabla = QTableWidget(n, len(cabeceras))
        tabla.setHorizontalHeaderLabels(cabeceras)
        tabla.verticalHeader().setVisible(False);tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectRows);tabla.setWordWrap(False)
        for fila, (r, nuevo) in enumerate(pares):
            fechas = (fo.periodo_visible(r.get("periodo_proyectado")), fo.periodo_visible(nuevo.get("periodo_proyectado"))) if con_fechas else ()
            celdas = [str(r.get("numero_fila", "")), str(r.get("item", "")), *fechas, f"{r['factor_icociv']:.6f}", f"{nuevo['factor_icociv']:.4f}",
                      f"{nuevo['diferencia_porcentual']:.2f} %", pesos_ui(r["valor_proyectado"]), pesos_ui(nuevo["valor_proyectado"])]
            for columna, texto in enumerate(celdas):
                celda = QTableWidgetItem(texto);celda.setToolTip(texto)
                if columna != 1:
                    celda.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                tabla.setItem(fila, columna, celda)
        cabecera = tabla.horizontalHeader();cabecera.setSectionResizeMode(QHeaderView.ResizeToContents)
        if con_fechas:  # más columnas: «Actividad» con ancho propio y la última ocupa el sobrante
            cabecera.setSectionResizeMode(1, QHeaderView.Interactive);tabla.setColumnWidth(1, 150);cabecera.setStretchLastSection(True)
        else:
            cabecera.setSectionResizeMode(1, QHeaderView.Stretch)
        tabla.setFocusPolicy(Qt.NoFocus);layout.addWidget(tabla, 1)
        antes = sum(r.get("valor_proyectado") or 0 for r, _ in pares);despues = sum(x.get("valor_proyectado") or 0 for _, x in pares)
        resumen = QLabel(f"Suma de valores principales: <b>{escape(pesos_ui(antes))}</b> → <b>{escape(pesos_ui(despues))}</b><br>"
                         "Se conservan los índices, el pronóstico y los valores originales (en «Ver detalle» y en el historial de ediciones). "
                         "No se ejecuta el motor. Se puede deshacer.")
        resumen.setWordWrap(True);resumen.setObjectName("texto_secundario");layout.addWidget(resumen)
        botones = QDialogButtonBox(QDialogButtonBox.Cancel);actualizar = botones.addButton(boton, QDialogButtonBox.AcceptRole)
        # El QSS pone el texto en peso medio, más ancho que la fuente con la que Qt mide: se reserva su ancho real.
        negrita = QFont(actualizar.font());negrita.setWeight(QFont.Weight.DemiBold)
        actualizar.setStyleSheet(f"min-width: {QFontMetrics(negrita).horizontalAdvance(boton) + 40}px;")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar");botones.button(QDialogButtonBox.Cancel).setObjectName("boton_secundario")
        actualizar.setDefault(True);botones.accepted.connect(dialogo.accept);botones.rejected.connect(dialogo.reject)
        layout.addWidget(botones)
        return dialogo.exec() == QDialog.Accepted

    def _crear_aviso_legados(self):
        """Franja de aviso con «Actualizar factores de N actividades» y «Ver detalle» (oculta si no hay legados)."""
        aviso = QFrame();aviso.setObjectName("aviso_legados")
        fila = QHBoxLayout(aviso);fila.setContentsMargins(tokens.ESPACIO_3, tokens.ESPACIO_2, tokens.ESPACIO_3, tokens.ESPACIO_2)
        etiqueta = QLabel();etiqueta.setWordWrap(True)
        actualizar = QPushButton("Actualizar factores");detalle = QPushButton("Ver detalle")
        actualizar.setObjectName("boton_compacto");detalle.setObjectName("boton_compacto")
        for boton in (actualizar, detalle):
            boton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        actualizar.clicked.connect(self.actualizar_legados_lote);detalle.clicked.connect(self._detalle_legados)
        fila.addWidget(etiqueta, 1);fila.addWidget(actualizar);fila.addWidget(detalle)
        aviso.hide()
        return aviso, etiqueta, actualizar, detalle

    def _detalle_legados(self) -> None:
        """Valores originales de las actividades con el criterio anterior (o de las ya convertidas)."""
        filas = []
        for r in self.valores:
            if es_factor_legado(r):
                filas.append(f"N.º {r.get('numero_fila', '?')} {r.get('item', '')} · criterio anterior · factor {r.get('factor_icociv')!r} · "
                             f"diferencia {r.get('diferencia_porcentual')!r} % · valor {r.get('valor_proyectado')!r}")
            else:
                previo = next((e["antes"] for e in reversed(r.get("historial_ediciones", [])) if e.get("motivo", "").startswith("actualización expresa")), None)
                if previo:
                    filas.append(f"N.º {r.get('numero_fila', '?')} {r.get('item', '')} · actualizado · original: factor {previo.get('factor_icociv')!r}, "
                                 f"diferencia {previo.get('diferencia_porcentual')!r} %, valor {previo.get('valor_proyectado')!r}")
        QMessageBox.information(self, "Criterio del factor por actividad", "\n".join(filas) or "Todas las actividades usan la regla vigente.")

    def actualizar_factor_legado(self, calculo_id) -> bool:
        """Fase 4I-C: recálculo EXPRESO de un registro histórico con la regla del porcentaje redondeado.

        Vista previa antes/después y confirmación; no ejecuta el motor ni toca el snapshot; queda en
        ``historial_ediciones`` y es deshacible.
        """
        registro = next((r for r in self.valores if r.get("calculo_id") == calculo_id), None)
        if registro is None or not es_factor_legado(registro):
            return False
        try:
            nuevo = self._convertir_legado(registro)
        except ValueError as error:
            self._avisar_edicion(f"No se pudo actualizar: {error}");return False
        if not self._confirmar_actualizacion([(registro, nuevo)]):
            return False
        self._registrar_cambio(f"actualizar factor de «{registro.get('item', '')}»",
                               [nuevo if r is registro else r for r in self.valores], calculo_id)
        return True

    def _pedir_posicion(self, calculo_id) -> None:
        total = len(self._valores_visibles)
        actual = next(i for i,r in enumerate(self._valores_visibles) if r.get("calculo_id") == calculo_id) + 1
        posicion, ok = QInputDialog.getInt(self, "Mover a posición", f"Nueva posición (1–{total}):", actual, 1, total)
        if ok:self.mover_actividad(calculo_id, posicion - 1)

    def _confirmar_vinculo_fuera_de_ambito(self) -> bool:
        caja = QMessageBox(self);caja.setIcon(QMessageBox.Icon.Question);caja.setWindowTitle('Proyección para el nuevo cálculo')
        caja.setText(f"Estás consultando {self._ambito_consulta['etiqueta']}, pero la actividad se vinculará a "
                     f"{self.etiqueta_activo()}, que no pertenece a esa selección. ¿Registrar de todos modos?")
        seguir = caja.addButton('Registrar con la proyección activa', QMessageBox.ButtonRole.AcceptRole)
        caja.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole);caja.exec()
        return caja.clickedButton() is seguir

    def _mostrar_resultado(self, r: dict[str, Any]) -> None:
        original = r
        self._registro_detalle = original
        r, estado = self.escenario_registro(original)
        filas = [
            ("Precio base P (COP)", pesos_ui(r.get("precio_base"))),
            ("Anticipo A (COP)", pesos_ui(r.get("anticipo_amortizado"))),
            ("Base ajustable P - A (COP)", pesos_ui(r.get("base_ajustable"))),
            ("I0 ICOCIV", numero_ui(r.get("i0_icociv"))),
            ("I ICOCIV proyectado", numero_ui(r.get("i_icociv"))),
            ("Factor ICOCIV aplicado" if not es_factor_legado(r) else "Factor ICOCIV (histórico)",
             f"{r.get('factor_icociv'):.4f}" if not es_factor_legado(r) and isinstance(r.get('factor_icociv'), (int, float))
             else numero_ui(r.get("factor_icociv"))),
            ("Criterio del factor", TEXTO_CRITERIO_FACTOR if not es_factor_legado(r) else TEXTO_FACTOR_LEGADO),
            ("Valor del ajuste R (COP)", pesos_ui(r.get("r_total"))),
            ("Valor proyectado (COP)", pesos_ui(r.get("valor_proyectado"))),
            ("Diferencia porcentual (%)", porcentaje_ui(r.get("diferencia_porcentual"))),
        ]
        filas_html = "".join(
            f"<tr><td style='padding:2px 10px 2px 0'><b>{escape(k)}</b></td>"
            f"<td style='padding:2px 0'>{escape(str(v))}</td></tr>"
            for k, v in filas
        )
        traza = escape(formula_ui(r.get("trazabilidad_formula", ""))).replace("\n", "<br>")
        detalle = "".join(
            f"<tr><td><b>{escape(str(clave).replace('_', ' '))}</b></td><td>{escape(formula_ui(valor) if clave == 'trazabilidad_formula' else detalle_ui(valor))}</td></tr>"
            for clave, valor in original.items()
        )
        self.resultado.setHtml(
            f"<h3>Actualización ICOCIV proyectada</h3><p>{escape(estado)} · Referencia {escape(self.fechas_registro(original)[0])} · Objetivo {escape(self.fechas_registro(original)[1])}</p><table>{filas_html}</table>"
            f"<h4>Desglose presupuestal complementario</h4><p>{escape(texto_desglose(original,r.get('valor_proyectado'),'Escenario económico vigente del slider')).replace(chr(10),'<br>')}</p>"
            "<p><a href='interpretacion'>Cambiar interpretación de P y A de este registro</a></p>"
            f"<h4>Desarrollo matemático · cifras visibles resumidas</h4><p style='font-family:monospace'>{traza}</p>"
            f"<h4>Detalle del registro conservado</h4><table>{detalle}</table>"
        )

    def _actualizar_resumen_presupuestal(self,*_):
        if not hasattr(self,'resumen_presupuestal'):return
        filas = {i.row() for i in self.tabla_valores.selectedIndexes()}
        fila = next(iter(filas)) if len(filas)==1 else None
        r = self._valores_visibles[fila] if fila is not None and fila<len(self._valores_visibles) else None
        self.resumen_presupuestal.setText(texto_desglose(r,self.escenario_registro(r)[0].get('valor_proyectado'),'Fila seleccionada · escenario vigente del slider') if r is not None else 'Seleccione una sola fila para consultar su desglose presupuestal.')

    def _editar_interpretacion(self,enlace):
        if enlace.toString()!='interpretacion':return
        r = getattr(self,'_registro_detalle',None)
        if not any(x is r for x in self.valores):return
        dialogo = QDialog(self);dialogo.setWindowTitle('Interpretación de P y A');layout = QVBoxLayout(dialogo)
        aviso = QLabel(AVISO_INTERPRETACION);aviso.setWordWrap(True);layout.addWidget(aviso)
        combo = ComboBoxSinRueda();combo.setAccessibleName('Interpretación de P y A del registro')
        for modo,titulo in MODALIDADES.items():combo.addItem(titulo,modo)
        combo.setCurrentIndex(combo.findData(validar_modalidad(r)));layout.addWidget(combo)
        botones = QDialogButtonBox(QDialogButtonBox.Save|QDialogButtonBox.Cancel);botones.accepted.connect(dialogo.accept);botones.rejected.connect(dialogo.reject);layout.addWidget(botones)
        if dialogo.exec()==QDialog.Accepted and any(x is r for x in self.valores):
            r['modalidad_importe'] = validar_modalidad({'modalidad_importe':combo.currentData()})
            self.pila_deshacer.clear();self._estado_pila = None  # cambio en sitio: la pila no debe restaurar la modalidad anterior
            self._mostrar_resultado(r);self._actualizar_columnas_comparativas()
            self.comparacion_cambiada.emit(self.resumen_comparacion_historica())

    def _detalle_proyeccion(self) -> None:
        indice = _seleccion(self.tabla_proyecciones)
        if indice is not None and 0 <= indice < len(self.proyecciones):
            r = self.proyecciones[indice]
            QMessageBox.information(self, "Detalle de la proyección", _detalle_texto(r, COLUMNAS_PROYECCIONES))

    def _detalle_valor(self) -> None:
        indice = _seleccion(self.tabla_valores)
        if indice is not None and 0 <= indice < len(self._valores_visibles):
            registro = self._valores_visibles[indice]
            # 4G-B: consulta pura; no escribe en la calculadora.
            self._mostrar_resultado(registro)

    def _hay_borrador(self) -> bool:
        """Datos digitados en la calculadora que aún no se han guardado como actividad."""
        actual = self._datos_calculadora()
        if self._formulario_guardado is not None and actual == self._formulario_guardado:
            return False
        return bool(self._item_editado or self.nombre_componente.text().strip() or self.cantidad.value()
                    or self.precio_base.value() or self.anticipo.value() or self.observacion.toPlainText().strip())

    def _confirmar_descartar_borrador(self, accion) -> bool:
        caja = QMessageBox(self);caja.setIcon(QMessageBox.Icon.Warning);caja.setWindowTitle('Datos sin guardar')
        caja.setText(f'La calculadora tiene datos sin guardar. {accion} los reemplazará. ¿Desea continuar?')
        seguir = caja.addButton('Continuar', QMessageBox.ButtonRole.AcceptRole)
        caja.addButton('Cancelar', QMessageBox.ButtonRole.RejectRole);caja.exec()
        return caja.clickedButton() is seguir

    def editar_seleccionado(self) -> bool:
        """Única ruta que carga los datos de una actividad guardada en la calculadora."""
        indice = _seleccion(self.tabla_valores)
        if indice is None or not 0 <= indice < len(self._valores_visibles):
            QMessageBox.information(self, "Editar", "Seleccione primero una actividad de la tabla.");return False
        registro = self._valores_visibles[indice]
        if self._hay_borrador() and not self._confirmar_descartar_borrador('Editar la actividad seleccionada'):return False
        if registro.get('analisis_id') and registro['analisis_id'] != self.analisis_activo_id:
            self.analisis_solicitado.emit(registro['analisis_id'])  # vínculo real de la actividad
            if self.analisis_activo_id != registro['analisis_id']:
                QMessageBox.warning(self, "Editar", "No se pudo activar el análisis de esta actividad; no se cargó nada.");return False
        elif not registro.get('analisis_id'):
            QMessageBox.information(self, "Editar", "Registro anterior sin vínculo con el historial: solo se puede consultar.");return False
        self.restaurar_calculadora({"modalidad_importe": validar_modalidad(registro), "tipo_componente": registro.get("tipo_componente") or "Capítulo",
            "nombre_componente": registro.get("nombre_componente",""), "item": registro.get("item",""), "unidad": registro.get("unidad"),
            "cantidad": registro.get("cantidad") or 0, "precio_base": registro.get("precio_base") or 0,
            "anticipo": registro.get("anticipo_amortizado") or 0, "observacion": registro.get("observacion_tecnica","")})
        self._edicion_calculo_id = registro.get('calculo_id')
        self._formulario_guardado = self._datos_calculadora()
        self.boton_calcular.setText("Guardar cambios de la actividad")
        self._mostrar_resultado(registro)
        return True

    def _salir_edicion(self) -> None:
        self._edicion_calculo_id = None
        self.boton_calcular.setText("Calcular y agregar a la tabla")

    def _eliminar_proyeccion(self) -> None:
        indice = _seleccion(self.tabla_proyecciones)
        if indice is not None and 0 <= indice < len(self.proyecciones):
            del self.proyecciones[indice]
            self._refrescar_tabla_proyecciones()
        else:
            QMessageBox.information(self, "Eliminar", "Seleccione primero una fila de la tabla para eliminarla.")

    def _eliminar_valor(self) -> None:
        indice = _seleccion(self.tabla_valores)
        if indice is not None and 0 <= indice < len(self._valores_visibles):
            registro = self._valores_visibles[indice]
            self.valores = [r for r in self.valores if r is not registro]
            self._refrescar_tabla_valores()
        else:
            QMessageBox.information(self, "Eliminar", "Seleccione primero una fila de la tabla para eliminarla.")

    # post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). "Eliminar todo"
    # vacía la vista y la lista interna que la respalda; el excel exportable
    # y el estado de la calculadora ya leen esas mismas listas por
    # referencia, así que reflejan el vacío sin pasos adicionales.
    def _eliminar_todas_proyecciones(self) -> None:
        if not self.proyecciones:
            return
        if not self._confirmar_eliminar_todo('Proyecciones ICOCIV realizadas'):
            return
        self.proyecciones.clear()
        self._refrescar_tabla_proyecciones()
        self._actualizar_estado_calculadora()

    def _eliminar_todos_valores(self) -> None:
        if not self.valores:
            return
        if not self._confirmar_eliminar_todo('Valores proyectados ICOCIV (calculadora)'):
            return
        self.valores.clear()
        self._refrescar_tabla_valores()
        self._actualizar_estado_calculadora()

    def _confirmar_eliminar_todo(self,nombre) -> bool:
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Warning)
        caja.setWindowTitle("Eliminar todos los registros")
        caja.setText(
            f"Tabla activa: {nombre}. ¿Desea eliminar todos los registros de esta tabla en la sesión, incluidos los ocultos "
            "por el filtro de análisis? Los análisis del historial se conservarán."
        )
        boton_eliminar = caja.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
        caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.exec()
        return caja.clickedButton() is boton_eliminar

    def _exportar_excel(self) -> None:
        if not self.proyecciones and not self.valores and not self.historial:
            QMessageBox.information(self, "Exportación", "No hay proyecciones ni valores para exportar.")
            return
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar proyecciones ICOCIV", "proyecciones_icociv.xlsx", "Excel (*.xlsx)"
        )
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta = f"{ruta}.xlsx"
        try:
            with self._preparando("Preparando exportación Excel…"):
                self._generar_excel(ruta)
        except Exception as exc:  # pragma: no cover - mensaje UI
            QMessageBox.critical(self, "Exportación", f"No fue posible generar el archivo:\n{exc}")
            return
        QMessageBox.information(self, "Exportación", f"Archivo generado: {Path(ruta).name}")

    # ------------------------------------------------------------ internos
    def _exportar_informe(self,formato):
        if not self.proyecciones and not self.valores and not self.historial:return
        filtro='Documento PDF (*.pdf)' if formato=='pdf' else 'Documento Word (*.docx)'
        ruta,_=QFileDialog.getSaveFileName(self,'Exportar informe de la sesión ICOCIV',f'proyecciones_icociv.{formato}',filtro)
        if not ruta:return
        if not Path(ruta).suffix:ruta+=f'.{formato}'
        try:
            with self._preparando(f"Preparando informe {formato.upper()}…"):
                self._generar_informe(ruta,formato)
        except Exception as exc:
            QMessageBox.critical(self,'Informe',f'No fue posible generar el informe:\n{exc}')
            return
        QMessageBox.information(self,'Informe',f'Informe generado: {Path(ruta).name}')

    def _generar_informe(self,ruta,formato,alcance=None):
        from app_icociv.reportes.sesion_modulos import construir_proyecciones,guardar
        with self._vista_exportacion(alcance or self._alcance_pendiente):
            informe = construir_proyecciones(self)
        return guardar(informe,ruta,formato)

    def _registrar_proyeccion(self, contexto: dict[str, Any]) -> None:
        fila = _fila_proyeccion(contexto)
        self.proyecciones.append(fila)
        self._refrescar_tabla_proyecciones()

    def _refrescar_tabla_proyecciones(self) -> None:
        for numero, fila in enumerate(self.proyecciones, start=1):
            fila["numero"] = numero
        df = _dataframe(self._filas_proyecciones_numericas(), COLUMNAS_PROYECCIONES)
        self.modelo_proyecciones.establecer_dataframe(df)

    def _filas_proyecciones_numericas(self):
        contextos={a['id']:a.get('contexto') or {} for a in self.historial}
        filas=[]
        for r in self.proyecciones:
            fila=dict(r)
            contexto=contextos.get(r.get('analisis_id'),{})
            if not contexto and self.contexto and r is self.proyecciones[-1] and r.get('modelo')==self.contexto.get('modelo') and r.get('item_ruta')==self.contexto.get('ruta_texto') and r.get('periodo_proyectado')==self.contexto.get('periodo_proyectado'):
                contexto=self.contexto
            for clave in ('indice_base','indice_proyectado','mae','rmse','mape','smape','mase'):
                fuente=contexto if clave.startswith('indice_') else contexto.get('metricas') or {}
                fila[clave]=numero_original(fuente[clave] if clave in fuente else r.get(clave))
            maximo=contexto.get('maximo_recomendado',r.get('maximo_recomendado'))
            fila['maximo_recomendado']=numero_original(maximo.removesuffix(' meses') if isinstance(maximo,str) else maximo)
            filas.append(fila)
        return filas

    def _refrescar_tabla_valores(self) -> None:
        if self.pila_deshacer.count() and not (self._estado_pila is not None and len(self._estado_pila) == len(self.valores)
                                               and all(a is b for a, b in zip(self._estado_pila, self.valores))):
            # ponytail: alta, eliminación o edición en la calculadora no son deshacibles; al ocurrir,
            # la pila se vacía para no deshacer sobre un presupuesto distinto.
            self.pila_deshacer.clear();self._estado_pila = None
        seleccionadas = {i.row() for i in self.tabla_valores.selectedIndexes()}
        seleccionado = self._valores_visibles[next(iter(seleccionadas))].get('calculo_id') if len(seleccionadas)==1 else None
        for numero, fila in enumerate(self.valores, start=1):
            fila["numero_fila"] = numero
        if self.solo_analisis_activo.isChecked():
            # Filtro de PRESENTACIÓN: ámbito ∩ proyección consultada; la colección canónica no cambia.
            ids = set(self.ids_ambito())
            if self._proyeccion_consulta:ids &= {self._proyeccion_consulta}
            self._valores_visibles = [r for r in self.valores if r.get("analisis_id") in ids]
        else:
            self._valores_visibles = list(self.valores)
        self.modelo_valores.claves = []  # fuerza la reconstrucción de las columnas
        self._actualizar_columnas_comparativas()
        if seleccionado:
            fila = next((i for i,r in enumerate(self._valores_visibles) if r.get('calculo_id')==seleccionado),None)
            if fila is not None:self._seleccionar_fila_valores(fila)
        relacionados = len({r.get("analisis_id") for r in self._valores_visibles if r.get("analisis_id")})
        self.lbl_filtro_valores.setText(
            f"{len(self._valores_visibles)} de {len(self.valores)} actividades · {relacionados} análisis relacionados · "
            + ("Vista filtrada por la selección: los demás registros siguen en el presupuesto." if self.solo_analisis_activo.isChecked()
               else "Todos los registros de la sesión. Ver detalle conserva la trazabilidad completa."))
        self.lbl_filtro_inferior.setText(self.lbl_filtro_valores.text())
        legados = sum(es_factor_legado(r) for r in self.valores)
        texto = (f"{legados} actividad{'es usan' if legados != 1 else ' usa'} el factor anterior (I/I0 sin redondear): "
                 "sus importes no siguen la regla vigente del porcentaje redondeado a 2 decimales." if legados else "")
        # Fase 4I-D (verificación): el mismo aviso arriba del módulo (donde se abre la sesión) y junto a la tabla.
        for aviso, etiqueta, boton in ((self.aviso_legados, self.lbl_legados, self.boton_actualizar_legados),
                                       (self.aviso_legados_superior, self.lbl_legados_superior, self.boton_actualizar_legados_superior)):
            aviso.setVisible(bool(legados));etiqueta.setText(texto)
            boton.setText(f"Actualizar factores de {legados} actividad{'es' if legados != 1 else ''}")
        self.sin_valores.setText("No hay actividades guardadas para esta selección." if self.valores
                                 else "Sin valores proyectados. Complete la calculadora y agregue un registro.")
        self.sincronizar_analisis_activo()

    def _actualizar_estado_calculadora(self) -> None:
        contexto = self.contexto
        valido = bool(contexto and contexto.get("proyeccion_generada"))
        self.boton_calcular.setEnabled(valido)
        if not contexto and self.historial and self.analisis_activo_id is None:
            self.lbl_contexto.setText("No hay análisis seleccionado. Elija uno del historial o ejecute una proyección para habilitar la calculadora.")
        elif not contexto:
            self.lbl_contexto.setText("Sin proyección activa. Ejecute una proyección para habilitar la calculadora.")
        elif not valido:
            self.lbl_contexto.setText(
                f"Proyección no generada para {contexto.get('ruta_texto', 'la ruta actual')}. "
                "La calculadora permanece deshabilitada."
            )
        else:
            self.lbl_contexto.setText(
                f"Proyección activa: {contexto.get('ruta_texto', '')} · "
                f"I0 registrado del pronóstico={numero_ui(contexto.get('indice_base'))} ({_periodo_visible(contexto.get('periodo_base'))}) · "
                f"I proyectado={numero_ui(contexto.get('indice_proyectado'))} ({_periodo_visible(contexto.get('periodo_proyectado'))}) · "
                f"Modelo: {contexto.get('modelo', 'No aplica')}"
            )
        self._sugerir_nombre_item()

    def _generar_excel(self, ruta: str, alcance=None) -> None:
        with self._vista_exportacion(alcance or self._alcance_pendiente):
            self._generar_excel_alcance(ruta)

    def _generar_excel_alcance(self, ruta: str) -> None:
        wb = Workbook();wb.active.title = HOJA_RESUMEN;_activar_recalculo_excel(wb)
        proyecto = self.datos_proyecto();contexto = self.contexto or {}
        _escribir_pares_excel(wb.active,1,'Resumen de la sesión ICOCIV',[
            ('Fecha de exportación',datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            *[(k,v) for k,v in proyecto.items()],
            ('Análisis activo',self.analisis_activo_id or 'Sin análisis activo'),
            ('Análisis incluidos',len(self.historial)),('Registros económicos',len(self.valores)),
            ('Alcance',getattr(self,'_descripcion_alcance',None) or 'Toda la sesión: todos los registros; el filtro visual no reduce la exportación'),
            ('Modo global para próxima selección',self.aplicar_global.isChecked()),
            ('Referencia','Escenarios hipotéticos sobre pronósticos guardados; originales consultables en Trazabilidad y sesión JSON'),
            ('Ruta activa',contexto.get('ruta_texto',''))])
        _escribir_tabla_excel(wb.active,16,'Referencias por análisis',
            ['ID análisis','Análisis','Referencia vigente','Estado','Archivo fuente'],
            [[a['id'],a['nombre'],self._periodo_por_analisis.get(a['id'],''),
              'Referencia modificada (escenario)' if self._overrides.get(a['id']) else 'Referencia predeterminada / original conservado',
              a['archivo_excel']] for a in self.historial])
        referencias = self._escribir_operativa_excel(wb.create_sheet(HOJA_VALORES))
        ws_proy = wb.create_sheet(HOJA_PROYECCIONES)
        _escribir_tabla_excel(ws_proy,1,'Proyecciones auténticas; no cambian con la referencia económica',
            [titulo for _,titulo in COLUMNAS_PROYECCIONES],
            [[fila.get(clave,'') for clave,_ in COLUMNAS_PROYECCIONES] for fila in self._filas_proyecciones_numericas()])
        for i,(clave,_) in enumerate(COLUMNAS_PROYECCIONES,1):
            if clave in ('indice_base','indice_proyectado','mae','rmse','mape','smape','mase'):
                for fila in range(3,3+len(self.proyecciones)):
                    cell = ws_proy.cell(fila,i)
                    cell.number_format = ('0.00E+00' if cell.value and abs(cell.value)<0.00005 else '#,##0.0000')+('" %"' if clave in ('mape','smape') else '')
        _escribir_tabla_excel(ws_proy,5+len(self.proyecciones),'Identidad y parámetros de los snapshots conservados',
            ['ID análisis','Análisis','Serie / ruta','Modelo','Horizonte','Objetivo','Creado','Fuente'],
            [[a['id'],a['nombre'],a['contexto'].get('ruta_texto',''),a['contexto'].get('modelo',''),
              a['parametros']['horizonte'],periodo_mensual(a['contexto'].get('periodo_proyectado')),a['creado'],a['resultado'].get('fuente','')]
             for a in self.historial])
        traza = wb.create_sheet(HOJA_TRAZABILIDAD)
        self._escribir_trazabilidad_excel(traza)
        from app_icociv.exportables.excel_modulos import agregar_desglose_importes
        agregar_desglose_importes(traza,[self.escenario_registro(r)[0] for r in self.valores],referencias,'valor_proyectado','Escenario vigente del slider')
        _escribir_pares_excel(wb.create_sheet(HOJA_METODOLOGIA),1,'Metodología y fórmulas ICOCIV',[
            ('Base ajustable','Base principal = P - A; Cantidad convierte los pares unitario/total según la modalidad declarada, sin modificar el principal'),
            ('Factor aplicado','Factor = 1 + ROUND(((I proyectado guardado / I0 efectivo) - 1) × 100; 2) / 100. La variación se redondea a dos decimales (mitad hacia arriba) ANTES de formar el factor; los índices y pronósticos no se alteran'),
            ('Ajuste económico','R = Base × (Factor aplicado - 1)'),
            ('Valor proyectado','Valor = Base + R = Base × Factor aplicado; los importes se muestran al peso'),
            ('Diferencia (%)','Variación aplicada = (Factor aplicado - 1) × 100, máximo dos decimales'),
            ('Registros con el criterio anterior','Si el alcance los incluye, conservan Factor = I / I0 original (fórmula y formato de 8 decimales) y NO siguen la regla vigente. Se convierten solo con la acción expresa «Actualizar todas al criterio vigente»'),
            ('Fórmulas principales',_texto_formulas(self._letras_excel_valores)),
            ('Fechas de índices','Fecha única de I0 o de I: va en su encabezado. Fecha distinta o ausente en alguna fila: columna auxiliar junto a ese índice, con el periodo AAAA-MM como texto (— si falta). Se evalúa sobre todos los registros exportados.'),
            ('Entradas editables','P, A e I0 efectivos. Editar una copia de Excel no modifica SAVIP ni ejecuta el motor'),
            ('Referencia predeterminada','Último índice observado auténtico; resultados originales sin intervención. Discrepancias de I0 se conservan y se avisan'),
            ('Referencia modificada','Mes observado elegido explícitamente: escenario económico calculado desde los registros originales, sin redondeo previo'),
            ('Modo global','Intersección real de meses observados de todos los análisis ICOCIV; aplicación atómica. Marcar solo configura la próxima selección'),
            ('Pronósticos','Motor estadístico original SAVIP: 21 candidatos, N0=12, horizonte hasta 24 meses; métricas, walk-forward e intervalos guardados sin recalcular'),
            ('Alcance','Un solo tramo ICOCIV, sin ICCP. Pronósticos estimados por SAVIP, no índices oficiales DANE'),
            ('Trazabilidad íntegra','Resultados, series y snapshots auténticos permanecen en la sesión JSON. IDs en Trazabilidad permiten localizar la evidencia, sin duplicarla en Excel'),
            ('Legados','Sin vínculo verificable se mantienen los resultados originales; no se asigna una serie por semejanza')])
        for hoja in wb.worksheets:
            _ajustar_hoja_excel(hoja)
            for fila in hoja:
                for celda in fila:
                    if isinstance(celda.value,str) and celda.data_type!='f':celda.data_type='s'
        wb[HOJA_VALORES].row_dimensions[2].height = 72
        letras = self._letras_excel_valores
        wb[HOJA_VALORES].column_dimensions[letras['i0_icociv']].width = 26
        wb[HOJA_VALORES].column_dimensions[letras['i_icociv']].width = 30
        for clave in ('fecha_i0','fecha_i'):
            if clave in letras:wb[HOJA_VALORES].column_dimensions[letras[clave]].width = 20
        guardar_atomico(ruta,lambda temporal:wb.save(temporal))

    def plan_excel_valores(self):
        """Columnas físicas del Excel: fechas evaluadas sobre TODOS los registros exportados."""
        return plan_columnas_valores([self.fechas_registro(r) for r in self.valores])

    def _escribir_operativa_excel(self, ws, calculable=True):
        registros = [self.escenario_registro(r)[0] for r in self.valores] if calculable else self.valores
        columnas, titulos = self.plan_excel_valores()
        fechas = [self.fechas_registro(r) for r in self.valores]
        filas = _dataframe_valores(registros, columnas, fechas).values.tolist()
        encabezados = [titulos.get(clave, titulo) for clave,titulo in columnas]
        # Mapa de coordenadas: cada fórmula se arma por clave, nunca por letra fija.
        n = {clave:i for i,(clave,_) in enumerate(columnas,1)}
        L = {clave:get_column_letter(i) for clave,i in n.items()}
        self._letras_excel_valores = L
        _escribir_tabla_excel(ws,1,'Valores proyectados ICOCIV · escenario vigente; pares según modalidad declarada',encabezados,filas)
        ws.freeze_panes='B3';ws.auto_filter.ref=f'A2:{get_column_letter(len(columnas))}{2+len(filas)}'
        from app_icociv.exportables.excel_modulos import estilo_escenario, validar_cantidad_excel
        validar_cantidad_excel(ws,L['cantidad'],len(filas)+2)
        moneda = {n[k] for k in ('precio_base','anticipo','base_unitaria','base_total','valor_unitario','valor_total')}
        indices = {n['i0_icociv'],n['i_icociv']}
        referencias=[];ids=[r.get('calculo_id') for r in registros]
        for f,r in enumerate(registros,3):
            referencias.append(None)
            for celda in ws[f]:
                if isinstance(celda.value,str):celda.data_type='s'
                if celda.column in moneda:celda.number_format='#,##0'  # Fase 4I: pesos COP enteros (valor interno completo)
                elif celda.column in indices:celda.number_format=FORMATO_INDICE_EXCEL
            p,a,i0,indice=(r.get(k) for k in ('precio_base','anticipo_amortizado','i0_icociv','i_icociv'))
            if not calculable or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in (p,a,i0,indice)) or p<=0 or a<0 or a>=p or i0<=0:continue
            if not all(numero_original(r.get(k)) is not None for k in ('base_ajustable','valor_proyectado')):continue
            Q,P,A,BU,BT,I0,I,F,VU,VT=(L[k] for k in ('cantidad','precio_base','anticipo','base_unitaria','base_total','i0_icociv','i_icociv','factor','valor_unitario','valor_total'))
            legado = es_factor_legado(r)
            formulas={n['factor']:f'={I}{f}/{I0}{f}' if legado else f'=1+ROUND(({I}{f}/{I0}{f}-1)*100,2)/100',
                      n['diferencia']:f'=({F}{f}-1)*100' if legado else f'=ROUND(({F}{f}-1)*100,2)'}
            d=desglose_presupuestal(r,r.get('valor_proyectado'));modo=validar_modalidad(r)
            if modo=='unitario':
                formulas.update({n['base_unitaria']:f'={P}{f}-{A}{f}',n['valor_unitario']:f'={BU}{f}+{BU}{f}*({F}{f}-1)'})
                if d['base_total'] is not None:formulas[n['base_total']]=f'={BU}{f}*{Q}{f}'
                if d['valor_total'] is not None:formulas[n['valor_total']]=f'={VU}{f}*{Q}{f}'
            elif modo=='total':
                formulas.update({n['base_total']:f'={P}{f}-{A}{f}',n['valor_total']:f'={BT}{f}+{BT}{f}*({F}{f}-1)'})
                if d['base_unitaria'] is not None:formulas[n['base_unitaria']]=f'={BT}{f}/{Q}{f}'
                if d['valor_unitario'] is not None:formulas[n['valor_unitario']]=f'={VT}{f}/{Q}{f}'
            for col,formula in formulas.items():
                ws.cell(f,col,formula);estilo_escenario(ws.cell(f,col))
            ws.cell(f,n['diferencia']).number_format='#,##0.00';ws.cell(f,n['factor']).number_format='#,##0.00000000' if legado else '0.0000'
            for clave in ('cantidad','precio_base','anticipo','i0_icociv','i_icociv'):estilo_escenario(ws.cell(f,n[clave]),editable=True)
            if r.get('calculo_id') and ids.count(r['calculo_id'])==1:
                hoja=f"'{ws.title}'!"
                principal=hoja+(VU if modo=='unitario' else VT)+str(f) if modo!='heredado' else f'({hoja}{P}{f}-{hoja}{A}{f})+({hoja}{P}{f}-{hoja}{A}{f})*({hoja}{F}{f}-1)'
                referencias[-1]={'valor':principal,'cantidad':f'{hoja}{Q}{f}',**{k:f'{hoja}{L[k]}{f}' for k in IMPORTES_TIPIFICADOS}}
        return referencias


    def _escribir_valores_excel(self, ws) -> None:
        encabezados = [titulo for _, titulo in COLUMNAS_VALORES_TECNICAS]
        from app_icociv.interfaz.widgets.empalme_iccp_icociv import (
            _escribir_titulo_seccion_excel,
            _estilo_celda_tabla,
            _estilo_encabezado_tabla,
        )

        fila = _escribir_titulo_seccion_excel(ws, 1, "Valores proyectados ICOCIV", max(11, len(encabezados)))
        for columna, titulo in enumerate(encabezados, start=1):
            _estilo_encabezado_tabla(ws.cell(row=fila, column=columna, value=titulo))
        ws.row_dimensions[fila].height = 40
        base_datos = fila + 1
        for indice, r in enumerate(self.valores):
            fila += 1
            f = fila
            valores = [
                indice + 1,
                r.get("item", ""),
                r.get("unidad", ""),
                _numero_excel(r.get("cantidad")),
                _numero_excel(r.get("precio_base")),
                _numero_excel(r.get("anticipo_amortizado")),
                f"=E{f}-F{f}",  # base = P - A
                r.get("ruta_icociv", ""),
                _numero_excel(r.get("i0_icociv")),
                _numero_excel(r.get("i_icociv")),
                f"=IF(I{f}=0,0,J{f}/I{f})",  # factor = I / I0
                f'=IF(I{f}=0,0,(E{f}-F{f})*((J{f}/I{f})-1))',  # R
                f"=(E{f}-F{f})+L{f}",  # valor proyectado
                f'=IF((E{f}-F{f})=0,0,(L{f}/(E{f}-F{f}))*100)',  # diferencia %
                r.get("modelo_proyeccion", ""),
                r.get("horizonte", ""),
                str(r.get("fecha_calculo", "")),
                r.get("observacion_tecnica", ""),
            ]
            for columna, valor in enumerate(valores, start=1):
                celda = ws.cell(row=f, column=columna, value=valor)
                _estilo_celda_tabla(celda)
                if columna in (2, 3, 8, 15, 17, 18) and isinstance(valor, str):
                    celda.data_type = 's'
            for columna in (5, 6, 7, 12, 13):
                ws.cell(row=f, column=columna).number_format = FORMATO_MONEDA_EXCEL
            for columna in (9, 10):
                ws.cell(row=f, column=columna).number_format = FORMATO_INDICE_EXCEL
        _ = base_datos

    def _escribir_trazabilidad_excel(self, ws) -> None:
        filas = []
        for i,r in enumerate(self.valores,1):
            e,estado = self.escenario_registro(r);a = self._analisis_comparacion.get(r.get('analisis_id'),{})
            modificado = e != r
            originales = [r.get(k) for k in ('factor_icociv','r_total','valor_proyectado','diferencia_porcentual')]
            efectivos = [e.get(k) if modificado else None for k in ('factor_icociv','r_total','valor_proyectado','diferencia_porcentual')]
            externa = self._referencias_externas.get(r.get('analisis_id'),{}).get(self.fechas_registro(r)[0]) if modificado else None
            origen = (f"Anexo posterior {Path(externa['archivo']).name} · huella {externa['huella_fuente'][:12]} · aplicado {externa['aplicado']}" if externa
                      else 'Snapshot del análisis' if r.get('analisis_id') in self._analisis_comparacion else 'Registro sin vínculo')
            filas.append([i,r.get('calculo_id',''),r.get('analisis_id',''),a.get('nombre',''),r.get('ruta_icociv',''),a.get('archivo_excel',''),
                periodo_mensual(r.get('periodo_base')) or '',r.get('i0_icociv'),*self.fechas_registro(r)[:1],e.get('i0_icociv'),
                self.fechas_registro(r)[1],r.get('i_icociv'),estado,*originales,*efectivos,origen,'Sí' if modificado else 'No'])
        _escribir_tabla_excel(ws,1,'Original registrado y referencia efectiva; evidencia íntegra en la sesión JSON',
            ['N.º','ID cálculo','ID análisis','Análisis','Serie / ruta','Archivo fuente','Periodo I0 original','I0 original',
             'Periodo I0 efectivo','I0 efectivo','Periodo objetivo','I proyectado guardado','Estado fuente / vínculo',
             'Factor original','R original','Valor original','Diferencia original (%)',
             'Factor modificado','R modificado','Valor modificado','Diferencia modificada (%)',
             'Origen del I0 efectivo','Actualización expresa'],filas)
        for fila in ws.iter_rows(min_row=3):
            for celda in fila:
                if isinstance(celda.value,(int,float)):celda.number_format='#,##0.00000000' if celda.column in (14,18) else '#,##0.000'



def _texto_formulas(L: dict[str, str]) -> str:
    """Descripción de las fórmulas con las letras reales de esta exportación."""
    Q,P,A,BU,BT,I0,I,F,VU,VT,D=(L[k] for k in ('cantidad','precio_base','anticipo','base_unitaria','base_total','i0_icociv','i_icociv','factor','valor_unitario','valor_total','diferencia'))
    return (f'{F}3: ={I}3/{I0}3; {D}3: =({F}3-1)*100. Unitario: {BU}3={P}3-{A}3, {BT}3={BU}3*{Q}3, {VU}3={BU}3+{BU}3*({F}3-1), {VT}3={VU}3*{Q}3. '
            f'Total: {BT}3={P}3-{A}3, {BU}3={BT}3/{Q}3, {VT}3={BT}3+{BT}3*({F}3-1), {VU}3={VT}3/{Q}3. '
            'Sin clasificar: los cuatro importes tipificados quedan vacíos; principal consultable en Trazabilidad.')


def _extraer_contexto(resultado_ui: dict[str, Any]) -> dict[str, Any]:
    proyeccion = resultado_ui.get("proyeccion", {}) or {}
    solicitado = proyeccion.get("resultado_horizonte_solicitado", {}) or {}
    info = proyeccion.get("analisis_horizontes_completo") or proyeccion.get("horizonte_info") or {}
    if "alcance_maximo_proyeccion" not in info:
        info = proyeccion.get("horizonte_info", {}) or {}
    serie_df = resultado_ui.get("serie_df")
    indice_base = None
    periodo_base = ""
    periodo_inicial_serie = ""
    if isinstance(serie_df, pd.DataFrame) and not serie_df.empty and "Indice" in serie_df.columns:
        indice_base = float(serie_df["Indice"].iloc[-1])
        if "Periodo" in serie_df.columns:
            periodo_base = str(serie_df["Periodo"].iloc[-1])
            periodo_inicial_serie = str(serie_df["Periodo"].iloc[0])
    ruta = resultado_ui.get("ruta_jerarquica") or []
    ruta_sin_tabla = [item for item in ruta if item.get("nivel") != "Tabla ICOCIV"]
    metricas = (proyeccion.get("backtesting", {}) or {}).get("metricas", {}) or {}
    periodo_ini_proy, periodo_fin_proy = _ventana_proyeccion(proyeccion, periodo_base)
    return {
        "proyeccion_generada": bool(solicitado.get("proyeccion_generada")) and solicitado.get("indice_proyectado") is not None,
        "ruta": ruta,
        "ruta_texto": " · ".join(item.get("valor", "") for item in ruta_sin_tabla) or "Ruta no disponible",
        "serie_final": ruta_sin_tabla[-1]["valor"] if ruta_sin_tabla else "",
        "tabla_icociv": resultado_ui.get("fuente_visible", ""),
        "indice_base": indice_base,
        "periodo_base": periodo_base,
        "indice_proyectado": solicitado.get("indice_proyectado"),
        "periodo_proyectado": periodo_fin_proy or solicitado.get("periodo_proyectado") or proyeccion.get("periodo_proj", ""),
        "periodo_inicial_serie": periodo_inicial_serie,
        "fecha_final_serie": periodo_base,
        "fecha_inicial_proyeccion": periodo_ini_proy,
        "fecha_final_proyeccion": periodo_fin_proy,
        "horizonte_solicitado": solicitado.get("horizonte_solicitado"),
        "maximo_recomendado": info.get("alcance_maximo_proyeccion"),
        "estado": solicitado.get("estado"),
        "modelo": solicitado.get("modelo_aplicado") or proyeccion.get("model_name"),
        "metricas": metricas,
        "advertencia": solicitado.get("razon_principal") or "",
    }


def _ventana_proyeccion(proyeccion: dict[str, Any], periodo_base: str) -> tuple[str, str]:
    """Devuelve (primer periodo proyectado, último periodo proyectado) en ISO.

    Usa la tabla de proyecciones de la app cuando existe; si no, calcula desde
    el último periodo observado + horizonte.
    """
    proy_df = proyeccion.get("proyecciones")
    if isinstance(proy_df, pd.DataFrame) and not proy_df.empty and "periodo" in proy_df.columns:
        periodos = [str(p) for p in proy_df["periodo"].tolist() if str(p).strip()]
        if periodos:
            return _periodo_iso(periodos[0]), _periodo_iso(periodos[-1])
    solicitado = proyeccion.get("resultado_horizonte_solicitado", {}) or {}
    horizonte = solicitado.get("horizonte_solicitado") or proyeccion.get("horizonte_solicitado")
    if periodo_base and horizonte:
        try:
            anio, mes = (int(x) for x in str(periodo_base).replace("-", "_").split("_")[:2])
            inicio = _sumar_meses(anio, mes, 1)
            fin = _sumar_meses(anio, mes, int(horizonte))
            return inicio, fin
        except (TypeError, ValueError):
            return "", ""
    return "", ""


def _sumar_meses(anio: int, mes: int, delta: int) -> str:
    total = anio * 12 + (mes - 1) + delta
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _periodo_iso(periodo: Any) -> str:
    texto = str(periodo or "").strip().replace("/", "_").replace("-", "_")
    partes = [p for p in texto.split("_") if p]
    if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
        return f"{int(partes[0]):04d}-{int(partes[1]):02d}"
    return str(periodo or "")


_ESTADOS = {
    "proyeccion_tecnica": "Proyección técnica",
    "escenario": "Escenario",
    "no_admisible": "No admisible",
}


def _fila_proyeccion(contexto: dict[str, Any]) -> dict[str, Any]:
    metricas = contexto.get("metricas", {}) or {}
    maximo = contexto.get("maximo_recomendado")
    return {
        "calculo_id": uuid4().hex[:8],
        "item": contexto.get("serie_final", ""),
        "item_ruta": contexto.get("ruta_texto", ""),
        "tabla_icociv": contexto.get("tabla_icociv", ""),
        "serie_final": contexto.get("serie_final", ""),
        "fecha_final_serie": _periodo_iso(contexto.get("fecha_final_serie")),
        "fecha_inicial_proyeccion": contexto.get("fecha_inicial_proyeccion", ""),
        "fecha_final_proyeccion": contexto.get("fecha_final_proyeccion", ""),
        "periodo_proyectado": contexto.get("periodo_proyectado", ""),
        "indice_base": _fmt_indice(contexto.get("indice_base")),
        "indice_proyectado": _fmt_indice(contexto.get("indice_proyectado")),
        "periodo_proyectado": contexto.get("periodo_proyectado", ""),
        "horizonte_solicitado": _entero(contexto.get("horizonte_solicitado")),
        "maximo_recomendado": f"{int(maximo)} meses" if maximo else "No identificado",
        "estado": _ESTADOS.get(str(contexto.get("estado")), "No evaluado"),
        "modelo": str(contexto.get("modelo") or "No aplica"),
        # P0-C / C2: no se publica intervalo; se dice, no se deja "No aplica".
        "ic95": "No se publica en esta versión",
        "mae": _fmt_indice(metricas.get("mae")),
        "rmse": _fmt_indice(metricas.get("rmse")),
        "mape": _fmt_porcentaje(metricas.get("mape")),
        "smape": _fmt_porcentaje(metricas.get("smape")),
        "mase": _fmt_indice(metricas.get("mase")),
        "advertencia": str(contexto.get("advertencia") or ""),
        "fecha_calculo": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def _dataframe_valores(valores: list[dict[str, Any]], columnas=None, fechas=None) -> pd.DataFrame:
    columnas = columnas or COLUMNAS_VALORES
    fechas = fechas or [('', '')] * len(valores)
    filas=[]
    for numero,(r,(fecha_i0,fecha_i)) in enumerate(zip(valores,fechas),1):
        d=desglose_presupuestal(r,r.get('valor_proyectado'))
        fila={'numero':numero,'proyecto':r.get('proyecto',''),'componente':r.get('nombre_componente',''),
              'item':r.get('item',''),'unidad':r.get('unidad',''),'cantidad':r.get('cantidad'),
              'precio_base':numero_original(r.get('precio_base')),'anticipo':numero_original(r.get('anticipo_amortizado')),
              'i0_icociv':numero_original(r.get('i0_icociv')),'i_icociv':numero_original(r.get('i_icociv')),
              'factor':numero_original(r.get('factor_icociv')),'diferencia':numero_original(r.get('diferencia_porcentual')),
              'observacion':r.get('observacion_tecnica',''),'fecha_i0':fecha_i0 or '—','fecha_i':fecha_i or '—',**d}
        filas.append([fila[k] for k,_ in columnas])
    return pd.DataFrame(filas,columns=[t for _,t in columnas],dtype=object)


def _dataframe(filas: list[dict[str, Any]], columnas: list[tuple[str, str]]) -> pd.DataFrame:
    titulos = [titulo for _, titulo in columnas]
    registros = [{titulo: fila.get(clave, "") for clave, titulo in columnas} for fila in filas]
    return pd.DataFrame(registros, columns=titulos)


def _detalle_texto(fila: dict[str, Any], columnas: list[tuple[str, str]]) -> str:
    numericas = {"indice_base", "indice_proyectado", "mae", "rmse", "mape", "smape", "mase"}
    return "\n".join(f"{titulo}: {numero_tecnico_ui(fila.get(clave, '')) if clave in numericas else detalle_ui(fila.get(clave, ''))}"
                     for clave, titulo in columnas)


def _seleccion(tabla: QTableView) -> int | None:
    indices = tabla.selectionModel().selectedRows() if tabla.selectionModel() else []
    if indices:
        return indices[0].row()
    actual = tabla.currentIndex()
    return actual.row() if actual.isValid() else None


def _entero(valor: Any) -> Any:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return "No disponible"
