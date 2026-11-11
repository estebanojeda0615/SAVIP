"""Plugin pytest PASIVO (diagnóstico G2): adjunta registros a la ventana REAL creada por la prueba, sin cambiar su
lógica ni el orden de los slots de producción (los registros se conectan después de los de producción).

Uso: PYTHONPATH=<dir de este archivo> TRAZA_3CA=<archivo.jsonl> pytest -p plugin_traza_3ca <nodo>
Registra con tiempo monotónico: resizeEvent (vía filtro de eventos), la creación de cada QSignalSpy de la prueba, _temporizador_ancho.timeout (con ancho, modo
compacto y estado de contracción DESPUÉS del ajuste de producción), boton_contraer.clicked y contraccion_cambiada
(con la pila de llamadas de app_icociv/tests que la originó). Al terminar cada prueba escribe el registro y el resultado.
"""
import json
import os
import time
import traceback
from pathlib import Path

import pytest

T0 = time.monotonic()
REGISTRO: list[dict] = []
_ULTIMO_RESIZE = {"t": None}


def _ms():
    return round((time.monotonic() - T0) * 1000, 2)


def _origen():
    pila = traceback.extract_stack()[:-2]
    return [f"{Path(f.filename).name}:{f.lineno}:{f.name}" for f in pila
            if "app_icociv" in f.filename or "test_interaccion" in f.filename][-6:]


_APLICADO = {"ok": False}


def pytest_runtest_setup(item):
    """Se aplica tras importar el módulo de prueba (que fija QSettings y QT_QPA_PLATFORM antes de importar la app)."""
    if _APLICADO["ok"]:
        return
    _APLICADO["ok"] = True
    from PySide6.QtCore import QEvent, QObject

    from app_icociv.interfaz import ventana_principal as vp

    class _Filtro(QObject):
        def eventFilter(self, obj, ev):  # noqa: N802
            if ev.type() == QEvent.Type.Resize:
                _ULTIMO_RESIZE["t"] = time.monotonic()
                REGISTRO.append({"t_ms": _ms(), "evento": "resizeEvent", "tam": [ev.size().width(), ev.size().height()]})
            return False  # no consume el evento

    original_init = vp.VentanaPrincipal.__init__

    def init_con_registro(self, *a, **k):
        original_init(self, *a, **k)
        self._filtro_traza_3ca = _Filtro()
        self.installEventFilter(self._filtro_traza_3ca)
        nav = self.navegacion

        def desde_resize():
            return None if _ULTIMO_RESIZE["t"] is None else round((time.monotonic() - _ULTIMO_RESIZE["t"]) * 1000, 2)

        nav.contraccion_cambiada.connect(lambda c: REGISTRO.append(
            {"t_ms": _ms(), "evento": "contraccion_cambiada", "arg": c, "desde_resize_ms": desde_resize(), "origen": _origen()}))
        nav.boton_contraer.clicked.connect(lambda *_: REGISTRO.append({"t_ms": _ms(), "evento": "boton_contraer.clicked"}))
        self._temporizador_ancho.timeout.connect(lambda: REGISTRO.append(
            {"t_ms": _ms(), "evento": "_temporizador_ancho.timeout", "desde_resize_ms": desde_resize(), "ancho": self.width(),
             "modo_compacto_tras_ajuste": self._modo_compacto, "contraida_tras_ajuste": nav.esta_contraida()}))

    vp.VentanaPrincipal.__init__ = init_con_registro

    # Momento de creación de cada QSignalSpy de la prueba (delimita la ventana observada por la aserción).
    modulo = item.module
    spy_original = modulo.QSignalSpy

    def spy_con_registro(senal, *a, **k):
        REGISTRO.append({"t_ms": _ms(), "evento": "QSignalSpy_creado", "senal": repr(senal)[:80],
                         "desde_resize_ms": None if _ULTIMO_RESIZE["t"] is None else round((time.monotonic() - _ULTIMO_RESIZE["t"]) * 1000, 2)})
        return spy_original(senal, *a, **k)

    modulo.QSignalSpy = spy_con_registro


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    informe = resultado.get_result()
    if informe.when == "call":
        destino = os.environ.get("TRAZA_3CA")
        if destino:
            with open(destino, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps({"tipo": "resultado", "nodo": item.nodeid, "resultado": informe.outcome,
                                    "error": (str(call.excinfo.value)[:300] if call.excinfo else None)}, ensure_ascii=False) + "\n")
                for r in REGISTRO:
                    f.write(json.dumps({"tipo": "traza", **r}, ensure_ascii=False) + "\n")
        REGISTRO.clear()
