"""Lector mínimo, de solo lectura, del archivo PyInstaller embebido en SAVIP.exe (CArchive + PYZ).

Uso: python leer_pyinstaller.py <SAVIP.exe> <salida_dir>
Escribe en <salida_dir>:
  - carchive_toc.txt  (entradas del CArchive: nombre, tipo, tamaños)
  - pyz/<modulo>.code  (código marshal de cada módulo del PYZ, descomprimido; no se ejecuta)
  - pyz_toc.txt        (módulo, es_paquete, tamaño)
  - pyinstaller.txt    (versión de Python declarada por el PYZ y por el cookie)
No modifica el EXE.
"""
import marshal
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b"MEI\014\013\012\013\016"


def leer_carchive(datos: bytes):
    pos = datos.rfind(MAGIC)
    assert pos >= 0, "no hay cookie de PyInstaller"
    # Cookie PyInstaller >= 3: magic(8) len_pkg(i) toc_off(i) toc_len(i) pyver(i) pylib(64s)
    magic, len_pkg, toc_off, toc_len, pyver, pylib = struct.unpack("!8sIIIi64s", datos[pos:pos + 88])
    inicio = pos + 88 - len_pkg
    toc = []
    p = inicio + toc_off
    fin = p + toc_len
    while p < fin:
        (tam_entrada,) = struct.unpack("!i", datos[p:p + 4])
        off, clen, ulen, cflag, tipo = struct.unpack("!iiiBc", datos[p + 4:p + 18])
        nombre = datos[p + 18:p + tam_entrada].rstrip(b"\0").decode("utf-8")
        toc.append((nombre, tipo.decode(), off + inicio, clen, ulen, cflag))
        p += tam_entrada
    return toc, pyver, pylib.rstrip(b"\0").decode()


def leer_pyz(blob: bytes):
    assert blob[:4] == b"PYZ\0", blob[:4]
    pyc_magic = blob[4:8]
    (toc_off,) = struct.unpack("!i", blob[8:12])
    toc = marshal.loads(blob[toc_off:])
    entradas = toc.items() if isinstance(toc, dict) else toc
    mods = {}
    for nombre, info in entradas:
        tipo, off, longitud = info
        crudo = zlib.decompress(blob[off:off + longitud]) if longitud else b""  # tipo 3: paquete de espacio de nombres, sin código
        mods[nombre] = (tipo, crudo)
    return pyc_magic, mods


def main(exe: str, salida: str):
    datos = Path(exe).read_bytes()
    out = Path(salida)
    (out / "pyz").mkdir(parents=True, exist_ok=True)
    toc, pyver, pylib = leer_carchive(datos)
    with open(out / "carchive_toc.txt", "w", encoding="utf-8", newline="\n") as f:
        for nombre, tipo, off, clen, ulen, cflag in toc:
            f.write(f"{tipo}\t{nombre}\t{clen}\t{ulen}\t{cflag}\n")
    pyz = [e for e in toc if e[1] == "z"]
    assert len(pyz) == 1, pyz
    _, _, off, clen, _, _ = pyz[0]
    pyc_magic, mods = leer_pyz(datos[off:off + clen])
    with open(out / "pyz_toc.txt", "w", encoding="utf-8", newline="\n") as f:
        for nombre, (tipo, crudo) in sorted(mods.items()):
            f.write(f"{nombre}\t{tipo}\t{len(crudo)}\n")
            (out / "pyz" / f"{nombre}.code").write_bytes(crudo)
    import importlib.util
    with open(out / "pyinstaller.txt", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"cookie_pyver={pyver} pylib={pylib}\n")
        f.write(f"pyz_pyc_magic={pyc_magic.hex()} interprete_actual={importlib.util.MAGIC_NUMBER.hex()}\n")
        f.write(f"modulos_pyz={len(mods)} app_icociv={sum(1 for m in mods if m.startswith('app_icociv'))}\n")
    print(open(out / "pyinstaller.txt", encoding="utf-8").read())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
