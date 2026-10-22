"""Ventana principal PySide6 para la aplicación ICOCIV."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from copy import deepcopy
from html import escape
from pathlib import Path
from typing import Any, Callable

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
from app_icociv.interfaz.formato_numerico import numero_ui, detalle_ui
from PySide6.QtCore import QEvent, QSettings, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QAbstractSpinBox,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QStackedWidget,
    QTableView,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.interfaz.controladores.trabajadores import TrabajadorFuncion
from app_icociv.interfaz.estilos.constantes_visuales import (
    ALTURA_CHECKBOX,
    ALTURA_CONTROL,
    ANCHO_BOTON_INCREMENTO,
    ESPACIADO_GRUPOS,
    ESPACIADO_PANEL,
    GRAFICA_MIN_HEIGHT,
    GRAFICA_MIN_WIDTH,
    MARGEN_PANEL,
    PANEL_MAX_WIDTH,
    PANEL_MIN_WIDTH,
    PANEL_SCROLL_MAX_WIDTH,
    PANEL_SCROLL_MIN_WIDTH,
    TOOLTIPS_TECNICOS,
    VENTANA_MIN_HEIGHT,
    VENTANA_MIN_WIDTH,
    hoja_estilos,
    normalizar_tema,
    paleta_tema,
)
from app_icociv.interfaz.tema import tokens
from app_icociv.interfaz.animaciones import (
    aplicar_elevacion,
    aplicar_preferencia_sistema,
    detener_todas,
    elevar_tarjetas,
    establecer_movimiento_reducido,
    establecer_sombras,
    movimiento_reducido,
    transicion_vista,
)
from app_icociv.interfaz.componentes import (
    CabeceraApp,
    GestorNotificaciones,
    NavegacionLateral,
    PantallaInicio,
    VeloCarga,
)
from app_icociv.interfaz.efectos import alto_contraste_activo, preparar_ventana
from app_icociv.interfaz.presentacion_resultados import (
    construir_html_detalle_horizonte,
    construir_html_explicacion_tarjeta,
    construir_html_resultados,
)
from app_icociv.interfaz.widgets.modelo_tabla import ModeloTablaPandas
from app_icociv.interfaz.widgets.empalme_iccp_icociv import WidgetEmpalmeICCPICOCIV
from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV
from app_icociv.persistencia.historial_icociv import serializar_resultado, recuperar_resultado
from app_icociv.persistencia.gestor_sesiones import (
    cargar_sesion,
    generar_nombre_sesion,
    guardar_sesion,
)
from app_icociv.interfaz.widgets.dialogo_informe import pedir_configuracion
from app_icociv.reportes.generador_reportes import (
    generar_csv_reproducibilidad,
    generar_nombre_reproducibilidad_csv,
    generar_reporte_pdf,
    generar_reporte_proyeccion,
)
from app_icociv.reportes.modelo import nombre_archivo_informe
from app_icociv.interfaz.widgets.historial_series import huella_datos, identidad_serie
from app_icociv.proyeccion.servicio_proyeccion import H_OPERATIVO_MAX
from app_icociv.utilidades.utilidades import ANIO_BASE, t_a_periodo
from app_icociv.utilidades.nomenclatura_icociv import (
    ETIQUETA_TABLA_ACTIVA,
    NOMBRE_SECCION_SELECCION,
    TEXTO_TABLA_SIN_SELECCION,
    nombre_nivel,
    nombre_tabla_icociv,
    texto_checkbox,
)
from app_icociv.config.rutas import (
    CARPETA_REPORTES,
    CARPETA_SESIONES,
    VERSION,
    TITULO_APLICACION,
    asegurar_carpeta,
    carpeta_logs,
    es_ejecutable_congelado,
    ruta_recurso,
)
from app_icociv.interfaz.widgets.controles import ComboBoxSinRueda, SpinEnteroSinRueda, SpinHorizonte
from app_icociv.interfaz.widgets.switch_tema import SwitchTema
from app_icociv.interfaz.widgets.comparacion_historica import periodo_mensual
from app_icociv.servicios import fecha_objetivo as fo
from app_icociv.interfaz.widgets.visor_grafica import (
    VisorGraficaDialog,
    configurar_ejes_dinamicos,
)


class TarjetaInteractiva(QFrame):
    """Tarjeta KPI activable con mouse o teclado."""

    clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tarjeta_kpi")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mousePressEvent(self, event) -> None:  # noqa: N802 - firma Qt
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:  # noqa: N802 - firma Qt
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


TEXTO_SIN_DANE = "Primero debe cargar un archivo Excel del DANE."
_CLAVES_CORTE = ("corte_dane", "periodo_base", "fecha_final_serie", "ultimo_periodo_icociv_real")


def corte_requerido_sesion(datos: dict[str, Any]) -> str:
    """Corte DANE (AAAA-MM) con el que se creó la sesión: el campo «corte_dane» o, en sesiones
    anteriores, el último periodo observado que registran sus análisis, valores, serie o empalmes."""
    encontrados: list[str] = []

    def recorrer(nodo: Any) -> None:
        if isinstance(nodo, dict):
            for clave, valor in nodo.items():
                if clave in _CLAVES_CORTE and isinstance(valor, str) and periodo_mensual(valor.strip()):
                    encontrados.append(periodo_mensual(valor.strip()))
                elif isinstance(valor, (dict, list)):
                    recorrer(valor)
        elif isinstance(nodo, list):
            for valor in nodo:
                recorrer(valor)

    if periodo_mensual(str(datos.get("corte_dane") or "")):
        return periodo_mensual(str(datos["corte_dane"]))
    recorrer(datos)
    encontrados += [periodo_a_iso(r.get("Periodo")) for r in datos.get("serie_historica") or [] if isinstance(r, dict) and r.get("Periodo")]
    return max((x for x in encontrados if periodo_mensual(x)), default="")


def leer_sesion_json(ruta: str | Path) -> dict[str, Any]:
    """Lee y valida la estructura básica de un JSON de sesión. Sin Qt: se ejecuta en un hilo secundario."""
    try:
        datos = cargar_sesion(ruta)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"«{Path(ruta).name}» no es un archivo de sesión JSON válido ({error}).") from error
    except OSError as error:
        raise ValueError(f"No se pudo leer «{Path(ruta).name}»: {error}") from error
    if not isinstance(datos, dict):
        raise ValueError('La sesión no es un objeto JSON válido.')
    if datos.get('archivo_excel') is not None and not isinstance(datos.get('archivo_excel'), str):
        raise ValueError('Referencia de archivo de sesión inválida.')
    if datos.get('tipo_resultado_visible', 'icociv') not in ('icociv', 'empalme'):
        raise ValueError('Tipo de resultado guardado inválido.')
    return datos


def periodo_a_iso(periodo: Any) -> str:
    """Convierte etiquetas de periodo a formato visible AAAA-MM."""
    texto = str(periodo).strip().replace("/", "_").replace("-", "_")
    partes = texto.split("_")
    if len(partes) >= 2:
        try:
            return f"{int(partes[0]):04d}-{int(partes[1]):02d}"
        except ValueError:
            return str(periodo).strip()
    return str(periodo).strip()


def _pixmap_logo(lado: int) -> QPixmap | None:
    """Carga el logo de SAVIP escalado a ``lado`` px, conservando proporciones."""
    ruta = ruta_recurso("app_icociv/interfaz/recursos/savip_logo.png")
    if not ruta.is_file():
        return None
    pixmap = QPixmap(str(ruta))
    if pixmap.isNull():
        return None
    return pixmap.scaled(
        lado,
        lado,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def icono_savip() -> QIcon | None:
    """Devuelve el icono de la aplicación para ventanas y barra de tareas."""
    ruta = ruta_recurso("app_icociv/interfaz/recursos/savip_icono.png")
    if ruta.is_file():
        icono = QIcon(str(ruta))
        if not icono.isNull():
            return icono
    return None


ANCHO_MINIMO_VENTANA = 640
ALTO_MINIMO_VENTANA = 520
ANCHO_COMPACTO = 1180  # por debajo: navegación contraída y rótulos con ajuste de línea
ANCHO_AMPLIO = 1260  # por encima: se restablece el diseño aprobado (histéresis de 80 px)


class VentanaPrincipal(QMainWindow):
    """Interfaz principal ligera basada en Qt Widgets."""

    def __init__(self) -> None:
        super().__init__()
        self.controlador = ControladorPrincipal()
        self.trabajador: TrabajadorFuncion | None = None
        self._trabajador_empalme: TrabajadorFuncion | None = None
        self.usuario_actual = ""
        self.nombre_sesion_actual: str | None = None
        self.sesion_pendiente: dict[str, Any] | None = None
        # Fase 4I-G: ruta del JSON asociado (guardado rápido), operación de apertura/guardado en curso y
        # firmas del espacio de trabajo (vacío / último guardado o apertura) para detectar contenido y cambios.
        self.ruta_sesion_actual: Path | None = None
        self._operacion_sesion: str | None = None
        self._trabajador_sesion: TrabajadorFuncion | None = None
        self._firma_vacia = self._firma_guardada = ""
        self._restaurando_registros_icociv = False
        self.botones_periodo: list[QPushButton] = []
        self.preferencias = QSettings("ICOCIV", "ICOCIV")
        self.tema_actual = normalizar_tema(self.preferencias.value("tema", "oscuro"))
        # Evita ciclos infinitos en la sincronización bidireccional de los
        # parámetros de proyección (horizonte, meses, año y mes).
        self._sincronizando = False
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). Un intento de
        # superar el alcance operativo (>24 meses) muestra un solo popup;
        # esta bandera evita repetirlo mientras el valor siga fuera de rango.
        self._horizonte_popup_mostrado = False
        self.resultado_ui_actual: dict[str, Any] | None = None
        # Fase 4I-P: análisis del historial cuyo snapshot muestra Resultados (para aplicar su consulta vigente).
        self._analisis_resultados_id: str | None = None
        self.detalles_horizonte: dict[int, dict[str, Any]] = {}
        self.horizonte_detalle_actual: int | None = None

        # Mismo texto que applicationDisplayName: Qt no lo vuelve a anexar al título.
        self.setWindowTitle(TITULO_APLICACION)
        _icono = icono_savip()
        if _icono is not None:
            self.setWindowIcon(_icono)
        self.resize(1500, 900)
        # Pantalla dividida: el mínimo anterior (VENTANA_MIN_WIDTH = 1100 px) impedía el Snap de Windows
        # a media pantalla (~960 px en 1920 y ~683 px en 1366). Por debajo de ANCHO_COMPACTO la
        # navegación se contrae y los rótulos largos ajustan línea; el contenido se desplaza en vertical.
        self.setMinimumSize(ANCHO_MINIMO_VENTANA, ALTO_MINIMO_VENTANA)
        self._modo_compacto = False
        self._navegacion_auto = False
        self._rotulos_ajustados = []
        self._temporizador_ancho = QTimer(self)
        self._temporizador_ancho.setSingleShot(True)
        self._temporizador_ancho.setInterval(60)
        self._temporizador_ancho.timeout.connect(self._adaptar_ancho)

        # Preferencias de accesibilidad antes de construir: si el sistema pide
        # reducir movimiento, los componentes nacen ya en su estado final.
        self.movimiento_reducido_sistema = aplicar_preferencia_sistema()
        self.alto_contraste = alto_contraste_activo()
        if self.alto_contraste:
            # En alto contraste manda la legibilidad: sin sombras ni movimiento.
            establecer_sombras(False)
            establecer_movimiento_reducido(True)

        self._crear_acciones()
        self._crear_interfaz()
        self._cargar_estilos()
        self._actualizar_controles_habilitados(False)
        # Material de fondo de la ventana; degrada a opaco si no está disponible.
        self.capacidades_ventana = preparar_ventana(self, self.tema_actual)
        # Estado inicial de Resultados, para dejarlo igual al cerrar una sesión.
        self._resultados_iniciales = (self.texto_resultados.toHtml(), [
            (etiqueta, etiqueta.text()) for etiqueta in (self.lbl_dashboard_ruta, self.lbl_dashboard_estado,
                                                         self.lbl_horizonte_recomendado, *self.valores_kpi.values())])
        self._firma_vacia = self._firma_guardada = self._firma_trabajo()

    def _crear_acciones(self) -> None:
        menu_archivo = self.menuBar().addMenu("Archivo")
        accion_cargar = menu_archivo.addAction("Cargar Excel")
        accion_cargar.triggered.connect(self.seleccionar_archivo)
        menu_archivo.addSeparator()
        menu_archivo.addAction("Salir", self.close)

        menu_sesion = self.menuBar().addMenu("Sesiones")
        menu_sesion.addAction("Abrir sesión", self.abrir_sesion)
        self.accion_guardar_sesion = menu_sesion.addAction("Guardar sesión", self.guardar_rapido)
        self.accion_guardar_sesion.setShortcut(QKeySequence.StandardKey.Save)
        self.accion_guardar_como = menu_sesion.addAction("Guardar sesión como…", lambda: self.guardar_rapido(como=True))
        self.accion_guardar_como.setShortcut(QKeySequence("Ctrl+Shift+S"))
        menu_sesion.addSeparator()
        self.accion_cerrar_sesion = menu_sesion.addAction("Cerrar sesión", self.cerrar_sesion)
        # La barra de menú vive en la cabecera: los atajos se registran también en la ventana.
        self.addActions([self.accion_guardar_sesion, self.accion_guardar_como])

        menu_reporte = self.menuBar().addMenu("Reportes")
        menu_reporte.addAction("Generar informe DOCX", self.generar_informe)
        menu_reporte.addAction("Generar informe PDF", self.generar_informe_pdf)
        menu_reporte.addAction("Exportar datos reproducibles CSV", self.exportar_reproducibilidad_csv)

        menu_ayuda = self.menuBar().addMenu("Ayuda")
        menu_ayuda.addAction("Acerca de SAVIP", self._mostrar_acerca_de)
        menu_ayuda.addAction("Abrir carpeta de registros", self._abrir_carpeta_logs)

        menu_vista = self.menuBar().addMenu("Vista")
        self.accion_modo_oscuro = menu_vista.addAction("Modo oscuro")
        self.accion_modo_oscuro.setCheckable(True)
        self.accion_modo_oscuro.setChecked(self.tema_actual == "oscuro")
        self.accion_modo_oscuro.triggered.connect(
            lambda activo: self._aplicar_tema("oscuro" if activo else "claro")
        )

        # Interruptor de tema en la barra superior (esquina derecha del menú).
        # Switch tipo pastilla (sol / luna lineales, sin texto): tamaño fijo, igual en ventana completa
        # y en pantalla dividida, por lo que nunca se recorta.
        self.boton_tema_toggle = SwitchTema()
        self.boton_tema_toggle.setObjectName("switch_tema")
        self.boton_tema_toggle.setChecked(self.tema_actual == "oscuro")
        self._actualizar_texto_toggle_tema()
        self.boton_tema_toggle.clicked.connect(
            lambda: self._aplicar_tema("oscuro" if self.boton_tema_toggle.isChecked() else "claro")
        )
        # Fase 4F: el interruptor se monta directamente en la cabecera
        # (_crear_interfaz). Como widget de esquina del menú inflaba la barra
        # hasta su altura aunque luego se trasladara.

    def menuBar(self) -> QMenuBar:  # noqa: N802 - firma Qt
        """Barra de menú propia, montada dentro de la cabecera (Fase 4F).

        La barra nativa de QMainWindow ocupa todo el ancho por encima de la
        navegación lateral y la corta; esta barra se integra en la cabecera, a la
        derecha de la navegación, conservando los mismos menús y acciones.
        """
        if getattr(self, "_barra_menu", None) is None:
            self._barra_menu = QMenuBar()
            self._barra_menu.setObjectName("barra_menu")
        return self._barra_menu

    def _actualizar_texto_toggle_tema(self) -> None:
        oscuro = self.tema_actual == "oscuro"
        self.boton_tema_toggle.establecer_tema(self.tema_actual)
        actual = "Oscuro" if oscuro else "Claro"
        self.boton_tema_toggle.setToolTip(f"Tema {actual.lower()} · cambiar a {'claro' if oscuro else 'oscuro'} (también en Vista › Modo oscuro)")
        self.boton_tema_toggle.setAccessibleName(f"Tema {actual}. Cambiar tema")
        self.boton_tema_toggle.updateGeometry()

    def _crear_interfaz(self) -> None:
        self.logo_marca = QLabel()
        self.logo_marca.setObjectName("logo_marca")
        self.logo_marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _logo = _pixmap_logo(72)
        if _logo is not None:
            self.logo_marca.setPixmap(_logo)

        titulo = QLabel("SAVIP")
        titulo.setObjectName("titulo_app")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitulo = QLabel("Sistema de Análisis de Variaciones de Precios")
        subtitulo.setObjectName("subtitulo_app")
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.etiqueta_archivo = QLabel("Sin archivo cargado")
        self.etiqueta_archivo.setWordWrap(True)
        self.etiqueta_archivo.setToolTip(TOOLTIPS_TECNICOS["archivo"])
        self.etiqueta_estado = QLabel("Seleccione un archivo Excel/.xlsb para comenzar.")
        self.etiqueta_estado.setObjectName("estado")
        self.etiqueta_estado.setWordWrap(True)

        self.boton_cargar = QPushButton("Cargar archivo Excel")
        self.boton_cargar.setToolTip(TOOLTIPS_TECNICOS["archivo"])
        self.boton_cargar.clicked.connect(self.seleccionar_archivo)

        self.combo_grupo = ComboBoxSinRueda()
        self._configurar_combo(self.combo_grupo, TOOLTIPS_TECNICOS["grupo_obra"])
        self.combo_grupo.currentIndexChanged.connect(lambda _: self._reiniciar_desde_nivel2())

        self.chk_t16 = QCheckBox(texto_checkbox("t16_costos"))
        self._configurar_checkbox(self.chk_t16, TOOLTIPS_TECNICOS["costos_globales"])
        self.chk_t16.stateChanged.connect(lambda _: self._reiniciar_desde_nivel2())

        self.chk_t16_1 = QCheckBox(texto_checkbox("subclase_costos"))
        self._configurar_checkbox(self.chk_t16_1, TOOLTIPS_TECNICOS["costos_subclase"])
        self.chk_t16_1.stateChanged.connect(lambda _: self._reiniciar_desde_nivel3())

        self.chk_t16_2 = QCheckBox(texto_checkbox("tipologia_costos"))
        self._configurar_checkbox(self.chk_t16_2, TOOLTIPS_TECNICOS["costos_tipologia"])
        self.chk_t16_2.stateChanged.connect(lambda _: self._reiniciar_desde_nivel4())

        self.chk_t16_3 = QCheckBox(texto_checkbox("capitulo_costos"))
        self._configurar_checkbox(self.chk_t16_3, TOOLTIPS_TECNICOS["costos_capitulo"])
        self.chk_t16_3.stateChanged.connect(lambda _: self._reiniciar_desde_nivel5())

        self.combo_nivel2 = self._crear_combo_nivel(lambda: self._reiniciar_desde_nivel3())
        self.combo_nivel3 = self._crear_combo_nivel(lambda: self._reiniciar_desde_nivel4())
        self.combo_nivel4 = self._crear_combo_nivel(lambda: self._reiniciar_desde_nivel5())
        self.combo_nivel5 = self._crear_combo_nivel(lambda: self._reiniciar_desde_nivel6())
        self.combo_nivel6 = self._crear_combo_nivel(lambda: self._actualizar_jerarquia())

        self.lbl_nivel2 = QLabel("Nivel 2")
        self.lbl_nivel3 = QLabel("Nivel 3")
        self.lbl_nivel4 = QLabel("Nivel 4")
        self.lbl_nivel5 = QLabel("Nivel 5")
        self.lbl_nivel6 = QLabel("Nivel 6")
        self.lbl_tabla_activa = QLabel(TEXTO_TABLA_SIN_SELECCION)
        self.lbl_tabla_activa.setObjectName("tabla_activa")
        self.lbl_tabla_activa.setWordWrap(True)
        self.lbl_ruta_jerarquica = QLabel("Ruta jerárquica: sin selección")
        self.lbl_ruta_jerarquica.setObjectName("ruta_jerarquica")
        self.lbl_ruta_jerarquica.setWordWrap(True)
        self.lbl_ruta_jerarquica.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_ruta_jerarquica.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.scroll_ruta_jerarquica = QScrollArea()
        self.scroll_ruta_jerarquica.setObjectName("ruta_scroll")
        self.scroll_ruta_jerarquica.setWidgetResizable(True)
        self.scroll_ruta_jerarquica.setMaximumHeight(150)
        self.scroll_ruta_jerarquica.setFixedHeight(tokens.ESPACIO_8)
        self.scroll_ruta_jerarquica.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_ruta_jerarquica.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_ruta_jerarquica.setWidget(self.lbl_ruta_jerarquica)
        self._texto_ruta_copia = ""
        self.boton_copiar_ruta = QPushButton("Copiar ruta")
        self.boton_copiar_ruta.setObjectName("boton_compacto")
        self.boton_copiar_ruta.setToolTip("Copia la ruta jerárquica completa al portapapeles")
        self.boton_copiar_ruta.setAccessibleName("Copiar ruta jerárquica")
        self.boton_copiar_ruta.setEnabled(False)
        self.boton_copiar_ruta.clicked.connect(self._copiar_ruta)
        self.scroll_ruta_jerarquica.setToolTip(
            "Ruta jerárquica seleccionada. Use el scroll del recuadro si el texto supera el espacio visible."
        )

        self.spin_anio = SpinEnteroSinRueda()
        self.spin_anio.setRange(2021, 2100)
        self.spin_anio.setValue(2026)
        self.spin_anio.setAccelerated(True)
        self.spin_anio.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_anio.setMinimumHeight(ALTURA_CONTROL)
        self.spin_anio.setToolTip(TOOLTIPS_TECNICOS["anio"])
        self.spin_mes = SpinEnteroSinRueda()
        self.spin_mes.setRange(1, 12)
        self.spin_mes.setValue(6)
        self.spin_mes.setAccelerated(True)
        self.spin_mes.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_mes.setMinimumHeight(ALTURA_CONTROL)
        self.spin_mes.setToolTip(TOOLTIPS_TECNICOS["mes"])
        # Sincronización inversa: la fecha objetivo actualiza el horizonte.
        self.spin_anio.valueChanged.connect(lambda _: self._periodo_objetivo_cambiado())
        self.spin_mes.valueChanged.connect(lambda _: self._periodo_objetivo_cambiado())
        self.control_anio = self._crear_control_incremental(
            self.spin_anio,
            self.spin_anio.stepDown,
            self.spin_anio.stepUp,
        )
        self.control_mes = self._crear_control_incremental(
            self.spin_mes,
            self._disminuir_mes,
            self._aumentar_mes,
        )
        self.combo_horizonte = ComboBoxSinRueda()
        self._configurar_combo(self.combo_horizonte, TOOLTIPS_TECNICOS.get("horizonte", "Horizonte de proyección en meses."))
        for texto, valor in (("1 mes", 1), ("3 meses", 3), ("6 meses", 6), ("12 meses", 12), ("18 meses", 18), ("Personalizado", None)):
            self.combo_horizonte.addItem(texto, valor)
        self.combo_horizonte.currentIndexChanged.connect(lambda _: self._horizonte_predefinido_cambiado())

        self.spin_horizonte_personalizado = SpinHorizonte()
        self.spin_horizonte_personalizado.setObjectName("spin_meses")
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Alcance operativo
        # maximo de SAVIP: H_OPERATIVO_MAX=24. El control no debe permitir
        # llegar a 25: es el bug de origen del horizonte personalizado.
        self.spin_horizonte_personalizado.setRange(1, H_OPERATIVO_MAX)
        self.spin_horizonte_personalizado.setValue(18)
        self.spin_horizonte_personalizado.setMinimumHeight(ALTURA_CONTROL)
        self.spin_horizonte_personalizado.setEnabled(False)
        self.spin_horizonte_personalizado.setToolTip(
            f"Horizonte personalizado en meses (1 a {H_OPERATIVO_MAX}): el alcance máximo de proyección de "
            "SAVIP es de 24 meses."
        )
        self.spin_horizonte_personalizado.valueChanged.connect(lambda _: self._meses_personalizados_cambiados())
        self.combo_grupo.currentIndexChanged.connect(lambda _: self._actualizar_edicion_horizonte())
        self.spin_horizonte_personalizado.maximo_intentado.connect(lambda: self._alertar_horizonte_excedido())

        self.lbl_horizonte_recomendado = QLabel("Horizonte solicitado: pendiente de análisis")
        self.lbl_horizonte_recomendado.setObjectName("horizonte_recomendado")
        self.lbl_horizonte_recomendado.setWordWrap(True)

        self.boton_ejecutar = QPushButton("Ejecutar proyección")
        self.boton_ejecutar.setToolTip(TOOLTIPS_TECNICOS["ejecutar"])
        self.boton_ejecutar.clicked.connect(self.ejecutar_proyeccion)
        self.boton_guardar_sesion = QPushButton("Guardar sesión")
        self.boton_guardar_sesion.setObjectName("boton_secundario")
        self.boton_guardar_sesion.setToolTip(TOOLTIPS_TECNICOS["sesion"])
        self.boton_guardar_sesion.clicked.connect(lambda: self.guardar_rapido())
        self.boton_abrir_sesion = QPushButton("Abrir sesión")
        self.boton_abrir_sesion.setObjectName("boton_secundario")
        self.boton_abrir_sesion.setToolTip("Paso 2: abre una sesión JSON. Requiere un Excel DANE cargado con fecha igual o posterior a la de la sesión.")
        self.boton_abrir_sesion.clicked.connect(self.abrir_sesion)
        self.boton_cerrar_sesion = QPushButton("Cerrar sesión")
        self.boton_cerrar_sesion.setObjectName("boton_secundario")
        self.boton_cerrar_sesion.clicked.connect(self.cerrar_sesion)
        # Selector de exportación (DOCX / PDF / CSV) para la barra superior derecha.
        self.boton_exportar_informe = QToolButton()
        self.boton_exportar_informe.setObjectName("boton_exportar_informe")
        self.boton_exportar_informe.setText("Generar informe ")
        self.boton_exportar_informe.setToolTip(TOOLTIPS_TECNICOS["reporte"])
        self.boton_exportar_informe.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu_exportar = QMenu(self.boton_exportar_informe)
        menu_exportar.addAction("Generar informe DOCX", self.generar_informe)
        menu_exportar.addAction("Generar informe PDF", self.generar_informe_pdf)
        menu_exportar.addAction("Exportar archivo CSV", self.exportar_reproducibilidad_csv)
        self.boton_exportar_informe.setMenu(menu_exportar)

        # La navegación entre módulos se separa del formulario de selección: en
        # el diseño anterior competían por la atención dentro del mismo panel.
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). Orden final:
        # Inicio, Proyecciones ICOCIV, Empalme, Resultados. Esta lista, las
        # pestañas de self.tabs_principales y SECCIONES deben mantenerse
        # sincronizadas por posición: no hay un índice nombrado por página,
        # salvo INDICE_RESULTADOS.
        self.navegacion = NavegacionLateral(
            [
                ("inicio", "Inicio", "Resumen del archivo cargado y accesos rápidos"),
                ("proyecciones", "Proyecciones ICOCIV", "Calculadora y tablas acumulativas"),
                ("empalme", "Empalme ICCP-ICOCIV", "Actualización de precios por empalme"),
                ("resultados", "Resultados", "Panel de análisis, métricas y proyección"),
            ]
        )
        self.navegacion.seleccion_cambiada.connect(self._cambiar_seccion)
        # Compatibilidad con el código que aún consulta los botones por índice.
        self.botones_navegacion = self.navegacion.botones
        self.navegacion.setFixedWidth(tokens.NAVEGACION_ANCHO_EXPANDIDO)

        panel = QFrame()
        panel.setObjectName("panel_controles")
        self.panel_lateral = panel
        panel.setMinimumWidth(PANEL_MIN_WIDTH)
        panel.setMaximumWidth(PANEL_MAX_WIDTH)
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(MARGEN_PANEL, MARGEN_PANEL, MARGEN_PANEL, MARGEN_PANEL)
        layout_panel.setSpacing(ESPACIADO_PANEL)
        # La identidad vive en la cabecera superior; las acciones de archivo y
        # sesión pasan al panel de navegación, de modo que no quede una segunda
        # columna vertical dedicada solo a cargar, abrir y guardar.
        self.logo_marca.setVisible(False)
        titulo.setVisible(False)
        subtitulo.setVisible(False)

        self.grupo_archivo = QGroupBox(NOMBRE_SECCION_SELECCION)
        form = QFormLayout(self.grupo_archivo)
        form.setContentsMargins(12, 14, 12, 12)
        form.setSpacing(ESPACIADO_GRUPOS)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form.addRow(self.lbl_tabla_activa)
        # Ajuste visual: ruta con botón «Copiar ruta» en la misma fila (sin saturar la vista).
        fila_ruta = QWidget();caja_ruta = QHBoxLayout(fila_ruta);caja_ruta.setContentsMargins(0, 0, 0, 0)
        caja_ruta.addWidget(self.scroll_ruta_jerarquica, 1)
        caja_ruta.addWidget(self.boton_copiar_ruta, 0, Qt.AlignmentFlag.AlignTop)
        form.addRow(fila_ruta)
        form.addRow(nombre_nivel("grupo_obra"), self.combo_grupo)
        form.addRow(self.chk_t16)
        form.addRow(self.lbl_nivel2, self.combo_nivel2)
        form.addRow(self.chk_t16_1)
        form.addRow(self.lbl_nivel3, self.combo_nivel3)
        form.addRow(self.chk_t16_2)
        form.addRow(self.lbl_nivel4, self.combo_nivel4)
        form.addRow(self.chk_t16_3)
        form.addRow(self.lbl_nivel5, self.combo_nivel5)
        form.addRow(self.lbl_nivel6, self.combo_nivel6)
        # El selector jerárquico ya no vive en el panel lateral: se monta dentro
        # del módulo de Proyecciones ICOCIV más abajo (montar_controles_seleccion).

        self.grupo_parametros = QGroupBox("Parámetros de proyección")
        form_param = QFormLayout(self.grupo_parametros)
        form_param.setContentsMargins(12, 14, 12, 12)
        form_param.setSpacing(ESPACIADO_GRUPOS)
        form_param.addRow("Horizonte", self.combo_horizonte)
        form_param.addRow("Meses personalizados", self.spin_horizonte_personalizado)
        form_param.addRow("Año", self.control_anio)
        form_param.addRow("Mes", self.control_mes)
        # Fase 4I-J: el MISMO bloque fija la fecha objetivo del presupuesto en las trayectorias guardadas
        # (sin motor). «Todas» es lo predeterminado; «Solo análisis seleccionado» es la excepción avisada.
        self.combo_alcance_fecha = ComboBoxSinRueda()
        self.combo_alcance_fecha.addItem("Todas las series del presupuesto", "todas")
        self.combo_alcance_fecha.addItem("Solo análisis seleccionado", "individual")
        self.combo_alcance_fecha.setToolTip("Alcance de «Aplicar fecha objetivo»: todas las revisiones vigentes (predeterminado) "
                                            "o solo el análisis activo, con advertencia si queda en otra fecha.")
        form_param.addRow("Aplicar cambio a", self.combo_alcance_fecha)
        self.boton_aplicar_fecha = QPushButton("Aplicar fecha objetivo a análisis guardados")
        self.boton_aplicar_fecha.setObjectName("boton_secundario")
        self.boton_aplicar_fecha.setToolTip("Toma el índice de ese mes de la trayectoria de 24 meses ya calculada de cada análisis. "
                                            "No ejecuta el motor ni modifica actividades guardadas.")
        self.boton_aplicar_fecha.clicked.connect(self.aplicar_fecha_objetivo)
        form_param.addRow(self.boton_aplicar_fecha)
        self.lbl_fecha_presupuesto = QLabel("")
        self.lbl_fecha_presupuesto.setWordWrap(True);self.lbl_fecha_presupuesto.setVisible(False)
        form_param.addRow(self.lbl_fecha_presupuesto)
        self.boton_reanalizar_dane = QPushButton("Actualizar análisis con DANE más reciente")
        self.boton_reanalizar_dane.setObjectName("boton_secundario")
        self.boton_reanalizar_dane.setToolTip("Repite el backtesting de las series vigentes con el Excel DANE cargado y crea "
                                              "revisiones nuevas desde su último dato observado. Solo al confirmar.")
        self.boton_reanalizar_dane.clicked.connect(self.actualizar_analisis_dane)
        form_param.addRow(self.boton_reanalizar_dane)
        form_param.addRow(self.lbl_horizonte_recomendado)

        # Archivo y sesión viven en el panel de navegación, debajo de los
        # módulos: son acciones de apoyo y no deben leerse antes que ellos.
        # Cargar es la acción principal de su grupo; abrir y guardar quedan como
        # secundarias para no competir con la navegación.
        self.boton_abrir_sesion.setObjectName("boton_secundario")
        self.boton_guardar_sesion.setObjectName("boton_secundario")
        self.navegacion.agregar_accion(
            self.boton_cargar, "＋", "Carga un anexo ICOCIV en Excel o XLSB"
        )
        self.navegacion.agregar_accion(
            self.boton_abrir_sesion, "↥", "Abre una sesión guardada"
        )
        self.navegacion.agregar_accion(
            self.boton_guardar_sesion, "↧", "Guarda la sesión actual en su archivo (Ctrl+S); «Guardar sesión como…» en el menú Sesiones"
        )
        self.navegacion.agregar_accion(
            self.boton_cerrar_sesion, "✕", "Cierra el presupuesto actual (pregunta si guardar) y deja SAVIP listo para uno nuevo con el mismo Excel DANE"
        )
        self.etiqueta_archivo.setObjectName("nav_archivo")
        self.etiqueta_archivo.setWordWrap(True)
        self.navegacion.agregar_accion(self.etiqueta_archivo)
        self.etiqueta_estado.setWordWrap(True)
        self.navegacion.agregar_al_pie(self.etiqueta_estado)
        layout_panel.addStretch()

        panel_scroll = QScrollArea()
        panel_scroll.setObjectName("panel_scroll")
        panel_scroll.setWidgetResizable(True)
        panel_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        panel_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        panel_scroll.setFrameShape(QFrame.Shape.NoFrame)
        panel_scroll.setMinimumWidth(PANEL_SCROLL_MIN_WIDTH)
        panel_scroll.setMaximumWidth(PANEL_SCROLL_MAX_WIDTH)
        panel_scroll.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        panel_scroll.setWidget(panel)
        self.panel_scroll = panel_scroll

        self.texto_resultados = QTextBrowser()
        self.texto_resultados.setReadOnly(True)
        self.texto_resultados.setMinimumHeight(360)
        self.texto_resultados.setOpenLinks(False)
        self.texto_resultados.anchorClicked.connect(self._mostrar_detalle_horizonte)
        self.texto_resultados.setToolTip("")
        self.texto_resultados.viewport().setToolTip("")
        self.texto_resultados.setMouseTracking(False)
        self.texto_resultados.viewport().setMouseTracking(False)
        self.texto_resultados.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.texto_resultados.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.texto_resultados.setObjectName("visor_resultados")

        panel_resultados = QWidget()
        layout_resultados = QVBoxLayout(panel_resultados)
        layout_resultados.setContentsMargins(0, 0, 0, 0)
        layout_resultados.setSpacing(8)
        layout_resultados.addWidget(QLabel("Análisis de Proyecciones ICOCIV guardados en esta sesión"))
        self.selector_resultados_icociv = ComboBoxSinRueda()
        self.selector_resultados_icociv.setAccessibleName("Análisis ICOCIV mostrado en Resultados")
        self.selector_resultados_icociv.currentIndexChanged.connect(self._seleccionar_resultado_icociv)
        layout_resultados.addWidget(self.selector_resultados_icociv)
        self.lbl_comparacion_resultados = QLabel('Comparación histórica de índices · Sin análisis')
        self.lbl_comparacion_resultados.setTextFormat(Qt.PlainText);self.lbl_comparacion_resultados.setWordWrap(True)
        layout_resultados.addWidget(self.lbl_comparacion_resultados)
        layout_resultados.addWidget(self.texto_resultados, 1)
        self.scroll_resultados = QScrollArea()
        self.scroll_resultados.setWidgetResizable(True)
        self.scroll_resultados.setWidget(panel_resultados)
        self.scroll_resultados.viewport().installEventFilter(self)

        # Modelos de datos para Serie histórica y Fila fuente; se muestran en
        # ventanas emergentes desde los botones bajo las tarjetas.
        self.modelo_serie = ModeloTablaPandas(formateador=detalle_ui)
        self.modelo_fila = ModeloTablaPandas(formateador=detalle_ui)

        self.widget_proyecciones = WidgetProyeccionesICOCIV()
        self.widget_proyecciones.analisis_solicitado.connect(self._activar_analisis)
        self.widget_proyecciones.grafica_solicitada.connect(self._ver_grafica_analisis)
        # Fase 4G: «Sin análisis activo» real en todos los selectores, y acceso al anexo
        # cargado solo para la acción expresa «Usar último índice DANE disponible».
        self.widget_proyecciones.analisis_desactivado.connect(self._analisis_icociv_desactivado)
        self.widget_proyecciones.fuente_dane = lambda: (
            (self.controlador.tablas, self.controlador.periodos, self.controlador.ruta_archivo)
            if self.controlador.archivo_cargado else None)
        self.widget_proyecciones.comparacion_cambiada.connect(self.lbl_comparacion_resultados.setText)
        # Fase 4I-J: deshacer/rehacer una actualización de fecha objetivo refresca también la fecha visible.
        # Fase 4I-P: y repinta historial/Resultados con la consulta vigente restaurada.
        self.widget_proyecciones.pila_deshacer.indexChanged.connect(self._al_cambiar_pila_deshacer)
        self.lbl_comparacion_resultados.setText(self.widget_proyecciones.resumen_comparacion_historica())
        self.widget_proyecciones.selector_analisis.currentIndexChanged.connect(self._sincronizar_selector_resultados)
        self._sincronizar_selector_resultados()
        # El selector jerárquico, los parámetros y el botón de ejecución se
        # integran dentro del módulo de proyecciones (antes en el panel lateral).
        self.widget_proyecciones.montar_controles_seleccion(
            self.grupo_archivo, self.grupo_parametros, self.boton_ejecutar
        )
        self.widget_empalme = WidgetEmpalmeICCPICOCIV()
        self.widget_empalme.configurar_proyeccion_icociv(self._ejecutar_proyeccion_para_empalme_async)
        self.widget_empalme.historial_cambiado.connect(self._sincronizar_resultados_empalme)
        self.selector_tipo_resultado = ComboBoxSinRueda()
        self.selector_tipo_resultado.addItems(['Proyecciones ICOCIV', 'Empalme ICCP-ICOCIV'])
        self.selector_tipo_resultado.setAccessibleName('Tipo de resultado mostrado')
        self.resultados_por_modulo = QStackedWidget()
        self.resultados_por_modulo.addWidget(self.scroll_resultados)
        panel_empalme = QWidget();layout_empalme = QVBoxLayout(panel_empalme)
        layout_empalme.addWidget(QLabel('Historial de análisis de Empalme'))
        self.selector_resultados_empalme = ComboBoxSinRueda()
        self.selector_resultados_empalme.setAccessibleName('Análisis Empalme mostrado en Resultados')
        self.selector_resultados_empalme.currentIndexChanged.connect(self._seleccionar_resultado_empalme)
        layout_empalme.addWidget(self.selector_resultados_empalme)
        self.texto_resultados_empalme = QTextBrowser()
        self.texto_resultados_empalme.setObjectName('visor_resultados')
        layout_empalme.addWidget(self.texto_resultados_empalme, 1)
        self.resultados_por_modulo.addWidget(panel_empalme)
        self.selector_tipo_resultado.currentIndexChanged.connect(self.resultados_por_modulo.setCurrentIndex)
        self.panel_resultados_modulos = QWidget();layout_modulos = QVBoxLayout(self.panel_resultados_modulos)
        layout_modulos.setContentsMargins(0,0,0,0)
        layout_modulos.addWidget(self.selector_tipo_resultado)
        layout_modulos.addWidget(self.resultados_por_modulo, 1)
        self._sincronizar_resultados_empalme()

        self.pantalla_inicio = PantallaInicio(VERSION, self.tema_actual)
        self.pantalla_inicio.agregar_acceso(
            "1. Cargar anexo ICOCIV",
            "Paso 1: selecciona el archivo Excel o XLSB publicado por el DANE",
            self.seleccionar_archivo,
        )
        self.pantalla_inicio.agregar_acceso(
            "2. Abrir sesión guardada",
            "Paso 2 (con el Excel DANE ya cargado): recupera una sesión previa con sus análisis guardados",
            self.abrir_sesion,
        )
        self.pantalla_inicio.agregar_acceso(
            "Ir a resultados",
            "Abre el panel de análisis con la serie seleccionada",
            lambda: self._cambiar_seccion(self.INDICE_RESULTADOS),
        )
        self.pantalla_inicio.finalizar_accesos()

        self.tabs_principales = QTabWidget()
        self.tabs_principales.setDocumentMode(True)
        self.tabs_principales.addTab(self.pantalla_inicio, "Inicio")
        self.tabs_principales.addTab(self.widget_proyecciones, "Proyecciones ICOCIV")
        self.tabs_principales.addTab(self.widget_empalme, "Empalme ICCP-ICOCIV")
        self.tabs_principales.addTab(self.panel_resultados_modulos, "Resultados")
        self.tabs_principales.tabBar().hide()
        self.tabs_principales.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        cabecera = QFrame()
        cabecera.setObjectName("dashboard_cabecera")
        self.cabecera_dashboard = cabecera
        layout_cabecera = QHBoxLayout(cabecera)
        layout_cabecera.setContentsMargins(18, 14, 18, 14)
        textos_cabecera = QVBoxLayout()
        titulo_dashboard = QLabel("Panel de análisis ICOCIV")
        titulo_dashboard.setObjectName("titulo_dashboard")
        self.lbl_dashboard_ruta = QLabel("Seleccione una ruta jerárquica para iniciar.")
        self.lbl_dashboard_ruta.setObjectName("ruta_dashboard")
        self.lbl_dashboard_ruta.setWordWrap(True)
        self.lbl_dashboard_estado = QLabel("Sin análisis ejecutado")
        self.lbl_dashboard_estado.setObjectName("estado_dashboard")
        textos_cabecera.addWidget(titulo_dashboard)
        textos_cabecera.addWidget(self.lbl_dashboard_ruta)
        textos_cabecera.addWidget(self.lbl_dashboard_estado)
        layout_cabecera.addLayout(textos_cabecera, 1)
        acciones_cabecera = QHBoxLayout()
        self.acciones_cabecera = acciones_cabecera
        acciones_cabecera.addWidget(self.boton_exportar_informe)
        layout_cabecera.addLayout(acciones_cabecera)

        tarjetas = QFrame()
        tarjetas.setObjectName("panel_tarjetas")
        self.tarjetas_dashboard = tarjetas
        layout_tarjetas = QGridLayout(tarjetas)
        layout_tarjetas.setContentsMargins(0, 0, 0, 0)
        layout_tarjetas.setHorizontalSpacing(10)
        layout_tarjetas.setVerticalSpacing(10)
        self.valores_kpi: dict[str, QLabel] = {}
        self.tarjetas_kpi: dict[str, TarjetaInteractiva] = {}
        for indice, (clave, etiqueta) in enumerate(
            (
                ("indice", "Índice proyectado"),
                ("horizonte", "Horizonte solicitado"),
                ("modelo", "Modelo seleccionado"),
                ("estado", "Estado del horizonte"),
                # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Retirada
                # la tarjeta de IC95 (intervalos productivos retirados desde
                # P0-C): mostrar "No se publica" en una tarjeta principal
                # invita al usuario a buscar algo que la metodologia no
                # entrega. Se sustituye por una referencia util: el MAE
                # historico del horizonte solicitado (NO es un intervalo de
                # confianza, ver `_seccion_error_historico`).
                ("error_historico", "Error histórico de referencia"),
                ("maximo", "Alcance máximo de proyección"),
            )
        ):
            tarjeta, valor = self._crear_tarjeta_kpi(etiqueta)
            self.valores_kpi[clave] = valor
            self.tarjetas_kpi[clave] = tarjeta
            tarjeta.clicked.connect(lambda c=clave: self._mostrar_explicacion_tarjeta(c))
            layout_tarjetas.addWidget(tarjeta, indice // 3, indice % 3)

        # Fila de botones con ventanas emergentes, debajo de las tarjetas.
        fila_popups = QFrame()
        fila_popups.setObjectName("fila_popups")
        self.fila_popups = fila_popups
        layout_popups = QHBoxLayout(fila_popups)
        layout_popups.setContentsMargins(0, 0, 0, 0)
        layout_popups.setSpacing(10)
        self.boton_popup_serie = QPushButton("Serie histórica")
        self.boton_popup_serie.setObjectName("boton_secundario")
        self.boton_popup_serie.setToolTip(TOOLTIPS_TECNICOS["serie"])
        self.boton_popup_serie.clicked.connect(self._abrir_popup_serie)
        self.boton_popup_fila = QPushButton("Fila fuente")
        self.boton_popup_fila.setObjectName("boton_secundario")
        self.boton_popup_fila.setToolTip(TOOLTIPS_TECNICOS["fila"])
        self.boton_popup_fila.clicked.connect(self._abrir_popup_fila)
        self.boton_popup_grafica = QPushButton("Gráfica")
        self.boton_popup_grafica.setObjectName("boton_secundario")
        self.boton_popup_grafica.setToolTip(TOOLTIPS_TECNICOS["grafica"])
        self.boton_popup_grafica.clicked.connect(self._abrir_popup_grafica)
        for boton in (self.boton_popup_serie, self.boton_popup_fila, self.boton_popup_grafica):
            boton.setEnabled(False)
            layout_popups.addWidget(boton)
        layout_popups.addStretch()

        dashboard = QFrame()
        dashboard.setObjectName("dashboard_principal")
        layout_dashboard = QVBoxLayout(dashboard)
        layout_dashboard.setContentsMargins(14, 14, 14, 14)
        layout_dashboard.setSpacing(12)
        layout_resultados.insertWidget(0, cabecera)
        layout_resultados.insertWidget(1, tarjetas)
        layout_resultados.insertWidget(2, fila_popups)
        layout_dashboard.addWidget(self.tabs_principales, 1)

        # El panel de archivo y sesión se vació al pasar sus acciones a la
        # navegación: se conserva el objeto por compatibilidad, pero no se monta.
        panel_scroll.setVisible(False)
        self.panel_scroll_lateral = panel_scroll
        self.splitter_principal = None

        # Cabecera propia con identidad, vista activa y estado del archivo.
        self.cabecera_app = CabeceraApp(_pixmap_logo(tokens.ESPACIO_7))
        self.cabecera_app.agregar_accion(self.boton_tema_toggle)
        # Menús a continuación de la identidad, antes del espacio flexible.
        self.cabecera_app.layout().insertWidget(2, self.menuBar())

        cuerpo = QWidget()
        layout_cuerpo = QHBoxLayout(cuerpo)
        layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        layout_cuerpo.setSpacing(0)
        layout_cuerpo.addWidget(dashboard, 1)

        central = QWidget()
        layout_central = QGridLayout(central)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.setSpacing(0)
        layout_central.addWidget(self.navegacion, 0, 0, 2, 1)
        layout_central.addWidget(self.cabecera_app, 0, 1)
        layout_central.addWidget(cuerpo, 1, 1)
        layout_central.setColumnStretch(1, 1)
        layout_central.setRowStretch(1, 1)
        self.setCentralWidget(central)

        # Superposiciones: cubren el área de trabajo sin tapar la cabecera.
        self.velo_carga = VeloCarga(cuerpo, self.tema_actual)
        self.notificaciones = GestorNotificaciones(cuerpo, self.tema_actual)
        # Ayudas largas en párrafo con ajuste de línea (no una franja de media pantalla).
        from app_icociv.interfaz.tema.tooltips import AjusteTooltips
        from PySide6.QtWidgets import QApplication
        self._ajuste_tooltips = AjusteTooltips(self)
        QApplication.instance().installEventFilter(self._ajuste_tooltips)
        self._contenedor_superposiciones = cuerpo

        self._elevar_superficies()
        self._ordenar_tabulacion()
        self._cambiar_seccion(0)
        self._ocultar_niveles()
        self._actualizar_indicador_resultados()

    def _ordenar_tabulacion(self) -> None:
        """El recorrido con Tab sigue el orden visual del panel, no el de creación."""
        secuencia: list[QWidget] = [
            *self.navegacion.botones,
            self.boton_cargar,
            self.boton_abrir_sesion,
            self.boton_guardar_sesion,
            self.navegacion.boton_contraer,
        ]
        secuencia = [w for w in secuencia if w is not None]
        for anterior, siguiente in zip(secuencia, secuencia[1:]):
            self.setTabOrder(anterior, siguiente)

    @staticmethod
    def _crear_tarjeta_kpi(etiqueta: str) -> tuple[TarjetaInteractiva, QLabel]:
        tarjeta = TarjetaInteractiva()
        tarjeta.setAccessibleName(f"{etiqueta}. Abrir explicación")
        tarjeta.setToolTip("Abrir explicación")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        titulo = QLabel(etiqueta)
        titulo.setObjectName("etiqueta_kpi")
        titulo.setWordWrap(True)
        titulo.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        valor = QLabel("—")
        valor.setObjectName("valor_kpi")
        valor.setWordWrap(True)
        valor.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        accion = QLabel("Ver explicación")
        accion.setObjectName("accion_kpi")
        layout.addWidget(titulo)
        layout.addWidget(valor, 1)
        layout.addWidget(accion)
        return tarjeta, valor

    def _ajustar_tarjetas_resultados(self) -> None:
        if not getattr(self, "tarjetas_kpi", None):
            return
        ancho = self.scroll_resultados.viewport().width()
        columnas = 1 if ancho < 520 else 2 if ancho < 1000 else 3
        grid = self.tarjetas_dashboard.layout()
        for i, tarjeta in enumerate(self.tarjetas_kpi.values()):
            grid.removeWidget(tarjeta)
            grid.addWidget(tarjeta, i // columnas, i % columnas)
        for i in range(3):
            grid.setColumnStretch(i, 1 if i < columnas else 0)
        ancho_texto = max(120, (ancho - 10 * (columnas - 1)) // columnas - 28)
        altura = 120
        for tarjeta in self.tarjetas_kpi.values():
            etiquetas = tarjeta.findChildren(QLabel)
            altura = max(altura, 32 + sum(max(l.minimumSizeHint().height(), l.heightForWidth(ancho_texto)) for l in etiquetas))
        for tarjeta in self.tarjetas_kpi.values():
            tarjeta.setMinimumHeight(altura)

    def eventFilter(self, objeto, evento):
        if hasattr(self, "scroll_resultados") and objeto is self.scroll_resultados.viewport() and evento.type() == QEvent.Resize:
            QTimer.singleShot(0, self._ajustar_tarjetas_resultados)
        return super().eventFilter(objeto, evento)

    # Índice de pestaña -> (nombre visible, muestra el panel de selección).
    # post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). Orden final del
    # menú lateral: Inicio, Proyecciones ICOCIV, Empalme, Resultados.
    SECCIONES = (
        ("Inicio", False),
        ("Proyecciones ICOCIV", True),
        ("Empalme ICCP-ICOCIV", True),
        ("Resultados", True),
    )
    INDICE_RESULTADOS = 3

    def _actualizar_indicador_resultados(self) -> None:
        """post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). Única función que
        decide si "Resultados" se destaca en la navegación: existe una proyección
        cargada (self.resultado_ui_actual) o no. Se llama desde cada punto que
        cambia esa disponibilidad, para no duplicar la regla en varias ventanas."""
        if hasattr(self, "navegacion"):
            self.navegacion.establecer_destacado(
                self.INDICE_RESULTADOS, self.resultado_ui_actual is not None or bool(self.widget_empalme.historial_empalme)
            )

    def _cambiar_seccion(self, indice: int) -> None:
        indice = max(0, min(int(indice), len(self.SECCIONES) - 1))
        transicion_vista(self.tabs_principales, indice)
        nombre, muestra_seleccion = self.SECCIONES[indice]

        # El encabezado de análisis solo aplica a la pestaña de Resultados.
        es_resultados = indice == self.INDICE_RESULTADOS
        for atributo in ("cabecera_dashboard", "tarjetas_dashboard", "fila_popups"):
            if hasattr(self, atributo):
                getattr(self, atributo).setVisible(es_resultados)
        _ = muestra_seleccion  # el panel lateral independiente se retiró
        if hasattr(self, "cabecera_app"):
            self.cabecera_app.establecer_vista(nombre)
        if hasattr(self, "navegacion"):
            self.navegacion.marcar_seleccion(indice)
        if indice == 0 and hasattr(self, "pantalla_inicio"):
            self._actualizar_pantalla_inicio()

    def _elevar_superficies(self) -> None:
        """Aplica la elevación de tarjeta a las superficies de primer nivel."""
        superficies = [
            getattr(self, nombre, None)
            for nombre in ("cabecera_dashboard", "grupo_archivo", "grupo_parametros")
        ]
        elevar_tarjetas(
            [s for s in superficies if s is not None], tokens.ELEVACION_1, self.tema_actual
        )
        for tarjeta in getattr(self, "tarjetas_kpi", {}).values():
            aplicar_elevacion(tarjeta, tokens.ELEVACION_1, self.tema_actual)

    def _actualizar_pantalla_inicio(self) -> None:
        """Vuelca en la portada el estado real de la sesión."""
        if not hasattr(self, "pantalla_inicio"):
            return
        archivo = self.etiqueta_archivo.text() if hasattr(self, "etiqueta_archivo") else ""
        serie_df = getattr(self.controlador, "serie_actual", None)
        periodo = observaciones = ""
        valores: list[float] = []
        if serie_df is not None and getattr(serie_df, "empty", True) is False:
            try:
                periodo = periodo_a_iso(serie_df["Periodo"].iloc[-1])
                observaciones = str(len(serie_df))
                valores = [float(v) for v in serie_df["Indice"].tolist()]
            except Exception:
                periodo, observaciones, valores = "", "", []
        # La portada muestra solo el último nivel de la ruta (la serie); vacío = su propio texto de estado.
        copia = getattr(self, "_texto_ruta_copia", "")
        ruta = copia.splitlines()[-1].split(": ", 1)[-1] if copia else ""
        self.pantalla_inicio.actualizar_estado(
            archivo=archivo,
            periodo=periodo,
            serie=ruta,
            observaciones=observaciones,
            valores=valores,
        )

    def _actualizar_tarjetas(self, proyeccion: dict[str, Any]) -> None:
        solicitado = proyeccion.get("resultado_horizonte_solicitado") or {}
        info = proyeccion.get("analisis_horizontes_completo") or proyeccion.get("horizonte_info") or {}
        generado = bool(solicitado.get("proyeccion_generada"))
        indice = solicitado.get("indice_proyectado")
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 10): alcance operativo
        # fijo (24 meses), no un maximo derivado de evidencia por horizonte.
        maximo = info.get("alcance_maximo_proyeccion")
        maximo_texto = f"{int(maximo)} meses" if maximo else "No identificado"
        self.valores_kpi["indice"].setText(
            self._formatear_metrica(indice) if generado else "No generado"
        )
        self.valores_kpi["horizonte"].setText(
            f"{int(solicitado.get('horizonte_solicitado'))} meses"
            if solicitado.get("horizonte_solicitado")
            else "No disponible"
        )
        self.valores_kpi["modelo"].setText(
            str(solicitado.get("modelo_aplicado") or "No aplica")
        )
        self.valores_kpi["estado"].setText(
            {
                "proyeccion_tecnica": "Proyección técnica",
                "escenario": "Escenario",
                "no_admisible": "No admisible",
            }.get(str(solicitado.get("estado")), "No evaluado")
        )
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Sustituida la
        # tarjeta de IC95 (retirado) por el MAE del horizonte solicitado: una
        # referencia descriptiva del error historico, NO un intervalo de
        # confianza. Ver `_seccion_error_historico` para la explicacion.
        mae_h = ((proyeccion.get("backtesting") or {}).get("metricas") or {}).get("mae")
        try:
            mae_texto = f"± {numero_ui(mae_h)} puntos" if mae_h is not None and float(mae_h) == float(mae_h) else "No disponible"
        except (TypeError, ValueError):
            mae_texto = "No disponible"
        self.valores_kpi["error_historico"].setText(mae_texto if generado else "No disponible")
        self.valores_kpi["maximo"].setText(maximo_texto)
        QTimer.singleShot(0, self._ajustar_tarjetas_resultados)

    def _crear_combo_nivel(self, accion_cambio) -> QComboBox:
        combo = ComboBoxSinRueda()
        self._configurar_combo(combo)
        combo.currentIndexChanged.connect(lambda _: accion_cambio())
        return combo

    def _configurar_combo(self, combo: QComboBox, tooltip_base: str | None = None) -> None:
        combo.setProperty("tooltip_base", tooltip_base or "")
        combo.setMinimumHeight(ALTURA_CONTROL)
        combo.setMinimumContentsLength(18)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.setMaxVisibleItems(18)
        combo.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        combo.view().setMouseTracking(True)
        combo.view().entered.connect(lambda indice, c=combo: self._actualizar_tooltip_opcion_combo(c, indice))
        combo.currentTextChanged.connect(lambda texto, c=combo: self._actualizar_tooltip_combo(c, texto))
        if tooltip_base:
            combo.setToolTip(tooltip_base)

    def _actualizar_tooltip_opcion_combo(self, combo: QComboBox, indice) -> None:
        texto = str(indice.data() or "")
        if texto:
            combo.view().setToolTip(texto)

    def _actualizar_tooltip_combo(self, combo: QComboBox, texto: str | None = None) -> None:
        base = str(combo.property("tooltip_base") or "")
        texto_actual = texto if texto is not None else combo.currentText()
        if base and texto_actual:
            combo.setToolTip(f"{base}\n\nSelección actual: {texto_actual}")
        else:
            combo.setToolTip(base or texto_actual or "")

    @staticmethod
    def _formatear_metrica(valor: Any, decimales: int = 3) -> str:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return "No aplica"
        return numero_ui(numero, decimales, ausente="No aplica")

    @staticmethod
    def _formatear_porcentaje(valor: Any) -> str:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return "No aplica"
        return numero_ui(numero * 100, ausente="No aplica") + "%"

    def _configurar_checkbox(self, checkbox: QCheckBox, tooltip: str) -> None:
        checkbox.setMinimumHeight(ALTURA_CHECKBOX)
        checkbox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        checkbox.setToolTip(tooltip)
        checkbox.setCursor(Qt.CursorShape.PointingHandCursor)

    def _crear_control_incremental(self, spin: QSpinBox, accion_menos, accion_mas) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        boton_menos = QPushButton("-")
        boton_mas = QPushButton("+")
        for boton in (boton_menos, boton_mas):
            boton.setObjectName("boton_incremento")
            boton.setFixedWidth(ANCHO_BOTON_INCREMENTO)
            boton.setMinimumHeight(ALTURA_CONTROL)
            boton.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.botones_periodo.append(boton)

        boton_menos.clicked.connect(accion_menos)
        boton_mas.clicked.connect(accion_mas)
        layout.addWidget(boton_menos)
        layout.addWidget(spin, 1)
        layout.addWidget(boton_mas)
        return contenedor

    def _alertar_horizonte_excedido(self) -> None:
        """post-r1-metodologia-12-24, 19-08-2026 (Prompt UI 01). Ventana emergente
        que explica el limite de 24 meses cuando el usuario intenta superarlo, por
        cualquier ruta de la UI. Un intento produce un solo popup."""
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Information)
        caja.setWindowTitle("Horizonte fuera del alcance de SAVIP")
        caja.setText("SAVIP permite realizar proyecciones entre 1 y 24 meses.")
        caja.setInformativeText(
            "El máximo de 24 meses corresponde al alcance operativo definido para la "
            "herramienta. Seleccione un periodo igual o inferior a 24 meses."
        )
        caja.exec()

    def _detectar_horizonte_personalizado_excedido(self, texto: str) -> None:
        """Detecta un intento manual de escribir >24 antes de que Qt lo normalice."""
        try:
            valor = int(texto.strip())
        except (TypeError, ValueError):
            self._horizonte_popup_mostrado = False
            return
        if valor > H_OPERATIVO_MAX:
            if not self._horizonte_popup_mostrado:
                self._horizonte_popup_mostrado = True
                self._alertar_horizonte_excedido()
        else:
            self._horizonte_popup_mostrado = False

    def _aumentar_mes(self) -> None:
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). El boton "+" no
        # debe permitir superar la fecha maxima de alcance (24 meses).
        maximo = self._fecha_maxima_alcance()
        if maximo is not None:
            siguiente_anio = self.spin_anio.value() + (1 if self.spin_mes.value() == 12 else 0)
            siguiente_mes = 1 if self.spin_mes.value() == 12 else self.spin_mes.value() + 1
            if (siguiente_anio, siguiente_mes) > maximo:
                self._alertar_horizonte_excedido()
                return
        if self.spin_mes.value() < 12:
            self.spin_mes.stepUp()
            return
        self.spin_mes.setValue(1)
        if self.spin_anio.value() < self.spin_anio.maximum():
            self.spin_anio.stepUp()

    def _disminuir_mes(self) -> None:
        if self.spin_mes.value() > 1:
            self.spin_mes.stepDown()
            return
        if self.spin_anio.value() > self.spin_anio.minimum():
            self.spin_anio.stepDown()
            self.spin_mes.setValue(12)

    # ------------------------------------------------------------------
    # Sincronización bidireccional de los parámetros de proyección.
    # Fuente de verdad: el horizonte en meses, materializado en la fecha
    # objetivo (año/mes). Los cuatro controles se mantienen coherentes en
    # todo momento; `_sincronizando` evita ciclos infinitos de señales.
    # ------------------------------------------------------------------

    def _ultimo_periodo_serie(self) -> tuple[int, int] | None:
        """Último periodo observado de la serie cargada, como (año, mes)."""
        periodos = getattr(self.controlador, "periodos", None)
        if not periodos:
            return None
        try:
            anio, mes = [int(parte) for parte in str(periodos[-1]).strip().split("_")[:2]]
        except (TypeError, ValueError):
            return None
        return anio, mes

    def _fecha_maxima_alcance(self) -> tuple[int, int] | None:
        """post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Ultima fecha
        objetivo valida: ultimo periodo observado + H_OPERATIVO_MAX (24)
        meses. Se calcula dinamicamente a partir de la serie cargada; no se
        hardcodea ningun ano/mes."""
        base = self._ultimo_periodo_serie()
        if base is None:
            return None
        anio_base, mes_base = base
        total = anio_base * 12 + (mes_base - 1) + H_OPERATIVO_MAX
        return total // 12, (total % 12) + 1

    def _horizonte_desde_controles(self) -> int:
        """Horizonte que indican el desplegable y el spin de meses."""
        valor = self.combo_horizonte.currentData()
        if valor is None:
            return int(self.spin_horizonte_personalizado.value())
        return int(valor)

    def _horizonte_desde_periodo(self) -> int | None:
        """Meses entre el último periodo observado y la fecha objetivo."""
        base = self._ultimo_periodo_serie()
        if base is None:
            return None
        anio_base, mes_base = base
        total_base = anio_base * 12 + (mes_base - 1)
        total_objetivo = int(self.spin_anio.value()) * 12 + (int(self.spin_mes.value()) - 1)
        return total_objetivo - total_base

    def _horizonte_solicitado(self) -> int:
        """Horizonte efectivo que se usa para ejecutar y reportar.

        Se deriva de la fecha objetivo porque es la que se entrega al motor
        estadístico; si aún no hay serie cargada, se usan los controles.
        """
        horizonte = self._horizonte_desde_periodo()
        return self._horizonte_desde_controles() if horizonte is None else horizonte

    # Compatibilidad con llamadas existentes.
    def _horizonte_actual_meses(self) -> int:
        return self._horizonte_solicitado()

    def _horizonte_predefinido_cambiado(self) -> None:
        self._actualizar_edicion_horizonte()
        self._actualizar_tooltip_combo(self.combo_horizonte)
        if self._sincronizando:
            return
        self._sincronizando = True
        try:
            # Un horizonte predefinido también fija los meses personalizados.
            valor = self.combo_horizonte.currentData()
            if valor is not None and 1 <= int(valor) <= self.spin_horizonte_personalizado.maximum():
                self.spin_horizonte_personalizado.setValue(int(valor))
            self._aplicar_horizonte_a_periodo(self._horizonte_desde_controles())
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _meses_personalizados_cambiados(self) -> None:
        """El spin de meses manda: actualiza fecha objetivo y desplegable."""
        if self._sincronizando:
            return
        self._sincronizando = True
        try:
            horizonte = int(self.spin_horizonte_personalizado.value())
            self.combo_horizonte.setCurrentIndex(self.combo_horizonte.findData(None))
            self._aplicar_horizonte_a_periodo(horizonte)
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _periodo_objetivo_cambiado(self) -> None:
        """El usuario editó año o mes: recalcula horizonte y controles."""
        if self._sincronizando:
            return
        horizonte = self._horizonte_desde_periodo()
        if horizonte is None:
            return
        self._sincronizando = True
        try:
            # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Si la fecha
            # objetivo editada manualmente supera el alcance maximo (24
            # meses), se recorta a la ultima fecha valida en vez de dejar
            # pasar un horizonte >24 al motor. Nunca se sale de 1..24.
            if horizonte > H_OPERATIVO_MAX:
                self._alertar_horizonte_excedido()
                maximo = self._fecha_maxima_alcance()
                if maximo is not None:
                    self.spin_anio.setValue(maximo[0])
                    self.spin_mes.setValue(maximo[1])
                horizonte = H_OPERATIVO_MAX
            if 1 <= horizonte <= self.spin_horizonte_personalizado.maximum():
                self.spin_horizonte_personalizado.setValue(int(horizonte))
            self._seleccionar_horizonte_en_combo(horizonte)
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _seleccionar_horizonte_en_combo(self, horizonte: int) -> None:
        """Marca el horizonte predefinido equivalente o 'Personalizado'."""
        indice = self.combo_horizonte.findData(int(horizonte))
        if indice < 0:
            indice = self.combo_horizonte.findData(None)  # Personalizado
        if indice >= 0 and indice != self.combo_horizonte.currentIndex():
            self.combo_horizonte.setCurrentIndex(indice)
        self._actualizar_edicion_horizonte()
        self._actualizar_tooltip_combo(self.combo_horizonte)

    def _aplicar_horizonte_a_periodo(self, horizonte: int) -> None:
        """Traslada un horizonte en meses a la fecha objetivo (año/mes)."""
        base = self._ultimo_periodo_serie()
        if base is None:
            return
        anio_base, mes_base = base
        total = (anio_base * 12 + (mes_base - 1)) + int(horizonte)
        anio_objetivo, mes_objetivo = total // 12, (total % 12) + 1
        if not (self.spin_anio.minimum() <= anio_objetivo <= self.spin_anio.maximum()):
            return
        self.spin_anio.setValue(int(anio_objetivo))
        self.spin_mes.setValue(int(mes_objetivo))

    def _sincronizar_periodo_desde_horizonte(self) -> None:
        """Recalcula la fecha objetivo al cambiar la serie o cargar archivo."""
        if self._sincronizando:
            return
        self._sincronizando = True
        try:
            self._aplicar_horizonte_a_periodo(self._horizonte_desde_controles())
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _actualizar_etiqueta_horizonte_pendiente(self) -> None:
        """Mantiene coherente el texto del horizonte solicitado antes del análisis.

        post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Retirado "Horizonte
        estadístico: pendiente de análisis": esa nomenclatura pertenece a la
        rejilla triangular retirada. El alcance máximo de SAVIP es fijo (24
        meses, decisión operativa, no frontera estadística).
        """
        if not hasattr(self, "lbl_horizonte_recomendado"):
            return
        base = self._ultimo_periodo_serie()
        if base is None:
            self.lbl_horizonte_recomendado.setText("Horizonte solicitado: pendiente de análisis")
            return
        horizonte = self._horizonte_solicitado()
        objetivo = f"{int(self.spin_anio.value()):04d}-{int(self.spin_mes.value()):02d}"
        if horizonte <= 0:
            self.lbl_horizonte_recomendado.setText(
                f"Fecha objetivo inválida ({objetivo}): debe ser posterior a "
                f"{base[0]:04d}-{base[1]:02d}, último periodo observado."
            )
            return
        self.lbl_horizonte_recomendado.setText(
            f"Horizonte solicitado: {horizonte} mes(es) (objetivo {objetivo}). "
            f"Alcance máximo de SAVIP: {H_OPERATIVO_MAX} meses."
        )

    def seleccionar_archivo(self) -> None:
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo ICOCIV",
            "",
            "Archivos Excel (*.xlsx *.xlsb)",
        )
        if ruta_archivo:
            self._cargar_archivo(ruta_archivo)

    def _cargar_archivo(self, ruta_archivo: str) -> None:
        self._establecer_ocupado(True, "Cargando archivo Excel...")
        self.trabajador = TrabajadorFuncion(self.controlador.cargar_archivo, ruta_archivo)
        self.trabajador.resultado.connect(self._archivo_cargado)
        self.trabajador.error.connect(self._mostrar_error)
        self.trabajador.finished.connect(lambda: self._establecer_ocupado(False))
        self.trabajador.start()

    def _archivo_cargado(self, resultado: dict[str, Any]) -> None:
        vacio = self._firma_trabajo() == self._firma_vacia
        nombre_archivo = Path(resultado["archivo"]).name
        self.etiqueta_archivo.setText(nombre_archivo)
        self.etiqueta_archivo.setToolTip(resultado["archivo"])
        periodos = resultado.get("periodos") or []
        if hasattr(self, "cabecera_app"):
            self.cabecera_app.establecer_estado_archivo(nombre_archivo, "cargado")
        if hasattr(self, "notificaciones"):
            ultimo = periodo_a_iso(periodos[-1]) if periodos else ""
            self.notificaciones.exito(
                "Archivo cargado",
                f"{nombre_archivo} · {len(periodos)} periodos" + (f" · hasta {ultimo}" if ultimo else ""),
            )
        self._llenar_combo(self.combo_grupo, self.controlador.opciones_grupo())
        self._ajustar_periodo_por_defecto(resultado["periodos"])
        self._actualizar_controles_habilitados(True)
        self.widget_empalme.actualizar_icociv(self.controlador.tablas, self.controlador.periodos, self.controlador.ruta_archivo)
        self._actualizar_jerarquia()
        self.etiqueta_estado.setText("Archivo cargado correctamente.")
        if vacio:
            self._firma_vacia = self._firma_guardada = self._firma_trabajo()

        if self.sesion_pendiente:
            self._restaurar_sesion_pendiente()

    def ejecutar_proyeccion(self) -> None:
        seleccion = self._seleccion_actual()
        if seleccion.get("idx_g") is None:
            QMessageBox.warning(self, "Validación", f"Debe seleccionar al menos un {nombre_nivel('grupo_obra').lower()}.")
            return

        # El horizonte efectivo se consolida desde la fecha objetivo mostrada,
        # que ya está sincronizada con el desplegable y los meses personalizados.
        # No se sobrescribe: lo que el usuario ve es lo que se ejecuta.
        base = self._ultimo_periodo_serie()
        horizonte = self._horizonte_solicitado()
        if base is not None and horizonte <= 0:
            QMessageBox.warning(
                self,
                "Validación",
                "La fecha objetivo debe ser posterior al último periodo observado de la serie "
                f"({base[0]:04d}-{base[1]:02d}). Ajuste el año, el mes o el horizonte.",
            )
            return
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Mensaje correcto
        # para h>24: no es un problema de "entero positivo" (MENSAJE_HORIZONTE_
        # INVALIDO), sino de exceder el alcance operativo de SAVIP.
        if horizonte > H_OPERATIVO_MAX:
            QMessageBox.warning(
                self,
                "Validación",
                "El horizonte solicitado debe estar entre 1 y 24 meses. "
                "El alcance máximo de proyección de SAVIP es de 24 meses.",
            )
            return

        if not self._restaurando_registros_icociv:
            # Fase 4I-J (decisión del usuario): misma serie y mismos datos DANE ⇒ se reutiliza la trayectoria
            # de 24 meses ya calculada (el modelo se eligió con RMSE rectangular H1–H24 y no depende de H):
            # sin motor, sin entrada nueva en el historial y sin diálogo. Datos DANE distintos ⇒ las revisiones
            # solo se crean con «Actualizar análisis con DANE más reciente».
            equivalente, datos_distintos = self._analisis_equivalente(seleccion)
            if equivalente is not None:
                self._reutilizar_trayectoria(equivalente)
                return
            if datos_distintos is not None:
                self._aviso("Esta serie ya tiene un análisis con otros datos DANE",
                            f"«{datos_distintos['nombre']}». Para incorporar los datos del archivo cargado use "
                            "«Actualizar análisis con DANE más reciente»; no se ejecutó el motor.", nivel="advertencia")
                self.etiqueta_estado.setText("Proyección no ejecutada: la serie ya está en el presupuesto con otros datos DANE.")
                return

        self._establecer_ocupado(True, "Ejecutando proyección...")
        self.trabajador = TrabajadorFuncion(
            self.controlador.ejecutar_analisis,
            seleccion,
            int(self.spin_anio.value()),
            int(self.spin_mes.value()),
            "manual" if self.combo_horizonte.currentData() is None else "predeterminado",
        )
        self.trabajador.resultado.connect(self._proyeccion_lista)
        self.trabajador.error.connect(self._mostrar_error)
        self.trabajador.finished.connect(lambda: self._establecer_ocupado(False))
        self.trabajador.start()

    def _proyeccion_lista(self, resultado: dict[str, Any], registrar: bool = True) -> None:
        self.widget_proyecciones.sincronizar_analisis_activo()
        proyeccion = resultado["proyeccion"]
        solicitado = proyeccion.get("resultado_horizonte_solicitado") or {}
        self.resultado_ui_actual = resultado
        if registrar:  # resultado nuevo del motor: todavía no pertenece a ningún análisis guardado
            self._analisis_resultados_id = None
        self._clave_vista_resultados = None
        self._actualizar_indicador_resultados()
        evaluaciones = (proyeccion.get("analisis_horizontes_completo") or {}).get("tabla_horizontes") or []
        self.detalles_horizonte = {
            int(item.get("horizonte")): item
            for item in evaluaciones
            if item.get("horizonte") is not None
        }
        self.horizonte_detalle_actual = None
        self.modelo_serie.establecer_dataframe(resultado["serie_df"])
        self.modelo_fila.establecer_dataframe(resultado["fila"])
        for boton in (self.boton_popup_serie, self.boton_popup_fila, self.boton_popup_grafica):
            boton.setEnabled(True)
        self._actualizar_tarjetas(self._resultado_visible()["proyeccion"])
        ruta_guardada = [i.get("valor", "") for i in resultado.get("ruta_jerarquica") or [] if i.get("nivel") != "Tabla ICOCIV"]
        if ruta_guardada and hasattr(self, "lbl_dashboard_ruta"):
            self.lbl_dashboard_ruta.setText(" · ".join(ruta_guardada))  # Fase 4I-B: coherente con el análisis mostrado
        self._renderizar_resultados_actuales()
        # Alimenta la calculadora ICOCIV; solo acumula una fila cuando el
        # análisis lo inicia el usuario (registrar=True), no el flujo de empalme.
        self.widget_proyecciones.actualizar_contexto(resultado, registrar=registrar and not self._restaurando_registros_icociv)
        if registrar and not self._restaurando_registros_icociv and self.widget_proyecciones.contexto.get("proyeccion_generada"):
            self.widget_proyecciones.registrar_analisis(
                resultado, self._seleccion_actual(),
                {"anio": int(self.spin_anio.value()), "mes": int(self.spin_mes.value()),
                 "horizonte": self._horizonte_solicitado(),
                 "origen_horizonte": "manual" if self.combo_horizonte.currentData() is None else "predeterminado"},
                self.controlador.ruta_archivo)
            self._analisis_resultados_id = self.widget_proyecciones.analisis_activo_id
        self._sincronizar_selector_resultados()
        self._restaurando_registros_icociv = False
        if not proyeccion.get("proyeccion_generada", True):
            self.lbl_horizonte_recomendado.setText(
                f"Horizonte solicitado: {solicitado.get('horizonte_solicitado', 'No disponible')} meses. "
                f"{solicitado.get('razon_principal', 'Proyección no generada.')}"
            )
            self.etiqueta_estado.setText("Proyección no generada para el horizonte solicitado.")
            self.lbl_dashboard_estado.setText("Horizonte no admisible · proyección no generada")
            return

        # H-4, 18-08-2026 (reauditoria dirigida V-CODEX-R2 residual). Ambas
        # etiquetas comparaban `solicitado["estado"]` contra el literal
        # "escenario", que `_estructurar_resultado_horizontes` no produce
        # desde el 08-08-2026 (solo entrega "proyeccion_tecnica" o
        # "no_admisible"): la rama nunca se ejecutaba.
        # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). Retirado
        # "Horizonte estadístico": el mensaje ahora resume el modelo
        # seleccionado y el horizonte efectivamente entregado.
        # post-r1-metodologia-12-24, 20-08-2026 (Prompt Calendario 04). El pool
        # productivo incluye candidatos Fourier K=1 ("fourier_k1__<base>") y
        # Seasonal Naive: el nombre visible (modelo_aplicado) distingue
        # modelo base y tratamiento calendario en vez de mostrar el codigo
        # interno del candidato.
        self.lbl_horizonte_recomendado.setText(
            f"Horizonte solicitado: {solicitado.get('horizonte_solicitado', '')} meses. "
            f"Modelo seleccionado: {solicitado.get('modelo_aplicado') or 'No aplica'}. "
            f"Alcance máximo de SAVIP: {H_OPERATIVO_MAX} meses."
        )
        self.etiqueta_estado.setText("Proyección ejecutada correctamente.")
        self.lbl_dashboard_estado.setText("Análisis actualizado correctamente")

    def _ejecutar_proyeccion_para_empalme_async(
        self,
        seleccion: dict[str, Any],
        anio: int,
        mes: int,
        al_terminar: Callable[[dict[str, Any] | None, str | None], None],
    ) -> None:
        """Ejecuta la proyección para Empalme en segundo plano.

        `_ejecutar_proyeccion_para_empalme` (sincrona, en el hilo principal)
        mostraba el velo de carga pero lo dejaba congelado durante el calculo:
        `QApplication.processEvents()` procesa la cola de eventos UNA vez antes
        de bloquear, no mientras el motor estadistico corre, asi que la barra
        indeterminada del velo no podia seguir animandose (el hilo que la
        pintaria estaba ocupado calculando). Se reutiliza el mismo worker
        (`TrabajadorFuncion`, un QThread) que usa el boton "Ejecutar" de
        Proyecciones, para que el hilo principal quede libre y el velo anime
        con normalidad durante todo el calculo. `al_terminar(resultado, None)`
        en exito, `al_terminar(None, mensaje)` en error; en ambos casos el
        velo se cierra antes de invocar el callback.
        """
        self._establecer_ocupado(True, "Calculando proyección ICOCIV...")
        controlador_empalme = ControladorPrincipal()
        controlador_empalme.ruta_archivo = self.controlador.ruta_archivo
        controlador_empalme.tablas = self.controlador.tablas
        controlador_empalme.periodos = self.controlador.periodos
        trabajador = TrabajadorFuncion(controlador_empalme.ejecutar_analisis, seleccion, int(anio), int(mes), "manual")
        self._trabajador_empalme = trabajador

        def _en_exito(resultado: dict[str, Any]) -> None:
            self._establecer_ocupado(False)
            al_terminar(resultado, None)

        def _en_error(mensaje: str) -> None:
            self._establecer_ocupado(False, exito=False)
            al_terminar(None, mensaje)

        trabajador.resultado.connect(_en_exito)
        trabajador.error.connect(_en_error)
        trabajador.finished.connect(lambda: setattr(self, "_trabajador_empalme", None))
        trabajador.start()

    def guardar_rapido(self, como: bool = False) -> bool:
        """Ctrl+S / botón: confirma antes la celda en edición (sin descartarla) y guarda la sesión."""
        foco = QApplication.focusWidget()
        if foco is not None:
            foco.clearFocus()  # el delegado de la tabla confirma su editor al perder el foco
        return self.guardar_sesion_actual(como=True) if como else self.guardar_sesion_actual()

    def guardar_sesion_actual(self, como: bool = False) -> bool:
        """Guarda la sesión. Con ruta asociada (abierta o ya guardada) escribe allí sin diálogos;
        sin ruta, o con «Guardar como…», pide el destino. Devuelve True solo si el archivo quedó escrito."""
        if self._operacion_sesion is not None:
            return False
        # Fase 4I-I: un cálculo de Empalme sin registrar también es trabajo que se guarda (como borrador).
        hay_empalme = bool(self.widget_empalme.calculos or self.widget_empalme.historial_empalme or self.widget_empalme.tiene_borrador())
        # Fase 4G: cargar un anexo nuevo vacía la proyección viva del controlador, pero el
        # historial ICOCIV guardado sigue siendo una sesión válida (instantáneas sin recalcular).
        hay_historial = bool(self.widget_proyecciones.historial)
        if self.controlador.proyeccion_actual is None and not hay_empalme and not hay_historial:
            self._aviso("Ejecute una proyección antes de guardar la sesión.", nivel="advertencia")
            return False

        destino = None if como else self.ruta_sesion_actual
        usuario = self.usuario_actual if destino is not None and self.usuario_actual else self._solicitar_usuario()
        if not usuario:
            return False

        seleccion = self._seleccion_actual()
        parametros = {"anio": int(self.spin_anio.value()), "mes": int(self.spin_mes.value()), "horizonte": self._horizonte_actual_meses()}
        ruta_jerarquica = self.controlador.construir_ruta_jerarquica(seleccion)
        nombre = generar_nombre_sesion(
            usuario,
            ruta_jerarquica,
            self.controlador.proyeccion_actual["periodo_proj"] if self.controlador.proyeccion_actual is not None
            else ((self.widget_proyecciones.analisis_activo() or {}).get("contexto", {}).get("periodo_proyectado") or "sin_objetivo")
            if hay_historial and not hay_empalme else self.widget_empalme._periodo_final(),
        )
        if destino is None:
            ruta_sugerida = (self.ruta_sesion_actual.parent if self.ruta_sesion_actual else asegurar_carpeta(CARPETA_SESIONES)) / nombre
            ruta_salida, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar sesión como" if como else "Guardar sesión",
                str(ruta_sugerida),
                "Sesión ICOCIV (*.json)",
            )
            if not ruta_salida:
                return False
            destino = Path(ruta_salida)

        datos = self.controlador.crear_datos_sesion(usuario, seleccion, parametros, ruta_jerarquica) if self.controlador.proyeccion_actual is not None else {'usuario': usuario, 'archivo_excel': str(self.controlador.ruta_archivo or '')}
        activo = self.widget_proyecciones.analisis_activo()
        if activo:
            datos.update(archivo_excel=activo["archivo_excel"], seleccion=deepcopy(activo["seleccion"]),
                         parametros_proyeccion=deepcopy(activo["parametros"]),
                         ruta_jerarquica=deepcopy(self.resultado_ui_actual["ruta_jerarquica"]))
        datos["proyecciones_icociv"] = self.widget_proyecciones.datos_sesion()
        datos["corte_dane"] = self._corte_dane_cargado() or corte_requerido_sesion(datos)
        if hay_empalme:datos['empalme_iccp_icociv'] = self.widget_empalme.datos_sesion()
        if hay_empalme:datos['tipo_resultado_visible'] = 'empalme' if self.selector_tipo_resultado.currentIndex() == 1 else 'icociv'
        if self.widget_proyecciones.historial and self.resultado_ui_actual is not None:
            datos["proyecciones_icociv"]["resultado_visible"] = serializar_resultado(self.resultado_ui_actual)
        self._operacion_sesion = "guardar"
        try:
            ruta = guardar_sesion(destino, datos)  # escritura atómica: el archivo anterior queda intacto si falla
        except (OSError, ValueError, TypeError) as error:
            QMessageBox.warning(self, "Guardar sesión", f"No se pudo guardar la sesión en «{destino}».\n\n{error}\n\n"
                                "Los datos siguen en memoria y quedan pendientes de guardar.")
            return False
        finally:
            self._operacion_sesion = None
        self.ruta_sesion_actual = ruta
        self.nombre_sesion_actual = ruta.name
        self._firma_guardada = self._firma_trabajo()
        self.etiqueta_estado.setText(f"Sesión guardada: {ruta.name}")
        if hasattr(self, "notificaciones"):
            self.notificaciones.exito("Sesión guardada", ruta.name)
        return True

    def _corte_dane_cargado(self) -> str:
        """Último periodo (AAAA-MM) del Excel DANE cargado; vacío si no hay ninguno."""
        periodos = self.controlador.periodos if self.controlador.archivo_cargado else None
        return periodo_a_iso(periodos[-1]) if periodos is not None and len(periodos) else ""

    def abrir_sesion(self) -> None:
        """Abre una sesión JSON sobre el Excel DANE YA cargado (paso 1), si su corte es igual o posterior.

        No abre ni busca el Excel original de la sesión y no recalcula nada: los análisis guardados se
        recuperan tal cual y el Excel cargado queda como contexto para el trabajo posterior. Fase 4I-G:
        la lectura del JSON corre en un hilo con el velo «Abriendo sesión…»; los widgets se reconstruyen
        en el hilo de la interfaz y, ante cualquier fallo, la sesión anterior queda intacta.
        """
        if self._operacion_sesion is not None:
            return
        corte_cargado = self._corte_dane_cargado()
        if not corte_cargado:
            QMessageBox.warning(self, "Abrir sesión", TEXTO_SIN_DANE)
            return
        ruta_sesion, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir sesión",
            str(self.ruta_sesion_actual.parent if self.ruta_sesion_actual else asegurar_carpeta(CARPETA_SESIONES)),
            "Sesión ICOCIV (*.json)",
        )
        if not ruta_sesion:
            return
        if self._hay_trabajo():
            decision = self._decidir_cierre("Abrir otra sesión", f"Para abrir «{Path(ruta_sesion).name}» se cerrará la sesión actual.")
            if decision == "cancelar" or (decision == "guardar" and not self.guardar_sesion_actual()):
                return
        self._operacion_sesion = "abrir"
        self._establecer_ocupado(True, "Abriendo sesión…")
        self._trabajador_sesion = TrabajadorFuncion(leer_sesion_json, ruta_sesion)
        self._trabajador_sesion.resultado.connect(lambda datos: self._sesion_leida(ruta_sesion, datos, corte_cargado))
        self._trabajador_sesion.error.connect(self._terminar_apertura)
        self._trabajador_sesion.start()

    def _sesion_leida(self, ruta_sesion: str, datos: dict[str, Any], corte_cargado: str) -> None:
        try:
            self.widget_proyecciones.validar_datos_sesion(datos.get("proyecciones_icociv"))
            self.widget_empalme.validar_datos_sesion(datos.get('empalme_iccp_icociv'))
        except (ValueError, TypeError, KeyError) as error:
            self._terminar_apertura(str(error))
            return
        requerido = corte_requerido_sesion(datos)
        if requerido and corte_cargado < requerido:  # AAAA-MM se compara bien como texto
            self._terminar_apertura(
                f"La sesión requiere un archivo ICOCIV con fecha base {requerido} o posterior. El archivo actualmente "
                f"cargado corresponde a {corte_cargado}. Cargue un archivo compatible para continuar.")
            return
        anterior = (self.widget_proyecciones.datos_sesion(), self.widget_empalme.datos_sesion(),
                    self.ruta_sesion_actual, self.nombre_sesion_actual, self._firma_guardada)
        try:
            self._reiniciar_espacio_trabajo()
            self.sesion_pendiente = datos
            self.nombre_sesion_actual = Path(ruta_sesion).name
            self._restaurar_sesion_pendiente()
        except Exception as error:  # noqa: BLE001 - se devuelve la sesión anterior completa, sin estados mixtos
            self.sesion_pendiente = None
            self.widget_proyecciones.restaurar_datos_sesion(anterior[0])
            self.widget_empalme.restaurar_datos_sesion(anterior[1])
            self.ruta_sesion_actual, self.nombre_sesion_actual, self._firma_guardada = anterior[2:]
            if self.widget_proyecciones.analisis_activo_id:
                self._activar_analisis(self.widget_proyecciones.analisis_activo_id, conservar_formulario=True)
            self._terminar_apertura(f"No se pudo abrir la sesión: {error}. Se conservó la sesión anterior.")
            return
        self.ruta_sesion_actual = Path(ruta_sesion)
        # El guardado rápido conserva el usuario de la sesión: no vuelve a pedir nombre ni ruta.
        self.usuario_actual = str(datos.get("usuario") or self.usuario_actual).strip()
        self._firma_guardada = self._firma_trabajo()
        self._terminar_apertura()
        self.boton_guardar_sesion.setEnabled(True)

    def _terminar_apertura(self, error: str = "") -> None:
        """Retira el velo (100 % solo con éxito) y, si hubo error, lo explica sin tocar la sesión vigente."""
        self._operacion_sesion = None
        self._establecer_ocupado(False, exito=not error)
        if error:
            self.etiqueta_estado.setText("No se abrió la sesión.")
            QMessageBox.warning(self, "Abrir sesión", error)

    def _firma_trabajo(self) -> str:
        """Huella de todo lo persistible del espacio de trabajo (ICOCIV, calculadora y Empalme)."""
        return json.dumps([self.widget_proyecciones.datos_sesion(), self.widget_empalme.datos_sesion()],
                          sort_keys=True, default=str)

    def _hay_trabajo(self) -> bool:
        """Hay algo que cerrar: un JSON asociado o cualquier dato distinto del espacio vacío
        (proyecto, análisis, actividades, borrador de calculadora o Empalme), no solo un análisis activo."""
        return self.ruta_sesion_actual is not None or self._firma_trabajo() != self._firma_vacia

    def _decidir_cierre(self, titulo: str, motivo: str) -> str:
        """Pregunta qué hacer con la sesión actual: «guardar», «descartar» o «cancelar»."""
        pendiente = "Hay cambios sin guardar." if self._firma_trabajo() != self._firma_guardada else "No hay cambios pendientes."
        texto = f"{motivo}\n\n{pendiente} ¿Desea guardar la sesión antes de cerrarla?"
        if self.widget_empalme.tiene_borrador():  # Fase 4I-I: el borrador viaja en la sesión al guardar
            texto += ("\n\nHay un cálculo de Empalme sin registrar: «Guardar y cerrar» lo conserva en la sesión "
                      "como borrador; «Cerrar sin guardar» lo descarta.")
        dialogo = QDialog(self);dialogo.setWindowTitle(titulo);dialogo.setObjectName("dialogo_cerrar_sesion")
        layout = QVBoxLayout(dialogo);layout.setContentsMargins(tokens.ESPACIO_5, tokens.ESPACIO_5, tokens.ESPACIO_5, tokens.ESPACIO_4)
        etiqueta = QLabel(texto);etiqueta.setWordWrap(True);etiqueta.setMinimumWidth(420);layout.addWidget(etiqueta)
        botones = QDialogButtonBox();layout.addWidget(botones)
        eleccion = {"valor": "cancelar"}
        for texto_boton, valor, rol, nombre in (("Guardar y cerrar", "guardar", QDialogButtonBox.ButtonRole.AcceptRole, ""),
                                                ("Cerrar sin guardar", "descartar", QDialogButtonBox.ButtonRole.DestructiveRole, "boton_secundario"),
                                                ("Cancelar", "cancelar", QDialogButtonBox.ButtonRole.RejectRole, "boton_secundario")):
            boton = QPushButton(texto_boton);boton.setObjectName(nombre)  # nombre antes de pulir el estilo
            botones.addButton(boton, rol)
            boton.clicked.connect(lambda _=False, valor=valor: (eleccion.update(valor=valor), dialogo.accept()))
            if valor == "guardar":
                boton.setDefault(True)
        dialogo.exec()  # Esc / cerrar la ventana = «Cancelar»
        return eleccion["valor"]

    def cerrar_sesion(self) -> bool:
        """Termina el presupuesto actual (preguntando siempre si guardar) y deja SAVIP listo para uno nuevo
        con el mismo Excel DANE. Nunca borra ni modifica el JSON en disco. Devuelve True si cerró."""
        if self._operacion_sesion is not None:
            return False
        if not self._hay_trabajo():
            self.etiqueta_estado.setText("No hay una sesión abierta que cerrar.")
            return False
        decision = self._decidir_cierre("Cerrar sesión", "Se cerrará el presupuesto actual; el archivo Excel del DANE seguirá cargado.")
        if decision == "cancelar" or (decision == "guardar" and not self.guardar_sesion_actual()):
            return False
        self._reiniciar_espacio_trabajo()
        self.etiqueta_estado.setText("Sesión cerrada. El archivo Excel del DANE sigue cargado.")
        return True

    def _reiniciar_espacio_trabajo(self) -> None:
        """Vacía proyecto, calculadora, actividades, historiales ICOCIV/Empalme, deshacer/rehacer, filtros,
        comparación y Resultados. Conserva el DANE cargado, la selección de serie, el tema y las preferencias."""
        self.widget_proyecciones.restaurar_datos_sesion(None)
        self.widget_empalme.restaurar_datos_sesion(None)
        c = self.controlador
        c.proyeccion_actual = c.serie_actual = c.fila_actual = c.fuente_actual = None
        self.resultado_ui_actual = None;self._analisis_resultados_id = None;self.detalles_horizonte = {};self.horizonte_detalle_actual = None
        html, etiquetas = self._resultados_iniciales
        self.texto_resultados.setHtml(html)
        for etiqueta, texto in etiquetas:
            etiqueta.setText(texto)
        self.modelo_serie.establecer_dataframe(None);self.modelo_fila.establecer_dataframe(None)
        for boton in (self.boton_popup_serie, self.boton_popup_fila, self.boton_popup_grafica):
            boton.setEnabled(False)
        self.selector_tipo_resultado.setCurrentIndex(0)
        self._sincronizar_selector_resultados();self._sincronizar_resultados_empalme()
        self._actualizar_indicador_resultados()
        self.ruta_sesion_actual = None;self.nombre_sesion_actual = None;self.sesion_pendiente = None
        self._firma_vacia = self._firma_guardada = self._firma_trabajo()
        self._actualizar_pantalla_inicio()

    # ------------------------------------------------------------ Fase 4I-J
    def _actualizar_fecha_presupuesto(self) -> None:
        texto = self.widget_proyecciones.resumen_fechas()
        self.lbl_fecha_presupuesto.setText(texto);self.lbl_fecha_presupuesto.setVisible(bool(texto))

    def aplicar_fecha_objetivo(self) -> bool:
        """Fecha objetivo (Año/Mes del bloque) sobre trayectorias guardadas: sin motor ni historial nuevo."""
        w = self.widget_proyecciones
        periodo = f"{int(self.spin_anio.value())}-{int(self.spin_mes.value()):02d}"
        solo = self.combo_alcance_fecha.currentData() == "individual"
        if solo and not w.analisis_activo_id:
            QMessageBox.information(self, "Fecha objetivo", "Seleccione un análisis para aplicar el cambio solo a él.")
            return False
        aplicado = w.aplicar_fecha_objetivo(periodo, w.analisis_activo_id if solo else None)
        if aplicado:
            self.etiqueta_estado.setText(f"Fecha objetivo aplicada: {fo.periodo_visible(periodo)} (sin ejecutar el motor).")
        self._actualizar_fecha_presupuesto()
        self._refrescar_vista_resultados()
        return aplicado

    def _resultado_visible(self) -> dict[str, Any] | None:
        """Fase 4I-P: lo que Resultados MUESTRA. Si el análisis mostrado tiene una consulta vigente, una copia
        transitoria con su fecha, H e índice (trayectoria guardada); si no, el resultado tal cual. Nunca se guarda:
        `resultado_ui_actual` sigue siendo el snapshot original."""
        resultado = self.resultado_ui_actual
        if not resultado or not self._analisis_resultados_id:
            return resultado
        analisis = next((a for a in self.widget_proyecciones.historial if a["id"] == self._analisis_resultados_id), None)
        return fo.resultado_consultado(resultado, analisis) if analisis else resultado

    def _al_cambiar_pila_deshacer(self, *_) -> None:
        if not hasattr(self, "lbl_fecha_presupuesto"):
            return
        try:
            self._refrescar_vista_resultados()
        except RuntimeError:  # la pila puede emitir al destruirse la ventana, con sus controles ya eliminados
            pass

    def _refrescar_vista_resultados(self) -> None:
        """Fase 4I-P: tras aplicar, deshacer o rehacer una fecha objetivo, Resultados y su selector se repintan
        con la consulta vigente. Solo presentación: sin motor, sin tocar análisis ni actividades."""
        self._sincronizar_selector_resultados()
        visible = self._resultado_visible()
        analisis = next((a for a in self.widget_proyecciones.historial if a["id"] == self._analisis_resultados_id), None)
        clave = (self._analisis_resultados_id, repr((analisis or {}).get("consulta_horizonte")))
        # Deshacer/rehacer de otras ediciones no cambia la consulta: no se repinta Resultados sin necesidad.
        if visible and clave != getattr(self, "_clave_vista_resultados", None):
            self._clave_vista_resultados = clave
            self._actualizar_tarjetas(visible["proyeccion"])
            self._renderizar_resultados_actuales()

    def _confirmar_reanalisis(self, texto: str) -> bool:
        caja = QMessageBox(QMessageBox.Icon.Question, "Actualizar proyecciones con datos DANE más recientes", texto,
                           QMessageBox.StandardButton.NoButton, self)
        actualizar = caja.addButton("Actualizar proyecciones", QMessageBox.ButtonRole.AcceptRole)
        cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(cancelar);caja.setEscapeButton(cancelar);caja.exec()
        return caja.clickedButton() is actualizar

    def actualizar_analisis_dane(self) -> None:
        """Solo por este botón y con confirmación: repite backtesting/selección de cada revisión VIGENTE cuyo
        origen es anterior al corte del DANE cargado y crea revisiones nuevas. Nada se recalcula al cargar
        un DANE, abrir o guardar sesiones; las revisiones anteriores y las actividades no cambian."""
        if self._operacion_sesion is not None or (self.trabajador is not None and self.trabajador.isRunning()):
            return
        corte = self._corte_dane_cargado()
        if not corte:
            QMessageBox.warning(self, "Actualizar análisis", TEXTO_SIN_DANE);return
        w = self.widget_proyecciones
        vigentes = fo.vigentes(w.historial)
        elegibles = [a for a in vigentes if fo.origen_analisis(a) and fo.origen_analisis(a) < corte]
        if not elegibles:
            QMessageBox.information(self, "Actualizar análisis", f"Ninguna revisión vigente tiene un corte anterior a "
                                    f"{fo.periodo_visible(corte)}: no hay observaciones nuevas que incorporar.");return
        planes, excluidos = [], []
        for a in elegibles:  # misma jerarquía exacta en el DANE nuevo; nunca una parecida
            try:
                ruta = [x.get("valor") for x in self.controlador.construir_ruta_jerarquica(a["seleccion"]) if x.get("nivel") != "Tabla ICOCIV"]
            except Exception:  # noqa: BLE001 - índice inexistente en el anexo nuevo
                ruta = None
            guardada = [x.get("valor") for x in (a["resultado"].get("ruta_jerarquica") or []) if x.get("nivel") != "Tabla ICOCIV"]
            if ruta != guardada:
                excluidos.append(f"«{a['nombre']}»: su serie no está disponible con la misma jerarquía en el DANE cargado.");continue
            objetivo = w.fecha_objetivo_presupuesto or fo.fecha_vigente(a)
            h = fo.meses_entre(corte, objetivo) if objetivo else 0
            destino = objetivo if 1 <= h <= fo.H_MAXIMO else fo.periodo_iso(f"{int(corte[:4]) + int(corte[5:]) // 12}-{int(corte[5:]) % 12 + 1}")
            planes.append((a["id"], deepcopy(a["seleccion"]), int(destino[:4]), int(destino[5:]), objetivo))
        texto = (f"Archivo DANE activo: {Path(str(self.controlador.ruta_archivo or '')).name}. Corte nuevo: {fo.periodo_visible(corte)}.\n"
                 f"Revisiones vigentes elegibles: {len(planes)}; no elegibles: {len(vigentes) - len(planes)}.\n\n"
                 "Al confirmar, se repetirá el backtesting y se generará una nueva proyección desde el último dato observado de "
                 "cada serie. Algunos meses antes estimados pasarán a ser observados. Podrían cambiar el modelo, las proyecciones, "
                 "las variaciones y el horizonte recomendado.\n\n"
                 "Las revisiones anteriores y todos los valores económicos guardados se conservarán sin cambios.")
        if excluidos:
            texto += "\n\nNo se actualizarán:\n" + "\n".join(excluidos)
        if not planes:
            QMessageBox.warning(self, "Actualizar análisis", texto);return
        if not self._confirmar_reanalisis(texto):
            return
        controlador = self.controlador

        def reanalizar():  # hilo secundario: solo el motor, una ejecución por revisión vigente (no por actividad)
            return [(id_, controlador.ejecutar_analisis(sel, anio, mes, "predeterminado"), objetivo)
                    for id_, sel, anio, mes, objetivo in planes]

        self._establecer_ocupado(True, "Actualizando análisis con el DANE más reciente…")
        self.trabajador = TrabajadorFuncion(reanalizar)
        self.trabajador.resultado.connect(lambda resultados: self._registrar_revisiones(resultados, excluidos))
        self.trabajador.error.connect(lambda error: (self._establecer_ocupado(False, exito=False),
                                                     QMessageBox.warning(self, "Actualizar análisis",
                                                                         f"No se creó ninguna revisión: {error}")))
        self.trabajador.start()

    def _registrar_revisiones(self, resultados, excluidos) -> None:
        """Hilo de interfaz: valida todo y registra las revisiones como un conjunto; ante fallo, nada cambia."""
        w = self.widget_proyecciones
        anterior = deepcopy(w.datos_sesion());activo = w.analisis_activo_id;borrador = w._datos_calculadora()
        avisos, nuevas = list(excluidos), {}
        try:
            fallidas = [a for a, r, _o in resultados if not (r.get("proyeccion") or {}).get("proyeccion_generada", True)]
            if fallidas:
                raise ValueError("el motor no generó proyección para alguna serie")
            for id_anterior, resultado, objetivo in resultados:
                previa = next(a for a in w.historial if a["id"] == id_anterior)
                w.actualizar_contexto(resultado, registrar=True)
                w.registrar_analisis(resultado, deepcopy(previa["seleccion"]), {
                    "anio": int(resultado["proyeccion"]["periodo_proj"].replace("-", "_").split("_")[0]),
                    "mes": int(resultado["proyeccion"]["periodo_proj"].replace("-", "_").split("_")[1]),
                    "horizonte": int(resultado["proyeccion"]["horizonte_solicitado"]),
                    "origen_horizonte": "predeterminado"}, self.controlador.ruta_archivo)
                nueva = w.historial[-1]
                revision = int(previa.get("revision", 1)) + 1
                nueva.update(revision_de=previa["id"], revision=revision, corte_anterior=fo.origen_analisis(previa),
                             corte_nuevo=fo.origen_analisis(nueva), modelo_anterior=previa["contexto"].get("modelo"),
                             archivo_dane=str(self.controlador.ruta_archivo or ""), reanalizado=datetime.now().isoformat(timespec="seconds"))
                nueva["nombre"] = (f"{len(w.historial)}. {nueva['contexto'].get('serie_final', '')} · DANE "
                                   f"{fo.periodo_visible(nueva['corte_nuevo'])} · revisión {revision}")
                try:  # se alinea con la fecha común si esa fecha es consultable en la nueva trayectoria
                    nueva["consulta_horizonte"] = {**fo.consultar(nueva, objetivo), "alcance": "todas",
                                                   "aplicado": nueva["reanalizado"]}
                except ValueError as error:
                    avisos.append(f"«{nueva['nombre']}»: la fecha objetivo no es consultable ({error}).")
                nuevas[id_anterior] = nueva["id"]
        except Exception as error:  # noqa: BLE001 - se restaura el presupuesto anterior completo
            w.restaurar_datos_sesion(anterior);w.restaurar_calculadora(borrador)
            if activo:
                self._activar_analisis(activo, conservar_formulario=True)
            self._establecer_ocupado(False, exito=False)
            QMessageBox.warning(self, "Actualizar análisis", f"No se creó ninguna revisión: {error}. El presupuesto no cambió.")
            return
        w.restaurar_calculadora(borrador)
        destino = nuevas.get(activo) or activo
        if destino:
            self._activar_analisis(destino, conservar_formulario=True)
        self._sincronizar_selector_resultados();self._actualizar_fecha_presupuesto()
        self._establecer_ocupado(False, exito=True)
        self.etiqueta_estado.setText(f"{len(nuevas)} revisiones nuevas creadas; las anteriores y las actividades se conservan.")
        if avisos:
            QMessageBox.information(self, "Actualizar análisis", "\n".join(avisos))

    def generar_informe(self) -> None:
        self._generar_informe("docx")

    def generar_informe_pdf(self) -> None:
        self._generar_informe("pdf")

    def _generar_informe(self, formato: str) -> None:
        """Pide la configuración, el destino y lanza la generación en segundo plano."""
        if self.controlador.proyeccion_actual is None:
            self._aviso("Ejecute el análisis antes de generar el informe.", nivel="advertencia")
            return

        usuario = self._solicitar_usuario()
        if not usuario:
            return

        configuracion = pedir_configuracion(self, tipo_inicial="ejecutivo", formato=formato.upper())
        if configuracion is None:
            return

        seleccion = self._seleccion_actual()
        ruta_jerarquica = self.controlador.construir_ruta_jerarquica(seleccion)
        nombre = nombre_archivo_informe(
            configuracion.tipo, self._referencia_nombre_informe(ruta_jerarquica), formato,
        )
        ruta_sugerida = asegurar_carpeta(CARPETA_REPORTES) / nombre
        filtro = "Documento PDF (*.pdf)" if formato == "pdf" else "Documento Word (*.docx)"
        ruta_salida, _ = QFileDialog.getSaveFileName(self, "Guardar informe", str(ruta_sugerida), filtro)
        if not ruta_salida:
            return

        parametros = {
            "anio": int(self.spin_anio.value()),
            "mes": int(self.spin_mes.value()),
            "horizonte": self._horizonte_actual_meses(),
        }
        funcion = generar_reporte_pdf if formato == "pdf" else generar_reporte_proyeccion
        self._establecer_ocupado(True, f"Generando informe {formato.upper()}...")
        self.trabajador = TrabajadorFuncion(
            funcion,
            ruta_salida,
            usuario,
            str(self.controlador.ruta_archivo or ""),
            seleccion,
            parametros,
            ruta_jerarquica,
            nombre_tabla_icociv(self.controlador.fuente_actual),
            self.controlador.fila_actual,
            self.controlador.serie_actual,
            self.controlador.proyeccion_actual,
            self.controlador.periodos,
            self.nombre_sesion_actual,
            configuracion,
        )
        self.trabajador.resultado.connect(
            lambda ruta: self.etiqueta_estado.setText(f"Informe generado: {Path(ruta).name}")
        )
        self.trabajador.error.connect(self._mostrar_error)
        self.trabajador.finished.connect(lambda: self._establecer_ocupado(False))
        self.trabajador.start()

    def _referencia_nombre_informe(self, ruta_jerarquica: Any) -> str:
        """Último nivel seleccionado; da nombres de archivo reconocibles."""
        items = list(ruta_jerarquica or [])
        utiles = [i for i in items if str(i.get("nivel", "")) != "Tabla ICOCIV" and str(i.get("valor", "")).strip()]
        if utiles:
            return str(utiles[-1].get("valor"))
        return nombre_tabla_icociv(self.controlador.fuente_actual) or "Serie"

    def exportar_reproducibilidad_csv(self) -> None:
        if self.controlador.proyeccion_actual is None:
            self._aviso("Ejecute el análisis antes de exportar datos reproducibles.", nivel="advertencia")
            return
        ruta_sugerida = asegurar_carpeta(CARPETA_REPORTES) / generar_nombre_reproducibilidad_csv()
        ruta_salida, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar datos reproducibles CSV",
            str(ruta_sugerida),
            "Archivo CSV (*.csv)",
        )
        if not ruta_salida:
            return
        self._establecer_ocupado(True, "Exportando CSV reproducible...")
        self.trabajador = TrabajadorFuncion(
            generar_csv_reproducibilidad,
            ruta_salida,
            self.controlador.serie_actual,
            self.controlador.proyeccion_actual,
        )
        self.trabajador.resultado.connect(lambda ruta: self.etiqueta_estado.setText(f"CSV generado: {Path(ruta).name}"))
        self.trabajador.error.connect(self._mostrar_error)
        self.trabajador.finished.connect(lambda: self._establecer_ocupado(False))
        self.trabajador.start()

    def _actualizar_jerarquia(self) -> None:
        if not self.controlador.archivo_cargado:
            return
        seleccion = self._seleccion_actual()
        estado = self.controlador.obtener_estado_jerarquia(seleccion)
        self._actualizar_tabla_activa(seleccion)
        self._actualizar_ruta_visible(seleccion)

        self._rellenar_nivel(self.lbl_nivel2, self.combo_nivel2, estado["nivel2"])
        self._rellenar_nivel(self.lbl_nivel3, self.combo_nivel3, estado["nivel3"])
        self._rellenar_nivel(self.lbl_nivel4, self.combo_nivel4, estado["nivel4"])
        self._rellenar_nivel(self.lbl_nivel5, self.combo_nivel5, estado["nivel5"])
        self._rellenar_nivel(self.lbl_nivel6, self.combo_nivel6, estado["nivel6"])

        self._establecer_visible_checkbox(self.chk_t16_1, estado["mostrar_chk_t16_1"])
        self._establecer_visible_checkbox(self.chk_t16_2, estado["mostrar_chk_t16_2"])
        self._establecer_visible_checkbox(self.chk_t16_3, estado["mostrar_chk_t16_3"])

    def _actualizar_tabla_activa(self, seleccion: dict[str, Any]) -> None:
        nombre = self.controlador.nombre_fuente_seleccion(seleccion)
        if nombre:
            self.lbl_tabla_activa.setText(f"{ETIQUETA_TABLA_ACTIVA}: {nombre}")
        else:
            self.lbl_tabla_activa.setText(TEXTO_TABLA_SIN_SELECCION)

    def _actualizar_ruta_visible(self, seleccion: dict[str, Any]) -> None:
        ruta = self.controlador.construir_ruta_jerarquica(seleccion)
        ruta_sin_tabla = [item for item in ruta if item.get("nivel") != "Tabla ICOCIV"]
        if not ruta_sin_tabla:
            self._texto_ruta_copia = "";self.boton_copiar_ruta.setEnabled(False)
            self.lbl_ruta_jerarquica.setTextFormat(Qt.TextFormat.PlainText)
            self.scroll_ruta_jerarquica.setFixedHeight(tokens.ESPACIO_8)
            self.lbl_ruta_jerarquica.setText("Ruta jerárquica: sin selección")
            self.lbl_ruta_jerarquica.setToolTip("Ruta jerárquica: sin selección")
            if hasattr(self, "lbl_dashboard_ruta"):
                self.lbl_dashboard_ruta.setText("Seleccione una ruta jerárquica para iniciar.")
            return
        lineas = ["Ruta jerárquica seleccionada:"]
        self.scroll_ruta_jerarquica.setMinimumHeight(72)
        self.scroll_ruta_jerarquica.setMaximumHeight(150)
        for item in ruta_sin_tabla:
            lineas.append(f"{item.get('nivel', '')}: {item.get('valor', '')}")
        texto = "\n".join(lineas)
        # Ajuste visual: etiquetas en negrita moderada y valor normal, una línea por nivel.
        self.lbl_ruta_jerarquica.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_ruta_jerarquica.setText("Ruta jerárquica seleccionada<br>" + "<br>".join(
            f"<b>{escape(str(item.get('nivel', '')))}:</b> {escape(str(item.get('valor', '')))}" for item in ruta_sin_tabla))
        self.lbl_ruta_jerarquica.setToolTip(texto)
        self._texto_ruta_copia = "\n".join(lineas[1:]);self.boton_copiar_ruta.setEnabled(True)
        # Alto según el contenido (todas las líneas visibles sin barra), con el tope previo de 150 px.
        ancho = max(200, self.scroll_ruta_jerarquica.viewport().width())
        contenido = max(self.lbl_ruta_jerarquica.heightForWidth(ancho - 2 * tokens.ESPACIO_3),
                        len(lineas) * self.lbl_ruta_jerarquica.fontMetrics().lineSpacing())
        self.scroll_ruta_jerarquica.setFixedHeight(min(150, max(72, contenido + 2 * tokens.ESPACIO_2 + 20)))
        if hasattr(self, "lbl_dashboard_ruta"):
            self.lbl_dashboard_ruta.setText(" · ".join(item.get("valor", "") for item in ruta_sin_tabla))
            self.lbl_dashboard_ruta.setToolTip(texto)

    def _copiar_ruta(self) -> None:
        """Copia la ruta jerárquica (una línea por nivel) y confirma en el propio botón, sin ventanas."""
        if not self._texto_ruta_copia:
            return
        QApplication.clipboard().setText(self._texto_ruta_copia)
        self.boton_copiar_ruta.setText("Ruta copiada ✓")
        self.etiqueta_estado.setText("Ruta jerárquica copiada al portapapeles.")
        QTimer.singleShot(1600, lambda: self.boton_copiar_ruta.setText("Copiar ruta"))

    def _rellenar_nivel(self, etiqueta: QLabel, combo: QComboBox, descriptor: dict[str, Any] | None) -> None:
        valor_actual = combo.currentData()
        if not descriptor or not descriptor["opciones"]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Sin selección", None)
            combo.setItemData(0, "Sin selección", Qt.ItemDataRole.ToolTipRole)
            self._actualizar_tooltip_combo(combo)
            combo.blockSignals(False)
            etiqueta.setVisible(False)
            combo.setVisible(False)
            return

        etiqueta.setText(descriptor["etiqueta"])
        etiqueta.setVisible(True)
        combo.setVisible(True)
        self._llenar_combo(combo, descriptor["opciones"], valor_actual)

    def _llenar_combo(self, combo: QComboBox, opciones: list[dict[str, Any]], valor_actual: Any = None) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Sin selección", None)
        combo.setItemData(0, "Sin selección", Qt.ItemDataRole.ToolTipRole)
        indice_a_restaurar = 0
        maximo_ancho = combo.minimumWidth()
        for opcion in opciones:
            combo.addItem(opcion["texto"], opcion["indice"])
            indice_item = combo.count() - 1
            combo.setItemData(indice_item, opcion["texto"], Qt.ItemDataRole.ToolTipRole)
            maximo_ancho = max(maximo_ancho, combo.fontMetrics().horizontalAdvance(opcion["texto"]) + 56)
            if opcion["indice"] == valor_actual:
                indice_a_restaurar = combo.count() - 1
        combo.setCurrentIndex(indice_a_restaurar)
        combo.view().setMinimumWidth(min(maximo_ancho, 900))
        self._actualizar_tooltip_combo(combo)
        combo.blockSignals(False)

    def _seleccion_actual(self) -> dict[str, Any]:
        return {
            "idx_g": self.combo_grupo.currentData(),
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

    def _restaurar_sesion_pendiente(self) -> None:
        datos = self.sesion_pendiente or {}
        self.sesion_pendiente = None
        if not (datos.get("proyecciones_icociv") or {}).get("historial_analisis"):
            self._restaurar_seleccion_y_parametros(datos.get("seleccion", {}), datos.get("parametros_proyeccion", {}))
        self.etiqueta_estado.setText(f"Sesión abierta: {self.nombre_sesion_actual}")
        self.widget_proyecciones.restaurar_datos_sesion(datos.get("proyecciones_icociv"))
        self.widget_empalme.restaurar_datos_sesion(datos.get('empalme_iccp_icociv'))
        self.selector_tipo_resultado.setCurrentIndex(1 if datos.get('tipo_resultado_visible') == 'empalme' else 0)
        self._sincronizar_selector_resultados()
        if self.widget_proyecciones.historial:
            activo = self.widget_proyecciones.analisis_activo_id
            if activo:
                self._activar_analisis(activo, conservar_formulario=True)
            elif datos["proyecciones_icociv"].get("resultado_visible"):
                self._analisis_resultados_id = None
                self._mostrar_resultado_guardado(recuperar_resultado(datos["proyecciones_icociv"]["resultado_visible"]))
            self._restaurando_registros_icociv = False
            return
        # Sin historial (formato V1.0): se recuperan selección y parámetros, pero NO se ejecuta el motor
        # al abrir; el usuario decide si proyectar con el Excel cargado.
        self._restaurando_registros_icociv = False
        if datos.get("seleccion") and not datos.get('empalme_iccp_icociv'):
            self.etiqueta_estado.setText(f"Sesión abierta: {self.nombre_sesion_actual}. Pulse «Ejecutar proyección» para proyectar con el archivo cargado.")

    def _restaurar_seleccion_y_parametros(self, seleccion, parametros) -> None:
        self._establecer_combo_por_data(self.combo_grupo, seleccion.get("idx_g"))
        self.chk_t16.setChecked(bool(seleccion.get("chk_T16", False)))
        self._actualizar_jerarquia()
        self._establecer_combo_por_data(self.combo_nivel2, seleccion.get("idx_l2"))
        self.chk_t16_1.setChecked(bool(seleccion.get("chk_T16_1", False)))
        self._actualizar_jerarquia()
        self._establecer_combo_por_data(self.combo_nivel3, seleccion.get("idx_l3"))
        self.chk_t16_2.setChecked(bool(seleccion.get("chk_T16_2", False)))
        self._actualizar_jerarquia()
        self._establecer_combo_por_data(self.combo_nivel4, seleccion.get("idx_l4"))
        self.chk_t16_3.setChecked(bool(seleccion.get("chk_T16_3", False)))
        self._actualizar_jerarquia()
        self._establecer_combo_por_data(self.combo_nivel5, seleccion.get("idx_l5"))
        self._establecer_combo_por_data(self.combo_nivel6, seleccion.get("idx_l6"))

        # Los cuatro controles se restauran en bloque para que no se
        # sobrescriban entre sí mientras se aplica la sesión guardada.
        horizonte = parametros.get("horizonte")
        self._sincronizando = True
        try:
            if horizonte:
                self._seleccionar_horizonte_en_combo(int(horizonte))
                if 1 <= int(horizonte) <= self.spin_horizonte_personalizado.maximum():
                    self.spin_horizonte_personalizado.setValue(int(horizonte))
            self.spin_anio.setValue(int(parametros.get("anio", self.spin_anio.value())))
            self.spin_mes.setValue(int(parametros.get("mes", self.spin_mes.value())))
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _sincronizar_selector_resultados(self) -> None:
        if hasattr(self, "lbl_fecha_presupuesto"):
            self._actualizar_fecha_presupuesto()
        selector = self.selector_resultados_icociv
        selector.blockSignals(True)
        selector.clear()
        selector.addItem("Sin análisis ICOCIV activo" if self.widget_proyecciones.historial else "Sin análisis ICOCIV guardados", None)
        for a in self.widget_proyecciones.historial:
            selector.addItem(fo.nombre_vigente(a), a["id"])  # Fase 4I-P: consulta vigente; el nombre guardado no cambia
            if fo.detalle_vigente(a):
                selector.setItemData(selector.count() - 1, fo.detalle_vigente(a), Qt.ItemDataRole.ToolTipRole)
        selector.setCurrentIndex(max(0, selector.findData(self.widget_proyecciones.analisis_activo_id)))
        selector.blockSignals(False)

    def _sincronizar_resultados_empalme(self):
        w = self.widget_empalme;s = self.selector_resultados_empalme
        s.blockSignals(True);s.clear();s.addItem('Sin análisis de Empalme activo' if w.historial_empalme else 'Sin análisis de Empalme guardados', None)
        for a in w.historial_empalme:s.addItem(a['nombre'], a['id'])
        s.setCurrentIndex(max(0,s.findData(w.analisis_empalme_activo_id)));s.blockSignals(False)
        a = w.analisis_empalme_activo()
        if a:
            r = w.resultado_analisis_empalme(a)
            fuente = a['archivo_excel'] or ('ICCP interno' if r.get('caso') == 'solo_iccp' else 'Referencia guardada sin archivo')
            self.texto_resultados_empalme.setHtml(f"<h3>{escape(a['nombre'])}</h3><p>Proyecto al calcular: {escape(str(r.get('contrato') or 'Sin nombre'))} · Fuente: {escape(fuente)}</p>" + w.resultado.toHtml())
        else:self.texto_resultados_empalme.setPlainText('Sin análisis de Empalme activo. Calcule una actualización o seleccione una ejecución guardada.')
        if hasattr(self, 'navegacion') and hasattr(self, 'tabs_principales'):
            self._actualizar_indicador_resultados()
            self.boton_guardar_sesion.setEnabled(bool(w.calculos or w.historial_empalme or self.widget_proyecciones.historial or self.controlador.archivo_cargado))

    def _seleccionar_resultado_empalme(self):
        identificador = self.selector_resultados_empalme.currentData()
        if identificador:self.widget_empalme.activar_analisis_empalme(identificador)
        self._sincronizar_resultados_empalme()

    def _seleccionar_resultado_icociv(self) -> None:
        identificador = self.selector_resultados_icociv.currentData()
        if identificador:
            self._activar_analisis(identificador)
        elif self.widget_proyecciones.analisis_activo_id is not None:
            self.widget_proyecciones.desactivar_analisis()
        else:
            self._sincronizar_selector_resultados()

    def _analisis_icociv_desactivado(self) -> None:
        """Sincroniza Resultados con «Sin análisis activo» sin borrar nada."""
        self._sincronizar_selector_resultados()
        self.etiqueta_estado.setText("No hay análisis ICOCIV seleccionado; historial y registros conservados.")
        self.lbl_dashboard_estado.setText("No hay análisis seleccionado")

    def _analisis_equivalente(self, seleccion: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """(análisis reutilizable, análisis de la misma serie con otros datos) entre las revisiones VIGENTES.

        La equivalencia se verifica con los datos que realmente recibiría el motor: identidad de la serie
        (tabla, fila fuente y ruta) y huella de la serie mensual observada (periodos y valores), no con el
        nombre ni la fecha del archivo. Solo es reutilizable si su instantánea conserva los 24 meses; una
        sesión anterior sin trayectoria se proyecta de nuevo (otra configuración del motor).
        """
        try:
            vista = self.controlador.vista_previa_ejecucion(seleccion)
        except Exception:  # noqa: BLE001 - sin vista previa no se puede demostrar la equivalencia
            return None, None
        clave, huella = identidad_serie(vista)[0], huella_datos(vista)
        if not clave or not huella:
            return None, None
        otros = None
        for a in reversed(fo.vigentes(self.widget_proyecciones.historial)):
            if identidad_serie(a["resultado"])[0] != clave:
                continue
            if huella_datos(a["resultado"]) == huella:
                if len(fo.trayectoria(a)) >= fo.H_MAXIMO:
                    return a, None
                continue
            otros = otros or a
        return None, otros

    def _reutilizar_trayectoria(self, analisis: dict[str, Any]) -> None:
        """Activa el análisis equivalente y aplica el mes pedido desde su trayectoria guardada (sin motor)."""
        w = self.widget_proyecciones
        periodo = f"{int(self.spin_anio.value())}-{int(self.spin_mes.value()):02d}"
        self._activar_analisis(analisis["id"], conservar_formulario=True)
        # Activar restaura los parámetros originales del análisis: se devuelve al bloque el mes que pidió el usuario.
        self.spin_anio.setValue(int(periodo[:4]));self.spin_mes.setValue(int(periodo[5:]))
        # Reutilizar en «Ejecutar proyección» solo consulta: las actividades se actualizan con el botón y su confirmación.
        if not w.aplicar_fecha_objetivo(periodo, analisis["id"], confirmar=False, actualizar_actividades=False):
            return
        consulta = analisis["consulta_horizonte"]
        detalle = (f"«{analisis['contexto'].get('serie_final', analisis['nombre'])}»: {fo.periodo_visible(periodo)} "
                   f"(H{consulta['horizonte']}) tomado de su trayectoria de 24 meses; no se ejecutó el motor.")
        comun = w.fecha_objetivo_presupuesto
        if comun and comun != periodo:
            detalle += f" Queda fuera de la fecha común del presupuesto ({fo.periodo_visible(comun)})."
        self._aviso("Se reutilizó la proyección guardada", detalle)
        self.etiqueta_estado.setText(f"Proyección reutilizada sin recalcular: {fo.periodo_visible(periodo)} · H{consulta['horizonte']}.")
        self._actualizar_fecha_presupuesto()
        self._refrescar_vista_resultados()

    def _mostrar_resultado_guardado(self, resultado) -> None:
        self.controlador.fuente_actual = resultado["fuente"]
        self.controlador.fila_actual = resultado["fila"]
        self.controlador.serie_actual = resultado["serie_df"]
        self.controlador.proyeccion_actual = resultado["proyeccion"]
        self._proyeccion_lista(resultado, registrar=False)

    def _activar_analisis(self, identificador: str, conservar_formulario: bool = False) -> None:
        w = self.widget_proyecciones
        if not conservar_formulario and ((self.trabajador is not None and self.trabajador.isRunning())
                or (self._trabajador_empalme is not None and self._trabajador_empalme.isRunning())):
            w._refrescar_historial()
            return
        analisis = next((a for a in w.historial if a["id"] == identificador), None)
        if analisis is None:
            return
        if not conservar_formulario:
            w.sincronizar_analisis_activo()
        resultado = recuperar_resultado(analisis["resultado"])
        misma_fuente = (self.controlador.archivo_cargado and self.controlador.ruta_archivo is not None
                        and Path(analisis["archivo_excel"]).resolve() == self.controlador.ruta_archivo.resolve())
        ruta_restaurada = False
        if misma_fuente:
            anterior = self._seleccion_actual()
            self._restaurar_seleccion_y_parametros(analisis["seleccion"], analisis["parametros"])
            ruta_actual = self.controlador.construir_ruta_jerarquica(self._seleccion_actual())
            ruta_restaurada = [r for r in ruta_actual if r.get("nivel") != "Tabla ICOCIV"] == [
                r for r in resultado["ruta_jerarquica"] if r.get("nivel") != "Tabla ICOCIV"]
            if not ruta_restaurada:
                self._restaurar_seleccion_y_parametros(anterior, analisis["parametros"])
        self._analisis_resultados_id = identificador
        self._mostrar_resultado_guardado(resultado)
        # Fase 4G-B: activar una proyección NO carga datos de ninguna actividad ni del
        # formulario guardado: la calculadora conserva lo que el usuario digitó.
        w.establecer_analisis_activo(identificador)
        self._sincronizar_selector_resultados()
        if not ruta_restaurada:
            w.lbl_analisis.setText(w.lbl_analisis.text() +
                " · Referencia guardada; los selectores corresponden al archivo cargado y pueden diferir. "
                "La calculadora utiliza exclusivamente el resultado guardado.")
        self.etiqueta_estado.setText(f"Análisis recuperado sin recalcular: {fo.nombre_vigente(analisis)}")

    def _establecer_combo_por_data(self, combo: QComboBox, valor: Any) -> None:
        for indice in range(combo.count()):
            if combo.itemData(indice) == valor:
                combo.setCurrentIndex(indice)
                return

    def _reiniciar_desde_nivel2(self) -> None:
        self._limpiar_combos(self.combo_nivel2, self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia()

    def _reiniciar_desde_nivel3(self) -> None:
        self._limpiar_combos(self.combo_nivel3, self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia()

    def _reiniciar_desde_nivel4(self) -> None:
        self._limpiar_combos(self.combo_nivel4, self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia()

    def _reiniciar_desde_nivel5(self) -> None:
        self._limpiar_combos(self.combo_nivel5, self.combo_nivel6)
        self._actualizar_jerarquia()

    def _reiniciar_desde_nivel6(self) -> None:
        self._limpiar_combos(self.combo_nivel6)
        self._actualizar_jerarquia()

    def _limpiar_combos(self, *combos: QComboBox) -> None:
        for combo in combos:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Sin selección", None)
            combo.blockSignals(False)

    def _ocultar_niveles(self) -> None:
        for widget in (
            self.lbl_nivel2, self.combo_nivel2, self.lbl_nivel3, self.combo_nivel3,
            self.lbl_nivel4, self.combo_nivel4, self.lbl_nivel5, self.combo_nivel5,
            self.lbl_nivel6, self.combo_nivel6, self.chk_t16_1, self.chk_t16_2, self.chk_t16_3,
        ):
            widget.setVisible(False)

    def _establecer_visible_checkbox(self, checkbox: QCheckBox, visible: bool) -> None:
        if not visible:
            checkbox.blockSignals(True)
            checkbox.setChecked(False)
            checkbox.blockSignals(False)
        checkbox.setVisible(visible)

    def _ajustar_periodo_por_defecto(self, periodos: list[str]) -> None:
        """Deja los cuatro controles coherentes tras cargar una serie nueva."""
        if not periodos:
            return
        anio, mes = [int(parte) for parte in periodos[-1].split("_")]
        mes += 1
        if mes == 13:
            anio += 1
            mes = 1
        self._sincronizando = True
        try:
            self.combo_horizonte.setCurrentIndex(0)  # 1 mes
            self.spin_horizonte_personalizado.setValue(1)
            self._actualizar_edicion_horizonte()
            self.spin_anio.setValue(anio)
            self.spin_mes.setValue(mes)
        finally:
            self._sincronizando = False
        self._actualizar_etiqueta_horizonte_pendiente()

    def _dibujar_grafica(self, figura, serie_df, proyeccion: dict[str, Any]) -> list[str]:
        colores = paleta_tema(self.tema_actual)
        figura.clear()
        figura.savip_detalle_proyeccion = {}  # Fase 4I-P: detalle por punto (se rellena al dibujar)
        figura.patch.set_facecolor(colores["grafica"])
        eje = figura.add_subplot(111)
        eje.set_facecolor(colores["grafica"])
        periodos_obs = [periodo_a_iso(p) for p in serie_df["Periodo"].tolist()]
        etiquetas = list(periodos_obs)
        proy_df = proyeccion.get("proyecciones")
        if proyeccion.get("proyeccion_generada", True) and hasattr(proy_df, "empty") and not proy_df.empty:
            for periodo in proy_df["periodo"].tolist():
                etiqueta = periodo_a_iso(periodo)
                if etiqueta not in etiquetas:
                    etiquetas.append(etiqueta)
        indice_x = {etiqueta: idx for idx, etiqueta in enumerate(etiquetas)}
        x_obs = [indice_x[p] for p in periodos_obs]
        # Cada serie tiene además forma propia (marcador y trazo): el color no es
        # el único portador de la distinción, para no depender de verlo bien.
        eje.plot(
            x_obs,
            proyeccion["y_obs"],
            marker="o",
            markersize=3.5,
            linewidth=1.8,
            color=colores["serie_historica"],
            label="Serie observada",
        )
        if proyeccion.get("proyeccion_generada", True):
            periodos_full = [periodo_a_iso(t_a_periodo(int(t), ANIO_BASE)) for t in proyeccion.get("t_full", [])]
            x_full = [indice_x[p] for p in periodos_full if p in indice_x]
            y_fit_full = list(proyeccion.get("y_fit_full", []))[: len(x_full)]
            if x_full and len(y_fit_full) == len(x_full):
                eje.plot(
                    x_full,
                    y_fit_full,
                    linestyle="--",
                    linewidth=1.4,
                    color=colores["serie_ajuste"],
                    label="Ajuste del modelo",
                )
            if hasattr(proy_df, "empty") and not proy_df.empty:
                x_future = [indice_x[periodo_a_iso(p)] for p in proy_df["periodo"].tolist()]
                # P0-H, 17-08-2026 (V-CODEX-R3, residual 3). Misma regla que en la
                # grafica de los informes: un mes no disponible no se une a sus
                # vecinos. La disponibilidad la calcula el servicio una sola vez y
                # viaja en `horizonte_disponible`; aqui solo se enmascara.
                y_future = proy_df["indice_proyectado"].astype(float).to_numpy()
                if "horizonte_disponible" in proy_df.columns:
                    disponible = proy_df["horizonte_disponible"].astype(bool).to_numpy()
                    y_future = np.where(disponible, y_future, np.nan)
                if x_obs and x_future:
                    # Línea divisoria entre lo observado y lo proyectado.
                    eje.axvline(
                        x_obs[-1],
                        color=colores["borde_fuerte"],
                        linewidth=1.0,
                        linestyle=":",
                        alpha=0.9,
                    )
                eje.plot(
                    x_future,
                    y_future,
                    marker="D",
                    markersize=3.5,
                    linewidth=1.8,
                    color=colores["serie_proyeccion"],
                    label="Proyección",
                )
                # post-r1-metodologia-12-24, 19-08-2026 (Prompt 13). P0-C RUTA
                # C2: el intervalo de confianza (IC80/IC95) sigue retirado de
                # las salidas. Ninguno de los trece metodos auditados resulto
                # adoptable y REQ 20 prohibe la combinacion que se venia
                # publicando; el calculo interno se conserva como diagnostico
                # y no se publica.
                #
                # Lo que SI se dibuja es una banda puramente DESCRIPTIVA
                # y_hat_h +/- MAE_h, tomada del MAE fuera de muestra por
                # horizonte del modelo YA seleccionado (mismo rectangulo que
                # decidio la seleccion, `horizonte_info.tabla_horizontes`). No
                # es un intervalo de confianza ni de prediccion probabilistico:
                # no decide nada, solo ilustra la magnitud historica del
                # error. Se omite el punto donde MAE_h no existe o no es
                # finito, sin inventar un valor.
                horizonte_info_grafica = proyeccion.get("horizonte_info") or {}
                mae_por_horizonte = {
                    int(item["horizonte"]): item.get("mae")
                    for item in (horizonte_info_grafica.get("tabla_horizontes") or [])
                    if item.get("horizonte") is not None
                }
                limite_inf, limite_sup = [], []
                # Fase 4I-P: el visor muestra al hacer clic en cada punto proyectado su H, I(h), MAE(h) y la
                # referencia I(h) ± MAE(h). Mismos valores que la banda; sin MAE(h) no se inventa ninguno.
                detalle_puntos: dict[int, dict[str, Any]] = {}
                for paso, (x_paso, valor) in enumerate(zip(x_future, y_future), start=1):
                    mae_h = mae_por_horizonte.get(paso)
                    try:
                        mae_h = float(mae_h) if mae_h is not None and np.isfinite(float(mae_h)) else None
                    except (TypeError, ValueError):
                        mae_h = None
                    if valor == valor and mae_h is not None:
                        limite_inf.append(float(valor) - mae_h)
                        limite_sup.append(float(valor) + mae_h)
                    else:
                        limite_inf.append(np.nan)
                        limite_sup.append(np.nan)
                    detalle_puntos[int(x_paso)] = {"horizonte": paso, "mae": mae_h, "inferior": limite_inf[-1],
                                                   "superior": limite_sup[-1]}
                figura.savip_detalle_proyeccion = detalle_puntos
                if any(v == v for v in limite_inf):
                    eje.fill_between(
                        x_future,
                        limite_inf,
                        limite_sup,
                        color=colores["banda_intervalo"],
                        alpha=0.16,
                        linewidth=0,
                        label="Referencia de error histórico ±MAE(h) (no es intervalo de confianza)",
                    )
        eje.set_title("Ajuste y proyección del índice ICOCIV", pad=12, fontsize=11, fontweight="600")
        eje.set_xlabel("Periodo (AAAA-MM)")
        eje.set_ylabel("Índice")
        if etiquetas:
            # Ticks dinámicos: se recalculan solos en cada zoom/desplazamiento
            # en lugar de fijarse una única vez (ver widgets/visor_grafica.py).
            configurar_ejes_dinamicos(eje, etiquetas)
        eje.tick_params(colors=colores["texto_secundario"], labelsize=8.5, length=0, pad=6)
        eje.title.set_color(colores["texto"])
        eje.xaxis.label.set_color(colores["texto_secundario"])
        eje.yaxis.label.set_color(colores["texto_secundario"])
        # Marco reducido a los ejes que orientan la lectura.
        for lado in ("top", "right"):
            eje.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            eje.spines[lado].set_color(colores["grafica_rejilla"])
        eje.grid(True, axis="y", color=colores["grafica_rejilla"], alpha=0.7, linewidth=0.8)
        eje.set_axisbelow(True)
        leyenda = eje.legend(
            loc="upper left",
            frameon=False,
            fontsize=8.5,
            ncols=2,
        )
        if leyenda:
            for texto in leyenda.get_texts():
                texto.set_color(colores["texto_secundario"])
        eje.yaxis.set_major_formatter(FuncFormatter(lambda valor, _: numero_ui(valor)))
        figura.tight_layout()
        return etiquetas

    def _abrir_popup_serie(self) -> None:
        if self.controlador.serie_actual is None:
            self._aviso("Ejecute primero un análisis para ver la serie histórica.", nivel="advertencia")
            return
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Serie histórica")
        dialogo.setModal(True)
        dialogo.resize(520, 560)
        dialogo.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialogo)
        etiqueta = QLabel(self._texto_ruta_popup())
        etiqueta.setWordWrap(True)
        tabla = QTableView()
        tabla.setModel(self.modelo_serie)
        tabla.setAlternatingRowColors(True)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(dialogo.accept)
        layout.addWidget(etiqueta)
        layout.addWidget(tabla, 1)
        layout.addWidget(boton_cerrar, 0, Qt.AlignmentFlag.AlignRight)
        dialogo.exec()

    def _abrir_popup_fila(self) -> None:
        if self.controlador.fila_actual is None:
            self._aviso("Ejecute primero un análisis para ver la fila fuente.", nivel="advertencia")
            return
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Fila fuente del anexo ICOCIV")
        dialogo.setModal(True)
        dialogo.resize(760, 480)
        dialogo.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialogo)
        etiqueta = QLabel(self._texto_ruta_popup())
        etiqueta.setWordWrap(True)
        tabla = QTableView()
        tabla.setModel(self.modelo_fila)
        tabla.setAlternatingRowColors(True)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.clicked.connect(dialogo.accept)
        layout.addWidget(etiqueta)
        layout.addWidget(tabla, 1)
        layout.addWidget(boton_cerrar, 0, Qt.AlignmentFlag.AlignRight)
        dialogo.exec()

    def _ver_grafica_analisis(self, identificador: str) -> None:
        """Fase 4I-A V4: «Ver gráfica de la proyección» desde los historiales ICOCIV.

        Reutiliza el visor y el dibujo de Resultados con el resultado GUARDADO de ese
        ``analisis_id`` (snapshot de la sesión): no ejecuta el motor, no relee el Excel DANE,
        no crea registros ni toca la calculadora, la consulta o el análisis activo.
        """
        analisis = next((a for a in self.widget_proyecciones.historial if a["id"] == identificador), None)
        if analisis is None:
            self._aviso("La proyección seleccionada ya no está en la sesión.", nivel="advertencia")
            return
        try:
            resultado = recuperar_resultado(analisis["resultado"])
            resultado["serie_df"], resultado["proyeccion"]  # noqa: B018 - datos mínimos de la gráfica
        except (KeyError, TypeError, ValueError):
            self._aviso("Gráfica no disponible para este registro.", "La sesión no conserva la serie o la proyección guardadas.", nivel="advertencia")
            return
        nombre = analisis["nombre"]
        consulta = analisis.get("consulta_horizonte")
        if consulta:
            # Fase 4I-N: se dibuja la fecha APLICADA a este análisis (primeros H puntos de su trayectoria
            # guardada), no la tabla congelada de la ejecución original. Copia transitoria; sin motor.
            try:
                vigente = fo.consultar(analisis, consulta["periodo"])
                resultado["proyeccion"] = fo.proyeccion_consultada(resultado["proyeccion"], vigente)
            except (KeyError, TypeError, ValueError) as error:
                self._aviso("Gráfica no disponible para la fecha aplicada.", f"«{nombre}»: {error}.", nivel="advertencia")
                return
            nombre = fo.nombre_vigente(analisis)  # Fase 4I-P: mismo rótulo que historial y Resultados
        # Fase 4I-B: el visor se abre SOBRE Proyecciones ICOCIV; nunca cambia de sección ni de scroll.
        self._abrir_popup_grafica(resultado, nombre + "\n" + self._texto_ruta_popup(resultado))

    def _abrir_popup_grafica(self, resultado=None, subtitulo=None) -> None:
        if not resultado and subtitulo is None and self.resultado_ui_actual:
            # Fase 4I-P: el botón de Resultados abre la consulta vigente del análisis mostrado, con su rótulo.
            resultado = self._resultado_visible()
            analisis = next((a for a in self.widget_proyecciones.historial if a["id"] == self._analisis_resultados_id), None)
            if analisis is not None:
                subtitulo = fo.nombre_vigente(analisis) + "\n" + self._texto_ruta_popup()
        resultado = resultado or self.resultado_ui_actual
        if not resultado:
            self._aviso("Ejecute primero un análisis para ver la gráfica.", nivel="advertencia")
            return
        # La figura se construye una sola vez; el visor sólo cambia límites de
        # ejes al hacer zoom o desplazar, nunca recalcula la proyección.
        figura = Figure(figsize=(6, 4), dpi=100, facecolor=paleta_tema(self.tema_actual)["grafica"])
        self._dibujar_grafica(figura, resultado["serie_df"], resultado["proyeccion"])
        visor = VisorGraficaDialog(
            self,
            figura,
            "Gráfica de serie y proyección",
            hoja_estilo=self.styleSheet(),
            subtitulo=subtitulo if subtitulo is not None else self._texto_ruta_popup(),
        )
        visor.canvas.setMinimumSize(GRAFICA_MIN_WIDTH, GRAFICA_MIN_HEIGHT)
        visor.exec()

    def _texto_ruta_popup(self, resultado=None) -> str:
        resultado = resultado or self.resultado_ui_actual
        if not resultado:
            return ""
        ruta = resultado.get("ruta_jerarquica") or []
        ruta_sin_tabla = [item for item in ruta if item.get("nivel") != "Tabla ICOCIV"]
        tabla = resultado.get("fuente_visible", "")
        detalle = " · ".join(item.get("valor", "") for item in ruta_sin_tabla)
        return f"Tabla ICOCIV: {tabla}\nRuta: {detalle}" if detalle else f"Tabla ICOCIV: {tabla}"

    def _solicitar_usuario(self) -> str:
        usuario, ok = QInputDialog.getText(
            self,
            "Nombre de usuario",
            "Ingrese el nombre de usuario:",
            text=self.usuario_actual,
        )
        if not ok:
            return ""
        self.usuario_actual = usuario.strip()
        if not self.usuario_actual:
            QMessageBox.warning(self, "Trazabilidad", "Debe indicar un nombre de usuario.")
            return ""
        return self.usuario_actual

    def _actualizar_controles_habilitados(self, habilitado: bool) -> None:
        for widget in (
            self.combo_grupo, self.chk_t16, self.boton_ejecutar,
            self.boton_guardar_sesion, self.boton_exportar_informe,
            self.combo_horizonte, self.spin_horizonte_personalizado,
        ):
            widget.setEnabled(habilitado)
        self._actualizar_edicion_horizonte()

    def _actualizar_edicion_horizonte(self) -> None:
        self.spin_horizonte_personalizado.setEnabled(
            self.combo_horizonte.isEnabled()
            and self.controlador.archivo_cargado
            and self.combo_grupo.currentData() is not None
            and not (self.trabajador is not None and self.trabajador.isRunning())
        )

    def _establecer_ocupado(self, ocupado: bool, mensaje: str | None = None, exito: bool = True) -> None:
        self.boton_cargar.setEnabled(not ocupado)
        self.boton_ejecutar.setEnabled(not ocupado and self.controlador.archivo_cargado)
        self.boton_guardar_sesion.setEnabled(not ocupado and (self.controlador.archivo_cargado or bool(self.widget_proyecciones.historial) or bool(self.widget_empalme.calculos or self.widget_empalme.historial_empalme)))
        self.boton_exportar_informe.setEnabled(not ocupado and self.controlador.archivo_cargado)
        self.navegacion.setEnabled(not ocupado)
        self.selector_resultados_icociv.setEnabled(not ocupado)
        self.widget_proyecciones.selector_analisis.setEnabled(not ocupado)
        self.widget_proyecciones.selector_analisis_valores.setEnabled(not ocupado)
        self.widget_empalme.selector_analisis_empalme.setEnabled(not ocupado)
        self.selector_resultados_empalme.setEnabled(not ocupado)
        parametros_habilitados = not ocupado
        for widget in (self.spin_anio, self.spin_mes, self.combo_horizonte, self.spin_horizonte_personalizado, *self.botones_periodo):
            widget.setEnabled(parametros_habilitados)
        self._actualizar_edicion_horizonte()
        if mensaje:
            self.etiqueta_estado.setText(mensaje)
        # El trabajo ya corría en un hilo; ahora además se ve que corre.
        velo = getattr(self, "velo_carga", None)
        if velo is not None:
            if ocupado:
                velo.mostrar(mensaje or "Procesando…", "La aplicación sigue respondiendo.")
            else:
                # Fase 4I-B: 100 % visual solo con éxito real; ante error se retira sin completar.
                velo.ocultar(exito=exito)
        # El velo cubre todo `cuerpo` -incluida la esquina de las alertas- y se
        # eleva sobre sus hermanos al mostrarse (VeloCarga.mostrar hace
        # self.raise_()). Sin este reordenamiento, una alerta que ya estuviera
        # visible antes de esa elevación queda detrás del velo durante el
        # desvanecimiento de salida (que no bloquea clics, a diferencia de la
        # ocultación real) y su botón de cierre deja de recibir clics hasta
        # que el usuario interactúa con algo más. `reposicionar()` reutiliza
        # la misma lógica de `_reubicar()` para volver a elevar cada alerta
        # activa por encima de lo que haya quedado delante de ellas.
        notificaciones = getattr(self, "notificaciones", None)
        if notificaciones is not None:
            notificaciones.reposicionar()

    # Prefijos técnicos que no aportan nada al usuario y sí ruido al mensaje.
    _RUIDO_ERROR = ("Traceback", "Exception:", "ValueError:", "RuntimeError:", "KeyError:")

    def _mensaje_comprensible(self, mensaje: str) -> str:
        """Convierte un error técnico en una frase útil, sin perder el detalle."""
        texto = str(mensaje).strip()
        minusculas = texto.lower()
        if "no hay suficientes datos" in minusculas or "mínimo 8" in minusculas:
            return "La serie seleccionada no tiene observaciones suficientes para analizarse."
        if "posterior al último periodo" in minusculas:
            return "El periodo solicitado debe ser posterior al último dato publicado."
        if "permission" in minusculas or "denied" in minusculas or "being used" in minusculas:
            return "No se pudo escribir el archivo: ciérrelo si está abierto en otra aplicación."
        if "no such file" in minusculas or "no existe" in minusculas:
            return "No se encontró el archivo indicado."
        primera_linea = texto.splitlines()[0] if texto else "Error desconocido."
        if any(primera_linea.startswith(p) for p in self._RUIDO_ERROR):
            return "La operación no pudo completarse."
        return primera_linea

    def _mostrar_error(self, mensaje: str) -> None:
        self._restaurando_registros_icociv = False
        self._establecer_ocupado(False, exito=False)
        self.etiqueta_estado.setText("Ocurrió un error.")
        gestor = getattr(self, "notificaciones", None)
        if gestor is None:
            QMessageBox.critical(self, "Error", mensaje)
            return
        # Texto comprensible a la vista, detalle técnico disponible en el aviso.
        gestor.error(self._mensaje_comprensible(mensaje), str(mensaje))

    def _mostrar_acerca_de(self) -> None:
        """Muestra versión, entorno y ubicaciones de trabajo de la aplicación."""
        dialogo = QMessageBox(self)
        dialogo.setWindowTitle("Acerca de SAVIP")
        dialogo.setTextFormat(Qt.TextFormat.RichText)
        dialogo.setText(
            "<b>SAVIP — Sistema de Análisis de Variaciones de Precios</b><br><br>"
            f"Versión: <b>v{VERSION}</b><br>"
            f"Modo: {'ejecutable empaquetado' if es_ejecutable_congelado() else 'código fuente'}<br><br>"
            f"Reportes y exportables:<br><code>{CARPETA_REPORTES}</code><br><br>"
            f"Registros de ejecución:<br><code>{carpeta_logs()}</code><br><br>"
            "Apoyo al análisis de variaciones de precios en contratos de obra civil. "
            "Analiza índices oficiales ICOCIV del DANE y emplea información ICCP cuando "
            "corresponde. Los resultados son estimaciones estadísticas y no reemplazan la "
            "producción oficial del DANE ni el criterio del profesional responsable."
        )
        icono = _pixmap_logo(96)
        if icono is not None:
            dialogo.setIconPixmap(icono)
        dialogo.exec()

    def _abrir_carpeta_logs(self) -> None:
        """Abre la carpeta de registros en el explorador del sistema."""
        carpeta = asegurar_carpeta(carpeta_logs())
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(carpeta)))

    def _cargar_estilos(self) -> None:
        """Compone la hoja del tema activo desde los tokens del sistema visual."""
        self.setStyleSheet(hoja_estilos(self.tema_actual))
        # Paleta de la aplicación coherente con el tema: evita que los popups de
        # QComboBox, tooltips y vistas sin regla QSS hereden la paleta oscura del
        # sistema Windows en modo claro (texto oscuro sobre fondo oscuro).
        from PySide6.QtGui import QColor, QPalette
        from PySide6.QtWidgets import QApplication
        c = paleta_tema(self.tema_actual);p = QPalette()
        for rol, clave in ((QPalette.Window, "fondo"), (QPalette.WindowText, "texto"), (QPalette.Base, "campo"),
                           (QPalette.AlternateBase, "superficie_2"), (QPalette.Text, "texto"), (QPalette.Button, "superficie"),
                           (QPalette.ButtonText, "texto"), (QPalette.Highlight, "seleccion"), (QPalette.HighlightedText, "texto"),
                           (QPalette.ToolTipBase, "tooltip_fondo"), (QPalette.ToolTipText, "tooltip_texto"),
                           (QPalette.PlaceholderText, "texto_terciario"), (QPalette.BrightText, "texto")):
            p.setColor(rol, QColor(c[clave]))
        for rol in (QPalette.WindowText, QPalette.Text, QPalette.ButtonText):
            p.setColor(QPalette.Disabled, rol, QColor(c["texto_deshabilitado"]))
        QApplication.setPalette(p)
        # Qt reutiliza una única etiqueta de tooltip (QTipLabel) que no se repule al cambiar el tema:
        # se cierra, se le da la paleta nueva y se repule para que la siguiente ayuda use el tema vigente.
        from PySide6.QtWidgets import QToolTip
        QToolTip.hideText();QToolTip.setPalette(p)
        for etiqueta in QApplication.topLevelWidgets():
            if etiqueta.metaObject().className() == "QTipLabel":
                etiqueta.setPalette(p);etiqueta.style().unpolish(etiqueta);etiqueta.style().polish(etiqueta)

    def resizeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Las superposiciones no participan del layout: se recolocan a mano."""
        super().resizeEvent(event)
        if hasattr(self, "velo_carga"):
            self.velo_carga.reposicionar()
        if hasattr(self, "notificaciones"):
            self.notificaciones.reposicionar()
        if hasattr(self, "_temporizador_ancho"):
            self._temporizador_ancho.start()  # un solo ajuste tras la ráfaga de redimensionado

    def _adaptar_ancho(self) -> None:
        """Modo compacto con histéresis (entra < ANCHO_COMPACTO, sale > ANCHO_AMPLIO).

        No recrea widgets ni toca datos: contrae la navegación existente (si el usuario no la había
        contraído él mismo) y activa el ajuste de línea de los rótulos largos; al ampliar, lo revierte.
        """
        if not hasattr(self, "navegacion"):
            return
        ancho = self.width()
        if not self._modo_compacto and ancho < ANCHO_COMPACTO:
            self._modo_compacto = True
            if not self.navegacion.esta_contraida():
                self._navegacion_auto = True
                self.navegacion.establecer_contraccion(True)
            for etiqueta in self.tabs_principales.findChildren(QLabel):
                if not etiqueta.wordWrap() and len(etiqueta.text()) > 30:
                    etiqueta.setWordWrap(True);self._rotulos_ajustados.append(etiqueta)
            self.widget_proyecciones.modo_compacto = True;self.widget_proyecciones._ajustar_distribucion()
            self._actualizar_texto_toggle_tema()
        elif self._modo_compacto and ancho > ANCHO_AMPLIO:
            self._modo_compacto = False
            if self._navegacion_auto and self.navegacion.esta_contraida():
                self.navegacion.establecer_contraccion(False)
            self._navegacion_auto = False
            for etiqueta in self._rotulos_ajustados:
                try:
                    etiqueta.setWordWrap(False)
                except RuntimeError:  # rótulo ya destruido
                    pass
            self._rotulos_ajustados = []
            self.widget_proyecciones.modo_compacto = False;self.widget_proyecciones._ajustar_distribucion()
            self._actualizar_texto_toggle_tema()

    def closeEvent(self, event) -> None:  # noqa: N802 - firma Qt
        """Detiene el movimiento en curso para no repintar widgets destruidos.

        Fase 4I-G: al cerrar con la X (evento del sistema) con cambios sin guardar, se ofrece la misma
        decisión que «Cerrar sesión»; un close() programático no pregunta. Durante una apertura o un
        guardado en curso no se cierra.
        """
        if event.spontaneous():
            if self._operacion_sesion is not None:
                event.ignore();return
            if self._hay_trabajo() and self._firma_trabajo() != self._firma_guardada:
                decision = self._decidir_cierre("Cerrar SAVIP", "Hay cambios sin guardar en la sesión actual.")
                if decision == "cancelar" or (decision == "guardar" and not self.guardar_sesion_actual()):
                    event.ignore();return
        detener_todas()
        super().closeEvent(event)

    def _aviso(self, titulo: str, detalle: str = "", nivel: str = "informacion") -> None:
        """Aviso no modal; recurre al diálogo solo si aún no hay gestor."""
        gestor = getattr(self, "notificaciones", None)
        if gestor is None:
            QMessageBox.information(self, "SAVIP", f"{titulo}\n\n{detalle}".strip())
            return
        gestor.mostrar(titulo, detalle, nivel)

    def _aplicar_tema(self, tema: str, persistir: bool = True) -> None:
        self.tema_actual = normalizar_tema(tema)
        if hasattr(self, "accion_modo_oscuro"):
            self.accion_modo_oscuro.blockSignals(True)
            self.accion_modo_oscuro.setChecked(self.tema_actual == "oscuro")
            self.accion_modo_oscuro.blockSignals(False)
        if hasattr(self, "boton_tema_toggle"):
            self.boton_tema_toggle.blockSignals(True)
            self.boton_tema_toggle.setChecked(self.tema_actual == "oscuro")
            self.boton_tema_toggle.blockSignals(False)
            self._actualizar_texto_toggle_tema()
        self._cargar_estilos()
        # Las sombras llevan el color del tema y los componentes propios tienen
        # su propio estado visual: hay que repintarlos, no solo recargar la hoja.
        self._elevar_superficies()
        for atributo in ("pantalla_inicio", "velo_carga", "notificaciones"):
            componente = getattr(self, atributo, None)
            if componente is not None:
                componente.actualizar_tema(self.tema_actual)
        preparar_ventana(self, self.tema_actual)
        if persistir:
            self.preferencias.setValue("tema", self.tema_actual)
            self.preferencias.sync()
        self._renderizar_resultados_actuales()

    def _renderizar_resultados_actuales(self) -> None:
        if not self.resultado_ui_actual:
            return
        self.texto_resultados.setHtml(
            construir_html_resultados(self._resultado_visible(), self.tema_actual)
        )

    def _crear_dialogo_explicacion(self, titulo: str, html: str) -> QDialog:
        dialogo = QDialog(self)
        dialogo.setObjectName("dialogo_explicacion")
        dialogo.setWindowTitle(titulo)
        dialogo.setModal(True)
        dialogo.resize(760, 640)
        dialogo.setMinimumSize(620, 460)
        dialogo.setStyleSheet(self.styleSheet())
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(14, 14, 14, 14)
        visor = QTextBrowser(dialogo)
        visor.setObjectName("visor_explicacion")
        visor.setOpenExternalLinks(False)
        visor.setHtml(html)
        boton_cerrar = QPushButton("Cerrar", dialogo)
        boton_cerrar.setObjectName("boton_cerrar_dialogo")
        boton_cerrar.clicked.connect(dialogo.accept)
        layout.addWidget(visor, 1)
        layout.addWidget(boton_cerrar, 0, Qt.AlignmentFlag.AlignRight)
        dialogo.visor_explicacion = visor
        dialogo.boton_cerrar = boton_cerrar
        return dialogo

    def _mostrar_modal_explicacion(self, titulo: str, html: str) -> None:
        self._crear_dialogo_explicacion(titulo, html).exec()

    def _mostrar_explicacion_tarjeta(self, clave: str) -> None:
        titulos = {
            "indice": "Índice proyectado",
            "horizonte": "Horizonte solicitado",
            "modelo": "Selección del modelo",
            "estado": "Estado del horizonte",
            "error_historico": "Error histórico de referencia",
            "maximo": "Alcance máximo de proyección",
        }
        html = construir_html_explicacion_tarjeta(
            clave,
            self._resultado_visible(),
            self.tema_actual,
        )
        self._mostrar_modal_explicacion(titulos.get(clave, "Información del resultado"), html)

    def _mostrar_detalle_horizonte(self, enlace) -> None:
        texto = enlace.toString()
        if not texto.startswith("detalle-horizonte:"):
            return
        try:
            horizonte = int(texto.rsplit(":", 1)[-1])
        except ValueError:
            return
        evaluacion = self.detalles_horizonte.get(horizonte)
        if evaluacion is None:
            return
        self.horizonte_detalle_actual = horizonte
        self._mostrar_modal_explicacion(
            f"Detalle del horizonte h={horizonte}",
            construir_html_detalle_horizonte(evaluacion, self.tema_actual),
        )


def ejecutar_aplicacion() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SAVIP")
    app.setApplicationDisplayName(TITULO_APLICACION)
    app.setApplicationVersion(VERSION)
    _icono = icono_savip()
    if _icono is not None:
        app.setWindowIcon(_icono)
    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(ejecutar_aplicacion())
