"""Fase 1A (AS-007): carpeta para lo que las pruebas escribían en docs/ (capturas, JSON de evidencia, ajustes de Qt).

Vive en el temporal del sistema: las pruebas ya no escriben en el árbol del código ni necesitan docs/ publicado.
Las lecturas de evidencia histórica (copias `respaldo_inicio/*.bak`, salidas ANTES_*) siguen apuntando a docs/ y
se documentan como dependencias históricas en docs/fase_v112_antislop_01a_pruebas/02."""

import tempfile
from pathlib import Path

RAIZ = Path(tempfile.gettempdir()) / "savip_pruebas_salidas"


def carpeta_salida(nombre: str) -> Path:
    ruta = RAIZ / nombre
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta
