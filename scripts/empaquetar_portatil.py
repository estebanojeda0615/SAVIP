"""Arma el ZIP portatil de SAVIP a partir de dist/SAVIP (salida de PyInstaller).

Estructura del ZIP (la misma de los paquetes entregados):

    SAVIP_<VERSION>_Portatil/
        SAVIP.exe
        _internal/...
        LEEME_PORTATIL.txt

Deflate nivel 9, entradas en orden alfabetico. Verifica el CRC de todas las
entradas (testzip), escribe el SHA-256 junto al ZIP y termina con codigo 1 ante
cualquier problema.

Uso: python scripts/empaquetar_portatil.py
"""
from __future__ import annotations

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    version = (RAIZ / "VERSION").read_text(encoding="utf-8").strip()
    origen = RAIZ / "dist" / "SAVIP"
    if not (origen / "SAVIP.exe").is_file() or not (origen / "_internal").is_dir():
        print(f"ERROR: falta {origen}\\SAVIP.exe o _internal. Ejecute antes scripts\\build_exe.ps1", file=sys.stderr)
        return 1

    nombre = f"SAVIP_{version}_Portatil"
    staging = RAIZ / "release" / "staging"
    carpeta = staging / nombre
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(origen, carpeta)
    shutil.copy2(RAIZ / "packaging" / "LEEME_PORTATIL.txt", carpeta / "LEEME_PORTATIL.txt")

    zip_ruta = RAIZ / "release" / f"{nombre}_Windows_x64.zip"
    zip_ruta.unlink(missing_ok=True)
    with zipfile.ZipFile(zip_ruta, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in sorted(carpeta.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(staging).as_posix())

    with zipfile.ZipFile(zip_ruta) as zf:
        malo = zf.testzip()
        nombres = zf.namelist()
    raices = {n.split("/")[0] for n in nombres}
    esenciales = [f"{nombre}/SAVIP.exe", f"{nombre}/LEEME_PORTATIL.txt", f"{nombre}/_internal/VERSION",
                  f"{nombre}/_internal/app_icociv/datos/iccp_historico.json",
                  f"{nombre}/_internal/app_icociv/interfaz/tema/plantilla.qss"]
    faltan = [e for e in esenciales if e not in nombres]
    if malo or raices != {nombre} or faltan:
        print(f"ERROR: testzip={malo} raices={raices} faltan={faltan}", file=sys.stderr)
        return 1

    sha = hashlib.sha256(zip_ruta.read_bytes()).hexdigest()
    Path(f"{zip_ruta}.sha256").write_text(f"{sha}  {zip_ruta.name}\n", encoding="ascii")
    print(f"ZIP:      {zip_ruta}")
    print(f"Entradas: {len(nombres)} (CRC correcto; raiz unica {nombre}/)")
    print(f"Tamano:   {zip_ruta.stat().st_size} bytes")
    print(f"SHA-256:  {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
