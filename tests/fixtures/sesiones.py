"""Fase 1A (AS-007): sesiones SINTÉTICAS de desarrollo que antes se leían de docs/ (no publicado).

Están en tests/fixtures/sesiones_sinteticas/*.json.gz; su procedencia y la única transformación aplicada están
en el README de esa carpeta: rutas locales de archivo_excel reducidas a una relativa docs\\..., inexistente en un clon."""

import gzip
import json
import tempfile
from functools import lru_cache
from pathlib import Path

CARPETA = Path(__file__).resolve().parent / "sesiones_sinteticas"


@lru_cache(maxsize=None)
def _texto(nombre: str) -> str:
    return gzip.decompress((CARPETA / f"{nombre}.json.gz").read_bytes()).decode("utf-8")


def cargar(nombre: str) -> dict:
    """Copia nueva en cada llamada: las pruebas pueden modificarla sin afectar a otras."""
    return json.loads(_texto(nombre))


def ruta_temporal(nombre: str) -> Path:
    """La sesión escrita como archivo JSON en una carpeta temporal (para pruebas que la abren desde disco)."""
    ruta = Path(tempfile.mkdtemp(prefix="savip_sesion_")) / f"{nombre}.json"
    ruta.write_text(_texto(nombre), encoding="utf-8")
    return ruta
