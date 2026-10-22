"""No reemplazar un exportable existente hasta terminar el archivo nuevo."""
import os
import tempfile
from pathlib import Path


def guardar_atomico(ruta,escribir):
    destino=Path(ruta);destino.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destino.parent,suffix=destino.suffix,delete=False) as archivo:
        temporal=Path(archivo.name)
    try:
        escribir(temporal)
        os.replace(temporal,destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino
