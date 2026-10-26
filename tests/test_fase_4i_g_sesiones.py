"""Fase 4I-G: velo al abrir sesiones, «Cerrar sesión» con tres salidas, Ctrl+S y «Guardar como…»."""

import json
import os
import time
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QFontDatabase, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QLabel, QMessageBox, QPushButton

from tests.test_slider_comparacion_historica_fase_4d import APP, reales
from tests.test_switch_tema_sesion_dane import MOTOR, _ventana_con_dane
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.persistencia import gestor_sesiones
from tests.fixtures.salidas import carpeta_salida

CAPTURAS = carpeta_salida("fase_4i_g_capturas")  # Fase 1A (AS-007): antes en docs/, no publicado
for _fuente in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"):  # capturas legibles (offscreen)
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / _fuente))
CLAVES_REFERENCIA = ("i0_icociv", "i_icociv", "periodo_base", "periodo_proyectado", "factor_icociv", "diferencia_porcentual",
                     "valor_proyectado", "criterio_factor", "numero_fila", "item", "calculo_id", "analisis_id")


def _escribir(ruta, **extra):
    datos = {"usuario": "QA", "archivo_excel": "C:/no/existe/anexo.xlsx", "proyecciones_icociv": reales(), **extra}
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def _esperar(v):
    while v._operacion_sesion:
        APP.processEvents()


def _abrir(v, ruta, decision="descartar"):
    with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")) as dialogo, \
         patch.object(v, "_decidir_cierre", return_value=decision) as decidir, \
         patch.object(QMessageBox, "warning") as aviso, patch(MOTOR, side_effect=AssertionError("motor")), \
         patch.object(VentanaPrincipal, "_cargar_archivo", side_effect=AssertionError("no se abre el Excel de la sesión")):
        v.abrir_sesion(); _esperar(v)
    return dialogo, decidir, aviso


def _guardar(v, destino="", como=False, atajo=False):
    """Guarda por el botón/menú (o Ctrl+S real si ``atajo``); devuelve (resultado, diálogo de ruta)."""
    with patch.object(v, "_solicitar_usuario", return_value="QA"), \
         patch.object(QFileDialog, "getSaveFileName", return_value=(str(destino), "")) as dialogo:
        if atajo:
            v.activateWindow(); v.widget_proyecciones.tabla_valores.setFocus(); APP.processEvents()
            QTest.keyClick(v.widget_proyecciones.tabla_valores, Qt.Key.Key_S,
                           Qt.KeyboardModifier.ControlModifier | (Qt.KeyboardModifier.ShiftModifier if como else Qt.KeyboardModifier.NoModifier))
            APP.processEvents(); return None, dialogo
        return v.guardar_rapido(como=como), dialogo


def _referencias(v):
    w = v.widget_proyecciones
    return ([{k: r.get(k) for k in CLAVES_REFERENCIA} for r in w.valores],
            [(a["id"], a["contexto"]) for a in w.historial])


def _vacio(v):
    w, e = v.widget_proyecciones, v.widget_empalme
    return (not w.historial and not w.valores and not w.proyecciones and w.analisis_activo_id is None
            and not e.calculos and not e.historial_empalme and v.resultado_ui_actual is None
            and w.pila_deshacer.count() == 0 and not w.solo_analisis_activo.isChecked()
            and w.nombre_proyecto.text() == "" and v.ruta_sesion_actual is None
            and v.controlador.proyeccion_actual is None and not v._hay_trabajo())


def test_1_2_apertura_con_velo_errores_y_sesion_previa_intacta(tmp_path):
    ruta = tmp_path / "tres.json"; datos = _escribir(ruta)
    v = _ventana_con_dane()
    try:
        real = gestor_sesiones.cargar_sesion
        lenta = lambda r: (time.sleep(0.9), real(r))[1]  # sesión «pesada»: el velo debe verse mientras se lee
        visto, porcentajes, modos = False, set(), set()
        with patch("app_icociv.interfaz.ventana_principal.cargar_sesion", side_effect=lenta), \
             patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")) as dialogo, \
             patch(MOTOR, side_effect=AssertionError("motor")):
            v.abrir_sesion()
            v.abrir_sesion()  # doble pulsación: se ignora mientras se abre
            inicio = time.time()
            while v._operacion_sesion:
                APP.processEvents()
                efecto = v.velo_carga.graphicsEffect()
                if v.velo_carga.isVisible() and v.velo_carga.property("modo") == "esqueleto" and (efecto is None or efecto.opacity() > 0.5):
                    if not visto:
                        v.grab().save(str(CAPTURAS / f"apertura_velo_{v.tema_actual}.png"))
                    visto = True
                if v._operacion_sesion:  # aún trabajando
                    porcentajes.add(v.velo_carga.franja.porcentaje()); modos.add(v.velo_carga.property("modo"))
            assert time.time() - inicio >= 0.8
        # Fase V1.1.2-01: esqueleto de la sesión y avance indeterminado (la lectura no se puede medir):
        # ningún porcentaje inventado mientras trabaja ni un 100 % simulado al terminar.
        # Fase V1.1.2-01B: primero la franja inmediata y, pasados 0,4 s, el esqueleto; etapas reales.
        assert v.velo_carga.franja.porcentaje() is None and porcentajes == {None} and modos == {"franja", "esqueleto"}
        assert dialogo.call_count == 1 and visto
        assert v.velo_carga.etiqueta.text() == "Abriendo sesión: restaurando análisis, actividades y Empalme…"
        QTest.qWait(400); assert not v.velo_carga.isVisible() and v.navegacion.isEnabled()
        assert [a["id"] for a in v.widget_proyecciones.historial] == [a["id"] for a in datos["proyecciones_icociv"]["historial_analisis"]]
        assert v.ruta_sesion_actual == ruta and not v._operacion_sesion
        antes = (v._firma_trabajo(), _referencias(v), v.ruta_sesion_actual)
        # JSON inválido y DANE insuficiente: aviso claro, velo retirado y sesión anterior intacta.
        invalido = tmp_path / "roto.json"; invalido.write_text("{ no es json", encoding="utf-8")
        _, _, aviso = _abrir(v, invalido)
        assert "no es un archivo de sesión JSON válido" in aviso.call_args[0][2]
        futura = tmp_path / "futura.json"; _escribir(futura, corte_dane="2027-05")
        _, _, aviso = _abrir(v, futura)
        assert "fecha base 2027-05 o posterior" in aviso.call_args[0][2] and "2026-12" in aviso.call_args[0][2]
        QTest.qWait(400)
        assert (v._firma_trabajo(), _referencias(v), v.ruta_sesion_actual) == antes
        assert not v.velo_carga.isVisible() and v.navegacion.isEnabled() and v.boton_abrir_sesion.isEnabled()
        # Cancelar el selector no cambia nada.
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")):
            v.abrir_sesion()
        assert v._firma_trabajo() == antes[0] and v._operacion_sesion is None
    finally:
        v.close()


def test_3_4_5_guardar_primera_vez_rapido_y_guardar_como(tmp_path):
    v = _ventana_con_dane()
    try:
        v.sesion_pendiente = {"proyecciones_icociv": reales()}; v._restaurar_sesion_pendiente()  # trabajo en memoria, nunca guardado
        assert v._hay_trabajo() and v.ruta_sesion_actual is None
        assert v.accion_guardar_sesion.shortcut() == QKeySequence(QKeySequence.StandardKey.Save)
        assert v.accion_guardar_como.shortcut() == QKeySequence("Ctrl+Shift+S")
        primero = tmp_path / "primera.json"
        _, dialogo = _guardar(v, primero, atajo=True)  # Ctrl+S real
        assert dialogo.call_count == 1 and primero.exists() and v.ruta_sesion_actual == primero
        assert json.loads(primero.read_text(encoding="utf-8"))["corte_dane"] == "2026-12"
        assert v._firma_trabajo() == v._firma_guardada
        # Editar (reordenar actividades) y Ctrl+S: misma ruta, sin diálogo.
        w = v.widget_proyecciones
        w._registrar_cambio("reordenar", list(reversed(w.valores)), w.valores[0]["calculo_id"]); APP.processEvents()
        orden = [r["calculo_id"] for r in w.valores]
        assert v._firma_trabajo() != v._firma_guardada
        _, dialogo = _guardar(v, tmp_path / "no_debe_usarse.json", atajo=True)
        assert not dialogo.called and not (tmp_path / "no_debe_usarse.json").exists()
        guardado = json.loads(primero.read_text(encoding="utf-8"))
        assert [r["calculo_id"] for r in guardado["proyecciones_icociv"]["valores"]] == orden
        assert not list(tmp_path.glob("*.tmp")) and len(list(tmp_path.glob("*.json"))) == 1  # sin temporales
        # Guardar como: archivo distinto, ruta activa nueva y el anterior intacto.
        bytes_primero = primero.read_bytes()
        copia = tmp_path / "copia.json"
        ok, dialogo = _guardar(v, copia, como=True)
        assert ok and dialogo.call_count == 1 and copia.exists() and v.ruta_sesion_actual == copia
        assert primero.read_bytes() == bytes_primero
        # Reabrir en otra ventana reproduce datos y orden.
        otra = _ventana_con_dane()
        try:
            _abrir(otra, copia)
            assert [r["calculo_id"] for r in otra.widget_proyecciones.valores] == orden
            assert _referencias(otra) == _referencias(v)
        finally:
            otra.close()
    finally:
        v.close()


def test_6_7_8_9_cerrar_sesion_tres_salidas_y_nuevo_presupuesto(tmp_path):
    ruta = tmp_path / "sesion.json"; _escribir(ruta)
    v = _ventana_con_dane()
    try:
        _abrir(v, ruta)
        original = ruta.read_bytes()
        w = v.widget_proyecciones
        w.nombre_proyecto.setText("Proyecto en curso")
        w._registrar_cambio("reordenar", list(reversed(w.valores)), w.valores[0]["calculo_id"]); APP.processEvents()
        estado = (v._firma_trabajo(), v.ruta_sesion_actual, w.pila_deshacer.count())
        # 8) Cancelar el cierre, cancelar el «Guardar como» y fallo de permisos: nada cambia ni se cierra.
        with patch.object(v, "_decidir_cierre", return_value="cancelar"):
            assert not v.cerrar_sesion()
        v.ruta_sesion_actual = None  # sin ruta: «Guardar y cerrar» pide destino
        with patch.object(v, "_decidir_cierre", return_value="guardar"):
            assert not _guardar_cerrando(v, "")
        v.ruta_sesion_actual = ruta
        with patch.object(v, "_decidir_cierre", return_value="guardar"), \
             patch("app_icociv.interfaz.ventana_principal.guardar_sesion", side_effect=PermissionError("Acceso denegado")), \
             patch.object(QMessageBox, "warning") as aviso:
            assert not v.cerrar_sesion()
        assert "Acceso denegado" in aviso.call_args[0][2] and "siguen en memoria" in aviso.call_args[0][2]
        assert (v._firma_trabajo(), v.ruta_sesion_actual, w.pila_deshacer.count()) == estado and ruta.read_bytes() == original
        # 7) Cerrar sin guardar: el JSON en disco no se toca y al reabrir están los valores originales.
        with patch.object(v, "_decidir_cierre", return_value="descartar"):
            assert v.cerrar_sesion()
        assert ruta.read_bytes() == original and _vacio(v)
        _abrir(v, ruta)
        assert w.nombre_proyecto.text() == reales()["proyecto"]["nombre_proyecto"] and [r["calculo_id"] for r in w.valores] == [r["calculo_id"] for r in reales()["valores"]]
        # 6) Guardar y cerrar: guarda en su ruta y solo después limpia; el DANE sigue cargado.
        w.nombre_proyecto.setText("Proyecto guardado al cerrar")
        with patch.object(v, "_decidir_cierre", return_value="guardar") as decidir, \
             patch.object(QFileDialog, "getSaveFileName", side_effect=AssertionError("ya tiene ruta")):
            assert v.cerrar_sesion()
        assert decidir.call_args[0][0] == "Cerrar sesión"
        assert json.loads(ruta.read_text(encoding="utf-8"))["proyecciones_icociv"]["proyecto"]["nombre_proyecto"] == "Proyecto guardado al cerrar"
        # 9) Espacio vacío, DANE conservado y nueva proyección sin recargarlo.
        assert _vacio(v) and v._corte_dane_cargado() == "2026-12" and v.controlador.archivo_cargado
        assert v.texto_resultados.toPlainText() == QTextoInicial(v) and v.lbl_dashboard_estado.text() == "Sin análisis ejecutado"
        with patch.object(v, "_decidir_cierre", side_effect=AssertionError("sin trabajo no se pregunta")):
            assert not v.cerrar_sesion()
        with patch.object(VentanaPrincipal, "_cargar_archivo", side_effect=AssertionError("no se recarga el DANE")):
            v.combo_grupo.setCurrentIndex(1); v.ejecutar_proyeccion()
            fin = time.time() + 120
            while v.resultado_ui_actual is None and time.time() < fin:
                APP.processEvents(); QTest.qWait(50)
        assert v.resultado_ui_actual is not None and len(w.historial) == 1 and v._hay_trabajo()
    finally:
        v.close()


def QTextoInicial(v):
    doc = v.texto_resultados.document().clone(); doc.setHtml(v._resultados_iniciales[0]); return doc.toPlainText()


def _guardar_cerrando(v, destino):
    with patch.object(v, "_solicitar_usuario", return_value="QA"), \
         patch.object(QFileDialog, "getSaveFileName", return_value=(str(destino), "")):
        return v.cerrar_sesion()


def test_10_cambiar_de_sesion_y_x_de_windows(tmp_path):
    a = tmp_path / "a.json"; _escribir(a)
    b = tmp_path / "b.json"; datos_b = _escribir(b); datos_b["proyecciones_icociv"]["proyecto"]["nombre_proyecto"] = "Sesión B"
    b.write_text(json.dumps(datos_b, ensure_ascii=False), encoding="utf-8")
    v = _ventana_con_dane()
    try:
        _abrir(v, a)
        antes = (v._firma_trabajo(), v.ruta_sesion_actual)
        _, decidir, _ = _abrir(v, b, decision="cancelar")
        assert decidir.call_args[0][0] == "Abrir otra sesión" and (v._firma_trabajo(), v.ruta_sesion_actual) == antes
        _abrir(v, b, decision="descartar")
        assert v.ruta_sesion_actual == b and v.widget_proyecciones.nombre_proyecto.text() == "Sesión B"
        # X de Windows con cambios: misma decisión; «Cancelar» deja la ventana abierta. close() programático no pregunta.
        v.widget_proyecciones.nombre_proyecto.setText("cambio sin guardar")

        class Evento:
            ignorado = False
            def spontaneous(self): return True
            def ignore(self): Evento.ignorado = True
        with patch.object(v, "_decidir_cierre", return_value="cancelar") as decidir:
            v.closeEvent(Evento())
        assert Evento.ignorado and decidir.call_args[0][0] == "Cerrar SAVIP" and v.isVisible()
    finally:
        with patch.object(v, "_decidir_cierre", side_effect=AssertionError("close() programático no pregunta")):
            v.close()


def test_11_12_controles_temas_pantalla_dividida_y_referencias(tmp_path):
    ruta = tmp_path / "anterior.json"; _escribir(ruta, corte_dane="2026-08")  # sesión anterior; DANE posterior (2026-12)
    v = _ventana_con_dane()
    try:
        _abrir(v, ruta)
        originales = _referencias(v)
        assert originales == ([{k: r.get(k) for k in CLAVES_REFERENCIA} for r in reales()["valores"]],
                              [(x["id"], x["contexto"]) for x in reales()["historial_analisis"]])
        ok, _ = _guardar(v)
        assert ok and json.loads(ruta.read_text(encoding="utf-8"))["corte_dane"] == "2026-12"
        otra = _ventana_con_dane()
        try:
            _abrir(otra, ruta)
            assert _referencias(otra) == originales  # I0, fecha base, índice, factor y valores intactos
        finally:
            otra.close()
        b = v.boton_cerrar_sesion
        for tema in ("claro", "oscuro"):
            v._aplicar_tema(tema, persistir=False)
            for ancho in (1920, 683):
                v.resize(ancho, 820); QTest.qWait(700)  # la barra lateral se anima al expandirse
                nav = v.navegacion
                assert b.isVisible() and b.isEnabled() and b.geometry().right() == v.boton_guardar_sesion.geometry().right()
                assert b.size() == v.boton_guardar_sesion.size()  # mismo formato que sus hermanos
                assert b.height() <= 48 and (b.text() == "Cerrar sesión" if ancho == 1920 else (b.text() == "" and not b.icon().isNull()))
                v.grab(QRect(0, 0, min(ancho, 420), v.height())).save(str(CAPTURAS / f"cerrar_sesion_{ancho}_{tema}.png"))

            visto = {}

            def capturar(tema=tema):
                caja = next((x for x in QApplication.topLevelWidgets() if isinstance(x, QDialog) and x.isVisible()), None)
                if caja is None:
                    QTimer.singleShot(100, capturar); return
                botones = caja.findChildren(QPushButton)
                visto.update(titulo=caja.windowTitle(), botones=sorted(x.text() for x in botones), texto=caja.findChild(QLabel).text(),
                             completos=all(x.width() >= x.sizeHint().width() for x in botones))
                caja.grab().save(str(CAPTURAS / f"confirmacion_cerrar_{tema}.png"))
                next(x for x in botones if x.text() == "Cancelar").click()
            v.resize(1366, 820); QTest.qWait(150)
            QTimer.singleShot(300, capturar)
            assert not v.cerrar_sesion() and v.ruta_sesion_actual == ruta  # «Cancelar» real en el cuadro
            assert visto["titulo"] == "Cerrar sesión" and visto["botones"] == ["Cancelar", "Cerrar sin guardar", "Guardar y cerrar"]
            assert "No hay cambios pendientes." in visto["texto"] and visto["completos"]  # recién guardada: se pregunta igual
    finally:
        v.close()
