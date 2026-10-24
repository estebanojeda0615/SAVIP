"""Fase V1.1.2-01B: indicadores visibles al abrir, guardar y cerrar sesiones (y cerrar SAVIP).

Plataforma Qt `offscreen`: valida que el indicador se activa desde cada acceso real, que llega a
pintarse (eventos Paint de la franja) antes y durante el trabajo, que se retira siempre y que el éxito
solo se anuncia tras persistir. La evidencia en ventanas reales de Windows está en
docs/fase_v112_01b_indicadores_sesiones/.
"""
import json
import os
import time
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QObject, QPoint, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QFontDatabase, QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QDialog, QGraphicsEffect, QMenu, QFileDialog, QMessageBox, QPushButton, QWidget

from tests.test_slider_comparacion_historica_fase_4d import APP, reales
from tests.test_switch_tema_sesion_dane import MOTOR, _ventana_con_dane
from app_icociv.interfaz.animaciones.transiciones import establecer_movimiento_reducido, movimiento_reducido
from app_icociv.interfaz.componentes import VeloCarga
from app_icociv.interfaz.tema.tokens import GROSOR_BORDE_FOCO
from app_icociv.interfaz.ventana_principal import TEXTO_SIN_DANE, VentanaPrincipal
from app_icociv.persistencia import gestor_sesiones

VP = "app_icociv.interfaz.ventana_principal"
GUARDAR_REAL = gestor_sesiones.guardar_sesion
LEER_REAL = gestor_sesiones.cargar_sesion
for _fuente in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf", "seguisym.ttf"):  # métricas de Windows en offscreen
    QFontDatabase.addApplicationFont(str(Path("C:/Windows/Fonts") / _fuente))


def _escribir(ruta, **extra):
    datos = {"usuario": "QA", "archivo_excel": "C:/no/existe/anexo.xlsx", "proyecciones_icociv": reales(), **extra}
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return datos


def _ligera(ruta):
    """Sesión mínima (formato V1.0, sin análisis): se abre en milisegundos."""
    ruta.write_text(json.dumps({"usuario": "QA", "archivo_excel": "x.xlsx", "corte_dane": "2026-01"}), encoding="utf-8")


def _esperar(v):
    while v._operacion_sesion:
        APP.processEvents()


def esperar(ms):
    fin = time.perf_counter() + ms / 1000
    while time.perf_counter() < fin:
        APP.processEvents(); QTest.qWait(10)


class Pintados(QObject):
    """Registra cada Paint real de la franja: (instante, modo del velo, texto)."""

    def __init__(self, velo):
        super().__init__()
        self.velo = velo; self.registro = []
        velo.franja.installEventFilter(self)

    def eventFilter(self, objeto, evento):  # noqa: N802
        if evento.type() == QEvent.Type.Paint:
            self.registro.append((time.perf_counter(), self.velo.property("modo"), self.velo.etiqueta.text()))
        return False

    def textos(self):
        return [t for _, _, t in self.registro]


def _avisos(v):
    registro = []
    original = v.notificaciones.mostrar

    def mostrar(titulo, detalle="", nivel="informacion", *a, **k):
        registro.append((time.perf_counter(), titulo, nivel)); return original(titulo, detalle, nivel, *a, **k)
    v.notificaciones.mostrar = mostrar  # exito()/informacion() llaman a self.mostrar
    return registro


def _con_trabajo(v, ruta=None):
    """Espacio con 3 análisis reales; con `ruta`, ya guardado allí."""
    v.sesion_pendiente = {"proyecciones_icociv": reales()}; v._restaurar_sesion_pendiente()
    v.usuario_actual = "QA"
    if ruta is not None:
        with patch.object(QFileDialog, "getSaveFileName", return_value=(str(ruta), "")),              patch.object(v, "_solicitar_usuario", return_value="QA"):
            assert v.guardar_sesion_actual(como=True)
    return v


def _cambiar(v):
    v.widget_proyecciones.nombre_proyecto.setText(f"cambio {time.perf_counter()}")


def _lento(segundos, registro=None):
    def guardar(destino, datos):
        time.sleep(segundos)
        ruta = GUARDAR_REAL(destino, datos)
        if registro is not None:
            registro.append(time.perf_counter())  # el archivo ya fue reemplazado
        return ruta
    return guardar


def _accion(v, menu, texto):
    m = next(x for x in v.menuBar().findChildren(QMenu) if x.title() == menu)
    return next(a for a in m.actions() if a.text() == texto)


def _libre(v):
    esperar(350)  # fundido de salida
    return not v.velo_carga.activo and not v.velo_carga.isVisible() and not v.velo_carga.animacion_activa()


# ------------------------------------------------------------------ VeloCarga (componente)
def _velo():
    base = QWidget(); base.resize(900, 600); base.show()
    velo = VeloCarga(base); esperar(50)  # ventana ya expuesta, como la de SAVIP
    return base, velo


def test_franja_inmediata_visible_y_esqueleto_solo_tras_el_umbral():
    base, velo = _velo()
    velo.mostrar("Abriendo sesión: leyendo el archivo…", esqueleto="sesion", inmediato=True)
    assert velo.isVisible() and velo.property("modo") == "franja" and velo.graphicsEffect() is None
    assert velo.geometry() == base.rect() and velo.franja.isVisible() and not velo.esqueleto.isVisible()
    esperar(150); assert velo.property("modo") == "franja"
    esperar(400); assert velo.property("modo") == "esqueleto" and velo.esqueleto.isVisible()
    velo.ocultar(); esperar(350)
    assert not velo.isVisible() and not velo.animacion_activa() and velo.graphicsEffect() is None


def test_franja_sin_esqueleto_no_cambia_y_se_retira():
    base, velo = _velo()
    velo.mostrar("Guardando sesión…", inmediato=True); esperar(700)
    assert velo.isVisible() and velo.property("modo") == "franja" and velo.franja.porcentaje() is None
    velo.ocultar(); esperar(350)
    assert not velo.isVisible() and not velo.animacion_activa()


def test_pintar_ahora_aplica_el_umbral_vencido_sin_bucle_de_eventos():
    base, velo = _velo(); p = Pintados(velo)
    velo.mostrar("x", esqueleto="sesion", inmediato=True)
    velo.pintar_ahora()  # antes de 0,4 s: sigue la franja, ya pintada
    assert velo.property("modo") == "franja" and p.registro and p.registro[-1][1] == "franja"
    time.sleep(0.45)  # tramo síncrono: el temporizador no puede dispararse
    velo.actualizar_mensaje("y"); velo.pintar_ahora()
    assert velo.property("modo") == "esqueleto" and p.registro[-1][1:] == ("esqueleto", "y")
    velo.ocultar(); esperar(350)
    velo.mostrar("w", esqueleto="sesion", inmediato=True); velo.pintar_ahora(largo=True)  # tramo largo conocido
    assert velo.property("modo") == "esqueleto" and p.registro[-1][1:] == ("esqueleto", "w")
    velo.ocultar(); esperar(350); assert not velo.isVisible()
    # Sin `inmediato` (otros loaders de Fase 01) el comportamiento no cambia: invisible hasta 0,4 s.
    velo.mostrar("z", esqueleto="anexo"); velo.pintar_ahora()
    assert velo.graphicsEffect() is not None and velo.graphicsEffect().opacity() == 0.0
    time.sleep(0.45); velo.pintar_ahora()
    assert velo.graphicsEffect() is None and velo.property("modo") == "esqueleto"
    velo.ocultar(); esperar(350); assert not velo.animacion_activa()


def test_franja_estatica_con_animaciones_de_windows_desactivadas():
    previo = movimiento_reducido(); establecer_movimiento_reducido(True)
    try:
        base, velo = _velo()
        velo.mostrar("Guardando sesión…", esqueleto="sesion", inmediato=True); esperar(600)
        assert velo.isVisible() and velo.property("modo") == "esqueleto" and not velo._animacion.isActive()
        velo.ocultar(); assert not velo.isVisible()
    finally:
        establecer_movimiento_reducido(previo)


def test_ciclos_franja_sin_fugas():
    base, velo = _velo()
    velo.mostrar("x", inmediato=True); esperar(50); velo.ocultar(); esperar(350)
    vivos = lambda: [type(o).__name__ for o in velo.findChildren(QObject)
                     if isinstance(o, (QPropertyAnimation, QGraphicsEffect, QTimer))]  # lo que podría fugarse
    inicial = vivos()
    for i in range(20):
        velo.mostrar(f"ciclo {i}", esqueleto="sesion" if i % 2 else None, inmediato=bool(i % 3))
        esperar(30 if i % 2 else 450); velo.ocultar()
    esperar(400)
    assert vivos() == inicial and not velo.animacion_activa() and not velo.isVisible()


# ------------------------------------------------------------------ Abrir sesión
def test_T01B_1_abrir_desde_menu_boton_y_portada_franja_inmediata(tmp_path):
    ruta = tmp_path / "ligera.json"; _ligera(ruta)
    v = _ventana_con_dane()
    try:
        p = Pintados(v.velo_carga); avisos = _avisos(v)
        portada = next(b for b in v.pantalla_inicio.findChildren(QPushButton) if b.text() == "2. Abrir sesión guardada")
        accesos = {"menú": _accion(v, "Sesiones", "Abrir sesión").trigger, "botón": v.boton_abrir_sesion.click, "portada": portada.click}
        for nombre, disparar in accesos.items():
            antes = len(p.registro)
            with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")), \
                 patch.object(v, "_decidir_cierre", return_value="descartar"), patch(MOTOR, side_effect=AssertionError("motor")), \
                 patch.object(QMessageBox, "warning", side_effect=AssertionError("sin error")):
                disparar()
                # Al volver de la señal, sin procesar eventos: la franja ya está y bloquea el área de trabajo.
                velo = v.velo_carga
                assert velo.activo and velo.isVisible() and velo.property("modo") == "franja", nombre
                assert velo.etiqueta.text() == "Abriendo sesión: leyendo el archivo…" and velo.geometry() == velo.parentWidget().rect()
                assert not v.navegacion.isEnabled()
                _esperar(v)
            assert len(p.registro) > antes and p.registro[antes][1] == "franja", nombre  # se pintó de verdad
            assert all(m == "franja" for _, m, _ in p.registro[antes:]), "sesión ligera: sin esqueleto fugaz"
            assert avisos[-1][1:] == ("Sesión abierta", "exito") and v.ruta_sesion_actual == ruta
            assert _libre(v) and v.navegacion.isEnabled()
    finally:
        v.close()


def test_T01B_2_abrir_sesion_grande_lenta_esqueleto_etapas_y_respuesta(tmp_path):
    ruta = tmp_path / "grande.json"; datos = _escribir(ruta)
    v = _ventana_con_dane()
    try:
        p = Pintados(v.velo_carga); avisos = _avisos(v)
        ticks = []; reloj = QTimer(); reloj.timeout.connect(lambda: ticks.append(time.perf_counter())); reloj.start(50)
        al_reconstruir = []
        reiniciar = v._reiniciar_espacio_trabajo
        lenta = lambda r: (time.sleep(0.9), LEER_REAL(r))[1]
        with patch(f"{VP}.cargar_sesion", side_effect=lenta), \
             patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")), patch(MOTOR, side_effect=AssertionError("motor")), \
             patch.object(v, "_reiniciar_espacio_trabajo", side_effect=lambda: (al_reconstruir.append(
                 (v.velo_carga.property("modo"), v.velo_carga.etiqueta.text(), p.textos()[-1])), reiniciar())):
            inicio = time.perf_counter()
            v.abrir_sesion(); _esperar(v)
        reloj.stop()
        lectura = [t for t in ticks if t < inicio + 0.9]
        assert len(lectura) >= 10  # la interfaz atiende temporizadores mientras se lee
        modos = [m for t, m, _ in p.registro if t < inicio + 0.9]
        assert modos[0] == "franja" and "esqueleto" in modos  # esqueleto pasados 0,4 s, animado
        texto = "Abriendo sesión: restaurando análisis, actividades y Empalme…"
        assert al_reconstruir == [("esqueleto", texto, texto)]  # pintado ANTES del tramo síncrono
        validando = [m for _, m, t in p.registro if t == "Abriendo sesión: validando el contenido…"]
        assert validando and validando[0] == "esqueleto"  # sesión de 6,8 MB: esqueleto antes de validar
        assert [a["id"] for a in v.widget_proyecciones.historial] == [a["id"] for a in datos["proyecciones_icociv"]["historial_analisis"]]
        assert avisos[-1][1] == "Sesión abierta" and _libre(v)
    finally:
        v.close()


def test_T01B_3_errores_de_apertura_sin_falso_exito_ni_velo_perpetuo(tmp_path):
    previa = tmp_path / "previa.json"; _ligera(previa)
    v = _ventana_con_dane()
    try:
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(previa), "")):
            v.abrir_sesion(); _esperar(v)
        estado = (v._firma_trabajo(), v.ruta_sesion_actual)
        avisos = _avisos(v)
        roto = tmp_path / "roto.json"; roto.write_text("{ no es json", encoding="utf-8")
        futura = tmp_path / "futura.json"; futura.write_text(json.dumps({"usuario": "QA", "corte_dane": "2027-05"}), encoding="utf-8")
        casos = {"JSON inválido": (roto, None, "no es un archivo de sesión JSON válido"),
                 "DANE incompatible": (futura, None, "fecha base 2027-05 o posterior"),
                 "carpeta en vez de archivo": (tmp_path, None, ""),
                 "lectura denegada": (previa, PermissionError("Acceso denegado"), "Acceso denegado")}
        for nombre, (ruta, fallo, esperado) in casos.items():
            visto = {}
            with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")), \
                 patch.object(v, "_decidir_cierre", return_value="descartar"), \
                 patch(f"{VP}.cargar_sesion", side_effect=fallo or LEER_REAL), \
                 patch.object(QMessageBox, "warning", side_effect=lambda *a: visto.update(texto=a[2], velo=v.velo_carga.activo)):
                v.abrir_sesion(); _esperar(v)
            assert esperado in visto["texto"] and visto["velo"] is False, nombre  # el velo se retira antes del aviso
            assert (v._firma_trabajo(), v.ruta_sesion_actual) == estado and _libre(v), nombre
            assert v.etiqueta_estado.text() == "No se abrió la sesión."
        assert not [a for a in avisos if a[1] == "Sesión abierta"]
        # Selector cancelado: nada, ni franja.
        with patch.object(QFileDialog, "getOpenFileName", return_value=("", "")), patch.object(v.velo_carga, "mostrar") as mostrar:
            v.abrir_sesion()
        assert not mostrar.called and v._operacion_sesion is None
    finally:
        v.close()
    # Sin DANE: solo el aviso existente; ni selector ni franja.
    sin = VentanaPrincipal(); sin.show()
    try:
        with patch.object(QMessageBox, "warning") as aviso, patch.object(QFileDialog, "getOpenFileName") as selector, \
             patch.object(sin.velo_carga, "mostrar") as mostrar:
            sin.abrir_sesion()
        assert aviso.call_args[0][2] == TEXTO_SIN_DANE and not selector.called and not mostrar.called
    finally:
        sin.close()


def test_T01B_4_abrir_otra_guardando_la_actual_primero(tmp_path):
    actual = tmp_path / "actual.json"; otra = tmp_path / "otra.json"; _ligera(otra)
    v = _con_trabajo(_ventana_con_dane(), actual)
    try:
        p = Pintados(v.velo_carga); avisos = _avisos(v); _cambiar(v)
        with patch.object(v, "_decidir_cierre", return_value="guardar"), \
             patch.object(QFileDialog, "getOpenFileName", return_value=(str(otra), "")), \
             patch(f"{VP}.guardar_sesion", side_effect=PermissionError("Acceso denegado")), patch.object(QMessageBox, "warning"):
            v.abrir_sesion(); _esperar(v)
        assert v.ruta_sesion_actual == actual and "Abriendo sesión: leyendo el archivo…" not in p.textos()  # falló: no se abre
        with patch.object(v, "_decidir_cierre", return_value="guardar"), \
             patch.object(QFileDialog, "getOpenFileName", return_value=(str(otra), "")), patch(f"{VP}.guardar_sesion", side_effect=_lento(0.5)):
            v.abrir_sesion(); _esperar(v)
        textos = p.textos()
        assert textos.count("Guardando la sesión actual antes de abrir otra…") >= 2  # pintada y animada
        assert textos.index("Guardando la sesión actual antes de abrir otra…") < textos.index("Abriendo sesión: leyendo el archivo…")
        assert [a[1] for a in avisos][-2:] == ["Sesión guardada", "Sesión abierta"] and v.ruta_sesion_actual == otra
        assert json.loads(actual.read_text(encoding="utf-8"))["proyecciones_icociv"]["proyecto"]["nombre_proyecto"].startswith("cambio")
        assert _libre(v)
    finally:
        v.close()


# ------------------------------------------------------------------ Guardar / Ctrl+S / Guardar como
def test_T01B_5_ctrl_s_ruta_conocida_lento_exito_solo_tras_persistir(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        assert v.accion_guardar_sesion.shortcut() == QKeySequence(QKeySequence.StandardKey.Save)
        p = Pintados(v.velo_carga); avisos = _avisos(v); _cambiar(v)
        hecho, reentrada, ticks = [], [], []
        reloj = QTimer(); reloj.timeout.connect(lambda: ticks.append(1)); reloj.start(50)

        class Evento:
            ignorado = False
            def spontaneous(self): return True
            def ignore(self): Evento.ignorado = True
        QTimer.singleShot(300, lambda: (reentrada.append(v.guardar_rapido()), v.closeEvent(Evento())))
        with patch(f"{VP}.guardar_sesion", side_effect=_lento(1.0, hecho)), \
             patch.object(QFileDialog, "getSaveFileName", side_effect=AssertionError("ya tiene ruta")):
            v.activateWindow(); v.widget_proyecciones.tabla_valores.setFocus(); APP.processEvents()
            inicio = time.perf_counter()
            QTest.keyClick(v.widget_proyecciones.tabla_valores, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
        reloj.stop()
        assert hecho and len(ticks) >= 12  # la ventana siguió atendiendo temporizadores durante la escritura
        durante = [x for x in p.registro if inicio <= x[0] <= hecho[0]]
        assert len(durante) >= 10 and {m for _, m, _ in durante} == {"franja"} and {t for _, _, t in durante} == {"Guardando sesión…"}
        guardada = [t for t, titulo, _ in avisos if titulo == "Sesión guardada"]
        assert len(guardada) == 1 and guardada[0] > hecho[0]  # éxito anunciado después del reemplazo atómico
        assert reentrada == [False] and Evento.ignorado and any(a[1].startswith("Espere a que termine") for a in avisos)
        assert v._firma_trabajo() == v._firma_guardada and v.etiqueta_estado.text() == "Sesión guardada: s.json"
        assert json.loads(ruta.read_text(encoding="utf-8"))["usuario"] == "QA" and not list(tmp_path.glob("*.tmp"))
        assert _libre(v)
    finally:
        v.close()


def test_T01B_6_sin_ruta_guardar_como_y_selector_cancelado(tmp_path):
    v = _con_trabajo(_ventana_con_dane())
    try:
        avisos = _avisos(v); durante_selector = []
        def selector(destino):
            def elegir(*_a, **_k):
                durante_selector.append(v.velo_carga.activo); return (str(destino), "")
            return elegir
        # Primera vez (sin ruta): el selector se abre sin franja; tras elegir, franja y aviso.
        with patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", side_effect=selector(tmp_path / "primera.json")):
            assert v.guardar_rapido()
        # Guardar como (Ctrl+Shift+S) cancelado: ni archivo, ni franja, ni éxito.
        with patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", side_effect=selector("")), patch.object(v.velo_carga, "mostrar") as mostrar:
            assert not v.guardar_rapido(como=True)
        assert not mostrar.called and sorted(x.name for x in tmp_path.iterdir()) == ["primera.json"]
        # Guardar como a otro archivo: el anterior queda intacto.
        original = (tmp_path / "primera.json").read_bytes()
        with patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", side_effect=selector(tmp_path / "copia.json")):
            assert v.guardar_rapido(como=True)
        assert durante_selector == [False, False, False] and (tmp_path / "primera.json").read_bytes() == original
        assert v.ruta_sesion_actual == tmp_path / "copia.json" and [a[1] for a in avisos] == ["Sesión guardada", "Sesión guardada"]
        assert _libre(v)
    finally:
        v.close()


def test_T01B_7_errores_de_escritura_no_marcan_guardado(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        original = ruta.read_bytes(); avisos = _avisos(v); _cambiar(v)
        bloqueo = tmp_path / "soy_un_archivo"; bloqueo.write_text("x")
        casos = {"permiso denegado": (ruta, patch(f"{VP}.guardar_sesion", side_effect=PermissionError("Acceso denegado")), "Acceso denegado"),
                 "carpeta inaccesible (real)": (bloqueo / "sub" / "s.json", patch(f"{VP}.guardar_sesion", side_effect=GUARDAR_REAL), ""),
                 "fallo a mitad de escritura": (ruta, patch("app_icociv.persistencia.gestor_sesiones.json.dump", side_effect=OSError("Disco lleno")), "Disco lleno")}
        for nombre, (destino, fallo, esperado) in casos.items():
            v.ruta_sesion_actual = destino; visto = {}
            with fallo, patch.object(QMessageBox, "warning", side_effect=lambda *a: visto.update(texto=a[2], velo=v.velo_carga.activo)):
                assert not v.guardar_rapido(), nombre
            assert esperado in visto["texto"] and "siguen en memoria" in visto["texto"] and visto["velo"] is False, nombre
            assert v.ruta_sesion_actual == destino and v._firma_trabajo() != v._firma_guardada, nombre
            assert v.etiqueta_estado.text() == "No se guardó la sesión." and _libre(v), nombre
        assert ruta.read_bytes() == original and not list(tmp_path.glob("*.tmp")) and not avisos
    finally:
        v.close()


def test_T01B_8_dos_guardados_consecutivos_y_ciclos_abrir_cerrar(tmp_path):
    ruta = tmp_path / "s.json"; ligera = tmp_path / "ligera.json"; _ligera(ligera)
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        avisos = _avisos(v); assert _libre(v)
        hijos = sorted(type(o).__name__ for o in v.velo_carga.findChildren(QObject) if isinstance(o, (QPropertyAnimation, QGraphicsEffect, QTimer)))
        for _ in range(2):
            _cambiar(v); assert v.guardar_rapido()
        for _ in range(3):
            with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ligera), "")), \
                 patch.object(v, "_decidir_cierre", return_value="descartar"):
                v.abrir_sesion(); _esperar(v)
                assert v.cerrar_sesion()
        assert [a[1] for a in avisos] == ["Sesión guardada"] * 2 + ["Sesión abierta", "Sesión cerrada"] * 3
        assert _libre(v) and sorted(type(o).__name__ for o in v.velo_carga.findChildren(QObject)
                                    if isinstance(o, (QPropertyAnimation, QGraphicsEffect, QTimer))) == hijos
        assert len(v.notificaciones._activas) <= v.notificaciones.MAXIMO_VISIBLES
    finally:
        v.close()


# ------------------------------------------------------------------ Cerrar sesión
def test_T01B_9_cerrar_sesion_guardar_y_cerrar_desde_menu_y_boton(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        for disparar in (_accion(v, "Sesiones", "Cerrar sesión").trigger, v.boton_cerrar_sesion.click):
            if not v._hay_trabajo():
                _con_trabajo(v); v.ruta_sesion_actual = ruta
            _cambiar(v); nombre = v.widget_proyecciones.nombre_proyecto.text()
            p = Pintados(v.velo_carga); avisos = _avisos(v); hecho = []; con_datos = []
            def lento(destino, datos):
                con_datos.append(bool(v.widget_proyecciones.historial))  # aún no se vació nada
                return _lento(0.6, hecho)(destino, datos)
            with patch.object(v, "_decidir_cierre", return_value="guardar"), patch(f"{VP}.guardar_sesion", side_effect=lento):
                disparar()
            assert con_datos == [True] and "Guardando sesión antes de cerrarla…" in p.textos()
            assert json.loads(ruta.read_text(encoding="utf-8"))["proyecciones_icociv"]["proyecto"]["nombre_proyecto"] == nombre
            assert [a[1] for a in avisos] == ["Sesión guardada", "Sesión cerrada"] and avisos[0][0] > hecho[0]
            assert not v._hay_trabajo() and _libre(v)
        # Fallo del guardado y selector cancelado: no se cierra y no queda velo.
        _con_trabajo(v); v.ruta_sesion_actual = ruta; _cambiar(v); estado = v._firma_trabajo()
        with patch.object(v, "_decidir_cierre", return_value="guardar"), \
             patch(f"{VP}.guardar_sesion", side_effect=PermissionError("Acceso denegado")), patch.object(QMessageBox, "warning"):
            assert not v.cerrar_sesion()
        v.ruta_sesion_actual = None
        with patch.object(v, "_decidir_cierre", return_value="guardar"), patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            assert not v.cerrar_sesion()
        assert v._firma_trabajo() == estado and v._hay_trabajo() and _libre(v)
    finally:
        v.close()


def test_T01B_10_cerrar_sin_guardar_y_cancelar_sin_escritura_ni_loader(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        _cambiar(v); original = ruta.read_bytes(); estado = v._firma_trabajo(); avisos = _avisos(v)
        with patch.object(v, "_decidir_cierre", return_value="cancelar"), patch.object(v.velo_carga, "mostrar") as mostrar, \
             patch(f"{VP}.guardar_sesion", side_effect=AssertionError("no escribe")):
            assert not v.cerrar_sesion()
        assert not mostrar.called and v._firma_trabajo() == estado and not avisos
        with patch.object(v, "_decidir_cierre", return_value="descartar"), patch.object(v.velo_carga, "mostrar") as mostrar, \
             patch(f"{VP}.guardar_sesion", side_effect=AssertionError("no escribe")):
            assert v.cerrar_sesion()
        assert not mostrar.called and ruta.read_bytes() == original and not v._hay_trabajo()
        assert [a[1:] for a in avisos] == [("Sesión cerrada", "informacion")]
    finally:
        v.close()


def test_T01B_11_dialogo_de_cierre_real_en_snap_un_tercio(tmp_path):
    v = _con_trabajo(_ventana_con_dane(), tmp_path / "s.json")
    try:
        v.resize(640, 520); esperar(700)
        visto = {}
        def medir():
            caja = next((x for x in APP.topLevelWidgets() if isinstance(x, QDialog) and x.isVisible()), None)
            if caja is None:
                QTimer.singleShot(50, medir); return
            botones = caja.findChildren(QPushButton)
            visto.update(dentro=v.frameGeometry().contains(caja.frameGeometry()), velo=v.velo_carga.activo,
                         botones=sorted(b.text() for b in botones),
                         completos=all(b.isVisible() and b.width() >= b.sizeHint().width() + 2 * GROSOR_BORDE_FOCO  # cabe con foco
                                       and caja.rect().contains(QRect(b.mapTo(caja, QPoint(0, 0)), b.size())) for b in botones))
            next(b for b in botones if b.text() == "Cancelar").click()
        QTimer.singleShot(100, medir)
        assert not v.cerrar_sesion() and v._hay_trabajo()
        assert visto == {"dentro": True, "velo": False, "botones": ["Cancelar", "Cerrar sin guardar", "Guardar y cerrar"], "completos": True}
    finally:
        v.close()


# ------------------------------------------------------------------ Cerrar SAVIP (X / Alt+F4 / Archivo › Salir)
def test_T01B_12_salir_guardar_y_cerrar_cierra_solo_tras_persistir(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta); _cambiar(v); nombre = v.widget_proyecciones.nombre_proyecto.text()
    p = Pintados(v.velo_carga); hecho = []; visible_al_escribir = []; oculta = []

    class Ocultar(QObject):
        def eventFilter(self, objeto, evento):  # noqa: N802
            if evento.type() == QEvent.Type.Hide:
                oculta.append(time.perf_counter())
            return False
    filtro = Ocultar(); v.installEventFilter(filtro)

    def lento(destino, datos):
        visible_al_escribir.append(v.isVisible())
        return _lento(0.8, hecho)(destino, datos)
    with patch.object(v, "_decidir_cierre", return_value="guardar") as decidir, patch(f"{VP}.guardar_sesion", side_effect=lento):
        _accion(v, "Archivo", "Salir").trigger()
    assert decidir.call_args[0][0] == "Cerrar SAVIP" and visible_al_escribir == [True] and hecho[0] < oculta[0]
    assert not v.isVisible() and "Guardando sesión antes de cerrar SAVIP…" in p.textos()
    assert json.loads(ruta.read_text(encoding="utf-8"))["proyecciones_icociv"]["proyecto"]["nombre_proyecto"] == nombre


def test_T01B_13_salir_con_fallo_cancelacion_o_sin_guardar(tmp_path):
    ruta = tmp_path / "s.json"
    v = _con_trabajo(_ventana_con_dane(), ruta)
    try:
        _cambiar(v); original = ruta.read_bytes()
        with patch.object(v, "_decidir_cierre", return_value="guardar"), \
             patch(f"{VP}.guardar_sesion", side_effect=PermissionError("Acceso denegado")), patch.object(QMessageBox, "warning"):
            v.salir()
        assert v.isVisible() and _libre(v)
        v.ruta_sesion_actual = None
        with patch.object(v, "_decidir_cierre", return_value="guardar"), patch.object(v, "_solicitar_usuario", return_value="QA"), \
             patch.object(QFileDialog, "getSaveFileName", return_value=("", "")):
            v.salir()
        with patch.object(v, "_decidir_cierre", return_value="cancelar"):
            v.salir()
        assert v.isVisible() and v._hay_trabajo() and ruta.read_bytes() == original
        with patch.object(v, "_decidir_cierre", return_value="descartar"), patch(f"{VP}.guardar_sesion", side_effect=AssertionError("no escribe")):
            v.salir()
        assert not v.isVisible() and ruta.read_bytes() == original
    finally:
        v.close()


def test_T01B_14_salir_durante_una_apertura_se_ignora_y_avisa(tmp_path):
    ruta = tmp_path / "s.json"; _ligera(ruta)
    v = _ventana_con_dane()
    try:
        avisos = _avisos(v)
        lenta = lambda r: (time.sleep(0.6), LEER_REAL(r))[1]
        with patch(f"{VP}.cargar_sesion", side_effect=lenta), patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")):
            v.abrir_sesion(); esperar(100)
            v.salir()
            assert v.isVisible() and avisos[-1][1].startswith("Espere a que termine")
            _esperar(v)
        assert v.ruta_sesion_actual == ruta and _libre(v)
    finally:
        v.close()
    assert not v.isVisible()
