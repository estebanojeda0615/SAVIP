"""Sonda G2 (externa, diagnóstica): repite la secuencia de test_a con instrumentación reversible y registra, para cada
clic del botón de contracción, todas las emisiones de `contraccion_cambiada` con su ORIGEN (pila de llamadas), el estado
del temporizador de ancho de la ventana (`_temporizador_ancho`) y el tiempo monotónico desde el último resize.

No modifica producción: usa `wraps`/conexiones adicionales que no cambian el orden de los eventos (los slots de
producción conservan su orden de conexión; los registros se conectan después) y deja todo como estaba al terminar.

Uso: python sonda_3ca.py <raiz_repo> <salida.jsonl> [--retraso-ms N]
  --retraso-ms N  (control): QTest.qWait(N) antes del clic de contracción (procesa eventos: deja vencer el temporizador
                  ANTES de crear el spy).
  --bloqueo-ms N  (control sintético): time.sleep(N/1000) antes de crear el spy, SIN procesar eventos: simula un paso
                  lento y deja el temporizador vencido pero sin despachar hasta el processEvents posterior al clic.
  Por defecto 0/0 = secuencia idéntica al test.
"""
import json
import os
import sys
import time
import traceback
from pathlib import Path

raiz = Path(sys.argv[1]).resolve()
salida = Path(sys.argv[2])
retraso = int(sys.argv[sys.argv.index("--retraso-ms") + 1]) if "--retraso-ms" in sys.argv else 0
bloqueo = int(sys.argv[sys.argv.index("--bloqueo-ms") + 1]) if "--bloqueo-ms" in sys.argv else 0
sys.path.insert(0, str(raiz))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import tempfile  # noqa: E402

runtime = Path(tempfile.mkdtemp(prefix="sonda3ca_"))
os.environ["MPLCONFIGDIR"] = str(runtime / "matplotlib")
from PySide6.QtCore import QPoint, QSettings, Qt  # noqa: E402

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
for scope in (QSettings.Scope.UserScope, QSettings.Scope.SystemScope):
    QSettings.setPath(QSettings.Format.IniFormat, scope, str(runtime / "settings"))
from PySide6.QtGui import QFontDatabase  # noqa: E402
from PySide6.QtTest import QSignalSpy, QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402

from app_icociv.interfaz.animaciones import establecer_movimiento_reducido  # noqa: E402
from app_icociv.interfaz.ventana_principal import VentanaPrincipal  # noqa: E402

app = QApplication.instance() or QApplication([])
for name in ("segoeui.ttf", "segoeuib.ttf", "seguisb.ttf"):
    QFontDatabase.addApplicationFont("C:/Windows/Fonts/" + name)
SIZES = ((1100, 700), (1366, 768), (1920, 1080))
T0 = time.monotonic()
registro = []
estado = {"ultimo_resize": None, "fase": "inicio"}


def ms(t=None):
    return round(((t or time.monotonic()) - T0) * 1000, 2)


def origen():
    pila = traceback.extract_stack()[:-2]
    utiles = [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in pila if "app_icociv" in f.filename or "sonda_3ca" in f.filename]
    return utiles[-6:]


def settle(v):
    v.show()
    v.activateWindow()
    app.processEvents()
    QTest.qWait(20)


def main():
    load, abrir, guardar = Mock(), Mock(), Mock()
    with patch.object(VentanaPrincipal, "seleccionar_archivo", lambda self: load()), \
         patch.object(VentanaPrincipal, "abrir_sesion", lambda self: abrir()), \
         patch.object(VentanaPrincipal, "guardar_sesion_actual", lambda self: guardar()):
        v = VentanaPrincipal()
        establecer_movimiento_reducido(True)
        nav = v.navegacion
        # Registros conectados DESPUÉS de los de producción: no alteran el orden de los slots existentes.
        nav.contraccion_cambiada.connect(lambda c: registro.append(
            {"t_ms": ms(), "evento": "contraccion_cambiada", "arg": c, "fase": estado["fase"],
             "desde_resize_ms": None if estado["ultimo_resize"] is None else round((time.monotonic() - estado["ultimo_resize"]) * 1000, 2),
             "origen": origen()}))
        nav.boton_contraer.clicked.connect(lambda *_: registro.append({"t_ms": ms(), "evento": "boton_contraer.clicked", "fase": estado["fase"]}))
        v._temporizador_ancho.timeout.connect(lambda: registro.append(
            {"t_ms": ms(), "evento": "_temporizador_ancho.timeout", "fase": estado["fase"], "ancho": v.width(),
             "modo_compacto_antes": v._modo_compacto, "contraida": nav.esta_contraida()}))
        original_resize = v.resizeEvent

        def resize_espia(evento):
            estado["ultimo_resize"] = time.monotonic()
            registro.append({"t_ms": ms(), "evento": "resizeEvent", "fase": estado["fase"],
                             "tam": [evento.size().width(), evento.size().height()]})
            original_resize(evento)
        v.resizeEvent = resize_espia
        actions = ((v.boton_cargar, load), (v.boton_abrir_sesion, abrir), (v.boton_guardar_sesion, guardar))
        resultados = []
        try:
            for theme in ("claro", "oscuro"):
                v._aplicar_tema(theme, persistir=False)
                for size in SIZES:
                    v.resize(*size)
                    for it in range(3):
                        estado["fase"] = f"{theme}|{size[0]}x{size[1]}|it{it}|prep"
                        nav.establecer_contraccion(True)
                        settle(v)
                        for b, method in actions:
                            b.setEnabled(True)
                            QTest.mouseClick(b, Qt.MouseButton.LeftButton)
                            b.setFocus()
                            app.processEvents()
                            QTest.keyClick(b, Qt.Key.Key_Space)
                            b.setEnabled(False)
                            QTest.mouseClick(b, Qt.MouseButton.LeftButton)
                            b.setEnabled(True)
                        QTest.mouseClick(nav.botones[1], Qt.MouseButton.LeftButton)
                        if retraso:
                            QTest.qWait(retraso)
                        if bloqueo:
                            time.sleep(bloqueo / 1000)
                        estado["fase"] = f"{theme}|{size[0]}x{size[1]}|it{it}|toggle"
                        timer_activo = v._temporizador_ancho.isActive()
                        restante = v._temporizador_ancho.remainingTime()
                        desde = None if estado["ultimo_resize"] is None else round((time.monotonic() - estado["ultimo_resize"]) * 1000, 2)
                        spy = QSignalSpy(nav.contraccion_cambiada)
                        QTest.mouseClick(nav.boton_contraer, Qt.MouseButton.LeftButton)
                        app.processEvents()
                        resultados.append({"fase": estado["fase"], "spy_count": spy.count(),
                                           "contraida_final": nav.esta_contraida(), "timer_activo_antes_clic": timer_activo,
                                           "timer_restante_ms": restante, "desde_resize_ms": desde,
                                           "modo_compacto": v._modo_compacto, "ancho": v.width()})
        finally:
            v.close()
    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        for r in resultados:
            f.write(json.dumps({"tipo": "resultado", **r}, ensure_ascii=False) + "\n")
        for r in registro:
            f.write(json.dumps({"tipo": "traza", **r}, ensure_ascii=False) + "\n")
    malos = [r for r in resultados if r["spy_count"] != 1 or r["contraida_final"]]
    print(f"clics={len(resultados)} anomalos={len(malos)}")
    for r in malos:
        print("  ANOMALO", r)


if __name__ == "__main__":
    main()
