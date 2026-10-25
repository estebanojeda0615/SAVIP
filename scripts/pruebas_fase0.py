"""Fase 0 (SAVIP 1.1.2): perfiles de pruebas y su ejecución desde un clon limpio.

    python scripts/pruebas_fase0.py --listar                 # archivos y pruebas recolectadas por perfil
    python scripts/pruebas_fase0.py esenciales [args pytest] # el perfil que corre en GitHub Actions

Perfiles (clasificación y motivos: docs/fase_v112_antislop_00/01_INVENTARIO_PRUEBAS_Y_DEPENDENCIAS.md):
  esenciales  autocontenidos: solo el repositorio publicado, datos sintéticos y el lock. Incluye los Golden Masters.
  dane        integración externa: necesitan la sesión con datos DANE reales (docs/fase_4d_slider/fixtures/
              TRES_ANALISIS_REALES.json), que no se publica. Fallan en un clon limpio por diseño.
  historicas  expectativas obsoletas, artefactos de docs/ no publicados o código retirado (AS-006, AS-007).
  gui         dependen del entorno gráfico (fuentes Segoe registradas por otro módulo) o son verificación
              física en Windows (lista manual al final del inventario).
Requisitos: requirements-lock.txt + requirements-test.txt instalados con --no-deps; Windows x64."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

ESENCIALES = [
    # Golden Masters de la Fase 0
    "tests/test_fase0_golden_motor.py", "tests/test_fase0_golden_economico.py", "tests/test_fase0_golden_sesion_exportables.py",
    # Suites existentes que pasan completas en un clon limpio (caracterización de la Fase 0)
    "tests/test_alertas_boton_cerrar.py", "tests/test_atipicos_calendario.py", "tests/test_auditoria_formulas_estadisticas.py",
    "tests/test_banda_prediccion_valida.py", "tests/test_calendario_y_clasificacion_intervalo.py", "tests/test_caso_acero_reproducible.py",
    "tests/test_cierre_semantico_ps01_ps05.py", "tests/test_cobertura_cero_valida.py", "tests/test_cobertura_local_g2.py",
    "tests/test_cobertura_origen_movil.py", "tests/test_cobertura_publicada_n_menor_16.py", "tests/test_consistencia_trayectoria.py",
    "tests/test_diagnostico_residual_formal.py", "tests/test_empalme_horizonte_futuro.py", "tests/test_empalme_iccp_icociv.py",
    "tests/test_errores_extremos_descriptivos.py", "tests/test_fase_4i_j_k_actividades.py", "tests/test_fase_4i_j_reutilizacion.py",
    "tests/test_fase_4i_n_grafica_horizonte.py", "tests/test_fase_4i_p2_comparacion_consulta.py", "tests/test_fase_4i_p_sincronizacion_mae.py",
    "tests/test_fundamentacion_metodologica.py", "tests/test_horizonte_24_ic95_mae.py", "tests/test_horizonte_editable.py",
    "tests/test_imports_modulos.py", "tests/test_interaccion_fase_3c_a.py", "tests/test_interfaz_componentes.py",
    "tests/test_interfaz_tema.py", "tests/test_intervalos_prediccion.py", "tests/test_jarque_bera.py",
    "tests/test_mensajes_ljung_box.py", "tests/test_metodologia_n0_12_h24.py", "tests/test_metricas_sin_bandas.py",
    "tests/test_nmin_adversarial.py", "tests/test_origen_inicial_backtesting.py", "tests/test_pool_calendario_fourier_seasonal.py",
    "tests/test_popup_carga_empalme_y_tema_observaciones.py", "tests/test_presentacion_resultados.py", "tests/test_proyecciones_fase_2b.py",
    "tests/test_proyecciones_fase_3.py", "tests/test_proyecciones_redisenio_visual.py", "tests/test_remediacion_r2_h1_h2_h3_h7.py",
    "tests/test_resultado_horizonte_solicitado.py", "tests/test_rutas_empaquetado.py", "tests/test_semantica_temporal.py",
    "tests/test_sincronizacion_horizonte_ui.py", "tests/test_ui_navegacion_y_usabilidad.py", "tests/test_umbral_090_descriptivo.py",
    "tests/test_v112_01_esqueleto_dialogos.py", "tests/test_verificabilidad_paso_exacto.py", "tests/test_vocabulario_cobertura.py",
    "tests/test_vocabulario_vc.py",
]
DANE = [
    "tests/test_ajuste_tooltips_pantalla_dividida.py", "tests/test_base_valor_presupuestal_fase_4e_a.py",
    "tests/test_fase_4g_historial_dane_fechas.py", "tests/test_fase_4i_a_deshacer_historial_pegado.py",
    "tests/test_fase_4i_a_v4_grafica_pegado_progreso.py", "tests/test_fase_4i_b_progreso_grafica_auditoria.py",
    "tests/test_fase_4i_c_factor_grafica_carga.py", "tests/test_fase_4i_d_legados_factor.py", "tests/test_fase_4i_d_verificacion_ventana.py",
    "tests/test_fase_4i_e_tema_rendimiento.py", "tests/test_fase_4i_g_sesiones.py", "tests/test_fase_4i_i_responsive_borrador.py",
    "tests/test_fase_4i_j_fecha_comun.py", "tests/test_fase_4i_tabla_editable.py", "tests/test_importes_presupuestales_fase_4e.py",
    "tests/test_microcorreccion_fase_4d_c.py", "tests/test_referencia_economica_fase_4d_b.py",
    "tests/test_slider_comparacion_historica_fase_4d.py", "tests/test_switch_tema_sesion_dane.py", "tests/test_v112_01b_indicadores_sesiones.py",
]
GUI = ["tests/test_v112_01c_dialogos_legibles.py"]
#: Se ejecutan en su propio proceso: al importarse apagan interruptores globales (sombras, movimiento) y,
#: recolectados junto a los demás, hacen fallar test_interfaz_componentes::test_sombras_… (contaminación heredada).
AISLADOS = {"tests/test_proyecciones_redisenio_visual.py"}
#: Verificación física en Windows que ninguna prueba automática cubre (se marca a mano).
GUI_MANUAL = [
    "Equipo sin Python instalado: extraer el ZIP del Release y abrir SAVIP.exe",
    "Escalas de pantalla 125 % y 150 %", "Segundo monitor y mover la ventana entre monitores",
    "Snap de Windows con teclado (Win + flechas) y diálogo de cierre en un tercio de pantalla",
    "Revisión visual completa de temas claro/oscuro, gráfica y diálogos largos con fuentes reales",
]


def historicas() -> list[str]:
    asignados = set(ESENCIALES) | set(DANE) | set(GUI)
    return sorted(p.relative_to(RAIZ).as_posix() for p in (RAIZ / "tests").glob("test_*.py") if p.relative_to(RAIZ).as_posix() not in asignados)


PERFILES = {"esenciales": ESENCIALES, "dane": DANE, "historicas": historicas(), "gui": GUI}


def _entorno() -> dict:
    return {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}


def listar() -> int:
    total = 0
    for nombre, archivos in PERFILES.items():
        r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                            "--continue-on-collection-errors", *archivos], cwd=RAIZ, env=_entorno(), capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        pruebas = sum(1 for linea in r.stdout.splitlines() if "::" in linea)
        errores = len(re.findall(r"^ERROR ", r.stdout, re.M))
        total += pruebas
        print(f"{nombre:<11} {len(archivos):>3} archivos  {pruebas:>4} pruebas recolectadas  {errores} errores de recolección")
    print(f"{'total':<11} {sum(map(len, PERFILES.values())):>3} archivos  {total:>4} pruebas")
    print("gui (manual): " + "; ".join(GUI_MANUAL))
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    if argv[0] == "--listar":
        return listar()
    perfil, extra = argv[0], argv[1:]
    if perfil not in PERFILES:
        sys.exit(f"Perfil desconocido: {perfil}. Opciones: {', '.join(PERFILES)}")
    faltan = [a for a in PERFILES[perfil] if not (RAIZ / a).exists()]
    if faltan:
        sys.exit(f"Archivos de prueba inexistentes en el perfil {perfil}: {faltan}")
    opciones = ["--continue-on-collection-errors"] if perfil == "historicas" else []
    juntos = [a for a in PERFILES[perfil] if a not in AISLADOS]
    aislados = [a for a in PERFILES[perfil] if a in AISLADOS]
    codigos = []
    for grupo, sufijo in ((juntos, ""), (aislados, "_aislados")):
        if grupo:
            argumentos = [a.replace(".xml", f"{sufijo}.xml") if a.startswith("--junitxml") else a for a in extra]
            codigos.append(subprocess.run([sys.executable, "-W", "ignore", "-m", "pytest", "-p", "no:cacheprovider", "-q", *opciones,
                                           *grupo, *argumentos], cwd=RAIZ, env=_entorno()).returncode)
    return max(codigos)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
