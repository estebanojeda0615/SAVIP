"""Control SINTÉTICO (no es una reproducción del fallo real): demuestra de forma determinista el mecanismo candidato.

Secuencia: ventana a 1920 px (modo normal) -> resize a 1100 px (arranca el temporizador de ancho de 60 ms) ->
contracción manual (como el test) -> espera BLOQUEANTE de N ms sin procesar eventos (simula pasos del test que tardan
más que el temporizador sin pasar por el bucle de eventos) -> spy -> clic en «contraer/expandir» -> processEvents().

Si el temporizador vence dentro de esa ventana, `_adaptar_ancho` entra en modo compacto y, como la navegación acaba de
expandirse por el clic, vuelve a contraerla: una 2.ª emisión de `contraccion_cambiada` no causada por el clic.
Con el grupo de control (sin espera, o procesando eventos con qWait ANTES del spy) no debe aparecer.
Control POSITIVO del parche: mismo bloqueo, pero con la espera por condición del test antes del spy -> spy=1.

Uso: python control_sintetico_3ca.py <raiz_repo>
"""
import os
import sys
import tempfile
import time
from pathlib import Path

raiz = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(raiz))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
runtime = Path(tempfile.mkdtemp(prefix="control3ca_"))
os.environ["MPLCONFIGDIR"] = str(runtime / "matplotlib")
from PySide6.QtCore import QSettings, Qt  # noqa: E402

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
for scope in (QSettings.Scope.UserScope, QSettings.Scope.SystemScope):
    QSettings.setPath(QSettings.Format.IniFormat, scope, str(runtime / "settings"))
from PySide6.QtTest import QSignalSpy, QTest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app_icociv.interfaz.animaciones import establecer_movimiento_reducido  # noqa: E402
from app_icociv.interfaz.ventana_principal import VentanaPrincipal  # noqa: E402

app = QApplication.instance() or QApplication([])


def caso(nombre, bloqueo_ms=0, qwait_ms=0, con_espera_del_parche=False):
    v = VentanaPrincipal()
    establecer_movimiento_reducido(True)
    try:
        v.resize(1920, 1080); v.show(); app.processEvents(); QTest.qWait(150)  # estado estable, modo normal
        assert not v._modo_compacto
        clicks = []
        v.navegacion.boton_contraer.clicked.connect(lambda *_: clicks.append(1))
        v.resize(1100, 700)                                 # arranca el temporizador de 60 ms
        v.navegacion.establecer_contraccion(True)           # preparación del test
        if qwait_ms:
            QTest.qWait(qwait_ms)                           # procesa eventos: el temporizador vence ANTES del spy
        if bloqueo_ms:
            time.sleep(bloqueo_ms / 1000)                   # NO procesa eventos: el temporizador queda vencido y pendiente
        if con_espera_del_parche:
            # Misma lógica que tests/test_interaccion_fase_3c_a.py::esperar_ajuste_de_ancho (control POSITIVO del parche):
            # un QTimer vencido pero sin despachar sigue isActive() hasta que el bucle procesa su evento; la espera lo despacha.
            fin = time.monotonic() + 1.0
            while v._temporizador_ancho.isActive() and time.monotonic() < fin:
                QTest.qWait(5)
            assert not v._temporizador_ancho.isActive()
        spy = QSignalSpy(v.navegacion.contraccion_cambiada)
        QTest.mouseClick(v.navegacion.boton_contraer, Qt.MouseButton.LeftButton)
        app.processEvents()
        print(f"{nombre:38} clicked={len(clicks)} spy={spy.count()} args={[spy.at(i) for i in range(spy.count())]} "
              f"contraida_final={v.navegacion.esta_contraida()} modo_compacto={v._modo_compacto}")
    finally:
        v.close()


caso("control: sin espera")
caso("control: qWait(100) antes del spy", qwait_ms=100)
caso("mecanismo: bloqueo 100 ms sin eventos", bloqueo_ms=100)
caso("mecanismo: bloqueo 100 ms (repetición)", bloqueo_ms=100)
caso("parche: bloqueo 100 ms + espera del parche", bloqueo_ms=100, con_espera_del_parche=True)
caso("parche: bloqueo 100 ms + espera (repetición)", bloqueo_ms=100, con_espera_del_parche=True)
