"""Fase 0: escribe los Golden Masters en ``golden/`` UNA sola vez, sobre el código congelado.

Uso (desde la raíz del repositorio, con el entorno de requirements-lock.txt + requirements-test.txt):

    python -m tests.fixtures.fase0.generar_golden

Se niega a ejecutarse si el código productivo difiere del commit de referencia o si ya existe algún
golden: los esperados no se actualizan solos. Regenerarlos exige una decisión explícita y documentada
(borrar los archivos a mano en un commit propio que explique el cambio de comportamiento aceptado)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ = Path(__file__).resolve().parents[3]
COMMIT_REFERENCIA = "66725293f304426ae6edf144b8f4dadbcbeefe10"  # develop/v1.1.2 = tag v1.1.2-rc.1
PRODUCTIVO = ("app_icociv", "aplicacion.py", "packaging", "scripts", ":!scripts/pruebas_fase0.py", "VERSION",
              "requirements.txt", "requirements-lock.txt", "requirements-build.txt")
PAQUETES = ("numpy", "pandas", "scipy", "statsmodels", "scikit-learn", "PySide6", "openpyxl", "python-docx", "reportlab", "pypdf", "pytest")


def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(RAIZ), *args], capture_output=True, text=True, check=True).stdout.strip()


def _escribir(ruta: Path, datos) -> None:
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    from tests.fixtures.fase0 import captura, captura_gui, generadores

    cambios = _git("diff", "--name-only", COMMIT_REFERENCIA, "--", *PRODUCTIVO)
    if cambios:
        sys.exit(f"BLOQUEO: el código productivo difiere de {COMMIT_REFERENCIA[:7]}:\n{cambios}")
    existentes = sorted(p.name for p in captura.GOLDEN.glob("*.json"))
    if existentes:
        sys.exit(f"BLOQUEO: ya existen golden ({', '.join(existentes)}); no se sobrescriben.")
    captura.GOLDEN.mkdir(parents=True, exist_ok=True)

    archivos = {
        "motor.json": lambda: {"escenarios": {n: captura.capturar_motor(n) for n in generadores.ESCENARIOS_MOTOR},
                               "rechazos": captura.capturar_rechazos()},
        "economico.json": captura.capturar_economico,
    }
    for nombre, funcion in archivos.items():
        print("generando", nombre, flush=True)
        _escribir(captura.GOLDEN / nombre, funcion())
    print("generando sesion_exportables.json", flush=True)
    with tempfile.TemporaryDirectory(prefix="savip_golden_") as tmp:
        escenario = captura_gui.escenario(Path(tmp))
    _escribir(captura.GOLDEN / "sesion_exportables.json", escenario)

    metadatos = {
        "commit_referencia": COMMIT_REFERENCIA,
        "arbol_app_icociv": _git("rev-parse", f"{COMMIT_REFERENCIA}:app_icociv"),
        "version_savip": (RAIZ / "VERSION").read_text(encoding="utf-8").strip(),
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(), "sistema": platform.platform(),
        "paquetes": {p: version(p) for p in PAQUETES},
        "tolerancia_flotantes": {"rel_tol": captura.REL_TOL, "abs_tol": captura.ABS_TOL},
        "archivos": sorted([*archivos, "sesion_exportables.json"]),
    }
    _escribir(captura.GOLDEN / "metadatos.json", metadatos)
    print("listo:", captura.GOLDEN)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
