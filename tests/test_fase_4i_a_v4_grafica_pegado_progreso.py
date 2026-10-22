"""Fase 4I-A V4: «Ver gráfica de la proyección», convenio de pegado, botones compactos y progreso.

Pruebas focalizadas con Qt real (offscreen); el motor estadístico queda bloqueado en todas.
"""
import json
import os
from copy import deepcopy
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from tests.test_slider_comparacion_historica_fase_4d import APP, cargar, reales
from tests.test_proyecciones_redisenio_visual import ventana_de_prueba
from tests.test_fase_4i_tabla_editable import _widget_con_actividades
from app_icociv.interfaz.widgets.numerico_icociv import normalizar_numero
from app_icociv.persistencia.historial_icociv import recuperar_resultado, serializar_resultado

from app_icociv.interfaz.widgets.visor_grafica import VisorGraficaDialog


class _VisorSinBloqueo(VisorGraficaDialog):
    """Mismo visor de Resultados; solo evita el bucle modal en offscreen (un mock de exec rompe Shiboken)."""
    def exec(self):
        return 0


MOTOR = "app_icociv.interfaz.controladores.controlador_principal.ControladorPrincipal.ejecutar_analisis"
MATRIZ = {"1250": 1250, "1,250": 1250, "4,559": 4559, "1.250": 1.25, "12.5": 12.5, "12,5": 12.5, "1,250.75": 1250.75,
          "6,561,232.00": 6561232, "$ 6,561,232.00": 6561232, "1.250,75": 1250.75, "1.250.000": 1250000,
          "1,250,000": 1250000, "1.250.000,50": 1250000.5, "1,250,000.50": 1250000.5, "0.250": 0.25, "1 250 000": 1250000,
          "0,250": 0.25, "1,25": 1.25, "0,25": 0.25, "COP 4,559": 4559}


def _pegar(editor, texto):
    APP.clipboard().setText(texto)
    QTest.keyClick(editor, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    APP.processEvents()


# ---------------------------------------------------------------- pegado
def test_A_matriz_de_pegado_del_convenio_v4():
    assert {t: float(normalizar_numero(t)) for t in MATRIZ} == MATRIZ
    for malo in ("12 a", "1e6", "1\t2", "1\n2", "4,559 5", "=1+1", "inf", "1.25,50", "$$"):
        try:
            normalizar_numero(malo)
        except ValueError:
            pass
        else:
            raise AssertionError(malo)


def test_B_ctrl_v_real_en_P_A_cantidad_y_celda():
    w = _widget_con_actividades(2); w.show(); w.activateWindow(); APP.processEvents()
    try:
        valores = deepcopy(w.valores)
        for control in (w.precio_base, w.anticipo, w.cantidad):
            for texto, esperado in (("1,250", 1250), ("1.250", 1.25), ("$ 6,561,232.00", 6561232), ("1.250.000,50", 1250000.5)):
                if control is w.cantidad and esperado > 1e9:
                    continue
                control.setFocus(); control.selectAll(); _pegar(control.lineEdit(), texto)
                assert control.value() == esperado, (control.accessibleName(), texto, control.value())
        w.cantidad.setValue(3); w.cantidad.selectAll(); _pegar(w.cantidad.lineEdit(), "12 a")  # inválido: sin cambio
        assert w.cantidad.value() == 3 and w.valores == valores and w.pila_deshacer.count() == 0
        m = w.modelo_valores; t = w.tabla_valores
        for clave, texto, campo, esperado in (("precio_base", "$ 6,561,232.00", "precio_base", 6561232),
                                              ("cantidad", "1.250", "cantidad", 1.25), ("cantidad", "1,250", "cantidad", 1250)):
            index = m.index(0, m.claves.index(clave)); t.setCurrentIndex(index); t.edit(index); APP.processEvents()
            editor = APP.focusWidget(); assert isinstance(editor, QLineEdit)
            editor.selectAll(); _pegar(editor, texto); QTest.keyClick(editor, Qt.Key.Key_Return); APP.processEvents()
            assert w.valores[0][campo] == esperado
        assert w.pila_deshacer.count() == 3  # cada edición confirmada es deshacible
    finally:
        w.close()


# ---------------------------------------------------------------- botones compactos y resaltado
def test_C_deshacer_rehacer_compactos_y_resaltado():
    w = _widget_con_actividades(3); w.show(); APP.processEvents()
    try:
        for boton in (w.boton_deshacer, w.boton_rehacer, w.boton_grafica_superior, w.boton_grafica_inferior):
            assert boton.objectName() == "boton_compacto"
        ids = [r["calculo_id"] for r in w.valores]
        w.tabla_valores.verticalHeader().moveSection(2, 0); APP.processEvents()
        assert w._resaltado_id == ids[2] and w.boton_deshacer.isEnabled()
        w.boton_deshacer.click(); assert [r["calculo_id"] for r in w.valores] == ids and w._resaltado_id == ids[2]
    finally:
        w.close()


# ---------------------------------------------------------------- gráfica
def _ventana(datos=None):
    v = ventana_de_prueba(); v.show()
    if datos is None:
        w = cargar(v)
    else:
        v.sesion_pendiente = {"proyecciones_icociv": datos}; v._restaurar_sesion_pendiente(); w = v.widget_proyecciones
    APP.processEvents()
    return v, w


def _estado(w):
    return json.dumps(w._datos_calculadora(), sort_keys=True, default=str), deepcopy(w.valores), len(w.historial)


def test_D_ver_grafica_abre_el_analisis_exacto_sin_recalcular():
    v, w = _ventana()
    dibujos = []
    original = v._dibujar_grafica
    def espia(figura, serie, proyeccion):
        dibujos.append((serie, proyeccion));return original(figura, serie, proyeccion)
    try:
        with patch(MOTOR, side_effect=AssertionError("motor")), \
             patch("app_icociv.interfaz.ventana_principal.VisorGraficaDialog", _VisorSinBloqueo), \
             patch.object(v, "_dibujar_grafica", side_effect=espia):
            # «Todas las proyecciones»: ningún análisis arbitrario.
            w.selector_analisis_valores.setCurrentIndex(0); APP.processEvents()
            assert not w.boton_grafica_superior.isEnabled() and not w.boton_grafica_inferior.isEnabled()
            assert "Selecciona una proyección" in w.boton_grafica_superior.toolTip()
            w.item.setText("Borrador intacto"); w._item_editado = True; w.cantidad.setValue(7); w.precio_base.setValue(123.45)
            # Revisión 1 desde el historial SUPERIOR.
            id1 = w.selector_analisis_valores.itemData(1)
            w.selector_analisis_valores.setCurrentIndex(1); APP.processEvents()
            antes = _estado(w); consulta = (w._ambito_consulta, w._proyeccion_consulta, w.analisis_activo_id)
            seccion = v.tabs_principales.currentIndex()
            w.boton_grafica_superior.click(); APP.processEvents()
            esperado = recuperar_resultado(next(a for a in w.historial if a["id"] == id1)["resultado"])
            assert len(dibujos) == 1 and dibujos[0][0].equals(esperado["serie_df"])
            assert dibujos[0][1]["resultado_horizonte_solicitado"] == esperado["proyeccion"]["resultado_horizonte_solicitado"]
            assert v.tabs_principales.currentIndex() == seccion  # Fase 4I-B: no sale de Proyecciones
            assert _estado(w) == antes and (w._ambito_consulta, w._proyeccion_consulta, w.analisis_activo_id) == consulta
            # Revisión 2 desde el historial INFERIOR: ambos selectores sincronizados y otra gráfica.
            id2 = w.selector_proyeccion_inferior.itemData(2)
            w.selector_proyeccion_inferior.setCurrentIndex(2); APP.processEvents()
            assert w.selector_analisis_valores.currentData() == id2 != id1
            w.boton_grafica_inferior.click(); APP.processEvents()
            esperado2 = recuperar_resultado(next(a for a in w.historial if a["id"] == id2)["resultado"])
            assert len(dibujos) == 2 and dibujos[1][0].equals(esperado2["serie_df"])
            assert dibujos[1][1]["resultado_horizonte_solicitado"] == esperado2["proyeccion"]["resultado_horizonte_solicitado"]
            assert dibujos[1][1]["resultado_horizonte_solicitado"] != dibujos[0][1]["resultado_horizonte_solicitado"]
            # Superior e inferior producen lo mismo para la misma proyección.
            w.boton_grafica_superior.click(); APP.processEvents()
            assert dibujos[2][0].equals(dibujos[1][0])
            # Análisis no activo: se muestra su gráfica sin cambiar el análisis activo.
            activo = w.analisis_activo_id; otro = next(a["id"] for a in w.historial if a["id"] != activo)
            w.grafica_solicitada.emit(otro); APP.processEvents()
            assert w.analisis_activo_id == activo and len(dibujos) == 4
            # Proyección ya inexistente: aviso, ninguna gráfica inventada.
            w.grafica_solicitada.emit("no-existe"); APP.processEvents(); assert len(dibujos) == 4
            assert _estado(w)[1] == antes[1] and len(w.historial) == antes[2]
    finally:
        v.close()


def test_E_homonimos_legado_sin_grafica_y_sesion_vacia():
    datos = reales()
    base = datos["historial_analisis"][2]
    gemelo = deepcopy(base); gemelo["id"] = "gemelo_homonimo"  # mismo rótulo, otra identidad y otros datos
    resultado = recuperar_resultado(gemelo["resultado"]); resultado["serie_df"] = resultado["serie_df"].assign(
        **{resultado["serie_df"].columns[-1]: resultado["serie_df"].iloc[:, -1] * 2})
    gemelo["resultado"] = serializar_resultado(resultado)
    from app_icociv.interfaz.widgets.proyecciones_icociv import _extraer_contexto
    gemelo["contexto"] = _extraer_contexto(resultado); gemelo["registros_ids"] = []
    datos["historial_analisis"].append(gemelo)
    v, w = _ventana(datos)
    # Registro heredado sin serie guardada (la validación de sesión lo rechaza al abrir; se inyecta en memoria).
    legado = deepcopy(w.historial[0]); legado["id"] = "legado_sin_grafica"; legado["resultado"].pop("serie_df")
    w.historial.append(legado); w._fichas = []; w._refrescar_historial()
    dibujos = []
    try:
        with patch(MOTOR, side_effect=AssertionError("motor")), \
             patch("app_icociv.interfaz.ventana_principal.VisorGraficaDialog", _VisorSinBloqueo), \
             patch.object(v, "_dibujar_grafica", side_effect=lambda f, s, p: dibujos.append(s)):
            for identificador in (base["id"], "gemelo_homonimo"):
                w.selector_proyeccion_inferior.setCurrentIndex(w.selector_proyeccion_inferior.findData(identificador)); APP.processEvents()
                assert w.boton_grafica_inferior.isEnabled(); w.boton_grafica_inferior.click(); APP.processEvents()
            assert len(dibujos) == 2 and not dibujos[0].equals(dibujos[1])  # cada homónimo, su propia serie
            w.selector_analisis_valores.setCurrentIndex(w.selector_analisis_valores.findData("legado_sin_grafica")); APP.processEvents()
            assert not w.boton_grafica_superior.isEnabled() and "no disponible" in w.boton_grafica_superior.toolTip()
        from app_icociv.interfaz.widgets.proyecciones_icociv import WidgetProyeccionesICOCIV
        vacio = WidgetProyeccionesICOCIV()  # sesión sin análisis guardados
        assert not vacio.boton_grafica_superior.isEnabled() and "No hay proyecciones" in vacio.boton_grafica_inferior.toolTip()
        vacio.close()
    finally:
        v.close()


# ---------------------------------------------------------------- progreso
def test_F_velo_veraz_sin_destello_y_con_tiempo_transcurrido():
    from app_icociv.interfaz.componentes import VeloCarga
    from app_icociv.interfaz.animaciones.transiciones import establecer_movimiento_reducido
    from PySide6.QtWidgets import QWidget
    establecer_movimiento_reducido(False)
    base = QWidget(); base.resize(400, 300); base.show()
    velo = VeloCarga(base)
    velo.mostrar("Leyendo datos…", "La aplicación sigue respondiendo.")
    assert velo.isVisible() and velo.barra.accessibleName() == "Progreso visual estimado"  # bloquea clics
    efecto = velo.graphicsEffect(); assert efecto is not None and efecto.opacity() == 0.0  # aún imperceptible
    # Fase 4I-B: barra determinada de progreso VISUAL estimado (rotulada), no indeterminada.
    velo.ocultar(); QTest.qWait(250); assert not velo.isVisible()  # tarea breve: no hubo destello
    velo.mostrar("Evaluando modelos…"); QTest.qWait(3300)
    assert "Completado" not in velo.etiqueta.text() and velo.barra.value() < velo.barra.maximum()  # Fase 4I-C: sin textos accesorios
    velo.ocultar(); QTest.qWait(250); assert not velo.isVisible() and not velo._animacion.isActive()
    base.close()


def test_G_exportacion_muestra_estado_y_lo_retira_tambien_si_falla(tmp_path):
    w = _widget_con_actividades(1); w.show()
    vistos = []
    try:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        def generar(ruta, *a, **k):
            vistos.append((w.aviso_tabla.isVisible(), w.aviso_tabla.text()));raise PermissionError("bloqueado")
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(tmp_path / "x.xlsx"), "")), \
             patch.object(w, "_generar_excel", side_effect=generar), patch.object(QMessageBox, "critical") as error, \
             patch.object(QMessageBox, "information") as ok:
            w._exportar_excel()
        assert vistos and vistos[0][0] and "Preparando exportación" in vistos[0][1]
        assert error.called and not ok.called and not w.aviso_tabla.isVisible() and QApplication.overrideCursor() is None
    finally:
        w.close()
