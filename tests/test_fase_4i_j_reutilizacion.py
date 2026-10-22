"""Fase 4I-J (ajuste): «Ejecutar proyección» sobre una serie ya analizada con los mismos datos DANE reutiliza
su trayectoria de 24 meses: sin motor, sin entradas nuevas en el historial y sin ventanas de confirmación.
Las revisiones nuevas solo nacen de «Actualizar análisis con DANE más reciente»."""

import math
import os
import shutil
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from openpyxl import Workbook
from PySide6.QtWidgets import QMessageBox

from tests.test_fase_4i_j_fecha_comun import APP, _calcular, _cargar, _esperar
from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.interfaz.ventana_principal import VentanaPrincipal
from app_icociv.servicios import fecha_objetivo as fo
from app_icociv.utilidades.utilidades import COLUMNAS_FIJAS_TABLAS

_MOTOR = ControladorPrincipal.ejecutar_analisis


def _anexo(ruta, meses=46, revision=0.0):
    """Desde 2023-01; `revision` altera los valores (publicación revisada con el mismo corte)."""
    libro = Workbook(); hoja = libro.active; hoja.title = "Anexo 16"
    periodos = [f"{2023 + i // 12}_{i % 12 + 1}" for i in range(meses)]
    for tag, columnas in COLUMNAS_FIJAS_TABLAS.items():
        hoja.append([tag + ". PRUEBA - datos sintéticos"]); hoja.append(columnas + periodos)
        for grupo in (1, 2):
            hoja.append([100.0 if "Ponderacion" in c else grupo if "cod" in c.lower() else f"{c} sintético {grupo}" for c in columnas]
                        + [100 + grupo + i * .2 + math.sin(i / 3) * .1 + revision for i in range(meses)])
        for _ in range(3):
            hoja.append([None])
    libro.save(ruta)
    return ruta


class _Contador:
    """Espía del motor real: cuenta llamadas (se instala como método con `.metodo`)."""

    def __init__(self):
        self.n = 0
        contador = self

        def metodo(controlador, *a, **k):
            contador.n += 1
            return _MOTOR(controlador, *a, **k)
        self.metodo = metodo


def _ejecutar(v, grupo, horizonte):
    """Pulsa «Ejecutar proyección»; prohíbe cualquier ventana modal de confirmación."""
    w = v.widget_proyecciones; n = len(w.historial)
    v.combo_grupo.setCurrentIndex(grupo)
    v.combo_horizonte.setCurrentIndex(v.combo_horizonte.findData(None)); v.spin_horizonte_personalizado.setValue(horizonte)
    with patch.object(QMessageBox, "exec", side_effect=AssertionError("ventana modal")), \
         patch.object(QMessageBox, "question", side_effect=AssertionError("ventana modal")):
        v.ejecutar_proyeccion()
        if v.trabajador is not None and v.trabajador.isRunning():
            _esperar(v, lambda: len(w.historial) > n)
    for _ in range(5):
        APP.processEvents()
    return len(w.historial) - n


def test_ejecutar_reutiliza_trayectoria_por_serie_y_datos_reales(tmp_path):
    octubre = _anexo(tmp_path / "anex-ICOCIV-oct2026.xlsx")
    copia = tmp_path / "copia con otro nombre.xlsx"; shutil.copy(octubre, copia)
    revisado = _anexo(tmp_path / "anex-ICOCIV-oct2026-revisado.xlsx", revision=0.05)
    diciembre = _anexo(tmp_path / "anex-ICOCIV-dic2026.xlsx", meses=48)
    v = VentanaPrincipal(); v.resize(1366, 900); v.show(); w = v.widget_proyecciones
    motor = _Contador()
    try:
        with patch.object(ControladorPrincipal, "ejecutar_analisis", motor.metodo):
            _cargar(v, octubre)
            assert _ejecutar(v, 1, 9) == 1 and motor.n == 1  # primera vez: motor
            a = w.historial[0]; original = deepcopy(a)
            for i in range(3):
                _calcular(w, f"Actividad {i + 1}")
            valores = deepcopy(w.valores)
            # Otro horizonte, misma serie y mismos datos: trayectoria guardada, sin motor ni historial nuevo.
            with patch.object(v.notificaciones, "mostrar") as aviso:
                assert _ejecutar(v, 1, 11) == 0
            assert motor.n == 1 and len(w.historial) == 1 and w.valores == valores
            c = a["consulta_horizonte"]
            assert (c["periodo"], c["horizonte"], c["indice"]) == ("2027-09", 11, fo.trayectoria(a)[10])
            assert (w.contexto["periodo_proyectado"], w.contexto["indice_proyectado"]) == ("2027-09", fo.trayectoria(a)[10])
            assert a["contexto"] == original["contexto"] and a["resultado"] == original["resultado"]
            assert "no se ejecutó el motor" in aviso.call_args[0][1] and (v.spin_anio.value(), v.spin_mes.value()) == (2027, 9)
            # Mismo horizonte de nuevo: también sin motor y sin ventana.
            assert _ejecutar(v, 1, 11) == 0 and motor.n == 1
            # La equivalencia es por datos, no por nombre: la misma publicación con otro nombre se reutiliza.
            _cargar(v, copia)
            assert _ejecutar(v, 1, 8) == 0 and motor.n == 1 and a["consulta_horizonte"]["horizonte"] == 8
            # Fecha común fijada y petición distinta: excepción registrada con aviso discreto, sin diálogo.
            v.spin_anio.setValue(2027); v.spin_mes.setValue(7); assert v.aplicar_fecha_objetivo()
            with patch.object(v.notificaciones, "mostrar") as aviso:
                assert _ejecutar(v, 1, 11) == 0
            assert "fuera de la fecha común" in aviso.call_args[0][1] and w.excepciones_fecha[-1]["periodo"] == "2027-09"
            # Datos DANE distintos para la misma serie: no hay motor ni revisión por este botón.
            _cargar(v, revisado)
            with patch.object(v.notificaciones, "mostrar") as aviso:
                assert _ejecutar(v, 1, 9) == 0
            assert motor.n == 1 and len(w.historial) == 1 and "Actualizar análisis con DANE más reciente" in aviso.call_args[0][1]
            # Otra serie: primera vez ⇒ motor.
            _cargar(v, octubre)
            assert _ejecutar(v, 2, 9) == 1 and motor.n == 2
            # La revisión solo nace del botón expreso con DANE posterior.
            _cargar(v, diciembre)
            with patch.object(v, "_confirmar_reanalisis", return_value=True), patch.object(QMessageBox, "information"):
                v.actualizar_analisis_dane(); _esperar(v, lambda: len(w.historial) == 4)
            assert motor.n == 4 and [x.get("revision_de") for x in w.historial[2:]] == [w.historial[0]["id"], w.historial[1]["id"]]
            assert w.historial[0]["resultado"] == original["resultado"] and w.valores == valores
            # Con el DANE de diciembre, la revisión vigente es la equivalente: se reutiliza.
            assert _ejecutar(v, 1, 5) == 0 and motor.n == 4 and w.analisis_activo_id == w.historial[2]["id"]
    finally:
        v.close()


def test_sesion_sin_trayectoria_completa_se_proyecta_de_nuevo(tmp_path):
    """Una instantánea antigua sin los 24 meses no es reutilizable (otra configuración del motor)."""
    v = VentanaPrincipal(); w = v.widget_proyecciones; motor = _Contador()
    try:
        with patch.object(ControladorPrincipal, "ejecutar_analisis", motor.metodo):
            _cargar(v, _anexo(tmp_path / "a.xlsx"))
            assert _ejecutar(v, 1, 9) == 1
            w.historial[0]["resultado"]["proyeccion"]["trayectoria_24_meses"] = []
            assert _ejecutar(v, 1, 9) == 1 and motor.n == 2
    finally:
        v.close()
