"""Fase 4I-N: «Ver gráfica» dibuja la fecha objetivo APLICADA a cada análisis (primeros H puntos de su
trayectoria de 24 meses guardada), sin motor y sin modificar el resultado guardado."""

import os
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox

from tests.test_fase_4i_j_fecha_comun import APP, _calcular, _cargar
from tests.test_fase_4i_j_k_actividades import _aplicar, _canonico
from tests.test_fase_4i_j_reutilizacion import _Contador, _anexo, _ejecutar
from app_icociv.interfaz import ventana_principal as vp
from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.servicios import fecha_objetivo as fo
from tests.fixtures.salidas import carpeta_salida

CAPTURAS = carpeta_salida("fase_4i_n_capturas")  # Fase 1A (AS-007): antes en docs/, no publicado


def _ver(v, analisis, captura=None):
    """Abre el visor real (offscreen) desde «Ver gráfica»; devuelve cabecera, puntos y límites del eje."""
    visto = {}

    def exec_(visor):
        visor.show(); APP.processEvents()
        eje = visor.canvas.figure.axes[0]
        linea = next(l for l in eje.get_lines() if l.get_label() == "Proyección")
        visto.update(cabecera=" | ".join(x.text() for x in visor.findChildren(QLabel)),
                     y=[float(y) for y in linea.get_ydata()], x_max=max(linea.get_xdata()), xlim=eje.get_xlim(),
                     banda=any(c.get_label().startswith("Referencia de error") for c in eje.collections))
        if captura:
            CAPTURAS.mkdir(parents=True, exist_ok=True); visor.grab().save(str(CAPTURAS / captura))
        visor.close()
        return 0
    with patch.object(vp.VisorGraficaDialog, "exec", exec_):
        v.widget_proyecciones.grafica_solicitada.emit(analisis["id"])
    return visto


def _comprobar(visto, analisis, periodo, h):
    tray = fo.trayectoria(analisis)
    assert f"· {periodo} · {h} meses" in visto["cabecera"], visto["cabecera"]
    assert len(visto["y"]) == h and visto["y"] == tray[:h] and visto["y"][-1] == tray[h - 1]
    assert visto["xlim"][1] >= visto["x_max"] and visto["banda"]


def test_grafica_sigue_fecha_aplicada_sin_motor(tmp_path):
    agosto = _anexo(tmp_path / "anex-ICOCIV-ago2026.xlsx", meses=44)   # último observado 2026-08
    octubre = _anexo(tmp_path / "anex-ICOCIV-oct2026.xlsx", meses=46)  # último observado 2026-10
    v = vp.VentanaPrincipal(); v.resize(1366, 900); v.show(); w = v.widget_proyecciones
    motor = _Contador()
    try:
        with patch.object(ControladorPrincipal, "ejecutar_analisis", motor.metodo):
            _cargar(v, agosto)
            assert _ejecutar(v, 1, 11) == 1
            a = w.historial[0]
            for i in range(2):
                _calcular(w, f"A{i + 1}")
            inicial = _ver(v, a, "grafica_h11_inicial.png")
            assert "· 2027-07 · 11 meses" in inicial["cabecera"] and len(inicial["y"]) == 11
            _cargar(v, octubre)
            assert _ejecutar(v, 2, 9) == 1
            b = w.historial[1]
            resultados = deepcopy([a["resultado"], b["resultado"], a["contexto"], b["contexto"]])
            n = motor.n

            # 1 y 3. Fecha común ene-2028 a todas: cada serie desde SU origen (ago → H17, oct → H15).
            assert _aplicar(v, 2028, 1)[0]
            _comprobar(_ver(v, a, "grafica_h17_aplicado.png"), a, "2028-01", 17)
            _comprobar(_ver(v, b), b, "2028-01", 15)
            # 5. Controles cambiados sin aplicar: no se anticipa.
            v.spin_anio.setValue(2027); v.spin_mes.setValue(3)
            _comprobar(_ver(v, a), a, "2028-01", 17)
            # 4. Solo el análisis seleccionado: b pasa a dic-2027 (H14); a conserva ene-2028.
            v._activar_analisis(b["id"])
            with patch.object(type(w), "_confirmar_fecha_individual", return_value=True):
                assert _aplicar(v, 2027, 12, alcance="individual")[0]
            _comprobar(_ver(v, b), b, "2027-12", 14)
            _comprobar(_ver(v, a), a, "2028-01", 17)
            # 2. Volver a jul-2027: a de nuevo H11.
            assert _aplicar(v, 2027, 7)[0]
            _comprobar(_ver(v, a, "grafica_h11_revertido.png"), a, "2027-07", 11)

            # 6. Guardar y reabrir con DANE compatible: misma gráfica, sin motor.
            assert _aplicar(v, 2028, 1)[0]
            antes = _ver(v, a); sesion = _canonico(w)
            ruta = tmp_path / "presupuesto.json"
            with patch.object(v, "_solicitar_usuario", return_value="QA"), \
                 patch.object(QFileDialog, "getSaveFileName", return_value=(str(ruta), "")):
                assert v.guardar_sesion_actual(como=True)
            otra = vp.VentanaPrincipal()
            try:
                _cargar(otra, octubre)
                with patch.object(QFileDialog, "getOpenFileName", return_value=(str(ruta), "")):
                    otra.abrir_sesion()
                    while otra._operacion_sesion:
                        APP.processEvents()
                a2 = otra.widget_proyecciones.historial[0]
                despues = _ver(otra, a2)
                assert despues["y"] == antes["y"] and despues["cabecera"] == antes["cabecera"]
                assert otra.widget_proyecciones.valores == w.valores
            finally:
                otra.close()
            # Ver la gráfica no toca resultados, contextos ni actividades; nunca llama al motor.
            assert [a["resultado"], b["resultado"], a["contexto"], b["contexto"]] == resultados
            assert _canonico(w) == sesion and motor.n == n == 2
    finally:
        v.close()


def test_trayectoria_insuficiente_avisa_y_no_inventa(tmp_path):
    v = vp.VentanaPrincipal(); w = v.widget_proyecciones
    try:
        _cargar(v, _anexo(tmp_path / "a.xlsx", meses=44))
        assert _ejecutar(v, 1, 11) == 1
        a = w.historial[0]
        a["consulta_horizonte"] = {"periodo": "2028-01", "horizonte": 17}
        a["resultado"]["proyeccion"]["trayectoria_24_meses"] = a["resultado"]["proyeccion"]["trayectoria_24_meses"][:12]
        with patch.object(v, "_aviso") as aviso, \
             patch.object(vp.VisorGraficaDialog, "exec", side_effect=AssertionError("no debe abrir")), \
             patch.object(QMessageBox, "exec", side_effect=AssertionError("ventana modal")):
            w.grafica_solicitada.emit(a["id"])
        assert "requiere H17" in aviso.call_args[0][1]
    finally:
        v.close()
