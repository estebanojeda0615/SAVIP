"""Fase 0 (SAVIP 1.1.2): perfiles de pruebas y su ejecución desde un clon limpio.

    python scripts/pruebas_fase0.py --listar                 # archivos y pruebas recolectadas por perfil
    python scripts/pruebas_fase0.py esenciales [args pytest] # el perfil que corre en GitHub Actions

Perfiles (clasificación y motivos: docs/fase_v112_antislop_00/01_INVENTARIO_PRUEBAS_Y_DEPENDENCIAS.md):
  esenciales  autocontenidos: solo el repositorio publicado, datos sintéticos y el lock. Incluye los Golden Masters.
  dane        integración externa con datos DANE reales. Vacío desde la Fase 1A: la sesión que se creía real era
              sintética y está publicada en tests/fixtures/sesiones_sinteticas.
  historicas  expectativas obsoletas, artefactos de docs/ no publicados o código retirado (AS-006, AS-007).
  gui         dependen del entorno gráfico (fuentes Segoe registradas por otro módulo) o son verificación
              física en Windows (lista manual al final del inventario).
Requisitos: requirements-lock.txt + requirements-test.txt instalados con --no-deps; Windows x64."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

ESENCIALES = [
    # Golden Masters de la Fase 0
    "tests/test_fase0_golden_motor.py", "tests/test_fase0_golden_economico.py", "tests/test_fase0_golden_sesion_exportables.py",
    # Fase 1A (AS-006): contrato del selector vigente _seleccionar_modelo_rectangular (+ AS-001 como xfail estricto)
    "tests/test_fase1a_selector_rectangular.py",
    # Fase 2C (AS-003): contratos de la ruta vigente que hoy solo se afirman sobre el subsistema heredado
    "tests/test_fase2c_contratos_vigentes.py",
    # AS-007: contratos P0-C/P0-E vigentes que solo afirmaba el script r3 (no recolectado)
    "tests/test_as007_contratos_p0c_vigentes.py",
    # Fase 1A (AS-007): ejecutable sin docs/ al regenerar el anexo sintético (4/4 en clon limpio)
    "tests/test_fase_4i_h_encabezado.py",
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
    # Fase 1A (AS-007): antes «dane» o históricas; pasan completas en clon limpio con los fixtures sintéticos
    # trasladados a tests/fixtures (sesiones_sinteticas, anexo_slider_4d) y, en 3 de ellas, la expectativa del
    # factor actualizada a la regla 4I-C (base_valor_4e_a, microcorreccion_4d_c, 4g_historial).
    "tests/test_ajuste_tooltips_pantalla_dividida.py", "tests/test_base_valor_presupuestal_fase_4e_a.py",
    "tests/test_componente_empalme_fase_4b_a.py", "tests/test_empalme_fase_4c.py", "tests/test_excel_formulas_principales.py",
    "tests/test_fase_4a_d.py", "tests/test_fase_4g_historial_dane_fechas.py", "tests/test_fase_4i_a_deshacer_historial_pegado.py",
    "tests/test_fase_4i_a_v4_grafica_pegado_progreso.py", "tests/test_fase_4i_b_progreso_grafica_auditoria.py",
    "tests/test_fase_4i_c_factor_grafica_carga.py", "tests/test_fase_4i_d_legados_factor.py", "tests/test_fase_4i_d_verificacion_ventana.py",
    "tests/test_fase_4i_g_sesiones.py", "tests/test_fase_4i_i_responsive_borrador.py", "tests/test_fase_4i_j_fecha_comun.py",
    "tests/test_fase_4i_tabla_editable.py", "tests/test_historial_empalme_fase_4b.py", "tests/test_importes_presupuestales_fase_4e.py",
    "tests/test_microcorreccion_fase_4d_c.py", "tests/test_referencia_economica_fase_4d_b.py", "tests/test_switch_tema_sesion_dane.py",
    "tests/test_v112_01b_indicadores_sesiones.py",
]
#: Fase 1A: vacío. Ninguna prueba necesita datos DANE reales: la «sesión DANE real» de la Fase 0
#: (TRES_ANALISIS_REALES.json) era sintética y ya está en tests/fixtures/sesiones_sinteticas.
DANE: list[str] = []
GUI =["tests/test_v112_01c_dialogos_legibles.py"]  # anchos offscreen sin fuentes Segoe registradas
#: Pruebas sueltas con carreras de tiempo heredadas: salen del perfil esencial (--deselect) y van al perfil gui.
GUI_NODOS = [
    # Comprueba el layout tras UN processEvents(), pero la ventana lo adapta con un temporizador de 60 ms
    # (resizeEvent -> _temporizador_ancho): falló en una corrida local conjunta y en el runner de GitHub.
    "tests/test_proyecciones_redisenio_visual.py::test_layout_adaptable_y_temas_sin_cambiar_entrada",
    # Guarda justo tras proyectar sin esperar a que termine el indicador de carga; en el runner (más lento)
    # guardar_sesion_actual devolvió False sin escribir (causa probable: regla 01B de no guardar durante una carga).
    "tests/test_proyecciones_fase_2b.py::test_integracion_sesion_con_excel_y_trabajadores_reales",
    # Fase 1A: expectativa del factor actualizada a la regla 4I-C; ya no necesita docs/. Pasa 3/3 aislada, pero
    # falló 1 de 4 al correr junto a otras suites (guardar sin esperar a que termine la carga): misma carrera que la anterior.
    "tests/test_fase_4g_historial_dane_fechas.py::test_B_sesion_agosto_con_dane_octubre_invariante_actualizacion_y_restauracion",
    # Fase 1A: pasan en local (copia limpia, cd59281) pero fallaron en el runner (run 40373565637): la primera por la
    # misma carrera de guardado tras una carga (guardar_sesion_actual -> False); la segunda cuenta >= 10 muestras del
    # indicador durante un guardado lento simulado y el runner, más lento, tomó 3.
    "tests/test_fase_4i_j_fecha_comun.py::test_presupuesto_fecha_comun_excepcion_exportacion_y_reanalisis_dane",
    "tests/test_v112_01b_indicadores_sesiones.py::test_T01B_5_ctrl_s_ruta_conocida_lento_exito_solo_tras_persistir",
]
#: Fase 1A: cada archivo corre en su propio proceso (ver ejecutar_por_archivo). Motivo documentado: p. ej.
#: test_proyecciones_redisenio_visual apaga las sombras globales AL IMPORTARSE y lo importan otras suites, de modo
#: que recolectado junto a ellas test_interfaz_componentes::test_sombras_… falla (contaminación heredada).
TIEMPO_MAXIMO_POR_ARCHIVO = 1200
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


PERFILES = {"esenciales": ESENCIALES, "dane": DANE, "historicas": historicas(), "gui": GUI + GUI_NODOS}


def opciones(perfil: str) -> list[str]:
    """Cada prueba en un solo perfil: los nodos movidos se deseleccionan en el perfil de su archivo de origen."""
    propios = set(PERFILES[perfil]); archivos = {a for a in propios if "::" not in a}
    movidos = [f"--deselect={n}" for n in GUI_NODOS if n not in propios and n.split("::")[0] in archivos]
    return (["--continue-on-collection-errors"] if perfil == "historicas" else []) + movidos


def _entorno() -> dict:
    return {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}


def listar() -> int:
    total = 0
    for nombre, archivos in PERFILES.items():
        if not archivos:  # pytest sin rutas recolectaría toda la carpeta
            print(f"{nombre:<11}   0 entradas     0 pruebas"); continue
        r = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
                            "--continue-on-collection-errors", *opciones(nombre), *archivos], cwd=RAIZ, env=_entorno(), capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        pruebas = sum(1 for linea in r.stdout.splitlines() if "::" in linea)
        errores = len(re.findall(r"^ERROR ", r.stdout, re.M))
        total += pruebas
        print(f"{nombre:<11} {len(archivos):>3} entradas  {pruebas:>4} pruebas  {errores} errores de recolección")
    print(f"{'total':<11} {total:>4} pruebas")
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
    if not PERFILES[perfil]:
        print(f"El perfil {perfil} está vacío: no hay pruebas que ejecutar."); return 0
    faltan = [a for a in PERFILES[perfil] if not (RAIZ / a.split("::")[0]).exists()]
    if faltan:
        sys.exit(f"Archivos de prueba inexistentes en el perfil {perfil}: {faltan}")
    return ejecutar_por_archivo(perfil, extra)


def ejecutar_por_archivo(perfil: str, extra: list[str]) -> int:
    """Cada archivo en su propio proceso, con límite de tiempo: la suite heredada tiene estado global (interruptores
    de sombras/movimiento al importar, ventanas, QSettings) y, juntos, unos archivos hacen fallar a otros o los cuelgan.
    Con --junitxml=<ruta>.xml se escribe un XML por archivo junto a esa ruta (<ruta>__<archivo>.xml)."""
    junit = next((Path(a.split("=", 1)[1]) for a in extra if a.startswith("--junitxml=")), None)
    resto = [a for a in extra if not a.startswith("--junitxml=")]
    grupos: dict[str, list[str]] = {}
    for objetivo in PERFILES[perfil]:
        grupos.setdefault(objetivo.split("::")[0], []).append(objetivo)
    resumen, fallidos, intermitentes = Counter(), [], []
    for archivo, objetivos in grupos.items():
        salida = junit.with_name(f"{junit.stem}__{Path(archivo).stem}.xml") if junit else None
        codigo = _pytest(perfil, archivo, objetivos, resto, salida)
        if salida and salida.exists():
            for suite in ET.parse(salida).getroot().iter("testsuite"):
                for clave in ("tests", "failures", "errors", "skipped"):
                    resumen[clave] += int(suite.get(clave, 0))
        if codigo == 1 and perfil != "historicas" and salida and salida.exists():
            # Un único reintento de las pruebas que fallaron (por id): un fallo determinista falla de nuevo y rompe el
            # perfil; las que pasan al reintento se listan por nombre como intermitentes (carreras de tiempo heredadas).
            nodos = _nodos_fallidos(salida)
            if nodos and _pytest(perfil, archivo, nodos, resto, salida.with_name(salida.stem + "__reintento.xml")) == 0:
                intermitentes += nodos; codigo = 0
        if codigo != 0 and not (perfil == "historicas" and codigo == 1):
            fallidos.append(f"{archivo} ({codigo})")
    if junit:
        print(f"\nResumen {perfil}: {len(grupos)} archivos; {resumen['tests']} pruebas, {resumen['failures']} fallos "
              f"en la primera ejecución, {resumen['errors']} errores, {resumen['skipped']} omitidas o xfail")
    print("Intermitentes (fallaron y pasaron al reintento): " + ("; ".join(intermitentes) if intermitentes else "ninguna"))
    print("Archivos con fallo: " + ("; ".join(fallidos) if fallidos else "ninguno"))
    return 1 if fallidos else 0


def _pytest(perfil: str, archivo: str, objetivos: list[str], resto: list[str], salida: Path | None):
    argumentos = [sys.executable, "-W", "ignore", "-m", "pytest", "-p", "no:cacheprovider", "-q", *opciones(perfil),
                  *objetivos, *resto, *([f"--junitxml={salida}"] if salida else [])]
    try:
        return subprocess.run(argumentos, cwd=RAIZ, env=_entorno(), timeout=TIEMPO_MAXIMO_POR_ARCHIVO).returncode
    except subprocess.TimeoutExpired:
        print(f"\n*** {archivo}: superó {TIEMPO_MAXIMO_POR_ARCHIVO} s; se detiene y se marca como fallo ***", flush=True)
        return "TIEMPO_AGOTADO"


def _nodos_fallidos(junit_xml: Path) -> list[str]:
    """IDs pytest de los casos con failure/error (classname tests.test_x[.Clase] + name)."""
    nodos = []
    for caso in ET.parse(junit_xml).getroot().iter("testcase"):
        if any(h.tag in ("failure", "error") for h in caso):
            partes = (caso.get("classname") or "").split(".")
            i = next((k for k, p in enumerate(partes) if p.startswith("test_")), None)
            if i is None:  # error de recolección: no hay nodo que reintentar
                return []
            nodos.append("/".join(partes[:i + 1]) + ".py::" + "::".join(partes[i + 1:] + [caso.get("name")]))
    return nodos


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
