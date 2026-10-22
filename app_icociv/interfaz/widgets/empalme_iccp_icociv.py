"""Widget independiente para actualización de precios ICCP -> ICOCIV."""

from __future__ import annotations

from datetime import datetime
from copy import deepcopy
from html import escape
from math import isfinite
from pathlib import Path
import re
import json
from typing import Any, Callable
from uuid import uuid4

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PySide6.QtCore import Qt, Signal, QModelIndex, QItemSelectionModel
from PySide6.QtGui import QAction,QKeySequence,QFont
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from app_icociv.utilidades.importes_presupuestales import MODALIDADES, OPCIONES_INGRESO, PREGUNTA_INGRESO, AVISO_INTERPRETACION, validar_modalidad, desglose_presupuestal, texto_desglose
from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.interfaz.estilos.constantes_visuales import ALTURA_CONTROL, ANCHO_BOTON_INCREMENTO
from app_icociv.interfaz.widgets.modelo_tabla import ModeloTablaPandas
from app_icociv.interfaz.widgets.tabla_numerica import ModeloTablaNumerica,TablaCopiable,numero_original,variacion_indice,texto_numero
from app_icociv.interfaz.widgets.acciones_tablas import BarraAccionesTablas
from app_icociv.exportables.archivo_atomico import guardar_atomico
from app_icociv.interfaz.widgets.numerico_icociv import NumeroICOCIV
from app_icociv.proyeccion.servicio_proyeccion import H_OPERATIVO_MAX, resolver_fila_seleccionada
from app_icociv.servicios.empalme_iccp_icociv import calcular_empalme_iccp_icociv, normalizar_periodo_empalme, series_iccp_por_tipo
from app_icociv.utilidades.nomenclatura_icociv import nombre_nivel, texto_checkbox


AYUDAS = {
    "fecha_inicial": "Fecha desde la cual se inicia la actualización del precio. Puede corresponder a fecha base contractual, cierre del proceso licitatorio, propuesta, firma, no objeción u otra fecha técnicamente justificada.",
    "fecha_final": "Fecha hasta la cual se desea actualizar el precio. Puede corresponder al mes de ejecución, acta, comparación o mes final definido por el usuario.",
    "precio": "Valor inicial que se desea actualizar. Puede ser el precio de un insumo, ítem, APU, acta parcial o componente contractual.",
    "anticipo": "Valor del anticipo ya amortizado que debe descontarse de la base de cálculo. Si no aplica, ingrese cero.",
    "base": "Base ajustable = P - A. Es el valor realmente sujeto a actualización.",
    "cantidad": "Cantidad del insumo o ítem actualizado. Puede usarse para calcular valores totales cuando aplique.",
    "unidad": "Unidad de medida: KG, M3, M2, ML, unidad, global, entre otras.",
    "grupo_iccp": "Grupo del ICCP usado para el primer tramo. Debe seleccionarse según criterio técnico del ingeniero.",
    "ruta_icociv": "Ruta jerárquica ICOCIV equivalente al grupo ICCP o insumo analizado. La selección es manual y debe justificarse técnicamente.",
    "observacion": "Justifique la equivalencia, fecha usada o cualquier criterio técnico aplicado en el empalme.",
    "p0": "P0 corresponde al valor base del insumo acero que será ajustado: ofertado, contractual o valor de acta parcial, según el caso.",
    "ix": "Ix corresponde al valor real facturado por kilogramo de acero, según factura, cotización u orden de compra validada.",
    "q": "q corresponde a la cantidad de kilogramos de acero ejecutados o reconocidos en el periodo analizado.",
}

AYUDAS.update(
    {
        "tipo_serie_iccp": "Define si el cálculo ICCP usará Total ICCP, Canasta general o Grupo de obra. Solo puede usarse una categoría.",
        "serie_iccp": "Serie ICCP activa tomada del Anexo 10 histórico; se usa para calcular I0 ICCP, I ICCP, factor ICCP y R1.",
        "canasta_general_iccp": "Serie general del ICCP tomada del Anexo 10 histórico.",
        "z": "Valor adicional por fluctuación del acero, cuando aplique.",
    }
)

COLUMNAS_EQUIVALENCIAS = [
    ("insumo_contractual", "INSUMO CONTRACTUAL"),
    ("grupo_iccp_equivalente", "GRUPO DE OBRA EQUIVALENTE ICCP"),
    ("insumo_icociv_equivalente", "INSUMO EQUIVALENTE ICOCIV"),
]

COLUMNAS_VALOR_AJUSTADO = [
    ("insumo_contractual", "INSUMO CONTRACTUAL"),
    ("unidad", "UNIDAD"),
    ("precio_base", "PRECIO INSUMO CONTRACTUAL-APU"),
    ("i0_iccp", "ÍNDICE ICCP INICIAL (I0)"),
    ("i_iccp", "ÍNDICE ICCP FINAL (I)"),
    ("r1", "R1"),
    ("i0_icociv", "ÍNDICE ICOCIV INICIAL (I0)"),
    ("i_icociv", "ÍNDICE ICOCIV FINAL (I)"),
    ("r2", "R2"),
    ("r_total", "VALOR DEL AJUSTE (R)"),
    ("valor_actualizado", "VALOR INSUMO AJUSTADO"),
]

COLUMNAS_DETALLE_EXPORTACION = [
    ("calculo_id", "ID cálculo"),
    ("numero_calculo", "N°"),
    ("codigo_item", "Código"),
    ("tipo_calculo", "Tipo"),
    ("fecha_inicial", "Fecha inicial"),
    ("fecha_final", "Fecha final"),
    ("ruta_iccp", "Ruta ICCP"),
    ("ruta_icociv", "Ruta ICOCIV"),
    ("diferencia_absoluta", "Diferencia absoluta"),
    ("icociv_final_es_proyectado", "ICOCIV final proyectado"),
    ("ultimo_periodo_icociv_real", "Último periodo ICOCIV real"),
    ("indice_icociv_final_proyectado", "Índice ICOCIV final proyectado"),
    ("modelo_proyeccion", "Modelo proyección"),
    ("horizonte_usado", "Horizonte usado"),
    ("estado_horizonte", "Estado horizonte"),
    ("advertencias_proyeccion", "Advertencias proyección"),
    ("observacion_tecnica", "Observación técnica"),
    ("fecha_calculo", "Fecha cálculo"),
    ("trazabilidad_formula", "Desarrollo matemático"),
]

UNIDADES_INGENIERIA = ["m lineal", "m2", "m3", "kg", "Unidad", "Global"]
HOJA_EXPORTACION_EMPALME = "Empalme ICCP-ICOCIV"
FORMATO_MONEDA_EXCEL = '$ #,##0.00'
FORMATO_INDICE_EXCEL = '#,##0.00'
FORMATO_FACTOR_EXCEL = '0.000000'
COLUMNA_VARIACION_INDICE = "Variación del índice (%)"

COLUMNAS_OPERATIVAS = [
    ("numero_calculo", "N.º"), ("contrato", "Proyecto"), ("nombre_componente", "Componente del proyecto"),
    ("item", "Ítem / insumo"), ("codigo_item", "Código"), ("unidad", "Unidad"), ("cantidad", "Cantidad"),
    ("base_unitaria", "Base ajustable unitaria (COP)"), ("base_total", "Base ajustable total (COP)"),
    ("fecha_inicial", "Período inicial"), ("fecha_final", "Período final"),
    ("escenario", "Escenario"), ("r_total", "Valor del ajuste R (COP)"),
    ("valor_unitario", "Valor ajustado unitario (COP)"), ("valor_total", "Valor ajustado total (COP)"),
    ("variacion_valor", "Variación del valor (%)"), ("observacion_tecnica", "Observación técnica"), ("calculo_id", "ID cálculo"),
]
DECIMALES_OPERATIVOS = {"N.º": 0, "Cantidad": 4, "Base ajustable unitaria (COP)": 2, "Base ajustable total (COP)": 2,
    "Valor del ajuste R (COP)": 2, "Valor ajustado unitario (COP)": 2, "Valor ajustado total (COP)": 2, "Variación del valor (%)": 3}


def _escenario_operativo(r):
    escenario = {"solo_iccp": "ICCP", "solo_icociv": "ICOCIV", "empalme_completo": "Transición ICCP–ICOCIV"}.get(r.get("caso"), "")
    return " · ".join(v for v in (escenario, "Acero" if str(r.get("tipo_calculo", "")).lower().endswith("acero") else "") if v)


def _fila_operativa(r):
    fila = {k: r.get(k) for k, _ in COLUMNAS_OPERATIVAS}
    fila.update(base_ajustable=r.get("base_ajustable"),valor_actualizado=r.get("valor_actualizado"))
    fila.update(desglose_presupuestal(r,r.get("valor_actualizado")))
    for k in ("fecha_inicial", "fecha_final"):
        try:
            anio, mes = _periodo_partes(r.get(k))
            fila[k] = f"{anio}-{mes:02d}"
        except (ValueError, TypeError):
            fila[k] = r.get(k) or ""
    fila["escenario"] = _escenario_operativo(r)
    base, ajuste = numero_original(r.get("base_ajustable")), numero_original(r.get("r_total"))
    fila["variacion_valor"] = (ajuste / base) * 100 if base is not None and base > 0 and ajuste is not None else None
    return fila


class _ModeloOperativoEmpalme(ModeloTablaNumerica):
    def __init__(self):
        super().__init__(DECIMALES_OPERATIVOS)
        self._dataframe = pd.DataFrame(columns=[titulo for _, titulo in COLUMNAS_OPERATIVAS])
        self.registros = []

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation==Qt.Horizontal and role==Qt.DisplayRole and section in (7,8,13,14):
            return COLUMNAS_OPERATIVAS[section][1].replace(' unitaria','\nunitaria').replace(' unitario','\nunitario').replace(' total','\ntotal')
        return super().headerData(section,orientation,role)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.UserRole + 1:
            return self.registros[index.row()].get("calculo_id")
        if role == Qt.UserRole and index.column() == 0:
            return self.registros[index.row()].get("numero_calculo")
        if index.column() in (7,8,13,14):
            modo=validar_modalidad(self.registros[index.row()])
            declarado=index.column() in ((7,13) if modo=="unitario" else (8,14)) and modo!="heredado"
            if role==Qt.DisplayRole and super().data(index,Qt.UserRole) is None:return "—"
            if role==Qt.FontRole and declarado:
                fuente=QFont();fuente.setBold(True);return fuente
        if role == Qt.ToolTipRole:
            from app_icociv.persistencia.historial_empalme import campos_componente
            r = self.registros[index.row()]
            valor = self._dataframe.iat[index.row(), index.column()]
            contexto = "\n".join(f"{k}: {v}" for k, v in campos_componente(r))
            if index.column() in (7,8,13,14):
                contexto += "\n" + ("Importe sin clasificar; originales en resumen y detalle" if modo=="heredado" else "Importe original declarado" if declarado else "Conversión complementaria por Cantidad")
            return _tooltip(f"{'' if pd.isna(valor) else valor}\nID cálculo: {r.get('calculo_id') or 'No registrado'}\n{contexto}")
        return super().data(index, role)


from app_icociv.interfaz.widgets.controles import (
    ComboBoxSinRueda,
    SpinEnteroSinRueda,
    SpinSinRueda,
)


class WidgetEmpalmeICCPICOCIV(QWidget):
    """Pestaña de cálculo contractual con trazabilidad acumulativa."""

    historial_cambiado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("empalme_iccp_icociv")
        self.controlador_icociv = ControladorPrincipal()
        self.calculos: list[dict[str, Any]] = []
        self.historial_empalme = []
        self.analisis_empalme_activo_id = None
        self._formulario_limpio = None
        self._datos_sesion_adicionales = {}
        self.indice_edicion: int | None = None
        # Asincrono: (seleccion, anio, mes, al_terminar) -> None. `al_terminar`
        # se invoca como (resultado, None) en exito o (None, mensaje) en error,
        # una vez que el worker en segundo plano termina. Ver
        # `ventana_principal._ejecutar_proyeccion_para_empalme_async`.
        self.callback_proyeccion_icociv: (
            Callable[[dict[str, Any], int, int, Callable[[dict[str, Any] | None, str | None], None]], None] | None
        ) = None
        self.modelo_equivalencias = ModeloTablaPandas()
        self.modelo_valor_ajustado = ModeloTablaNumerica({COLUMNA_VARIACION_INDICE:3})
        self.modelo_operativo = _ModeloOperativoEmpalme()
        self._registros_por_fila = []
        self._seleccion_clave = None
        self._sincronizando_seleccion = False
        self._tabla_tecnica_activa = 1
        self._crear_interfaz()
        for widget in self.findChildren(QWidget):
            if widget.toolTip():
                widget.setToolTip(_tooltip(widget.toolTip()))
        self._actualizar_controles_selector(False)
        self._formulario_limpio = self._estado_formulario()
        self._refrescar_historial()

    def configurar_proyeccion_icociv(
        self,
        callback: Callable[[dict[str, Any], int, int, Callable[[dict[str, Any] | None, str | None], None]], None],
    ) -> None:
        """Conecta el empalme con el flujo de proyección ICOCIV existente (asíncrono)."""
        self.callback_proyeccion_icociv = callback

    def _estado_formulario(self):
        return [self.item.text(), self.codigo.text(), self.unidad.currentData(),
                *[getattr(self, k).value() for k in ('cantidad', 'precio_base', 'anticipo', 'p0', 'ix', 'q')],
                self._periodo_inicial(), self._periodo_final(), self.chk_acero.isChecked(),
                self.combo_tipo_iccp.currentData(), self.combo_serie_iccp.currentData(),
                self._seleccion_icociv_actual(), self.observacion_item.toPlainText(),
                self.tipo_componente.currentData(), self.nombre_componente.text(), self.modalidad_importe.currentData()]

    def analisis_empalme_activo(self):
        return next((a for a in self.historial_empalme if a['id'] == self.analisis_empalme_activo_id), None)

    def resultado_analisis_empalme(self, analisis):
        from app_icociv.persistencia.historial_empalme import resultado_analisis
        return resultado_analisis(analisis, self.calculos)

    def _registrar_analisis_empalme(self, resultado, entrada):
        identificador = str(uuid4())
        resultado['analisis_empalme_id'] = identificador
        iguales = [a for a in self.historial_empalme if all(self.resultado_analisis_empalme(a).get(k) == resultado.get(k) for k in ('item', 'fecha_inicial', 'fecha_final', 'tipo_calculo'))]
        numero = len(self.historial_empalme) + 1
        escenario = {'solo_iccp': 'ICCP', 'solo_icociv': 'ICOCIV', 'empalme_completo': 'ICCP → ICOCIV'}[resultado['caso']]
        acero = ' · Acero' if str(resultado['tipo_calculo']).endswith('acero') else ''
        nombre = f"{numero}. {escenario}{acero} · {resultado['item']} · {_periodo_visible(resultado['fecha_inicial'])} → {_periodo_visible(resultado['fecha_final'])} · revisión {len(iguales)+1}"
        self.historial_empalme.append({'id': identificador, 'numero': numero, 'nombre': nombre,
            'creado': resultado['fecha_calculo'], 'calculo_id': resultado['calculo_id'], 'numero_calculo_original': resultado['numero_calculo'],
            'archivo_excel': str(self.controlador_icociv.ruta_archivo or ''),
            'formulario_original': {k: deepcopy(v) for k, v in entrada.items() if resultado.get(k) != v}})
        self.analisis_empalme_activo_id = identificador

    def _archivar_registro(self, registro):
        for a in self.historial_empalme:
            if a['calculo_id'] == registro.get('calculo_id') and 'resultado_archivado' not in a:
                a['resultado_archivado'] = deepcopy(self.resultado_analisis_empalme(a))

    def _refrescar_historial(self):
        s = self.selector_analisis_empalme
        s.blockSignals(True);s.clear()
        s.addItem('Sin análisis activo' if self.historial_empalme else 'Sin análisis de Empalme guardados', None)
        for a in self.historial_empalme:s.addItem(a['nombre'], a['id'])
        s.setCurrentIndex(max(0, s.findData(self.analisis_empalme_activo_id)));s.blockSignals(False)
        a = self.analisis_empalme_activo()
        self.lbl_historial_empalme.setText((a['nombre'] + ' · Instantánea original' if a else 'Calcular actualización crea un análisis. Editar una fila conserva su instantánea original.') )
        self.historial_cambiado.emit()

    def _seleccionar_analisis_empalme(self):
        identificador = self.selector_analisis_empalme.currentData()
        if identificador:self.activar_analisis_empalme(identificador)
        else:self._refrescar_historial()

    def activar_analisis_empalme(self, identificador, confirmar=True):
        a = next((a for a in self.historial_empalme if a['id'] == identificador), None)
        if a is None or getattr(self, '_calculando_historial', False):
            self._refrescar_historial();return False
        if confirmar and (self.indice_edicion is not None or self._formulario_limpio is not None and self._estado_formulario() != self._formulario_limpio):
            if QMessageBox.question(self, 'Cambios sin guardar', 'El formulario tiene cambios sin guardar. ¿Desea descartarlos y consultar el análisis guardado?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                self._refrescar_historial();return False
        r = self.resultado_analisis_empalme(a)
        self.indice_edicion = None
        disponible = self.controlador_icociv.archivo_cargado and str(self.controlador_icociv.ruta_archivo or '') == a['archivo_excel']
        self._restaurar_formulario_empalme({**r, **a.get('formulario_original', {})}, restaurar_ruta=disponible)
        if not disponible:
            # Los selectores muestran referencias guardadas, sin reconstruir un anexo ausente.
            seleccion = r.get('seleccion_icociv') or {}
            for combo, key in ((self.combo_grupo_icociv, 'idx_g'), (self.combo_nivel2, 'idx_l2'), (self.combo_nivel3, 'idx_l3'), (self.combo_nivel4, 'idx_l4'), (self.combo_nivel5, 'idx_l5'), (self.combo_nivel6, 'idx_l6')):
                combo.blockSignals(True);combo.clear();combo.addItem('Referencia guardada', seleccion.get(key));combo.setEnabled(False);combo.blockSignals(False)
            self._actualizar_controles_selector(False)
        self.lbl_ruta_icociv.setText('Ruta ICOCIV guardada: ' + str(r.get('ruta_icociv') or 'No aplica'))
        self.boton_calcular.setText('Calcular actualización')
        self.boton_calcular.setEnabled(bool(disponible or r['caso'] == 'solo_iccp'))
        self._mostrar_resultado(r)
        self.analisis_empalme_activo_id = identificador
        self._formulario_limpio = self._estado_formulario()
        self._refrescar_historial()
        if not disponible and r['caso'] != 'solo_iccp':
            self.lbl_historial_empalme.setText(self.lbl_historial_empalme.text() + ' · Consulta sin fuente. Cargue su archivo ICOCIV para una nueva ejecución.')
        return True

    def datos_sesion(self):
        datos = deepcopy(self._datos_sesion_adicionales)
        datos.update(generales={**datos.get('generales', {}), **self._datos_generales()}, calculos=deepcopy(self.calculos))
        if self.historial_empalme:
            datos.update(historial_empalme=deepcopy(self.historial_empalme), analisis_empalme_activo_id=self.analisis_empalme_activo_id)
        datos.pop('borrador_formulario', None)
        if self.tiene_borrador():
            # Fase 4I-I: el cálculo en curso (aún no registrado) viaja en la sesión tal como está escrito;
            # no se registra ni se calcula. Campo opcional: los JSON anteriores siguen abriéndose igual.
            datos['borrador_formulario'] = self._borrador_formulario()
        return datos

    def tiene_borrador(self) -> bool:
        """Hay un cálculo en el formulario que no coincide con lo registrado/consultado (o una edición abierta)."""
        return self.indice_edicion is not None or (self._formulario_limpio is not None and self._estado_formulario() != self._formulario_limpio)

    def _borrador_formulario(self) -> dict[str, Any]:
        """Entradas literales del formulario, con las mismas claves que usa _restaurar_formulario_empalme."""
        borrador = {
            "tipo_componente": self.tipo_componente.currentData(), "nombre_componente": self.nombre_componente.text(),
            "item": self.item.text(), "codigo_item": self.codigo.text(), "unidad": self.unidad.currentData(),
            "modalidad_importe": self.modalidad_importe.currentData(),
            "cantidad": self.cantidad.value(), "precio_base": self.precio_base.value(), "anticipo_amortizado": self.anticipo.value(),
            "fecha_inicial": self._periodo_inicial(), "fecha_final": self._periodo_final(),
            "tipo_serie_iccp": self.combo_tipo_iccp.currentData(), "serie_iccp": self.combo_serie_iccp.currentData(),
            "seleccion_icociv": self._seleccion_icociv_actual(), "observacion_tecnica": self.observacion_item.toPlainText(),
            "tipo_calculo": "acero" if self.chk_acero.isChecked() else "", "p0": self.p0.value(), "ix": self.ix.value(), "q": self.q.value(),
        }
        if self.indice_edicion is not None:
            borrador["calculo_id_en_edicion"] = self.calculos[self.indice_edicion].get("calculo_id")
        return borrador

    def _restaurar_borrador(self, borrador: dict[str, Any]) -> None:
        """Devuelve al formulario el cálculo en curso guardado; si era la edición de una fila, la reabre."""
        en_edicion = borrador.get("calculo_id_en_edicion")
        indice = next((i for i, r in enumerate(self.calculos) if en_edicion and r.get("calculo_id") == en_edicion), None)
        if indice is not None:
            self.indice_edicion = indice
            self._restaurar_formulario_empalme(self.calculos[indice])
            self.boton_calcular.setText("Actualizar cálculo");self.boton_calcular.setEnabled(True)
            self.boton_limpiar.setText("Cancelar edición");self.aviso_interpretacion_edicion.show()
            self._formulario_limpio = self._estado_formulario()
        self._restaurar_formulario_empalme(borrador, restaurar_ruta=self.controlador_icociv.archivo_cargado)

    def validar_datos_sesion(self, datos):
        from app_icociv.persistencia.historial_empalme import validar_sesion_empalme
        validar_sesion_empalme(datos)

    def restaurar_datos_sesion(self, datos):
        self.validar_datos_sesion(datos)
        datos = deepcopy(datos or {})
        self._datos_sesion_adicionales = datos
        self.calculos = datos.get('calculos', [])
        self.historial_empalme = datos.get('historial_empalme', [])
        self.analisis_empalme_activo_id = datos.get('analisis_empalme_activo_id')
        generales = datos.get('generales', {})
        for k, widget in (('contrato', self.contrato), ('objeto_contrato', self.objeto), ('responsable_tecnico', self.responsable), ('observacion_general', self.observacion_general)):
            (widget.setText if isinstance(widget, QLineEdit) else widget.setPlainText)(str(generales.get(k, '')))
        self.indice_edicion = None
        self._actualizar_tabla();self._refrescar_historial()
        if self.analisis_empalme_activo_id:self.activar_analisis_empalme(self.analisis_empalme_activo_id, confirmar=False)
        else:self.limpiar_formulario();self.resultado.clear();self._formulario_limpio = self._estado_formulario()
        if datos.get('borrador_formulario'):
            self._restaurar_borrador(datos['borrador_formulario'])

    def actualizar_icociv(self, tablas: dict[str, pd.DataFrame], periodos: list[str], ruta_archivo=None) -> None:
        """Carga el mismo árbol jerárquico ICOCIV usado por la app principal."""
        self.controlador_icociv.tablas = tablas
        self.controlador_icociv.periodos = periodos
        self.controlador_icociv.fuente_actual = None
        if ruta_archivo is not None:self.controlador_icociv.ruta_archivo = Path(ruta_archivo)
        self._llenar_combo(self.combo_grupo_icociv, self.controlador_icociv.opciones_grupo())
        self._actualizar_controles_selector(True)
        self._actualizar_jerarquia_icociv()
        self.boton_calcular.setEnabled(True)

    def _crear_interfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        contenido = QWidget()
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        titulo = QLabel("Actualización de precios / Empalme ICCP-ICOCIV")
        titulo.setObjectName("titulo_dashboard")
        subtitulo = QLabel(
            "Módulo independiente para contratos, ítems, insumos o APU. "
            "El ICCP histórico está cargado internamente desde el Anexo 10."
        )
        subtitulo.setWordWrap(True)
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        layout.addWidget(self._grupo_datos_generales())
        historial = QGroupBox('Historial de análisis de Empalme')
        historial_layout = QVBoxLayout(historial)
        self.selector_analisis_empalme = ComboBoxSinRueda()
        self.selector_analisis_empalme.setAccessibleName('Análisis activo del historial de Empalme')
        self.selector_analisis_empalme.currentIndexChanged.connect(self._seleccionar_analisis_empalme)
        self.lbl_historial_empalme = QLabel()
        self.lbl_historial_empalme.setWordWrap(True)
        historial_layout.addWidget(self.selector_analisis_empalme)
        historial_layout.addWidget(self.lbl_historial_empalme)
        layout.addWidget(historial)
        layout.addWidget(self._grupo_periodo())
        layout.addWidget(self._grupo_calculo())
        layout.addWidget(self._grupo_selector_iccp())
        layout.addWidget(self._grupo_selector_icociv())
        layout.addWidget(self._grupo_observacion())
        layout.addWidget(self._grupo_acero())
        layout.addWidget(self._grupo_boton())
        layout.addWidget(self._grupo_resultado())
        layout.addWidget(self._grupo_tabla(), 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(contenido)
        layout_principal.addWidget(scroll)

    def _grupo_datos_generales(self) -> QGroupBox:
        grupo = QGroupBox("1. Datos generales del análisis")
        form = QFormLayout(grupo)
        self.contrato = QLineEdit()
        self.objeto = QTextEdit()
        self.objeto.setMaximumHeight(64)
        self.responsable = QLineEdit()
        self.observacion_general = QTextEdit()
        self.observacion_general.setMaximumHeight(64)
        _fila(form, "Nombre del contrato", self.contrato, "Identificación corta del contrato o análisis.")
        _fila(form, "Objeto / descripción", self.objeto, "Descripción breve del contrato, actividad o conjunto de ítems evaluados.")
        _fila(form, "Responsable técnico", self.responsable, "Nombre del profesional que prepara o revisa el cálculo.")
        _fila(form, "Observación general", self.observacion_general, "Notas generales del análisis, alcance o criterio contractual.")
        return grupo

    def _grupo_periodo(self) -> QGroupBox:
        grupo = QGroupBox("2. Periodo de análisis")
        form = QFormLayout(grupo)
        self.fecha_inicial_anio, self.fecha_inicial_mes = _periodo_spins(2021, 1)
        self.fecha_final_anio, self.fecha_final_mes = _periodo_spins(2024, 8)
        for titulo, anio, mes, ayuda in (("Fecha inicial", self.fecha_inicial_anio, self.fecha_inicial_mes, AYUDAS["fecha_inicial"]),
                                       ("Fecha final", self.fecha_final_anio, self.fecha_final_mes, AYUDAS["fecha_final"])):
            etiqueta = QLabel(titulo)
            etiqueta.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            etiqueta.setMinimumHeight(ALTURA_CONTROL)
            _fila(form, etiqueta, _periodo_widget(anio, mes), ayuda)
        return grupo

    def _grupo_calculo(self) -> QGroupBox:
        grupo = QGroupBox("3. Datos del valor a actualizar")
        grid = QGridLayout(grupo)
        # Importación local: Proyecciones también importa este módulo.
        from .proyecciones_icociv import _SelectorComponente, TIPOS_COMPONENTE, NOMBRES_COMPONENTE
        self._etiquetas_componente = TIPOS_COMPONENTE
        self.tipo_componente = _SelectorComponente()
        self.tipo_componente.addItem("Seleccionar tipo", None)
        for tipo in ("Grupo de obra", "Subclase de obra", "Tipología", "Capítulo", "Actividad", "Ítem", "Insumo", "Otro"):
            self.tipo_componente.addItem(NOMBRES_COMPONENTE.get(tipo, tipo), tipo)
        self.nombre_componente = QLineEdit()
        self.lbl_nombre_componente = QLabel()
        self.lbl_nombre_componente.setBuddy(self.nombre_componente)
        etiqueta_tipo = QLabel("Tipo de componente")
        etiqueta_tipo.setBuddy(self.tipo_componente)
        self.tipo_componente.setAccessibleName("Tipo de componente")
        self.tipo_componente.currentIndexChanged.connect(self._actualizar_etiqueta_componente)
        self._actualizar_etiqueta_componente()
        grid.addWidget(etiqueta_tipo, 0, 0)
        grid.addWidget(self.lbl_nombre_componente, 0, 1)
        grid.addWidget(self.tipo_componente, 1, 0)
        grid.addWidget(self.nombre_componente, 1, 1)
        self.item = QLineEdit()
        self.codigo = QLineEdit()
        self.unidad = ComboBoxSinRueda()
        self._llenar_combo(self.unidad, [{"texto": unidad, "indice": unidad} for unidad in UNIDADES_INGENIERIA])
        self.modalidad_importe = ComboBoxSinRueda()
        for modo,titulo in OPCIONES_INGRESO.items():self.modalidad_importe.addItem(titulo,modo)
        self.modalidad_importe.setAccessibleName("Interpretación de P y A")
        self.modalidad_importe.setMinimumContentsLength(16)
        self.modalidad_importe.setMaximumWidth(360)
        self.modalidad_importe.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.cantidad = _spin(0, 1_000_000_000, 4)
        self.precio_base = _spin(0, 1_000_000_000_000_000, 2)
        self.anticipo = _spin(0, 1_000_000_000_000_000, 2)
        self.precio_base.lineEdit().setPlaceholderText("Ej.: 423467.54")
        self.anticipo.lineEdit().setPlaceholderText("Ej.: 0")
        campos = [
            ("Insumo / ítem", self.item, "Nombre del insumo, actividad, APU o componente contractual."),
            ("Código", self.codigo, "Código interno o contractual del ítem. Es opcional."),
            ("Unidad", self.unidad, AYUDAS["unidad"]),
            ("Cantidad", self.cantidad, "Cantidad presupuestal positiva; necesaria para ambos resultados. Es distinta de q del acero."),
            ("Interpretación de P y A",self.modalidad_importe,AVISO_INTERPRETACION),
            ("Precio o valor base P", self.precio_base, AYUDAS["precio"]),
            ("Anticipo amortizado A", self.anticipo, AYUDAS["anticipo"]),
        ]
        for fila, (etiqueta, widget, ayuda) in enumerate(campos, start=2):
            grid.addWidget(_etiqueta_ayuda(etiqueta, ayuda), fila, 0)
            grid.addWidget(_ayuda(widget, ayuda), fila, 1)
        self.aviso_interpretacion_edicion = QLabel(PREGUNTA_INGRESO+"\n"+AVISO_INTERPRETACION)
        self.aviso_interpretacion_edicion.setWordWrap(True)
        grid.addWidget(self.aviso_interpretacion_edicion,len(campos)+2,0,1,2)
        grid.setColumnStretch(1, 1)
        return grupo

    def _actualizar_etiqueta_componente(self) -> None:
        etiqueta = self._etiquetas_componente.get(self.tipo_componente.currentData(), "Nombre del componente")
        self.lbl_nombre_componente.setText(etiqueta)
        self.nombre_componente.setAccessibleName(etiqueta)

    def _grupo_selector_iccp(self) -> QGroupBox:
        grupo = QGroupBox("4. Serie ICCP")
        form = QFormLayout(grupo)
        self.series_iccp = series_iccp_por_tipo()
        self.combo_tipo_iccp = ComboBoxSinRueda()
        self.combo_tipo_iccp.addItem("Sin selección", None)
        self.combo_tipo_iccp.addItem("Total ICCP", "total_iccp")
        self.combo_tipo_iccp.addItem("Canasta general", "canasta_general")
        self.combo_tipo_iccp.addItem("Grupo de obra", "grupo_obra")
        self.combo_tipo_iccp.currentIndexChanged.connect(lambda _: self._actualizar_series_iccp())
        self.combo_serie_iccp = ComboBoxSinRueda()
        self.combo_serie_iccp.setEnabled(False)
        _fila(form, "Tipo de serie ICCP", self.combo_tipo_iccp, AYUDAS["tipo_serie_iccp"])
        _fila(form, "Serie ICCP", self.combo_serie_iccp, AYUDAS["serie_iccp"])
        self._actualizar_series_iccp()
        return grupo

    def _grupo_observacion(self) -> QGroupBox:
        grupo = QGroupBox("6. Observación técnica del empalme")
        form = QFormLayout(grupo)
        self.observacion_item = QTextEdit()
        self.observacion_item.setMaximumHeight(70)
        _fila(form, "Observación técnica", self.observacion_item, AYUDAS["observacion"])
        return grupo

    def _grupo_acero(self) -> QGroupBox:
        grupo = QGroupBox("7. Cálculo especial para acero")
        form = QFormLayout(grupo)
        self.chk_acero = QCheckBox("Cálculo especial para acero")
        self.chk_acero.setToolTip("Active este cálculo cuando aplique la fórmula especial de fluctuación del acero.")
        self.chk_acero.toggled.connect(self._alternar_acero)
        self.p0 = _spin(0, 1_000_000_000_000_000, 2)
        self.ix = _spin(0, 1_000_000_000, 4)
        self.q = _spin(0, 1_000_000_000, 4)
        form.addRow(self.chk_acero)
        _fila(form, "P0 — Valor base del acero", self.p0, AYUDAS["p0"])
        _fila(form, "Ix — Valor facturado por kilogramo", self.ix, AYUDAS["ix"])
        _fila(form, "q — Cantidad ejecutada en kg", self.q, AYUDAS["q"])
        self._alternar_acero(False)
        return grupo

    def _grupo_boton(self) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        self.boton_limpiar = QPushButton("Limpiar formulario")
        self.boton_limpiar.clicked.connect(self.limpiar_formulario)
        self.boton_calcular = QPushButton("Calcular actualización")
        self.boton_calcular.clicked.connect(self.calcular)
        layout.addWidget(self.boton_limpiar)
        layout.addWidget(self.boton_calcular)
        return contenedor

    def _grupo_selector_icociv(self) -> QGroupBox:
        grupo = QGroupBox("5. Ruta ICOCIV equivalente")
        form = QFormLayout(grupo)
        self.lbl_ruta_icociv = QLabel("Ruta ICOCIV: cargue un archivo y seleccione la jerarquía.")
        self.lbl_ruta_icociv.setWordWrap(True)
        self.lbl_ruta_icociv.setToolTip(AYUDAS["ruta_icociv"])
        self.combo_grupo_icociv = self._combo_selector(lambda: self._reiniciar_desde_nivel2())
        self.chk_t16 = QCheckBox(texto_checkbox("t16_costos"))
        self.chk_t16.stateChanged.connect(lambda _: self._reiniciar_desde_nivel2())
        self.chk_t16_1 = QCheckBox(texto_checkbox("subclase_costos"))
        self.chk_t16_1.stateChanged.connect(lambda _: self._reiniciar_desde_nivel3())
        self.chk_t16_2 = QCheckBox(texto_checkbox("tipologia_costos"))
        self.chk_t16_2.stateChanged.connect(lambda _: self._reiniciar_desde_nivel4())
        self.chk_t16_3 = QCheckBox(texto_checkbox("capitulo_costos"))
        self.chk_t16_3.stateChanged.connect(lambda _: self._reiniciar_desde_nivel5())
        self.combo_nivel2 = self._combo_selector(lambda: self._reiniciar_desde_nivel3())
        self.combo_nivel3 = self._combo_selector(lambda: self._reiniciar_desde_nivel4())
        self.combo_nivel4 = self._combo_selector(lambda: self._reiniciar_desde_nivel5())
        self.combo_nivel5 = self._combo_selector(lambda: self._reiniciar_desde_nivel6())
        self.combo_nivel6 = self._combo_selector(lambda: self._actualizar_jerarquia_icociv())
        self.lbl_nivel2 = QLabel("Nivel 2")
        self.lbl_nivel3 = QLabel("Nivel 3")
        self.lbl_nivel4 = QLabel("Nivel 4")
        self.lbl_nivel5 = QLabel("Nivel 5")
        self.lbl_nivel6 = QLabel("Nivel 6")
        form.addRow(self.lbl_ruta_icociv)
        _fila(form, nombre_nivel("grupo_obra"), self.combo_grupo_icociv, AYUDAS["ruta_icociv"])
        form.addRow(self.chk_t16)
        _fila(form, self.lbl_nivel2, self.combo_nivel2, "Segundo nivel de la jerarquía ICOCIV disponible para el grupo seleccionado.")
        form.addRow(self.chk_t16_1)
        _fila(form, self.lbl_nivel3, self.combo_nivel3, "Tercer nivel de la jerarquía ICOCIV, según la rama seleccionada.")
        form.addRow(self.chk_t16_2)
        _fila(form, self.lbl_nivel4, self.combo_nivel4, "Cuarto nivel de la jerarquía ICOCIV, si aplica.")
        form.addRow(self.chk_t16_3)
        _fila(form, self.lbl_nivel5, self.combo_nivel5, "Quinto nivel de la jerarquía ICOCIV, si aplica.")
        _fila(form, self.lbl_nivel6, self.combo_nivel6, "Nivel de insumo cuando existe desagregación suficiente.")
        self._ocultar_niveles()
        return grupo

    def _grupo_resultado(self) -> QGroupBox:
        grupo = QGroupBox("8. Resultado del cálculo")
        layout = QVBoxLayout(grupo)
        self.resultado = QTextBrowser()
        self.resultado.setMinimumHeight(220)
        self.resultado.setHtml("<p>Ejecute un cálculo para ver I, I0, R1, R2, explicaciones y trazabilidad.</p>")
        layout.addWidget(self.resultado)
        return grupo

    def _grupo_tabla(self) -> QGroupBox:
        grupo = QGroupBox("9. Tablas del análisis")
        layout = QVBoxLayout(grupo)
        self.vistas_tablas = QTabWidget()
        self.vistas_tablas.setAccessibleName("Vistas de tablas de Empalme")
        operativa = QWidget();operativa_layout = QVBoxLayout(operativa)
        self.tabla_operativa = TablaCopiable()
        self.tabla_operativa.setAccessibleName("Registros operativos de Empalme")
        self.tabla_operativa.setModel(self.modelo_operativo)
        self.tabla_operativa.setAlternatingRowColors(True)
        self.tabla_operativa.setSelectionBehavior(QTableView.SelectRows)
        self.tabla_operativa.setSelectionMode(QTableView.SingleSelection)
        self.tabla_operativa.setWordWrap(False)
        self.tabla_operativa.setTextElideMode(Qt.ElideRight)
        self.tabla_operativa.setMinimumHeight(300)
        self.tabla_operativa.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_operativa.verticalHeader().setDefaultSectionSize(32)
        operativa_layout.addWidget(self.tabla_operativa)
        nota = QLabel("Importes en COP. Variación del valor = 100 × R / Base; es distinta de la variación del índice. Cantidad convierte los pares unitario/total; no modifica el cálculo principal.")
        nota.setWordWrap(True);operativa_layout.addWidget(nota)
        tecnica = QWidget();tecnica_layout = QVBoxLayout(tecnica)
        self.vistas_tablas.addTab(operativa, "Vista operativa")
        self.vistas_tablas.addTab(tecnica, "Vista técnica")
        layout.addWidget(self.vistas_tablas)
        self.contexto_registro = QLabel("Seleccione un registro para consultar su componente y detalle.")
        self.contexto_registro.setTextFormat(Qt.PlainText)
        self.contexto_registro.setTextFormat(Qt.PlainText)
        self.contexto_registro.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        layout.addWidget(self.contexto_registro)

        tecnica_layout.addWidget(QLabel("1. Equivalencias ICCP-ICOCIV"))
        self.tabla_equivalencias = TablaCopiable()
        self.tabla_equivalencias.setModel(self.modelo_equivalencias)
        self.tabla_equivalencias.setAlternatingRowColors(True)
        self.tabla_equivalencias.setMinimumHeight(130)
        self.tabla_equivalencias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tecnica_layout.addWidget(self.tabla_equivalencias, 1)

        tecnica_layout.addWidget(QLabel("2. Cálculo del valor ajustado"))
        self.tabla = TablaCopiable()
        self.tabla.setModel(self.modelo_valor_ajustado)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setMinimumHeight(170)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        tecnica_layout.addWidget(self.tabla, 1)

        leyenda=QLabel('Importes en COP. El estado y el periodo de cada índice se conservan en encabezados, ayuda y detalle.')
        leyenda.setWordWrap(True);tecnica_layout.addWidget(leyenda)
        self.barra=BarraAccionesTablas(self,[(self.tabla_equivalencias,'Equivalencias ICCP–ICOCIV'),(self.tabla,'Cálculo del valor ajustado'),(self.tabla_operativa,'Vista operativa de Empalme')],
            lambda i:len(self.calculos),lambda:bool(self.calculos or self.historial_empalme),self.ver_detalle_seleccionado,self.eliminar_seleccionado,self.eliminar_todo,self._exportar_formato)
        layout.addWidget(self.barra)
        self.boton_detalle=self.barra.boton_detalle;self.boton_eliminar=self.barra.boton_eliminar
        self.boton_eliminar_todo=self.barra.boton_todo;self.boton_exportar=self.barra.boton_exportar
        self.accion_editar=QAction('Editar seleccionado',self)
        self.accion_editar.setShortcut(QKeySequence('Ctrl+E'));self.accion_editar.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.accion_editar.triggered.connect(self.editar_seleccionado)
        for i, (tabla, _) in enumerate(self.barra.tablas):
            tabla.addAction(self.accion_editar);tabla.setContextMenuPolicy(Qt.ActionsContextMenu)
            tabla.doubleClicked.connect(lambda index:self.editar_seleccionado())
            tabla.selectionModel().selectionChanged.connect(lambda *args,n=i:self._seleccionar_registro_tabla(n))
        self.vistas_tablas.currentChanged.connect(self._cambiar_vista_tablas)
        self.barra.activa = 2;self.barra.actualizar()
        fuente = self.tabla_operativa.horizontalHeader().fontMetrics()
        for col, (_, titulo) in enumerate(COLUMNAS_OPERATIVAS):
            ancho = max(170 if col in (1,2,3,11,16,17) else 135, fuente.horizontalAdvance(titulo) + 36)
            if col in (7,8,13,14):ancho = max(190,fuente.horizontalAdvance(titulo.split(' unit')[0].split(' total')[0])+36)
            self.tabla_operativa.setColumnWidth(col, ancho)
        self.tabla_operativa.setColumnWidth(0, 55)
        return grupo

    @staticmethod
    def _clave_registro(r):
        return ("id", r["calculo_id"]) if r.get("calculo_id") else ("referencia", id(r))

    def _restaurar_selecciones_tablas(self, origen=None):
        fila = next((i for i,r in enumerate(self._registros_por_fila) if self._clave_registro(r) == self._seleccion_clave), None)
        for i, (tabla, _) in enumerate(self.barra.tablas):
            if i == origen and fila is not None:
                continue
            seleccion = tabla.selectionModel();bloqueada = seleccion.blockSignals(True)
            if fila is None:
                tabla.clearSelection();tabla.setCurrentIndex(QModelIndex())
            else:
                index = tabla.model().index(fila, 0)
                seleccion.select(index, QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                seleccion.setCurrentIndex(index, QItemSelectionModel.NoUpdate)
            seleccion.blockSignals(bloqueada)
        if fila is None:
            self._seleccion_clave = None
            texto = "Seleccione un registro para consultar su componente y detalle."
        else:
            from app_icociv.persistencia.historial_empalme import campos_componente
            r = self._registros_por_fila[fila]
            texto = " · ".join([str(r.get("item") or ""), *[f"{k}: {v}" for k,v in campos_componente(r)]])
        if fila is not None:texto += "\n" + texto_desglose(r,r.get('valor_actualizado'),'Registro económico seleccionado')
        self.contexto_registro.setText(texto);self.contexto_registro.setToolTip(_tooltip(texto))
        self.barra.actualizar()

    def _seleccionar_registro_tabla(self, tabla_indice):
        if self._sincronizando_seleccion:
            return
        tabla = self.barra.tablas[tabla_indice][0]
        filas = {i.row() for i in tabla.selectionModel().selectedIndexes()}
        self.barra.activa = tabla_indice
        if len(filas) != 1:
            self._seleccion_clave = None
            self.contexto_registro.setText('Seleccione una sola fila para consultar su desglose presupuestal.')
            if not filas:
                self._restaurar_selecciones_tablas()
            self.barra.actualizar();return
        fila = filas.pop()
        if fila >= len(self._registros_por_fila):
            return
        self._seleccion_clave = self._clave_registro(self._registros_por_fila[fila])
        self._sincronizando_seleccion = True
        try:
            self.vistas_tablas.setCurrentIndex(0 if tabla_indice == 2 else 1)
            self._restaurar_selecciones_tablas(origen=tabla_indice)
            self.barra.activa = tabla_indice;self.barra.actualizar()
        finally:
            self._sincronizando_seleccion = False

    def _cambiar_vista_tablas(self, vista):
        if self._sincronizando_seleccion:
            return
        if self.barra.activa in (0,1):
            self._tabla_tecnica_activa = self.barra.activa
        self.barra.activa = 2 if vista == 0 else self._tabla_tecnica_activa
        self._restaurar_selecciones_tablas()

    def ver_detalle_seleccionado(self) -> None:
        indice = self._fila_seleccionada()
        if indice is not None:
            self._mostrar_resultado(self.calculos[indice])
            self._dialogo_detalle(self.calculos[indice])

    def _dialogo_detalle(self,registro):
        dialogo=QDialog(self);dialogo.setWindowTitle('Detalle del análisis de Empalme');dialogo.resize(760,560)
        layout=QVBoxLayout(dialogo);texto=QTextBrowser();texto.setHtml(self.resultado.toHtml());layout.addWidget(texto)
        botones=QDialogButtonBox(QDialogButtonBox.Close);editar=botones.addButton('Editar',QDialogButtonBox.ActionRole)
        def abrir_edicion():
            indice=next((i for i,r in enumerate(self.calculos) if r is registro),None)
            if indice is not None:
                self.barra.tablas[self.barra.activa][0].selectRow(indice);self.editar_seleccionado()
            dialogo.accept()
        editar.clicked.connect(abrir_edicion);botones.rejected.connect(dialogo.reject);layout.addWidget(botones);dialogo.exec()

    def _exportar_formato(self,formato):
        self.exportar_excel() if formato=='xlsx' else self.generar_informe(formato)

    def limpiar_formulario(self) -> None:
        if self.indice_edicion is not None:
            r = self.calculos[self.indice_edicion];self._restaurar_formulario_empalme(r)
            self.indice_edicion = None;self.boton_calcular.setText("Calcular actualización");self.boton_limpiar.setText("Limpiar formulario")
            self.aviso_interpretacion_edicion.show()
            self._mostrar_resultado(r);self._formulario_limpio = self._estado_formulario();return
        self.modalidad_importe.setCurrentIndex(0)
        self.indice_edicion = None
        self.tipo_componente.setCurrentIndex(0)
        self.nombre_componente.clear()
        self.item.clear()
        self.codigo.clear()
        self.unidad.setCurrentIndex(0)
        self.cantidad.setValue(0)
        self.precio_base.setValue(0)
        self.anticipo.setValue(0)
        self.combo_tipo_iccp.setCurrentIndex(0)
        self._actualizar_series_iccp()
        self.observacion_item.clear()
        self.chk_acero.setChecked(False)
        self.p0.setValue(0)
        self.ix.setValue(0)
        self.q.setValue(0)
        self.boton_calcular.setText("Calcular actualización")
        self.boton_calcular.setEnabled(True)
        self._formulario_limpio = self._estado_formulario()

    def calcular(self) -> None:
        if self.indice_edicion is not None and self._estado_formulario()[:-1]==self._formulario_limpio[:-1]:
            # Una declaración presupuestal no vuelve a ejecutar el servicio ni el pronóstico.
            r = self.calculos[self.indice_edicion]
            modo = validar_modalidad({'modalidad_importe':self.modalidad_importe.currentData()})
            if modo!=validar_modalidad(r):
                self._archivar_registro(r)
                r = {**r,'modalidad_importe':modo};self.calculos[self.indice_edicion] = r
            self.indice_edicion = None;self.analisis_empalme_activo_id = None
            self.boton_calcular.setText('Calcular actualización');self.boton_limpiar.setText('Limpiar formulario');self.aviso_interpretacion_edicion.show()
            self._mostrar_resultado(r);self._actualizar_tabla();self._formulario_limpio = self._estado_formulario();self._refrescar_historial()
            return
        opcion = self._opcion_icociv_o_vacia()
        fecha_final = self._periodo_final()

        # Validacion de horizonte: PRIMERO, inmediatamente despues de conocer
        # el ultimo periodo ICOCIV disponible y el periodo objetivo, antes de
        # cualquier otra validacion del formulario (item, unidad, serie ICCP).
        # Solo aplica cuando hay ICOCIV resuelto (indices no vacios); si no,
        # no hay horizonte que juzgar y el empalme sigue su camino habitual
        # (por ejemplo, un item que no usa ICOCIV en absoluto).
        horizonte = self._horizonte_meses_icociv(opcion, fecha_final)
        if horizonte is not None and horizonte > H_OPERATIVO_MAX:
            ultimo_real = _ultimo_periodo(opcion["indices"])
            QMessageBox.warning(
                self,
                "Horizonte de proyección fuera del alcance de SAVIP",
                f"El periodo seleccionado requiere proyectar {horizonte} meses desde el último dato "
                f"ICOCIV disponible ({_periodo_visible(ultimo_real)}). SAVIP admite un máximo operativo "
                "de 24 meses. Seleccione una fecha final que no exceda ese límite.",
            )
            self.fecha_final_mes.setFocus()
            return  # datos conservados; nada se ejecuta, nada se guarda.

        try:
            unidad = self.unidad.currentData()
            entrada = {
                "item": self.item.text().strip(),
                "codigo_item": self.codigo.text().strip(),
                "tipo_componente": self.tipo_componente.currentData(),
                "nombre_componente": self.nombre_componente.text(),
                "unidad": str(unidad or ""),
                "cantidad": self.cantidad.value() or None,
                "precio_base": self.precio_base.value(),
                "anticipo_amortizado": self.anticipo.value(),
                "fecha_inicial": self._periodo_inicial(),
                "fecha_final": fecha_final,
                **self._serie_iccp_actual(),
                "ruta_icociv": opcion["ruta"],
                "observacion_tecnica": self.observacion_item.toPlainText().strip(),
                "calculo_acero": self.chk_acero.isChecked(),
                "p0": self.p0.value(),
                "ix": self.ix.value(),
                "q": self.q.value(),
            }
            if self.modalidad_importe.currentData()!='heredado' or self.indice_edicion is not None and 'modalidad_importe' in self.calculos[self.indice_edicion]:
                entrada['modalidad_importe'] = self.modalidad_importe.currentData()
            if not entrada["item"]:
                raise ValueError("Debe ingresar el insumo contractual antes de calcular.")
            if not unidad:
                raise ValueError("Seleccione una unidad válida.")
        except ValueError as exc:
            QMessageBox.warning(self, "Validación empalme", str(exc))
            return

        from .controles import confirmar_ingreso_presupuestal
        if not confirmar_ingreso_presupuestal(self,self.modalidad_importe,entrada["cantidad"]):return
        entrada["modalidad_importe"]=self.modalidad_importe.currentData()

        if horizonte is not None and horizonte >= 1:
            # Necesita proyectar ICOCIV: camino asincrono con el worker de
            # Proyecciones (mismo motor, sin duplicarlo) para que el velo de
            # carga se anime durante todo el calculo en vez de congelarse.
            if self.callback_proyeccion_icociv is None:
                QMessageBox.warning(
                    self,
                    "Validación empalme",
                    "La fecha final solicitada supera el último periodo disponible en el archivo "
                    "ICOCIV, pero el módulo de proyección no está conectado.",
                )
                return
            self.boton_calcular.setEnabled(False)
            self._calculando_historial = True
            anio, mes = _periodo_partes(normalizar_periodo_empalme(fecha_final))

            def _continuar(resultado_ui: dict[str, Any] | None, mensaje_error: str | None) -> None:
                self.boton_calcular.setEnabled(True)
                self._calculando_historial = False
                if mensaje_error is not None:
                    QMessageBox.warning(
                        self, "Validación empalme",
                        f"No fue posible calcular la proyección ICOCIV.\n{mensaje_error}",
                    )
                    return
                try:
                    opcion_final = self._aplicar_resultado_proyeccion(opcion, resultado_ui or {}, fecha_final)
                except ValueError as exc:
                    QMessageBox.warning(self, "Validación empalme", str(exc))
                    return
                self._finalizar_calculo(entrada, opcion_final)

            self.callback_proyeccion_icociv(opcion["seleccion"], anio, mes, _continuar)
            return

        # h<=0 (el dato ya es real) o sin ICOCIV resuelto: camino sincrono,
        # sin popup de carga (no hay nada que proyectar).
        opcion_final = {
            **opcion,
            "metadata_proyeccion": opcion.get("metadata_proyeccion") or {"icociv_final_es_proyectado": False},
        }
        self._finalizar_calculo(entrada, opcion_final)

    def _finalizar_calculo(self, entrada: dict[str, Any], opcion: dict[str, Any]) -> None:
        try:
            validar_modalidad(entrada)
            entrada_economica = {k: v for k, v in entrada.items() if k not in ("tipo_componente", "nombre_componente", "modalidad_importe")}
            resultado = calcular_empalme_iccp_icociv(entrada_economica, opcion.get("indices") or {})
        except ValueError as exc:
            QMessageBox.warning(self, "Validación empalme", str(exc))
            return

        if 'modalidad_importe' in entrada:resultado['modalidad_importe'] = entrada['modalidad_importe']
        if entrada.get('modalidad_importe') in ('unitario','total') and any(x is None for x in desglose_presupuestal(resultado,resultado.get('valor_actualizado')).values()):
            QMessageBox.warning(self,'Desglose no disponible','Los importes o su conversión por Cantidad exceden el rango numérico. Corrija las entradas antes de guardar.')
            return
        resultado.update(self._datos_generales())
        resultado["tipo_componente"] = entrada.get("tipo_componente", self.tipo_componente.currentData())
        resultado["nombre_componente"] = entrada.get("nombre_componente", self.nombre_componente.text())
        resultado["seleccion_icociv"] = opcion["seleccion"]
        resultado["ruta_icociv_estructurada"] = opcion["ruta_estructurada"]
        resultado.update(opcion.get("metadata_proyeccion") or {})
        nuevo = self.indice_edicion is None
        if self.indice_edicion is None:
            self.calculos.append(resultado)
        else:
            self._archivar_registro(self.calculos[self.indice_edicion])
            resultado["calculo_id"] = self.calculos[self.indice_edicion].get("calculo_id")
            if self.calculos[self.indice_edicion].get('analisis_empalme_id'):
                resultado['analisis_empalme_id'] = self.calculos[self.indice_edicion]['analisis_empalme_id']
            self.calculos[self.indice_edicion] = resultado
            self.indice_edicion = None
            self.analisis_empalme_activo_id = None
            self.boton_calcular.setText("Calcular actualización")
        self.boton_limpiar.setText("Limpiar formulario")
        self.aviso_interpretacion_edicion.show()
        self._renumerar()
        if nuevo:
            self._registrar_analisis_empalme(resultado, entrada)
        self._mostrar_resultado(resultado)
        self._seleccion_clave=self._clave_registro(resultado)
        self._actualizar_tabla()
        self._formulario_limpio = self._estado_formulario()
        self._refrescar_historial()

    def editar_seleccionado(self) -> None:
        indice = self._fila_seleccionada()
        if indice is None:
            return
        r = self.calculos[indice]
        self.indice_edicion = indice
        self._restaurar_formulario_empalme(r)
        self.boton_calcular.setText("Actualizar cálculo")
        self.boton_calcular.setEnabled(True)
        self.boton_limpiar.setText("Cancelar edición")
        self.aviso_interpretacion_edicion.show()
        self._formulario_limpio = self._estado_formulario()

    def _restaurar_formulario_empalme(self, r, restaurar_ruta=True) -> None:
        self._establecer_combo_por_data(self.tipo_componente, r.get("tipo_componente"))
        self.nombre_componente.setText(r.get("nombre_componente", ""))
        self.item.setText(str(r.get("item", "")))
        self.codigo.setText(str(r.get("codigo_item", "")))
        self._establecer_combo_por_data(self.unidad, r.get("unidad"))
        self.modalidad_importe.setCurrentIndex(self.modalidad_importe.findData(validar_modalidad(r)))
        self.cantidad.setValue(float(r.get("cantidad") or 0))
        self.precio_base.setValue(float(r.get("precio_base") or 0))
        self.anticipo.setValue(float(r.get("anticipo_amortizado") or 0))
        self._establecer_periodo(self.fecha_inicial_anio, self.fecha_inicial_mes, r.get("fecha_inicial"))
        self._establecer_periodo(self.fecha_final_anio, self.fecha_final_mes, r.get("fecha_final"))
        self._restaurar_iccp(r)
        if restaurar_ruta:
            self._restaurar_seleccion_icociv(r.get("seleccion_icociv") or {})
        else:
            seleccion = r.get('seleccion_icociv') or {}
            for check, key in ((self.chk_t16,'chk_T16'), (self.chk_t16_1,'chk_T16_1'), (self.chk_t16_2,'chk_T16_2'), (self.chk_t16_3,'chk_T16_3')):
                check.blockSignals(True);check.setChecked(bool(seleccion.get(key,False)));check.blockSignals(False)
        self.observacion_item.setPlainText(str(r.get("observacion_tecnica", "")))
        es_acero = str(r.get("tipo_calculo", "")).lower().endswith("acero")
        self.chk_acero.setChecked(es_acero)
        self.p0.setValue(float(r.get("p0") or 0))
        self.ix.setValue(float(r.get("ix") or 0))
        self.q.setValue(float(r.get("q") or 0))

    def eliminar_seleccionado(self) -> None:
        indice = self._fila_seleccionada()
        if indice is None:
            QMessageBox.information(self, "Eliminar", "Seleccione primero una fila de la tabla para eliminarla.")
            return
        self._archivar_registro(self.calculos[indice])
        del self.calculos[indice]
        self.indice_edicion = None
        self.boton_calcular.setText("Calcular actualización")
        self._renumerar()
        self._actualizar_tabla()
        self._refrescar_historial()

    # post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). No toca las
    # fórmulas del empalme (ver calcular_empalme_iccp_icociv); solo vacía la
    # lista de cálculos acumulados y su vista. Exportar Excel/Generar informe
    # ya leen self.calculos por referencia, así que reflejan el vacío solos.
    def eliminar_todo(self) -> None:
        if not self.calculos:
            return
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Warning)
        caja.setWindowTitle("Eliminar todos los registros")
        caja.setText(
            f"Tabla activa: {self.barra.nombre}. ¿Desea eliminar todos los cálculos y sus equivalencias? "
            "Esta acción afecta todas las vistas del módulo en la sesión actual. Los análisis del historial se conservarán."
        )
        boton_eliminar = caja.addButton("Eliminar", QMessageBox.ButtonRole.DestructiveRole)
        caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.exec()
        if caja.clickedButton() is not boton_eliminar:
            return
        for r in self.calculos:self._archivar_registro(r)
        self.calculos.clear()
        self.indice_edicion = None
        self.boton_calcular.setText("Calcular actualización")
        self._renumerar()
        self._actualizar_tabla()
        self._refrescar_historial()

    def exportar_excel(self) -> None:
        if not self.calculos and not self.historial_empalme:
            QMessageBox.information(self, "Exportación", "No hay cálculos para exportar.")
            return
        errores = _errores_exportacion_excel(self.calculos)
        if errores:
            QMessageBox.warning(self, "Exportación", "No se puede exportar:\n- " + "\n- ".join(errores[:8]))
            return
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar cálculos de empalme", "calculos_empalme_iccp_icociv.xlsx", "Excel (*.xlsx)")
        if not ruta:
            return
        if not ruta.lower().endswith(".xlsx"):
            ruta = f"{ruta}.xlsx"
        try:
            self._generar_excel_empalme(ruta)
        except Exception as exc:  # pragma: no cover - mensaje de UI
            QMessageBox.critical(self, "Exportación", f"No fue posible generar el archivo:\n{exc}")
            return
        QMessageBox.information(self, "Exportación", f"Archivo generado: {Path(ruta).name}")

    def generar_informe(self,formato=None) -> None:
        """Informe de ajuste ICCP-ICOCIV en DOCX o PDF, con selector previo."""
        from app_icociv.config.rutas import CARPETA_REPORTES
        from app_icociv.interfaz.widgets.dialogo_informe import pedir_configuracion
        from app_icociv.reportes.modelo import nombre_archivo_informe

        if not self.calculos and not self.historial_empalme:
            QMessageBox.information(self, "Informe", "No hay cálculos para incluir en el informe.")
            return
        configuracion = pedir_configuracion(self, tipo_inicial="empalme", formato="DOCX/PDF", solo_empalme=True)
        if configuracion is None:
            return

        generales = self._datos_generales()
        referencia = configuracion.institucional.contrato or generales.get("contrato") or "Ajuste"
        sugerida = CARPETA_REPORTES / nombre_archivo_informe("empalme", referencia, formato or "docx")
        ruta, filtro = QFileDialog.getSaveFileName(
            self, "Guardar informe de ajuste", str(sugerida),
            ('Documento PDF (*.pdf)' if formato=='pdf' else 'Documento Word (*.docx)' if formato=='docx' else 'Documento Word (*.docx);;Documento PDF (*.pdf)'),
        )
        if not ruta:
            return
        formato = formato or ("pdf" if ruta.lower().endswith(".pdf") or "pdf" in filtro.lower() else "docx")
        if not Path(ruta).suffix:ruta+=f'.{formato}'
        try:
            destino = self._generar_informe(ruta,formato,configuracion)
        except Exception as exc:  # pragma: no cover - mensaje de UI
            QMessageBox.critical(self, "Informe", f"No fue posible generar el informe:\n{exc}")
            return
        QMessageBox.information(self, "Informe", f"Informe generado: {Path(destino).name}")

    def _generar_informe(self,ruta,formato,configuracion=None):
        from app_icociv.reportes.sesion_modulos import construir_empalme,guardar
        registros = self.calculos or [self.resultado_analisis_empalme(a) for a in self.historial_empalme]
        return guardar(construir_empalme(registros,self._datos_generales(),configuracion,self.historial_empalme,operativos=self.calculos),ruta,formato)

    def _generar_excel_empalme(self, ruta: str) -> None:
        """Exporta todos los cálculos y fórmulas en una sola hoja verificable."""
        wb = Workbook()
        ws = wb.active
        ws.title = HOJA_EXPORTACION_EMPALME
        _activar_recalculo_excel(wb)

        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=11)
        celda = ws.cell(row=1, column=1, value="ACTUALIZACIÓN DE PRECIOS CON EMPALME ICCP-ICOCIV")
        celda.font = Font(bold=True, size=14, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="1F2937")
        celda.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 26
        ws.freeze_panes = "A2"

        fila = 3
        fila = _escribir_pares_excel(ws, fila, "Información general", self._filas_info_general_excel())
        fila = _escribir_tabla_excel(ws, fila + 1, "Trazabilidad del cálculo", self._columnas_trazabilidad_excel(), self._filas_trazabilidad_excel())
        for row in ws.iter_rows():
            if row[0].value=='ID CÁLCULO':
                for i in range(row[0].row+1,row[0].row+1+len(self.calculos)):
                    cell=ws.cell(i,18);cell.number_format=('0.00E+00' if cell.value and abs(cell.value)<0.0005 else '#,##0.000')+'" %"'
                break
        fila = _escribir_tabla_excel(
            ws,
            fila + 1,
            "Equivalencias ICCP-ICOCIV",
            [titulo for _, titulo in COLUMNAS_EQUIVALENCIAS],
            [list(self._fila_equivalencia(r).values()) for r in self.calculos],
        )
        fila = self._escribir_calculo_valor_ajustado_excel(ws, fila + 1)
        fila = _escribir_pares_excel(ws, fila + 1, "Metodología general ICCP-ICOCIV", self._filas_metodologia_general_excel())
        if any(r.get("tipo_calculo") == "Cálculo especial acero" for r in self.calculos):
            fila = _escribir_pares_excel(ws, fila, "Metodología especial acero", self._filas_metodologia_acero_excel())
            fila = self._escribir_detalle_acero_excel(ws, fila)
        _escribir_pares_excel(ws, fila, "Observaciones / notas", self._filas_notas_excel())
        from app_icociv.exportables.excel_modulos import agregar_calculos_editables, agregar_resultados_empalme
        agregar_resultados_empalme(wb, self.calculos)
        agregar_calculos_editables(wb, self.calculos, empalme=True)
        if self.historial_empalme:
            ws_historial = wb.create_sheet('Historial de Empalme')
            filas_historial = []
            for a in self.historial_empalme:
                r = self.resultado_analisis_empalme(a)
                texto = json.dumps(a['resultado_archivado'], ensure_ascii=False) if 'resultado_archivado' in a else ''
                partes = [texto[i:i+30000] for i in range(0,len(texto),30000)] or ['']
                for parte, contenido in enumerate(partes,1):
                    filas_historial.append([a['id'],a['numero'],a['nombre'],a['creado'],a['calculo_id'],r.get('contrato',''),
                        r.get('fecha_inicial'),r.get('fecha_final'),r.get('caso'),'Archivado' if texto else 'Vinculado',
                        r.get('valor_actualizado'),contenido,parte if texto else None, r.get("tipo_componente"), r.get("nombre_componente", "")])
            _escribir_tabla_excel(ws_historial, 1, 'Historial independiente de Empalme',
                ['ID análisis', 'N.º', 'Análisis', 'Creado', 'ID cálculo', 'Proyecto al calcular', 'Periodo inicial', 'Periodo final', 'Escenario', 'Estado operativo', 'Valor original SAVIP', 'Registro original archivado JSON', 'Parte', 'Tipo de componente', 'Nombre del componente'], filas_historial)
        referencias = self._agregar_resumen_operativo_excel(wb, ws)
        from app_icociv.exportables.excel_modulos import agregar_desglose_importes
        agregar_desglose_importes(wb['Resultados registrados'],self.calculos,referencias,'valor_actualizado','Registro económico original; Cantidad presupuestal enlazada a la vista operativa, independiente de q')
        archivados = [a['resultado_archivado'] for a in self.historial_empalme if 'resultado_archivado' in a]
        if archivados:agregar_desglose_importes(wb['Historial de Empalme'],archivados,[None]*len(archivados),'valor_actualizado','Instantáneas históricas archivadas; importes fijos')
        for hoja in wb.worksheets:
            _ajustar_hoja_excel(hoja)
        guardar_atomico(ruta,lambda temporal:wb.save(temporal))

    def _agregar_resumen_operativo_excel(self, wb, principal):
        from app_icociv.exportables.excel_modulos import estilo_escenario, validar_cantidad_excel
        resumen=wb.create_sheet('Resumen operativo Empalme')
        filas=[[fila[k] for k,_ in COLUMNAS_OPERATIVAS] for fila in map(_fila_operativa,self.calculos)]
        _escribir_tabla_excel(resumen,1,'Pares según modalidad declarada; Cantidad presupuestal editable, independiente de q; restantes celdas vinculadas o registradas.',[t for _,t in COLUMNAS_OPERATIVAS],filas)
        encabezado_id=next((row[0].row for row in principal if row[0].value=='ID CÁLCULO'),None)
        ids=[r.get('calculo_id') for r in self.calculos];referencias=[]
        for i,r in enumerate(self.calculos):
            fila=i+3;origen=self._fila_datos_calculo+i;referencias.append(None)
            base=numero_original(r.get('base_ajustable'))
            vinculable=(r.get('calculo_id') and ids.count(r['calculo_id'])==1 and encabezado_id is not None
                and principal.cell(encabezado_id+1+i,1).value==r['calculo_id']
                and principal.cell(origen,10).data_type==principal.cell(origen,11).data_type=='f' and base is not None and base>0)
            if vinculable:
                hoja=f"'{principal.title}'!";base_formula=f'({hoja}C{origen}-{hoja}L{origen})';valor=f'{hoja}K{origen}'
                formulas={13:f'={hoja}J{origen}',16:f'=M{fila}/{base_formula}*100'}
                d=desglose_presupuestal(r,r.get('valor_actualizado'));modo=validar_modalidad(r)
                if modo=='unitario':
                    if d['base_unitaria'] is not None:formulas[8]='='+base_formula
                    if d['base_total'] is not None:formulas[9]=f'=H{fila}*G{fila}'
                    if d['valor_unitario'] is not None:formulas[14]='='+valor
                    if d['valor_total'] is not None:formulas[15]=f'=N{fila}*G{fila}'
                elif modo=='total':
                    if d['base_total'] is not None:formulas[9]='='+base_formula
                    if d['base_unitaria'] is not None:formulas[8]=f'=I{fila}/G{fila}'
                    if d['valor_total'] is not None:formulas[15]='='+valor
                    if d['valor_unitario'] is not None:formulas[14]=f'=O{fila}/G{fila}'
                for col,formula in formulas.items():resumen.cell(fila,col,formula)
                estilo_escenario(resumen.cell(fila,7),editable=True)
                op=f"'{resumen.title}'!"
                referencias[-1]={'valor':valor,'cantidad':f'{op}G{fila}',**{k:f'{op}{col}{fila}' for k,col in zip(('base_unitaria','base_total','valor_unitario','valor_total'),'HINO')}}
            for col,(_,titulo) in enumerate(COLUMNAS_OPERATIVAS,1):
                if titulo in DECIMALES_OPERATIVOS:
                    decimales=DECIMALES_OPERATIVOS[titulo]
                    resumen.cell(fila,col).number_format='#,##0'+('.'+'0'*decimales if decimales else '')
        validar_cantidad_excel(resumen,'G',len(filas)+2)
        resumen.freeze_panes='B3';resumen.auto_filter.ref=f'A2:R{len(filas)+2}';resumen.protection.sheet=True
        return referencias

    def _filas_info_general_excel(self) -> list[tuple[str, Any]]:
        datos = self._datos_generales()
        primero = self.calculos[0] if self.calculos else {}
        ultimo = self.calculos[-1] if self.calculos else {}
        return [
            ("Nombre del contrato", datos.get("contrato") or "No registrado"),
            ("Objeto / descripción", datos.get("objeto_contrato") or "No registrado"),
            ("Responsable técnico", datos.get("responsable_tecnico") or "No registrado"),
            ("Fecha inicial del análisis", _periodo_visible(primero.get("fecha_inicial"))),
            ("Fecha final del análisis", _periodo_visible(ultimo.get("fecha_final"))),
            ("Fecha de exportación", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            ("Archivo ICOCIV usado", str(self.controlador_icociv.ruta_archivo or "No registrado")),
            ("Fuente ICCP", "Anexo 10 histórico"),
            ("Observación general", datos.get("observacion_general") or "No registrado"),
        ]

    @staticmethod
    def _columnas_trazabilidad_excel() -> list[str]:
        return [
            "ID CÁLCULO",
            "INSUMO / ÍTEM",
            "FECHA INICIAL",
            "FECHA FINAL",
            "TIPO SERIE ICCP",
            "SERIE ICCP USADA",
            "RUTA ICCP COMPLETA",
            "RUTA ICOCIV COMPLETA",
            "ÍNDICE ICCP INICIAL (I0)",
            "ÍNDICE ICCP FINAL (I)",
            "ÍNDICE ICOCIV INICIAL (I0)",
            "ÍNDICE ICOCIV FINAL (I)",
            "ÍNDICE ICOCIV FINAL PROYECTADO",
            "MODELO DE PROYECCIÓN",
            "ESTADO DEL HORIZONTE",
            "OBSERVACIÓN TÉCNICA",
            "FECHA/HORA DEL CÁLCULO",
            "Variación del índice (%)",
        ]

    def _filas_trazabilidad_excel(self) -> list[list[Any]]:
        filas = []
        for r in self.calculos:
            proyectado = bool(r.get("icociv_final_es_proyectado"))
            filas.append(
                [
                    r.get("calculo_id") or r.get("numero_calculo") or "",
                    _insumo_contractual(r),
                    _periodo_visible(r.get("fecha_inicial")),
                    _periodo_visible(r.get("fecha_final")),
                    r.get("tipo_serie_iccp_visible") or r.get("tipo_serie_iccp") or "",
                    r.get("serie_iccp") or "",
                    r.get("ruta_iccp") or "",
                    r.get("ruta_icociv") or "",
                    _numero_excel(r.get("i0_iccp")),
                    _numero_excel(r.get("i_iccp")),
                    _numero_excel(r.get("i0_icociv")),
                    _numero_excel(r.get("i_icociv")),
                    "Sí" if proyectado else "No aplica",
                    r.get("modelo_proyeccion") if proyectado else "No aplica",
                    r.get("estado_horizonte") if proyectado else "No aplica",
                    r.get("observacion_tecnica") or "",
                    r.get("fecha_calculo") or "",
                    variacion_indice(r.get('i0_icociv'),r.get('i_icociv')),
                ]
            )
        return filas

    def _escribir_calculo_valor_ajustado_excel(self, ws, fila: int) -> int:
        encabezados = [titulo for _, titulo in self._columnas_valor_ajustado()]
        fila = _escribir_titulo_seccion_excel(ws, fila, "Cálculo del valor ajustado")
        for columna, titulo in enumerate(encabezados, start=1):
            celda = ws.cell(row=fila, column=columna, value=titulo)
            _estilo_encabezado_tabla(celda)
        ws.cell(row=fila, column=12, value="ANTICIPO AMORTIZADO / AUXILIAR")
        _estilo_encabezado_tabla(ws.cell(row=fila, column=12))
        ws.row_dimensions[fila].height = 48
        ws.auto_filter.ref = f"A{fila}:K{fila + len(self.calculos)}"
        self._fila_datos_calculo = fila + 1

        for r in self.calculos:
            fila += 1
            anticipo = 0.0 if r.get("tipo_calculo") == "Cálculo especial acero" else _numero_excel(r.get("anticipo_amortizado")) or 0.0
            base = f"(C{fila}-L{fila})"
            valores = [
                _insumo_contractual(r),
                r.get("unidad") or "",
                _numero_excel(r.get("precio_base")),
                _numero_excel(r.get("i0_iccp")),
                _numero_excel(r.get("i_iccp")),
                _numero_excel(r.get('r1')),
                _numero_excel(r.get("i0_icociv")),
                _numero_excel(r.get("i_icociv")),
                _numero_excel(r.get('r2')),
                _numero_excel(r.get('r_total')),
                _numero_excel(r.get('valor_actualizado')),
                anticipo,
            ]
            for columna, valor in enumerate(valores, start=1):
                celda = ws.cell(row=fila, column=columna, value=valor)
                _estilo_celda_tabla(celda)
                if columna in (1, 2) and isinstance(valor, str):
                    celda.data_type = 's'
            for columna in (3, 6, 9, 10, 11, 12):
                ws.cell(row=fila, column=columna).number_format = FORMATO_MONEDA_EXCEL
            for columna in (4, 5, 7, 8):
                ws.cell(row=fila, column=columna).number_format = FORMATO_INDICE_EXCEL
            for columna in (6, 9, 10):
                ws.cell(row=fila, column=columna).alignment = Alignment(horizontal="center", vertical="center")
            from app_icociv.exportables.excel_modulos import estilo_escenario
            from openpyxl.comments import Comment
            caso = r.get('caso')
            requeridas = ['precio_base'] + ([] if r.get('tipo_calculo') == 'Cálculo especial acero' else ['anticipo_amortizado'])
            if caso in ('solo_iccp', 'empalme_completo'):
                requeridas += ['i0_iccp', 'i_iccp']
            if caso in ('solo_icociv', 'empalme_completo'):
                requeridas += ['i0_icociv', 'i_icociv']
            entradas = [_numero_excel(r.get(k)) for k in requeridas]
            denominadores = [k for k in requeridas if k.startswith('i0_')]
            if caso not in ('solo_iccp', 'solo_icociv', 'empalme_completo') or any(v is None or not isfinite(v) for v in entradas) or any(_numero_excel(r.get(k)) == 0 for k in denominadores) or (_numero_excel(r.get('precio_base')) or 0) <= anticipo or anticipo < 0:
                ws.cell(fila, 1).comment = Comment('No reproducible con las entradas disponibles; cifras originales de SAVIP.', 'SAVIP')
                continue
            f = fila
            r1 = f'{base}*((E{f}/D{f})-1)'
            r2 = f'({base}+F{f})*((H{f}/G{f})-1)'
            formulas = {
                6: f'={r1}' if caso != 'solo_icociv' else '=0',
                9: f'={r2}' if caso != 'solo_iccp' else '=0',
                10: f'=F{f}+I{f}',
                11: f'={base}+J{f}',
            }
            for col, formula in formulas.items():
                cell = ws.cell(f, col);cell.value = formula;estilo_escenario(cell)
            for col in (3, 4, 5, 7, 8, 12):
                if col in (4, 5) and caso == 'solo_icociv' or col in (7, 8) and caso == 'solo_iccp':
                    continue
                estilo_escenario(ws.cell(f, col), editable=True)
            if r.get('tipo_calculo') == 'Cálculo especial acero':
                ws.cell(f, 12).value = '=0'
                estilo_escenario(ws.cell(f, 12))
        # El anticipo debe poder editarse en la misma tabla principal.
        ws.column_dimensions["L"].hidden = False
        return fila + 1

    def _filas_notas_excel(self) -> list[tuple[str, Any]]:
        return [
            ("Metodología", "R = R1 + R2 según los lineamientos de empalme ICCP a ICOCIV."),
            ("Fórmulas verificables", "Las columnas R1, R2, VALOR DEL AJUSTE (R) y VALOR INSUMO AJUSTADO se exportan como fórmulas de Excel."),
            ("Proyecciones", "Si se usó índice ICOCIV proyectado, queda marcado en la trazabilidad del cálculo."),
        ]

    @staticmethod
    def _filas_metodologia_general_excel() -> list[tuple[str, Any]]:
        return [
            ("R1", "R1 = (P - A) × [(I / I0) - 1]"),
            ("R2", "R2 = [(P - A) + R1] × [(I / I0) - 1]"),
            ("R", "R = R1 + R2"),
            ("Valor actualizado", "Valor actualizado = (P - A) + R"),
            ("Variables", "P: valor base. A: anticipo amortizado. I/I0: índices del tramo ICCP o ICOCIV."),
        ]

    @staticmethod
    def _filas_metodologia_acero_excel() -> list[tuple[str, Any]]:
        return [
            ("R1 acero", "R1 = P0 × [(I / I0) - 1]"),
            ("R2 acero", "R2 = (P0 + R1) × [(I / I0) - 1]"),
            ("R acero", "R = R1 + R2"),
            ("Z", "Z = (Ix × q) - (R + P0)"),
            ("Variables", "P0: valor base acero. Ix: valor facturado por kg. q: kg ejecutados. Z: valor adicional por fluctuación."),
        ]

    def _escribir_detalle_acero_excel(self, ws, fila: int) -> int:
        encabezados = ["INSUMO CONTRACTUAL", "P0", "Ix", "q", "Ix × q", "R1", "R2", "R", "P0 + R", "Z", "OBSERVACIÓN"]
        fila = _escribir_titulo_seccion_excel(ws, fila, "Detalle acero")
        for columna, titulo in enumerate(encabezados, start=1):
            celda = ws.cell(row=fila, column=columna, value=titulo)
            _estilo_encabezado_tabla(celda)
        ws.row_dimensions[fila].height = 36
        for indice, r in enumerate(self.calculos, start=1):
            if r.get("tipo_calculo") != "Cálculo especial acero":
                continue
            fila += 1
            # Referencia a la fila del mismo cálculo en la tabla de valor ajustado (misma hoja).
            fila_calculo = self._fila_datos_calculo + indice - 1
            valores = [
                _insumo_contractual(r),
                f"=C{fila_calculo}",
                _numero_excel(r.get("ix")),
                _numero_excel(r.get("q")),
                f'=IF(OR(C{fila}="",D{fila}=""),"",C{fila}*D{fila})',
                f'=F{fila_calculo}',
                f'=I{fila_calculo}',
                f'=J{fila_calculo}',
                f'=B{fila}+H{fila}',
                f'=IF(E{fila}="","No calculado",E{fila}-(H{fila}+B{fila}))',
                r.get("z_observacion") or r.get("observacion_tecnica") or "",
            ]
            for columna, valor in enumerate(valores, start=1):
                celda = ws.cell(row=fila, column=columna, value=valor)
                _estilo_celda_tabla(celda)
                if columna in (1, 11) and isinstance(valor, str):
                    celda.data_type = 's'
            for columna in (2, 3, 5, 6, 7, 8, 9, 10):
                ws.cell(row=fila, column=columna).number_format = FORMATO_MONEDA_EXCEL
            ws.cell(row=fila, column=4).number_format = FORMATO_INDICE_EXCEL
            from app_icociv.exportables.excel_modulos import estilo_escenario
            for col in (2, 3, 4, 5, 6, 7, 8, 9, 10):
                estilo_escenario(ws.cell(fila, col), editable=col in (3, 4))
        return fila + 1

    def _opcion_icociv_actual(self) -> dict[str, Any]:
        seleccion = self._seleccion_icociv_actual()
        if not self.controlador_icociv.archivo_cargado or seleccion.get("idx_g") is None:
            raise ValueError("Debe cargar un archivo ICOCIV y seleccionar al menos el grupo de obra.")
        fuente, fila = resolver_fila_seleccionada(self.controlador_icociv.tablas, self.controlador_icociv.periodos, seleccion)
        self.controlador_icociv.fuente_actual = fuente
        indices = {
            periodo: float(fila.iloc[0][periodo])
            for periodo in self.controlador_icociv.periodos
            if periodo in fila.columns and pd.notna(fila.iloc[0][periodo])
        }
        if not indices:
            raise ValueError("La ruta ICOCIV seleccionada no tiene índices mensuales disponibles.")
        ruta = self._texto_ruta_icociv(seleccion)
        return {
            "ruta": ruta,
            "ruta_estructurada": self.controlador_icociv.construir_ruta_jerarquica(seleccion),
            "indices": indices,
            "seleccion": seleccion,
        }

    def _opcion_icociv_o_vacia(self) -> dict[str, Any]:
        """Como `_opcion_icociv_actual`, pero sin lanzar: un item que no usa
        ICOCIV (o que aún no tiene ruta seleccionada) es un caso válido."""
        try:
            return self._opcion_icociv_actual()
        except ValueError:
            return {"ruta": "", "ruta_estructurada": [], "indices": {}, "seleccion": {}}

    def _horizonte_meses_icociv(self, opcion: dict[str, Any], fecha_final: Any) -> int | None:
        """Meses entre el último periodo ICOCIV real disponible en `opcion` y
        `fecha_final` (misma semántica que el módulo Proyecciones). `None` si
        no hay ICOCIV resuelto (nada que juzgar); puede ser <= 0 si la fecha
        ya está cubierta por datos reales."""
        indices = opcion.get("indices") or {}
        if not indices:
            return None
        periodo_final = normalizar_periodo_empalme(fecha_final)
        ultimo_real = _ultimo_periodo(indices)
        return _periodo_orden(periodo_final) - _periodo_orden(ultimo_real)

    def _aplicar_resultado_proyeccion(
        self, opcion: dict[str, Any], resultado_ui: dict[str, Any], fecha_final: Any
    ) -> dict[str, Any]:
        """Incorpora el resultado ya calculado (fuera del hilo principal) del
        callback de proyección a los índices ICOCIV del empalme."""
        indices = dict(opcion.get("indices") or {})
        periodo_final = normalizar_periodo_empalme(fecha_final)
        ultimo_real = _ultimo_periodo(indices)
        proyeccion = resultado_ui.get("proyeccion", {})
        solicitado = proyeccion.get("resultado_horizonte_solicitado") or {}
        indice_final = solicitado.get("indice_proyectado")
        if not solicitado.get("proyeccion_generada") or indice_final is None:
            razon = solicitado.get("razon_principal") or "Revise el estado del horizonte y el alcance máximo de proyección en la pestaña de proyección."
            raise ValueError(
                "No fue posible usar la fecha final solicitada porque el módulo de proyección no considera viable ese horizonte. "
                f"{razon}"
            )

        for fila in _filas_proyeccion(proyeccion):
            periodo = normalizar_periodo_empalme(fila.get("periodo"))
            indices[periodo] = float(fila["indice_proyectado"])
        indices[periodo_final] = float(indice_final)
        metadata = {
            "icociv_final_es_proyectado": True,
            "ultimo_periodo_icociv_real": ultimo_real,
            "indice_icociv_final_proyectado": float(indice_final),
            "modelo_proyeccion": solicitado.get("modelo_aplicado") or proyeccion.get("model_name", ""),
            "horizonte_usado": solicitado.get("horizonte_solicitado") or proyeccion.get("horizonte_solicitado"),
            "estado_horizonte": solicitado.get("estado", ""),
            "periodo_proyectado": solicitado.get("periodo_proyectado") or periodo_final,
            "advertencias_proyeccion": solicitado.get("razones_tecnicas") or [],
        }
        QMessageBox.information(
            self,
            "Índice ICOCIV proyectado",
            "Índice ICOCIV final proyectado usado en el empalme: "
            f"{_fmt_indice(indice_final)}\n"
            f"Periodo proyectado: {_periodo_visible(periodo_final)}\n"
            f"Modelo seleccionado: {metadata['modelo_proyeccion']}\n"
            f"Estado del horizonte: {metadata['estado_horizonte']}",
        )
        return {**opcion, "indices": indices, "metadata_proyeccion": metadata}

    def _actualizar_jerarquia_icociv(self) -> None:
        if not self.controlador_icociv.archivo_cargado:
            return
        seleccion = self._seleccion_icociv_actual()
        estado = self.controlador_icociv.obtener_estado_jerarquia(seleccion)
        self._rellenar_nivel(self.lbl_nivel2, self.combo_nivel2, estado["nivel2"])
        self._rellenar_nivel(self.lbl_nivel3, self.combo_nivel3, estado["nivel3"])
        self._rellenar_nivel(self.lbl_nivel4, self.combo_nivel4, estado["nivel4"])
        self._rellenar_nivel(self.lbl_nivel5, self.combo_nivel5, estado["nivel5"])
        self._rellenar_nivel(self.lbl_nivel6, self.combo_nivel6, estado["nivel6"])
        self._establecer_visible_checkbox(self.chk_t16_1, estado["mostrar_chk_t16_1"])
        self._establecer_visible_checkbox(self.chk_t16_2, estado["mostrar_chk_t16_2"])
        self._establecer_visible_checkbox(self.chk_t16_3, estado["mostrar_chk_t16_3"])
        self.lbl_ruta_icociv.setText(self._texto_ruta_icociv(self._seleccion_icociv_actual()))

    def _texto_ruta_icociv(self, seleccion: dict[str, Any]) -> str:
        try:
            fuente, _ = resolver_fila_seleccionada(self.controlador_icociv.tablas, self.controlador_icociv.periodos, seleccion)
            self.controlador_icociv.fuente_actual = fuente
        except Exception:
            return "Ruta ICOCIV: sin selección válida."
        ruta = self.controlador_icociv.construir_ruta_jerarquica(seleccion)
        ruta_sin_tabla = [item for item in ruta if item.get("nivel") != "Tabla ICOCIV"]
        if not ruta_sin_tabla:
            return "Ruta ICOCIV: sin selección válida."
        return "Ruta ICOCIV: " + " > ".join(item.get("valor", "") for item in ruta_sin_tabla)

    def _seleccion_icociv_actual(self) -> dict[str, Any]:
        return {
            "idx_g": self.combo_grupo_icociv.currentData(),
            "chk_T16": self.chk_t16.isChecked(),
            "idx_l2": self.combo_nivel2.currentData(),
            "idx_l3": self.combo_nivel3.currentData(),
            "idx_l4": self.combo_nivel4.currentData(),
            "idx_l5": self.combo_nivel5.currentData(),
            "idx_l6": self.combo_nivel6.currentData(),
            "chk_T16_1": self.chk_t16_1.isChecked(),
            "chk_T16_2": self.chk_t16_2.isChecked(),
            "chk_T16_3": self.chk_t16_3.isChecked(),
        }

    def _restaurar_seleccion_icociv(self, seleccion: dict[str, Any]) -> None:
        self._establecer_combo_por_data(self.combo_grupo_icociv, seleccion.get("idx_g"))
        self.chk_t16.setChecked(bool(seleccion.get("chk_T16", False)))
        self._actualizar_jerarquia_icociv()
        self._establecer_combo_por_data(self.combo_nivel2, seleccion.get("idx_l2"))
        self.chk_t16_1.setChecked(bool(seleccion.get("chk_T16_1", False)))
        self._actualizar_jerarquia_icociv()
        self._establecer_combo_por_data(self.combo_nivel3, seleccion.get("idx_l3"))
        self.chk_t16_2.setChecked(bool(seleccion.get("chk_T16_2", False)))
        self._actualizar_jerarquia_icociv()
        self._establecer_combo_por_data(self.combo_nivel4, seleccion.get("idx_l4"))
        self.chk_t16_3.setChecked(bool(seleccion.get("chk_T16_3", False)))
        self._actualizar_jerarquia_icociv()
        self._establecer_combo_por_data(self.combo_nivel5, seleccion.get("idx_l5"))
        self._establecer_combo_por_data(self.combo_nivel6, seleccion.get("idx_l6"))
        self._actualizar_jerarquia_icociv()

    def _combo_selector(self, accion_cambio) -> ComboBoxSinRueda:
        combo = ComboBoxSinRueda()
        combo.setMaxVisibleItems(18)
        combo.setMinimumContentsLength(18)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.currentIndexChanged.connect(lambda _: accion_cambio())
        return combo

    def _actualizar_series_iccp(self) -> None:
        tipo = self.combo_tipo_iccp.currentData()
        opciones = [{"texto": nombre, "indice": nombre} for nombre in self.series_iccp.get(tipo, [])]
        self._llenar_combo(self.combo_serie_iccp, opciones)
        self.combo_serie_iccp.setEnabled(bool(tipo))

    def _serie_iccp_actual(self) -> dict[str, str]:
        tipo = self.combo_tipo_iccp.currentData()
        serie = self.combo_serie_iccp.currentData()
        if not tipo:
            raise ValueError("Seleccione el tipo de serie ICCP.")
        if not serie:
            raise ValueError("Seleccione la serie ICCP.")
        if serie not in self.series_iccp.get(tipo, []):
            raise ValueError("La serie ICCP seleccionada no corresponde al tipo elegido.")
        return {
            "tipo_serie_iccp": str(tipo or ""),
            "serie_iccp": str(serie or ""),
        }

    def _periodo_inicial(self) -> str:
        return f"{self.fecha_inicial_anio.value()}_{self.fecha_inicial_mes.value()}"

    def _periodo_final(self) -> str:
        return f"{self.fecha_final_anio.value()}_{self.fecha_final_mes.value()}"

    @staticmethod
    def _establecer_periodo(spin_anio: QSpinBox, spin_mes: QSpinBox, periodo: Any) -> None:
        partes = str(periodo or "").replace("-", "_").split("_")
        if len(partes) >= 2 and partes[0].isdigit() and partes[1].isdigit():
            spin_anio.setValue(int(partes[0]))
            spin_mes.setValue(int(partes[1]))

    def _restaurar_iccp(self, resultado: dict[str, Any]) -> None:
        self._establecer_combo_por_data(self.combo_tipo_iccp, resultado.get("tipo_serie_iccp"))
        self._actualizar_series_iccp()
        self._establecer_combo_por_data(self.combo_serie_iccp, resultado.get("serie_iccp"))

    def _rellenar_nivel(self, etiqueta: QLabel, combo: QComboBox, descriptor: dict[str, Any] | None) -> None:
        valor_actual = combo.currentData()
        if not descriptor or not descriptor["opciones"]:
            self._llenar_combo(combo, [], None)
            etiqueta.setVisible(False)
            combo.parentWidget().setVisible(False)
            return
        etiqueta.setText(descriptor["etiqueta"])
        etiqueta.setVisible(True)
        combo.parentWidget().setVisible(True)
        self._llenar_combo(combo, descriptor["opciones"], valor_actual)

    def _llenar_combo(self, combo: QComboBox, opciones: list[dict[str, Any]], valor_actual: Any = None) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Sin selección", None)
        indice_restaurar = 0
        for opcion in opciones:
            combo.addItem(opcion["texto"], opcion["indice"])
            combo.setItemData(combo.count() - 1, opcion["texto"], Qt.ItemDataRole.ToolTipRole)
            if opcion["indice"] == valor_actual:
                indice_restaurar = combo.count() - 1
        combo.setCurrentIndex(indice_restaurar)
        combo.blockSignals(False)

    def _reiniciar_desde_nivel2(self) -> None:
        self._limpiar_combos(self.combo_nivel2, self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia_icociv()

    def _reiniciar_desde_nivel3(self) -> None:
        self._limpiar_combos(self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia_icociv()

    def _reiniciar_desde_nivel4(self) -> None:
        self._limpiar_combos(self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia_icociv()

    def _reiniciar_desde_nivel5(self) -> None:
        self._limpiar_combos(self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia_icociv()

    def _reiniciar_desde_nivel6(self) -> None:
        self._limpiar_combos(self.combo_nivel6)
        self._actualizar_jerarquia_icociv()

    def _limpiar_combos(self, *combos: QComboBox) -> None:
        for combo in combos:
            self._llenar_combo(combo, [])

    def _ocultar_niveles(self) -> None:
        for widget in (self.lbl_nivel2, self.lbl_nivel3, self.lbl_nivel4, self.lbl_nivel5, self.lbl_nivel6):
            widget.setVisible(False)
        for combo in (self.combo_nivel2, self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6):
            combo.parentWidget().setVisible(False)
        for checkbox in (self.chk_t16_1, self.chk_t16_2, self.chk_t16_3):
            checkbox.setVisible(False)

    def _establecer_visible_checkbox(self, checkbox: QCheckBox, visible: bool) -> None:
        if not visible:
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
        checkbox.setVisible(visible)

    def _actualizar_controles_selector(self, habilitado: bool) -> None:
        for widget in (self.combo_grupo_icociv, self.chk_t16, self.combo_nivel2, self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6):
            widget.setEnabled(habilitado)

    def _datos_generales(self) -> dict[str, str]:
        return {
            "contrato": self.contrato.text().strip(),
            "objeto_contrato": self.objeto.toPlainText().strip(),
            "responsable_tecnico": self.responsable.text().strip(),
            "observacion_general": self.observacion_general.toPlainText().strip(),
        }

    def _mostrar_resultado(self, r: dict[str, Any]) -> None:
        def numero(valor,decimales=2):
            return texto_numero(numero_original(valor),decimales)
        filas = [
            ("Precio base P", numero(r.get("precio_base"),2), AYUDAS["precio"]),
            ("Unidad", r.get("unidad"), AYUDAS["unidad"]),
            ("Anticipo amortizado A", numero(r.get("anticipo_amortizado"),2), AYUDAS["anticipo"]),
            ("Base ajustable P - A", numero(r.get("base_ajustable"),2), AYUDAS["base"]),
            ("Fecha inicial", r.get("fecha_inicial"), AYUDAS["fecha_inicial"]),
            ("Fecha final", r.get("fecha_final"), AYUDAS["fecha_final"]),
            ("Tipo de serie ICCP", r.get("tipo_serie_iccp_visible"), AYUDAS["tipo_serie_iccp"]),
            ("Serie ICCP usada", r.get("serie_iccp"), AYUDAS["serie_iccp"]),
            ("Ruta ICCP", r.get("ruta_iccp"), AYUDAS["grupo_iccp"]),
            ("I0 ICCP", numero(r.get("i0_iccp"),4), "Índice ICCP inicial correspondiente a la fecha inicial seleccionada."),
            ("I ICCP", numero(r.get("i_iccp"),4), "Índice ICCP final del primer tramo; normalmente diciembre de 2021 cuando cruza la transición."),
            ("Factor ICCP", numero(r.get("factor_iccp"),6), "Relación I ICCP / I0 ICCP usada para calcular R1."),
            ("R1", numero(r.get("r1"),2), "Primer valor parcial ajustado según lineamientos ICCP-ICOCIV."),
            ("Ruta ICOCIV", r.get("ruta_icociv"), AYUDAS["ruta_icociv"]),
            ("I0 ICOCIV", numero(r.get("i0_icociv"),4), "Índice ICOCIV inicial del segundo tramo; normalmente diciembre de 2021."),
            ("I ICOCIV", numero(r.get('i_icociv'),4), "Índice ICOCIV final correspondiente a la fecha final seleccionada."),
            ("Factor ICOCIV", numero(r.get("factor_icociv"),6), "Relación I ICOCIV / I0 ICOCIV usada para calcular R2."),
            ("R2", numero(r.get("r2"),2), "Segundo valor parcial ajustado según lineamientos ICCP-ICOCIV."),
            ("R total", numero(r.get("r_total"),2), "Valor definitivo del ajuste: R = R1 + R2."),
            ("Valor actualizado", numero(r.get("valor_actualizado"),2), "Resultado final después de aplicar el empalme ICCP-ICOCIV."),
            ("Diferencia absoluta", numero(r.get("diferencia_absoluta"),2), "Diferencia en pesos entre el valor actualizado y la base ajustable inicial."),
            ("Diferencia porcentual (%)", numero(r.get("diferencia_porcentual"),3), "Porcentaje de variación frente a la base ajustable inicial."),
        ]
        if r.get("tipo_calculo") == "Cálculo especial acero":
            filas.extend(
                [
                    ("P0", numero(r.get("p0"),2), AYUDAS["p0"]),
                    ("Ix", numero(r.get("ix"),2), AYUDAS["ix"]),
                    ("q", numero(r.get("q"),4), AYUDAS["q"]),
                    ("Valor facturado total Ix × q", numero(r.get("valor_facturado_total"),2), "Valor facturado total del acero. Se calcula como Ix × q."),
                    ("Z", numero(r.get("z"),2), "Valor adicional por fluctuación del acero: compara el valor facturado contra P0 + R."),
                ]
            )
        from app_icociv.persistencia.historial_empalme import campos_componente
        filas[0:0] = [("Proyecto al calcular", r.get("contrato"), "Proyecto guardado en este registro."),
            ("ID cálculo", r.get("calculo_id"), "Identificador del registro económico."),
            ("ID análisis", r.get("analisis_empalme_id"), "Vínculo al historial independiente de Empalme."),
            ("Insumo / ítem", r.get("item"), "Insumo contractual original."),
            ("Código", r.get("codigo_item"), "Código original del ítem."),
            ("Cantidad", numero(r.get("cantidad"),4), "Convierte los pares unitario/total según la modalidad declarada; no modifica el valor principal."),
            ("Escenario", _escenario_operativo(r), "Tramos aplicados y cálculo especial de acero cuando corresponda."),
            ("Observación técnica", r.get("observacion_tecnica"), "Observación guardada por el usuario.")]
        filas[0:0] = [(k, v, "Clasificación libre del proyecto; no modifica los índices ni el cálculo.") for k, v in campos_componente(r)]
        cuerpo = "".join(
            f"<tr><th>{escape(str(k))}</th><td>{escape('' if v is None else str(v))}</td><td>{escape(str(a))}</td></tr>"
            for k, v, a in filas
        )
        advertencias = "".join(f"<li>{escape(a)}</li>" for a in self._advertencias(r))
        acero = ""
        if r.get("tipo_calculo") == "Cálculo especial acero":
            acero = (
                "<h4>Resultado especial acero</h4>"
                "<table border='1' cellspacing='0' cellpadding='4'>"
                f"<tr><th>Valor facturado total Ix × q</th><td>{escape(numero(r.get('valor_facturado_total'),2))}</td></tr>"
                f"<tr><th>Ajuste R</th><td>{escape(numero(r.get('r_total'),2))}</td></tr>"
                f"<tr><th>Z</th><td>{escape(numero(r.get('z'),2))}</td></tr>"
                "</table>"
                "<h4>Fórmula especial de acero</h4>"
                "<pre>R1 = P0 × [(I ICCP / I0 ICCP) - 1]\n"
                "R2 = (P0 + R1) × [(I ICOCIV / I0 ICOCIV) - 1]\n"
                "R = R1 + R2\n"
                "Z = (Ix × q) - (R + P0)</pre>"
                "<p><b>P0</b>: valor base del acero. <b>Ix</b>: valor facturado por kg. "
                "<b>q</b>: kg ejecutados. <b>Z</b>: valor adicional por fluctuación.</p>"
            )
        self.resultado.setHtml(
            "<h3>Resultado de actualización</h3><p>Importes en COP. El estado y el periodo del índice figuran en la nota y en el detalle.</p>"
            "<table border='1' cellspacing='0' cellpadding='8'>"
            f"<tr><th>Valor actualizado</th><td><b>{escape(numero(r.get('valor_actualizado'),2))}</b></td></tr>"
            f"<tr><th>Valor del ajuste (R)</th><td>{escape(numero(r.get('r_total'),2))}</td></tr>"
            f"<tr><th>Índice ICOCIV final usado</th><td>{escape(numero(r.get('i_icociv'),4))}</td></tr>"
            f"<tr><th>Diferencia porcentual (%)</th><td>{escape(numero(r.get('diferencia_porcentual'),3))}</td></tr>"
            f"<tr><th>Base ajustable</th><td>{escape(numero(r.get('base_ajustable'),2))}</td></tr>"
            "</table>"
            f"<h4>Desglose presupuestal complementario</h4><p>{escape(texto_desglose(r,r.get('valor_actualizado'),'Registro económico original')).replace(chr(10),'<br>')}</p>"
            f"{_nota_proyeccion_html(r)}"
            "<h4>Detalle del cálculo</h4>"
            "<table border='1' cellspacing='0' cellpadding='4'>"
            "<tr><th>Campo</th><th>Valor</th><th>Qué significa</th></tr>"
            f"{cuerpo}</table>"
            f"{acero}"
            f"<h4>Advertencias</h4><ul>{advertencias}</ul>"
            "<h4>Desarrollo matemático</h4>"
            f"<pre>{escape(_trazabilidad_lineamientos(r))}</pre>"
        )

    def _advertencias(self, r: dict[str, Any]) -> list[str]:
        advertencias = ["La equivalencia ICCP-ICOCIV es una selección manual del usuario y requiere justificación técnica."]
        if r.get("caso") == "solo_iccp":
            advertencias.append("El cálculo usa solo ICCP porque ambas fechas son hasta diciembre de 2021.")
        if r.get("caso") == "solo_icociv":
            advertencias.append("El cálculo usa solo ICOCIV porque ambas fechas son posteriores a diciembre de 2021.")
        if r.get("ruta_icociv") and str(r.get("ruta_icociv")).count(" > ") < 2:
            advertencias.append("La ruta ICOCIV seleccionada parece general; revise si el nivel es suficiente.")
        if r.get("tipo_calculo") == "Cálculo especial acero":
            if r.get("z") is None:
                advertencias.append(r.get("z_observacion") or "Para calcular Z debe ingresar Ix y q.")
            elif r.get("z") <= 0:
                advertencias.append("El valor Z del acero es negativo o cero.")
        return advertencias

    def _actualizar_tabla(self) -> None:
        self._sincronizando_seleccion = True
        try:
            self._registros_por_fila = list(self.calculos)
            self._actualizar_tablas_tecnicas()
            self.modelo_operativo.registros = self._registros_por_fila
            filas = [[fila[k] for k, _ in COLUMNAS_OPERATIVAS] for fila in map(_fila_operativa, self.calculos)]
            self.modelo_operativo.establecer_dataframe(pd.DataFrame(filas, columns=[titulo for _,titulo in COLUMNAS_OPERATIVAS], dtype=object))
            self._restaurar_selecciones_tablas()
        finally:
            self._sincronizando_seleccion = False

    def _actualizar_tablas_tecnicas(self) -> None:
        self.modelo_equivalencias.establecer_dataframe(self._dataframe_equivalencias())
        dataframe = self._dataframe_valor_ajustado()
        # La columna derivada pertenece solo a la vista; Excel y sesión conservan su esquema.
        for clave,titulo in self._columnas_valor_ajustado():
            if clave in {'precio_base','i0_iccp','i_iccp','r1','i0_icociv','i_icociv','r2','r_total','valor_actualizado'}:
                dataframe[titulo]=pd.Series([numero_original(r.get(clave)) for r in self.calculos],dtype=object)
                self.modelo_valor_ajustado.decimales[titulo]=4 if clave.startswith('i') else 2
        dataframe.insert(dataframe.columns.get_loc("R2"), COLUMNA_VARIACION_INDICE,
                         pd.Series([variacion_indice(r.get("i0_icociv"),r.get("i_icociv")) for r in self.calculos],dtype=object))
        self.modelo_valor_ajustado.notas=[f"{'Proyectado' if r.get('icociv_final_es_proyectado') else 'Histórico'} · {r.get('fecha_final','')} · {r.get('modelo_proyeccion','')}" for r in self.calculos]
        self.modelo_valor_ajustado.establecer_dataframe(dataframe)
        nombres = {a['id']: a['nombre'] for a in self.historial_empalme}
        for i, r in enumerate(self.calculos):
            if r.get('analisis_empalme_id'):
                self.modelo_valor_ajustado.notas[i] += f" · {nombres.get(r['analisis_empalme_id'], '')} · ID {r['analisis_empalme_id']}"

    def _dataframe_equivalencias(self) -> pd.DataFrame:
        return _dataframe_desde_registros(
            [self._fila_equivalencia(r) for r in self.calculos],
            COLUMNAS_EQUIVALENCIAS,
        )

    def _dataframe_valor_ajustado(self) -> pd.DataFrame:
        return _dataframe_desde_registros(
            [self._fila_valor_ajustado(r) for r in self.calculos],
            self._columnas_valor_ajustado(),
        )

    def _dataframe_detalle_exportacion(self) -> pd.DataFrame:
        registros = []
        for r in self.calculos:
            fila = self._fila_valor_ajustado(r)
            fila.update({clave: _valor_detalle_exportacion(clave, r.get(clave)) for clave, _ in COLUMNAS_DETALLE_EXPORTACION})
            registros.append(fila)
        return _dataframe_desde_registros(registros, self._columnas_valor_ajustado() + COLUMNAS_DETALLE_EXPORTACION)

    def _columnas_valor_ajustado(self) -> list[tuple[str, str]]:
        if not self.calculos:
            return COLUMNAS_VALOR_AJUSTADO
        r = self.calculos[-1]
        fechas = _fechas_columnas_indices(r)
        return [
            (clave, _titulo_indice(clave, titulo, fechas.get(clave), bool(r.get("icociv_final_es_proyectado"))))
            for clave, titulo in COLUMNAS_VALOR_AJUSTADO
        ]

    def _fila_equivalencia(self, r: dict[str, Any]) -> dict[str, Any]:
        return {
            "insumo_contractual": _insumo_contractual(r),
            "grupo_iccp_equivalente": _equivalente_iccp(r),
            "insumo_icociv_equivalente": _equivalente_icociv(r),
        }

    def _fila_valor_ajustado(self, r: dict[str, Any]) -> dict[str, Any]:
        return {
            "insumo_contractual": _insumo_contractual(r),
            "unidad": r.get("unidad", ""),
            "precio_base": _fmt_moneda(r.get("precio_base")),
            "i0_iccp": _fmt_indice_o_na(r.get("i0_iccp")),
            "i_iccp": _fmt_indice_o_na(r.get("i_iccp")),
            "r1": _fmt_moneda_o_na(r.get("r1")),
            "i0_icociv": _fmt_indice_o_na(r.get("i0_icociv")),
            "i_icociv": _fmt_indice_proyectado(r),
            "r2": _fmt_moneda_o_na(r.get("r2")),
            "r_total": _fmt_moneda_o_na(r.get("r_total")),
            "valor_actualizado": _fmt_moneda(r.get("valor_actualizado")),
        }

    def _fila_seleccionada(self) -> int | None:
        indice=self.barra.indice()
        if indice is not None and indice < len(self._registros_por_fila):
            clave = self._clave_registro(self._registros_por_fila[indice])
            indice = next((i for i,r in enumerate(self.calculos) if self._clave_registro(r) == clave), None)
        else:
            indice = None
        if indice is None:
            QMessageBox.information(self, "Tabla de cálculos", "Seleccione un cálculo en la tabla.")
            return None
        return indice

    def _alternar_acero(self, activo: bool) -> None:
        for widget in (self.p0, self.ix, self.q):
            widget.setEnabled(activo)

    def _renumerar(self) -> None:
        for numero, calculo in enumerate(self.calculos, start=1):
            calculo["numero_calculo"] = numero
            if not calculo.get("calculo_id"):
                calculo["calculo_id"] = f"calc-{uuid4().hex[:8]}"

    @staticmethod
    def _seleccionar_texto(combo: QComboBox, texto: str) -> None:
        for indice in range(combo.count()):
            if combo.itemText(indice) == texto:
                combo.setCurrentIndex(indice)
                return

    @staticmethod
    def _establecer_combo_por_data(combo: QComboBox, valor: Any) -> None:
        for indice in range(combo.count()):
            if combo.itemData(indice) == valor:
                combo.setCurrentIndex(indice)
                return


def _fila(form: QFormLayout, etiqueta: str | QLabel, widget: QWidget, ayuda: str) -> None:
    # Fase 4I-I: si el campo no cabe junto a su etiqueta (media pantalla), pasa debajo de ella en lugar de
    # imponer su ancho a todo el módulo (el periodo Año/Mes exigía 551 px y desbordaba a 640 px).
    form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
    form.addRow(_etiqueta_ayuda(etiqueta, ayuda), _ayuda(widget, ayuda))


def _etiqueta_ayuda(etiqueta: str | QLabel, ayuda: str) -> QWidget:
    if isinstance(etiqueta, QLabel):
        etiqueta.setToolTip(ayuda)
        return etiqueta
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)
    texto = QLabel(str(etiqueta))
    texto.setToolTip(ayuda)
    layout.addWidget(texto)
    layout.addStretch()
    return contenedor


def _ayuda(widget: QWidget, texto: str) -> QWidget:
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)
    widget.setToolTip(texto)
    layout.addWidget(widget)
    return contenedor


def _periodo_spins(anio: int, mes: int) -> tuple[QSpinBox, QSpinBox]:
    spin_anio = SpinEnteroSinRueda()
    spin_anio.setRange(2000, 2100)
    spin_anio.setValue(anio)
    spin_mes = SpinEnteroSinRueda()
    spin_mes.setRange(1, 12)
    spin_mes.setValue(mes)
    for spin in (spin_anio, spin_mes):
        spin.setAccelerated(True)
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin.setMinimumHeight(ALTURA_CONTROL)
        spin.setToolTip("Seleccione año y mes; no permite texto libre.")
    return spin_anio, spin_mes


def _periodo_widget(spin_anio: QSpinBox, spin_mes: QSpinBox) -> QWidget:
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    for texto, spin, ancho in (("Año", spin_anio, 104), ("Mes", spin_mes, 64)):
        etiqueta = QLabel(texto)
        etiqueta.setFixedWidth(32)
        etiqueta.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        spin.setFixedWidth(ancho)
        layout.addWidget(etiqueta, 0, Qt.AlignVCenter)
        layout.addWidget(_control_incremental(spin), 0, Qt.AlignVCenter)
    layout.addStretch()
    return contenedor


def _control_incremental(spin: QSpinBox) -> QWidget:
    contenedor = QWidget()
    layout = QHBoxLayout(contenedor)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    boton_menos = _boton_incremento("-")
    boton_mas = _boton_incremento("+")
    boton_menos.clicked.connect(spin.stepDown)
    boton_mas.clicked.connect(spin.stepUp)
    layout.addWidget(boton_menos)
    layout.addWidget(spin, 1)
    layout.addWidget(boton_mas)
    return contenedor


def _boton_incremento(texto: str) -> QPushButton:
    boton = QPushButton(texto)
    boton.setObjectName("boton_incremento")
    boton.setProperty("fecha_empalme", True)
    boton.setAccessibleName("Disminuir fecha" if texto == "-" else "Incrementar fecha")
    boton.setFixedWidth(ANCHO_BOTON_INCREMENTO)
    boton.setMinimumHeight(ALTURA_CONTROL)
    boton.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    return boton


def _tooltip(texto: str) -> str:
    return f'<qt><table width="360"><tr><td>{escape(texto).replace(chr(10), "<br>")}</td></tr></table></qt>'


class NumeroEmpalme(NumeroICOCIV):
    """Editor compartido, con validación nativa y flechas originales de Empalme."""

    @staticmethod
    def normalizar_pegado(texto: str) -> str:
        texto = texto.strip()
        if not re.fullmatch(r'[+]?\d+(?:\.\d*)?|[+]?\d{1,3}(?:,\d{3})+(?:\.\d*)?', texto):
            raise ValueError('Pegue un número con coma de miles y punto decimal; ejemplo: 1,234.56.')
        return texto.replace(',', '')

    def validate(self, texto: str, pos: int):
        # Mantener la aceptación y el redondeo del QDoubleSpinBox original.
        return SpinSinRueda.validate(self, texto, pos)

    def _avisar(self, mensaje: str) -> None:
        self.entradaRechazada.emit(mensaje)
        QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), _tooltip(mensaje), self)


def _spin(minimo: float, maximo: float, decimales: int) -> NumeroEmpalme:
    spin = NumeroEmpalme(minimo, maximo, decimales)
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
    return spin


def _fmt_col(valor: Any, decimales: int) -> str:
    if valor is None or valor == "":
        return ""
    try:
        texto = f"{float(valor):,.{decimales}f}"
    except (TypeError, ValueError):
        return str(valor)
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _fmt_moneda(valor: Any) -> str:
    texto = _fmt_col(valor, 2)
    return f"$ {texto}" if texto else ""


def _fmt_moneda_o_no_calculado(valor: Any) -> str:
    return _fmt_moneda(valor) or "No calculado. Faltan Ix y/o q."


def _fmt_variacion_indice(inicial: Any, final: Any) -> str:
    if isinstance(inicial, bool) or isinstance(final, bool):
        return "N/D"
    try:
        inicial, final = float(inicial), float(final)
    except (TypeError, ValueError, OverflowError):
        return "N/D"
    if not isfinite(inicial) or not isfinite(final) or inicial == 0:
        return "N/D"
    if inicial == final:
        return "0 %"
    variacion = ((final / inicial) - 1) * 100
    if not isfinite(variacion):
        return "N/D"
    texto = f"{variacion:,.3f}".rstrip("0").rstrip(".")
    if texto in {"0", "-0"}:
        return "0 < Δ < 0.001 %" if (final > inicial) == (inicial > 0) else "-0.001 % < Δ < 0 %"
    return f"{texto} %"


def _fmt_porcentaje(valor: Any) -> str:
    texto = _fmt_col(valor, 2)
    return f"{texto} %" if texto else ""


def _fmt_indice(valor: Any) -> str:
    return _fmt_col(valor, 4)


def _fmt_factor(valor: Any) -> str:
    return _fmt_col(valor, 6)


def _fmt_indice_o_na(valor: Any) -> str:
    return _fmt_indice(valor) or "No aplica"


def _fmt_moneda_o_na(valor: Any) -> str:
    return _fmt_moneda(valor) or "No aplica"


def _fmt_indice_proyectado(r: dict[str, Any]) -> str:
    texto = _fmt_indice_o_na(r.get("i_icociv"))
    return f"{texto} (proyectado)" if r.get("icociv_final_es_proyectado") and texto != "No aplica" else texto


def _titulo_indice(clave: str, titulo: str, periodo: str | None, proyectado: bool = False) -> str:
    if clave not in {"i0_iccp", "i_iccp", "i0_icociv", "i_icociv"}:
        return titulo
    sufijo = "\n(PROYECTADO)" if clave == "i_icociv" and proyectado else ""
    return f"{titulo}\n{_periodo_visible(periodo)}{sufijo}"


def _fechas_columnas_indices(r: dict[str, Any]) -> dict[str, str | None]:
    caso = r.get("caso")
    return {
        "i0_iccp": r.get("fecha_inicial") if r.get("i0_iccp") is not None else None,
        "i_iccp": (r.get("fecha_final") if caso == "solo_iccp" else "2021_12") if r.get("i_iccp") is not None else None,
        "i0_icociv": (r.get("fecha_inicial") if caso == "solo_icociv" else "2021_12") if r.get("i0_icociv") is not None else None,
        "i_icociv": r.get("fecha_final") if r.get("i_icociv") is not None else None,
    }


def _periodo_visible(periodo: Any) -> str:
    if not periodo:
        return "NO APLICA"
    partes = str(periodo).replace("-", "_").split("_")
    if len(partes) < 2 or not partes[0].isdigit() or not partes[1].isdigit():
        return str(periodo).upper()
    meses = ["", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    mes = int(partes[1])
    return f"{meses[mes]} DE {partes[0]}" if 1 <= mes <= 12 else str(periodo).upper()


def _periodo_orden(periodo: Any) -> int:
    anio, mes = _periodo_partes(periodo)
    return anio * 12 + mes


def _periodo_partes(periodo: Any) -> tuple[int, int]:
    normalizado = normalizar_periodo_empalme(periodo)
    anio, mes = normalizado.split("_", 1)
    return int(anio), int(mes)


def _ultimo_periodo(indices: dict[str, Any]) -> str:
    periodos = [normalizar_periodo_empalme(periodo) for periodo in indices]
    return max(periodos, key=_periodo_orden)


def _filas_proyeccion(proyeccion: dict[str, Any]) -> list[dict[str, Any]]:
    tabla = proyeccion.get("proyecciones")
    if isinstance(tabla, pd.DataFrame):
        return tabla[["periodo", "indice_proyectado"]].dropna().to_dict(orient="records")
    if isinstance(tabla, list):
        return [fila for fila in tabla if isinstance(fila, dict) and fila.get("indice_proyectado") is not None]
    return []


def _nota_proyeccion_html(r: dict[str, Any]) -> str:
    if not r.get("icociv_final_es_proyectado"):
        return ""
    return (
        "<p><b>Nota:</b> El índice final ICOCIV fue obtenido mediante el módulo de proyección existente. "
        f"Modelo: {escape(str(r.get('modelo_proyeccion', '')))}. "
        f"Estado del horizonte: {escape(str(r.get('estado_horizonte', '')))}.</p>"
    )


def _trazabilidad_lineamientos(r: dict[str, Any]) -> str:
    lineas = []
    if r.get("factor_iccp") is not None:
        lineas.append(
            "R1 = (P - A) × [(I ICCP / I0 ICCP) - 1] = "
            f"{_fmt_moneda(r.get('base_ajustable'))} × [({_fmt_indice(r.get('i_iccp'))} / {_fmt_indice(r.get('i0_iccp'))}) - 1] = {_fmt_moneda(r.get('r1'))}"
        )
    else:
        lineas.append("R1 = No aplica")
    if r.get("factor_icociv") is not None:
        lineas.append(
            "R2 = [(P - A) + R1] × [(I ICOCIV / I0 ICOCIV) - 1] = "
            f"({_fmt_moneda(r.get('base_ajustable'))} + {_fmt_moneda(r.get('r1'))}) × "
            f"[({_fmt_indice(r.get('i_icociv'))} / {_fmt_indice(r.get('i0_icociv'))}) - 1] = {_fmt_moneda(r.get('r2'))}"
        )
    else:
        lineas.append("R2 = No aplica")
    lineas.append(f"R = R1 + R2 = {_fmt_moneda(r.get('r1'))} + {_fmt_moneda(r.get('r2'))} = {_fmt_moneda(r.get('r_total'))}")
    lineas.append(f"Valor insumo ajustado = (P - A) + R = {_fmt_moneda(r.get('base_ajustable'))} + {_fmt_moneda(r.get('r_total'))} = {_fmt_moneda(r.get('valor_actualizado'))}")
    return "\n".join(lineas)


def _dataframe_desde_registros(registros: list[dict[str, Any]], columnas: list[tuple[str, str]]) -> pd.DataFrame:
    titulos = [titulo for _, titulo in columnas]
    filas = [{titulo: registro.get(clave, "") for clave, titulo in columnas} for registro in registros]
    return pd.DataFrame(filas, columns=titulos)


def _activar_recalculo_excel(wb: Workbook) -> None:
    calculo = getattr(wb, "calculation", None) or getattr(wb, "calculation_properties", None)
    if calculo is not None:
        calculo.calcMode = 'auto'
        calculo.fullCalcOnLoad = True
        calculo.forceFullCalc = True


def _escribir_titulo_seccion_excel(ws, fila: int, titulo: str, columnas: int = 11) -> int:
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=columnas)
    celda = ws.cell(row=fila, column=1, value=titulo)
    celda.font = Font(bold=True, color="FFFFFF")
    celda.fill = PatternFill("solid", fgColor="334155")
    celda.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[fila].height = 22
    return fila + 1


def _escribir_pares_excel(ws, fila: int, titulo: str, pares: list[tuple[str, Any]]) -> int:
    fila = _escribir_titulo_seccion_excel(ws, fila, titulo)
    borde = _borde_excel()
    for etiqueta, valor in pares:
        ws.cell(row=fila, column=1, value=etiqueta)
        ws.cell(row=fila, column=2, value=valor)
        if isinstance(valor, str):
            ws.cell(row=fila, column=2).data_type = 's'
        for columna in (1, 2):
            celda = ws.cell(row=fila, column=columna)
            celda.border = borde
            celda.alignment = Alignment(vertical="top", wrap_text=True)
        ws.cell(row=fila, column=1).font = Font(bold=True)
        fila += 1
    return fila + 1


def _escribir_tabla_excel(ws, fila: int, titulo: str, encabezados: list[str], filas: list[list[Any]]) -> int:
    fila = _escribir_titulo_seccion_excel(ws, fila, titulo, max(11, len(encabezados)))
    for columna, encabezado in enumerate(encabezados, start=1):
        celda = ws.cell(row=fila, column=columna, value=encabezado)
        _estilo_encabezado_tabla(celda)
    ws.row_dimensions[fila].height = 42
    for valores in filas:
        fila += 1
        for columna, valor in enumerate(valores, start=1):
            celda = ws.cell(row=fila, column=columna, value=valor)
            _estilo_celda_tabla(celda)
            if isinstance(valor, str):
                celda.data_type = 's'
            if isinstance(valor, (int, float)):
                celda.number_format = FORMATO_INDICE_EXCEL
    return fila + 1


def _estilo_encabezado_tabla(celda) -> None:
    celda.font = Font(bold=True, color="FFFFFF")
    celda.fill = PatternFill("solid", fgColor="475569")
    celda.border = _borde_excel()
    celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _estilo_celda_tabla(celda) -> None:
    celda.border = _borde_excel()
    celda.alignment = Alignment(vertical="center", wrap_text=True)


def _borde_excel() -> Border:
    lado = Side(style="thin", color="CBD5E1")
    return Border(left=lado, right=lado, top=lado, bottom=lado)


def _ajustar_hoja_excel(ws) -> None:
    from app_icociv.exportables.excel_modulos import ajustar_presentacion
    ajustar_presentacion(ws)


def _numero_excel(valor: Any) -> float | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    texto = str(valor).strip()
    if not texto or texto.lower().startswith("no aplica"):
        return None
    texto = texto.replace("$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _errores_exportacion_excel(calculos: list[dict[str, Any]]) -> list[str]:
    errores: list[str] = []
    numericos = {
        "precio_base": "precio base",
        "r1": "R1",
        "r2": "R2",
        "r_total": "R",
    }
    for indice, calculo in enumerate(calculos, start=1):
        if not _insumo_contractual(calculo):
            errores.append(f"Cálculo {indice}: falta insumo contractual.")
        if not calculo.get("unidad") or calculo.get("unidad") == "Sin selección":
            errores.append(f"Cálculo {indice}: falta unidad válida.")
        if not calculo.get("fecha_inicial") or not calculo.get("fecha_final"):
            errores.append(f"Cálculo {indice}: faltan fechas para encabezados.")
        for clave, nombre in numericos.items():
            if _numero_excel(calculo.get(clave)) is None:
                errores.append(f"Cálculo {indice}: falta {nombre} numérico.")
    return errores


def _valor_detalle_exportacion(clave: str, valor: Any) -> Any:
    if clave == "diferencia_absoluta":
        return _fmt_moneda(valor)
    if clave == "advertencias_proyeccion" and isinstance(valor, list):
        return " | ".join(str(item) for item in valor)
    return valor


def _insumo_contractual(r: dict[str, Any]) -> str:
    return str(r.get("item") or r.get("insumo") or r.get("codigo_item") or "Sin insumo").strip()


def _equivalente_iccp(r: dict[str, Any]) -> str:
    serie = str(r.get("serie_iccp") or r.get("nombre_serie_iccp") or "").strip()
    if r.get("tipo_serie_iccp") == "canasta_general":
        return f"Canasta general > {serie}" if serie else "Canasta general"
    return serie or str(r.get("ruta_iccp") or "").strip()


def _equivalente_icociv(r: dict[str, Any]) -> str:
    for item in reversed(r.get("ruta_icociv_estructurada") or []):
        if isinstance(item, dict) and item.get("nivel") != "Tabla ICOCIV" and item.get("valor"):
            return _normalizar_nombre_icociv(item["valor"])
    ruta = str(r.get("ruta_icociv") or "")
    if ":" in ruta:
        ruta = ruta.split(":", 1)[1]
    partes = [parte.strip() for parte in ruta.split(">") if parte.strip()]
    return _normalizar_nombre_icociv(partes[-1]) if partes else ""


def _normalizar_nombre_icociv(texto: Any) -> str:
    return str(texto).replace("TEBERÍA", "TUBERÍA").replace("Tebería", "Tubería")
