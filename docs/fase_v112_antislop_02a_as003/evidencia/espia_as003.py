"""Fase 2A (AS-003), puerta G2: plugin de pytest que registra qué prueba ejecuta cada símbolo candidato.

Uso: PYTHONPATH=<carpeta de este archivo> ESPIA_AS003_CANDIDATOS=<grafo.json> ESPIA_AS003_SALIDA=<llamadas.jsonl>
     PYTEST_ADDOPTS="-p espia_as003" python scripts/pruebas_fase0.py esenciales

Antes de recolectar, envuelve (functools.wraps, sin cambiar el resultado) cada definición candidata —no alcanzable
desde producción según el grafo— en su módulo. Al terminar la sesión añade una línea JSON por par
(símbolo, prueba que lo ejecutó). Una prueba de la ruta productiva que no llama al símbolo deja constancia de que
el flujo real no lo atraviesa.
"""
import functools
import importlib
import json
import os

_llamadas: set[tuple[str, str]] = set()
_prueba_actual = ["<recolección>"]


def _envolver(clave, funcion):
    @functools.wraps(funcion)
    def espia(*args, **kwargs):
        _llamadas.add((clave, _prueba_actual[0]))
        return funcion(*args, **kwargs)
    return espia


def pytest_configure(config):
    grafo = json.load(open(os.environ["ESPIA_AS003_CANDIDATOS"], encoding="utf-8"))
    alcance = ("servicio_proyeccion.py", "modelos_interpretables.py", "validacion_series.py")
    for clave, v in grafo.items():
        if v["archivo"].endswith(alcance) and not v["produccion"] and v["tipo"] == "def":
            modulo, nombre = clave.split(":")
            mod = importlib.import_module(modulo)
            setattr(mod, nombre, _envolver(clave, getattr(mod, nombre)))


def pytest_runtest_setup(item):
    _prueba_actual[0] = item.nodeid


def pytest_sessionfinish(session):
    with open(os.environ["ESPIA_AS003_SALIDA"], "a", encoding="utf-8") as f:
        for clave, prueba in sorted(_llamadas):
            f.write(json.dumps({"simbolo": clave, "prueba": prueba}, ensure_ascii=False) + "\n")
