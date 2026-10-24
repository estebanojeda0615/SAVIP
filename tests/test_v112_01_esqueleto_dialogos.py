"""Fase V1.1.2-01: esqueletos de carga, progreso honesto y diálogos dentro de la ventana de SAVIP.

Plataforma Qt `offscreen` (automatización): valida lógica, ciclo de vida y geometría Qt. No sustituye
la comprobación en ventanas reales de Windows (ver docs/fase_v112_01_skeleton_dialogos/).
"""
import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QMargins, QObject, QPoint, QRect, QSize, Qt, QThread, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QDialog, QDialogButtonBox, QLabel, QMessageBox, QPushButton,
                               QScrollArea, QTextBrowser, QVBoxLayout, QWidget)

from app_icociv.interfaz.animaciones.transiciones import establecer_movimiento_reducido, movimiento_reducido
from app_icociv.interfaz.componentes import VeloCarga
from app_icociv.interfaz.componentes.dialogos import MARGEN, geometria_dialogo, instalar_ajuste_dialogos
from app_icociv.interfaz.componentes.esqueleto import VARIANTES, FranjaProgreso, bloques
from app_icociv.interfaz.controladores.trabajadores import TrabajadorFuncion

APP = QApplication.instance() or QApplication([])
instalar_ajuste_dialogos(APP)


def esperar(ms):
    fin = time.monotonic() + ms / 1000
    while time.monotonic() < fin:
        APP.processEvents(); QTest.qWait(10)


def velo_en(ancho=900, alto=600):
    base = QWidget(); base.resize(ancho, alto); base.show()
    return base, VeloCarga(base)


# ------------------------------------------------------------------ esqueleto
@pytest.mark.parametrize("variante", VARIANTES)
@pytest.mark.parametrize("ancho,alto", [(300, 200), (626, 450), (1340, 650), (1900, 980)])
def test_esqueleto_no_sale_de_su_area(variante, ancho, alto):
    tarjetas, barras = bloques(variante, ancho, alto)
    area = QRect(0, 0, ancho, alto)
    assert tarjetas, "cada variante dibuja al menos una tarjeta"
    for t in tarjetas:
        assert area.contains(t.toAlignedRect().adjusted(1, 1, -1, -1))
    for b in barras:  # toda barra dentro de alguna tarjeta: la silueta no se desborda
        assert any(t.contains(b) for t in tarjetas)


def test_variantes_tienen_geometria_distinta():
    huellas = {v: tuple((round(t.width()), round(t.height())) for t in bloques(v, 1300, 700)[0]) for v in VARIANTES}
    assert len(set(huellas.values())) == len(VARIANTES)


# ------------------------------------------------------------------ progreso honesto
def test_franja_indeterminada_no_inventa_porcentaje():
    f = FranjaProgreso()
    f.establecer_texto("Leyendo y validando el anexo DANE…")
    assert f.indeterminada and f.porcentaje() is None
    assert "avance no medible" in f.accessibleName()
    for _ in range(200):
        f.avanzar(0.05)
    assert f.porcentaje() is None  # avanzar la animación no crea progreso
    f.establecer_progreso(2, 5)
    assert f.porcentaje() == 40 and "40 %" in f.accessibleName()
    f.establecer_progreso(None)
    assert f.porcentaje() is None


def test_velo_sin_medicion_nunca_muestra_porcentaje():
    base, velo = velo_en()
    velo.mostrar("Evaluando los modelos de proyección…", esqueleto="resultados")
    esperar(900)
    assert velo.franja.porcentaje() is None
    velo.ocultar(exito=True)
    assert velo.franja.porcentaje() is None  # éxito sin medición: no se simula un 100 %


def test_progreso_medido_se_completa_solo_con_exito():
    base, velo = velo_en()
    velo.mostrar("Actualizando análisis…")
    velo.establecer_progreso(1, 4)
    assert velo.franja.porcentaje() == 25
    velo.ocultar(exito=False)
    assert velo.franja.porcentaje() == 25  # error: no salta a 100 %
    velo.mostrar("Actualizando análisis…")
    assert velo.franja.porcentaje() is None  # cada operación empieza sin avance heredado
    esperar(500); velo.establecer_progreso(3, 4); velo.ocultar(exito=True)
    assert velo.franja.porcentaje() == 100


def test_trabajador_informa_progreso_en_el_hilo_de_interfaz():
    hilos, valores = [], []

    def tarea(informar, n):
        for i in range(n):
            informar(i, n)
        return "ok"

    t = TrabajadorFuncion(tarea, 3, informar_progreso=True)
    t.progreso.connect(lambda h, n: (hilos.append(QThread.currentThread()), valores.append((h, n))))
    resultado = []
    t.resultado.connect(resultado.append)
    t.start()
    fin = time.monotonic() + 10
    while (t.isRunning() or len(valores) < 3) and time.monotonic() < fin:
        APP.processEvents(); QTest.qWait(10)
    assert resultado == ["ok"] and valores == [(0, 3), (1, 3), (2, 3)]
    assert all(h is APP.thread() for h in hilos)  # widgets se actualizan solo en el hilo principal


def test_trabajador_sin_progreso_conserva_su_firma():
    t = TrabajadorFuncion(lambda a, b=0: a + b, 2, b=3)
    assert t.args == (2,) and t.kwargs == {"b": 3}


# ------------------------------------------------------------------ ciclo de vida
def test_velo_esqueleto_cubre_el_area_y_se_limpia():
    base, velo = velo_en(1000, 640)
    velo.mostrar("Recuperando la sesión guardada…", esqueleto="sesion")
    assert velo.property("modo") == "esqueleto" and velo.esqueleto.variante == "sesion"
    assert velo.isVisible() and velo.geometry() == base.rect()  # bloquea clics desde el inicio
    esperar(700)
    assert velo.esqueleto.isVisible() and not velo.panel.isVisible()
    if not movimiento_reducido():
        assert velo.animacion_activa()
    velo.ocultar(exito=True)
    assert not velo.activo and not velo.animacion_activa()  # sin temporizadores tras ocultar
    esperar(400)
    assert not velo.isVisible() and velo.graphicsEffect() is None


def test_velo_panel_para_exportar():
    base, velo = velo_en(700, 500)
    velo.mostrar("Generando el informe PDF…")
    esperar(600)
    assert velo.property("modo") == "panel" and velo.panel.isVisible() and not velo.esqueleto.isVisible()
    assert velo.panel.width() <= base.width() and velo.etiqueta.text() == "Generando el informe PDF…"
    velo.ocultar(); esperar(400)
    assert not velo.isVisible()


def test_tarea_breve_no_destella():
    base, velo = velo_en()
    velo.mostrar("Leyendo y validando el anexo DANE…", esqueleto="anexo")
    esperar(100); velo.ocultar(exito=True)
    assert not velo.isVisible() and not velo.animacion_activa() and velo.graphicsEffect() is None


def test_desvanecimiento_no_oculta_una_operacion_nueva():
    base, velo = velo_en()
    velo.mostrar("Primera…", esqueleto="anexo"); esperar(600)
    velo.ocultar(exito=True)
    velo.mostrar("Segunda…", esqueleto="resultados")  # antes de que termine el desvanecimiento
    esperar(800)
    assert velo.activo and velo.isVisible() and velo.etiqueta.text() == "Segunda…"
    velo.ocultar(); esperar(400)


def test_ciclos_repetidos_sin_fugas():
    base, velo = velo_en()
    velo.mostrar("x", esqueleto="resultados"); esperar(500); velo.ocultar(); esperar(300)
    inicial = len(velo.findChildren(QObject))
    for i in range(30):
        velo.mostrar(f"ciclo {i}", esqueleto=VARIANTES[i % 3] if i % 4 else None)
        esperar(30 if i % 2 else 450)
        velo.ocultar(exito=bool(i % 2))
    esperar(400)
    assert len(velo.findChildren(QObject)) == inicial and not velo.animacion_activa() and not velo.isVisible()


def test_movimiento_reducido_esqueleto_estatico():
    previo = movimiento_reducido()
    establecer_movimiento_reducido(True)
    try:
        base, velo = velo_en()
        velo.mostrar("Evaluando los modelos de proyección…", esqueleto="resultados")
        esperar(600)
        assert velo.isVisible() and not velo._animacion.isActive()
        velo.ocultar()
        assert not velo.isVisible()
    finally:
        establecer_movimiento_reducido(previo)


def test_cancelar_retira_y_avisa():
    base, velo = velo_en()
    llamadas = []
    velo.mostrar("Procesando…", al_cancelar=lambda: llamadas.append(1)); esperar(500)
    assert velo.boton_cancelar.isVisible()
    velo.boton_cancelar.click()
    assert llamadas == [1] and velo.etiqueta.text() == "Cancelando…" and not velo.boton_cancelar.isEnabled()
    velo.ocultar(exito=False); esperar(400)
    assert not velo.isVisible()


# ------------------------------------------------------------------ geometría de diálogos (pura)
BORDES = QMargins(8, 31, 8, 8)
MONITOR = QRect(0, 0, 1920, 1032)


def _marco(cliente: QRect) -> QRect:
    return cliente.adjusted(-BORDES.left(), -BORDES.top(), BORDES.right(), BORDES.bottom())


@pytest.mark.parametrize("ventana", [QRect(0, 0, 640, 1032), QRect(640, 0, 640, 1032), QRect(0, 0, 960, 1032),
                                     QRect(1280, 0, 640, 1032), QRect(0, 0, 1366, 720), QRect(0, 0, 1920, 1032)])
@pytest.mark.parametrize("tamano", [QSize(1060, 420), QSize(760, 660), QSize(900, 640), QSize(420, 160)])
def test_dialogo_cabe_en_la_ventana(ventana, tamano):
    cliente, ambito = geometria_dialogo(tamano, QSize(300, 150), ventana, MONITOR, BORDES)
    assert ambito == "ventana" and ventana.contains(_marco(cliente)) and MONITOR.contains(_marco(cliente))
    assert cliente.width() <= tamano.width() and cliente.height() <= tamano.height()
    if tamano.width() + 2 * MARGEN + 16 <= ventana.width():  # cabe: se centra sobre la ventana
        assert abs(_marco(cliente).center().x() - ventana.center().x()) <= 1


def test_minimo_que_no_cabe_usa_el_monitor():
    ventana = QRect(0, 0, 640, 600)
    cliente, ambito = geometria_dialogo(QSize(800, 500), QSize(700, 300), ventana, MONITOR, BORDES)
    assert ambito == "monitor" and MONITOR.contains(_marco(cliente)) and cliente.width() >= 700


def test_ventana_parcialmente_fuera_del_monitor():
    ventana = QRect(1500, 100, 900, 700)  # sobresale por la derecha
    cliente, ambito = geometria_dialogo(QSize(600, 300), QSize(200, 100), ventana, MONITOR, BORDES)
    assert MONITOR.contains(_marco(cliente)) and ventana.intersected(MONITOR).contains(_marco(cliente))


def test_segundo_monitor_coordenadas_globales():
    monitor_2 = QRect(1920, 0, 1366, 728)
    ventana = QRect(1920, 0, 683, 728)
    cliente, _ = geometria_dialogo(QSize(1060, 420), QSize(300, 150), ventana, monitor_2, BORDES)
    assert ventana.contains(_marco(cliente)) and cliente.left() >= 1920


# ------------------------------------------------------------------ diálogos Qt reales (offscreen)
def _abrir(dialogo: QDialog, medir, cerrar=None):
    datos = {}

    def tomar():
        if not dialogo.isVisible():
            QTimer.singleShot(20, tomar); return
        datos.update(medir(dialogo)); (cerrar or QDialog.reject)(dialogo)
    QTimer.singleShot(30, tomar)
    dialogo.exec()
    return datos


def _visible_en(boton, dialogo) -> bool:
    """El botón está visible y entero dentro del área del diálogo."""
    return boton.isVisible() and dialogo.rect().contains(QRect(boton.mapTo(dialogo, QPoint(0, 0)), boton.size()))


def _ventana(ancho=640, alto=520):
    v = QWidget(); v.setWindowTitle("SAVIP prueba"); v.setGeometry(40, 30, ancho, alto); v.show(); esperar(50)
    return v


def test_mensaje_largo_dentro_de_la_ventana_y_botones_visibles():
    v = _ventana(640, 520)
    texto = "Se actualizarán las proyecciones de los análisis vigentes. " * 12
    caja = QMessageBox(QMessageBox.Icon.Question, "Actualizar proyecciones con datos DANE más recientes", texto,
                       QMessageBox.StandardButton.NoButton, v)
    actualizar = caja.addButton("Actualizar proyecciones", QMessageBox.ButtonRole.AcceptRole)
    cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    caja.setDefaultButton(cancelar); caja.setEscapeButton(cancelar)
    d = _abrir(caja, lambda c: {"marco": c.frameGeometry(), "botones": [_visible_en(b, c) for b in (actualizar, cancelar)],
                                "defecto": c.defaultButton() is cancelar, "escape": c.escapeButton() is cancelar},
               cerrar=lambda c: QTest.keyClick(c, Qt.Key.Key_Escape))
    assert v.frameGeometry().contains(d["marco"]) and all(d["botones"]) and d["defecto"] and d["escape"]
    assert caja.clickedButton() is cancelar  # Esc / reject sigue siendo «Cancelar»


def test_mensaje_muy_largo_desplaza_solo_el_texto():
    v = _ventana(640, 520)
    texto = "\n".join(f"• Análisis {i}: Pavimentos asfálticos / concreto · grupo sintético · 2027-07 · 11 meses" for i in range(60))
    caja = QMessageBox(QMessageBox.Icon.Warning, "Actualizar análisis", texto, QMessageBox.StandardButton.Ok, v)
    d = _abrir(caja, lambda c: {"marco": c.frameGeometry(), "area": c.findChild(QScrollArea, "savip_desplazamiento_mensaje"),
                                "ok": c.button(QMessageBox.StandardButton.Ok)})
    assert v.frameGeometry().contains(d["marco"]) and d["area"] is not None
    assert d["area"].isAncestorOf(caja.findChild(QLabel, "qt_msgbox_label"))
    assert not d["area"].isAncestorOf(d["ok"])  # el botón nunca queda dentro del área desplazable


def test_dialogo_de_escritorio_se_adapta_a_snap_un_tercio():
    v = _ventana(640, 1000)
    d = QDialog(v); d.setWindowTitle("Actualizar criterio vigente"); d.resize(1060, 420); d.setMinimumSize(620, 460)
    lay = QVBoxLayout(d); lay.addWidget(QTextBrowser()); caja = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
    aceptar = caja.addButton("Actualizar", QDialogButtonBox.ButtonRole.AcceptRole); lay.addWidget(caja)
    caja.rejected.connect(d.reject)
    r = _abrir(d, lambda x: {"marco": x.frameGeometry(), "boton": aceptar.isVisible(), "ambito": x.property("savip_ambito_dialogo")})
    assert r["ambito"] == "ventana" and v.frameGeometry().contains(r["marco"]) and r["boton"]
    assert r["marco"].width() <= v.frameGeometry().width() - 2 * MARGEN


def test_show_se_procesa_una_sola_vez():
    class Contador(QDialog):
        n = 0

        def showEvent(self, evento):  # noqa: N802
            Contador.n += 1
            super().showEvent(evento)

    instalar_ajuste_dialogos(APP)  # segunda instalación: no duplica el filtro
    v = _ventana()
    d = Contador(v); QVBoxLayout(d).addWidget(QPushButton("Aceptar"))
    _abrir(d, lambda x: {})
    assert Contador.n == 1


# ------------------------------------------------------------------ integración con la ventana
def test_portada_refleja_el_anexo_cargado_sin_cambiar_de_seccion(tmp_path):
    from app_icociv.interfaz.ventana_principal import VentanaPrincipal
    from tests.fixtures_dane_4g import anexo_dane_sintetico
    v = VentanaPrincipal(); v.show(); APP.processEvents()
    try:
        v._cambiar_seccion(0)
        assert v.pantalla_inicio.datos["archivo"].valor.text() == "Sin archivo cargado"
        ruta = anexo_dane_sintetico(tmp_path / "anexo_sintetico.xlsx", "2026-08")
        v._archivo_cargado(v.controlador.cargar_archivo(str(ruta))); APP.processEvents()
        assert v.pantalla_inicio.datos["archivo"].valor.text() == "anexo_sintetico.xlsx"
    finally:
        v._firma_guardada = v._firma_trabajo(); v.close()


def test_ventana_ocupada_y_error_de_anexo(tmp_path):
    from app_icociv.interfaz.ventana_principal import VentanaPrincipal
    v = VentanaPrincipal(); v.resize(1100, 720); v.show(); APP.processEvents()
    try:
        v._establecer_ocupado(True, "Leyendo y validando el anexo DANE…", esqueleto="anexo")
        assert v.velo_carga.activo and v.velo_carga.property("modo") == "esqueleto" and not v.navegacion.isEnabled()
        v._establecer_ocupado(False)
        assert not v.velo_carga.activo and v.navegacion.isEnabled() and v.boton_cargar.isEnabled()
        invalido = tmp_path / "anexo_invalido.xlsx"; invalido.write_bytes(b"no es un libro de Excel")
        v._cargar_archivo(str(invalido))
        fin = time.monotonic() + 30
        while v.trabajador is not None and v.trabajador.isRunning() and time.monotonic() < fin:
            APP.processEvents(); QTest.qWait(20)
        esperar(500)
        assert not v.velo_carga.activo and not v.velo_carga.isVisible() and not v.velo_carga.animacion_activa()
        assert v.boton_cargar.isEnabled() and v.navegacion.isEnabled()
        assert v.etiqueta_estado.text() == "Ocurrió un error."
    finally:
        v._firma_guardada = v._firma_trabajo(); v.close()
