"""Fase 4I-P: la CONSULTA VIGENTE (fecha, H e índice tomados de la trayectoria de 24 meses guardada) gobierna
historial, Resultados y gráfica, y cada punto proyectado muestra su propio MAE(h). Sin motor, sin tocar snapshots."""

import os
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QLabel

from tests.test_fase_4i_j_fecha_comun import APP, _calcular, _cargar
from tests.test_fase_4i_j_k_actividades import _aplicar, _canonico, _factor_vigente
from tests.test_fase_4i_j_reutilizacion import _Contador, _anexo, _ejecutar
from app_icociv.interfaz import ventana_principal as vp
from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
from app_icociv.servicios import fecha_objetivo as fo

CAPTURAS = Path(__file__).resolve().parents[1] / "docs/fase_4i_p/capturas"


def _tabla_mae(analisis):
    tabla = analisis["resultado"]["proyeccion"]["horizonte_info"]["tabla_horizontes"]
    return {int(x["horizonte"]): x["mae"] for x in tabla}


def _visor(v, abrir, inspeccionar=(), captura=None, acciones=None):
    """Abre el visor real (offscreen); devuelve cabecera, puntos, banda y la etiqueta de los puntos pedidos."""
    visto = {"textos": {}}

    def exec_(visor):
        visor.show(); APP.processEvents()
        eje = visor.canvas.figure.axes[0]
        linea = next(l for l in eje.get_lines() if l.get_label() == "Proyección")
        xs, ys = [float(x) for x in linea.get_xdata()], [float(y) for y in linea.get_ydata()]
        if acciones:
            acciones(visor)
        for h in inspeccionar:
            px, py = eje.transData.transform((xs[h - 1], ys[h - 1]))
            assert visor.inspeccionar(px, py)
            visto["textos"][h] = visor._anotacion.get_text()
        vertices = [tuple(p) for c in eje.collections for path in c.get_paths() for p in path.vertices]
        visto.update(cabecera=" | ".join(x.text() for x in visor.findChildren(QLabel)), x=xs, y=ys,
                     banda=[c.get_label() for c in eje.collections], vertices=vertices,
                     detalle={d["horizonte"]: d for d in visor.figura.savip_detalle_proyeccion.values()})
        if captura:
            CAPTURAS.mkdir(parents=True, exist_ok=True); visor.grab().save(str(CAPTURAS / captura))
        visor.close()
        return 0
    with patch.object(vp.VisorGraficaDialog, "exec", exec_):
        abrir()
    return visto


def _vistas(v, a):
    """Lo que el usuario VE para el análisis `a` en historiales y Resultados (Resultados = análisis mostrado)."""
    w = v.widget_proyecciones
    arbol = []
    for i in range(w.arbol_historial.topLevelItemCount()):
        serie = w.arbol_historial.topLevelItem(i)
        arbol += [serie.child(j).text(0) for j in range(serie.childCount())
                  if serie.child(j).data(0, Qt.UserRole) == ("analisis", a["id"])]
    return {"historial": w.selector_analisis.itemText(w.selector_analisis.findData(a["id"])),
            "historial_valores": w.selector_analisis_valores.itemText(w.selector_analisis_valores.findData(a["id"])),
            "arbol": arbol, "resultados": v.selector_resultados_icociv.itemText(v.selector_resultados_icociv.findData(a["id"])),
            "kpi_indice": v.valores_kpi["indice"].text(), "kpi_horizonte": v.valores_kpi["horizonte"].text(),
            "kpi_error": v.valores_kpi["error_historico"].text(), "html": v.texto_resultados.toPlainText()}


def _comprobar(v, a, periodo, h):
    """Historial, Resultados y ambas gráficas muestran la consulta (periodo, H) con I = trayectoria[H-1]."""
    tray = fo.trayectoria(a); indice = tray[h - 1]; texto = f"· {periodo} · {h} meses"
    vistas = _vistas(v, a)
    assert vistas["historial"].endswith(texto) and vistas["resultados"].endswith(texto), vistas
    assert f"#{w_numero(v, a)} · {periodo} · H={h}" in vistas["historial_valores"], vistas
    assert vistas["arbol"] and vistas["arbol"][0].startswith(f"#{w_numero(v, a)} · {periodo} · {h} meses"), vistas
    assert vistas["kpi_indice"] == f"{indice:.3f}" and vistas["kpi_horizonte"] == f"{h} meses", vistas
    mae = _tabla_mae(a)[h]
    assert vistas["kpi_error"].startswith(f"± {mae:.3f}"), (vistas["kpi_error"], mae)
    assert f"{indice:.3f}" in vistas["html"] and periodo in vistas["html"], "Resultados no muestra la consulta"
    for abrir in (lambda: v.widget_proyecciones.grafica_solicitada.emit(a["id"]), v._abrir_popup_grafica):
        g = _visor(v, abrir)
        assert texto in g["cabecera"] and len(g["y"]) == h and g["y"] == tray[:h] and g["y"][-1] == indice, g["cabecera"]
    return vistas


def w_numero(v, a):
    return v.widget_proyecciones.historial.index(a) + 1


def test_consulta_vigente_sincroniza_historial_resultados_y_grafica(tmp_path):
    agosto = _anexo(tmp_path / "anex-ICOCIV-ago2026.xlsx", meses=44)   # sintético, último observado 2026-08
    octubre = _anexo(tmp_path / "anex-ICOCIV-oct2026.xlsx", meses=46)  # sintético, último observado 2026-10
    v = vp.VentanaPrincipal(); v.resize(1366, 900); v.show(); w = v.widget_proyecciones
    motor = _Contador()
    try:
        with patch.object(ControladorPrincipal, "ejecutar_analisis", motor.metodo):
            _cargar(v, agosto)
            assert _ejecutar(v, 1, 11) == 1
            a = w.historial[0]
            originales = deepcopy([a["nombre"], a["resultado"], a["contexto"], a["parametros"]])
            actividades = [_calcular(w, "A1"), _calcular(w, "A2")]
            i0 = [(r["i0_icociv"], r["precio_base"], r["anticipo_amortizado"], r["cantidad"]) for r in actividades]
            _comprobar(v, a, "2027-07", 11)
            n = motor.n

            # D1. H11 -> H23 (jul-2028 desde ago-2026), con actualización confirmada de las actividades.
            assert _aplicar(v, 2028, 7)[0]
            _comprobar(v, a, "2028-07", 23)
            html = _vistas(v, a)["html"]
            assert "Consulta actual: 2028-07" in html and "Ejecución original: 2027-07" in html
            assert all(r["i_icociv"] == fo.trayectoria(a)[22] for r in w.valores)
            # D5. Deshacer / rehacer: las vistas vuelven a H11 y otra vez a H23; I0, P, A y cantidades intactos.
            w.pila_deshacer.undo(); APP.processEvents()
            _comprobar(v, a, "2027-07", 11)
            w.pila_deshacer.redo(); APP.processEvents()
            _comprobar(v, a, "2028-07", 23)
            assert [(r["i0_icociv"], r["precio_base"], r["anticipo_amortizado"], r["cantidad"]) for r in w.valores] == i0
            assert all(r["factor_icociv"] == _factor_vigente(r["i_icociv"], r["i0_icociv"]) for r in w.valores)
            # D2. Volver a H11: mismas tres vistas, sin análisis nuevo.
            assert _aplicar(v, 2027, 7)[0]
            _comprobar(v, a, "2027-07", 11)
            assert len(w.historial) == 1

            # D3. Dos series con orígenes distintos y el mismo mes objetivo: cada una con su H.
            _cargar(v, octubre)
            assert _ejecutar(v, 2, 9) == 1
            b = w.historial[1]
            assert _aplicar(v, 2028, 7)[0]
            v._activar_analisis(a["id"]); _comprobar(v, a, "2028-07", 23)
            v._activar_analisis(b["id"]); _comprobar(v, b, "2028-07", 21)
            # Solo la serie seleccionada cambia; la otra queda intacta.
            with patch.object(type(w), "_confirmar_fecha_individual", return_value=True):
                assert _aplicar(v, 2028, 1, alcance="individual")[0]
            _comprobar(v, b, "2028-01", 15)
            v._activar_analisis(a["id"]); _comprobar(v, a, "2028-07", 23)

            # D4. Guardar y reabrir con DANE compatible: mismas vistas; snapshots originales intactos.
            antes = _vistas(v, a); sesion = _canonico(w)
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
                otra._activar_analisis(a2["id"])
                assert _vistas(otra, a2) == antes
                _comprobar(otra, a2, "2028-07", 23)
            finally:
                otra.close()
            assert deepcopy([a["nombre"], a["resultado"], a["contexto"], a["parametros"]]) == originales
            assert _canonico(w) == sesion and motor.n == n + 1 == 2
    finally:
        v.close()


def test_mae_por_horizonte_en_cada_punto_y_sin_inventar(tmp_path):
    v = vp.VentanaPrincipal(); v.resize(1366, 900); v.show(); w = v.widget_proyecciones
    try:
        _cargar(v, _anexo(tmp_path / "anex-ICOCIV-ago2026.xlsx", meses=44))
        assert _ejecutar(v, 1, 11) == 1
        a = w.historial[0]
        assert _aplicar(v, 2028, 7)[0]   # H23
        tray, mae = fo.trayectoria(a), _tabla_mae(a)
        assert len(set(round(mae[h], 9) for h in (1, 12, 23))) == 3   # MAE distinto por horizonte, no constante

        def comprobar(g, horizontes):
            for h in horizontes:
                i, m = tray[h - 1], mae[h]
                d = g["detalle"][h]
                assert d["mae"] == m and d["inferior"] == i - m and d["superior"] == i + m
                texto = g["textos"][h]
                assert f"H={h}" in texto and f"I(h): {i:,.3f}" in texto and f"MAE histórico H{h}: {m:,.3f}" in texto
                assert f"{i - m:,.3f} a {i + m:,.3f}" in texto and "no es intervalo de confianza" in texto
                x = g["x"][h - 1]
                assert any(abs(vx - x) < 1e-9 and abs(vy - (i + m)) < 1e-9 for vx, vy in g["vertices"])  # banda superior
                assert any(abs(vx - x) < 1e-9 and abs(vy - (i - m)) < 1e-9 for vx, vy in g["vertices"])  # banda inferior
            assert g["banda"] == ["Referencia de error histórico ±MAE(h) (no es intervalo de confianza)"]

        # D6 y D7: ambos botones «Ver gráfica» del historial y el de Resultados; zoom; tema claro y oscuro.
        w._proyeccion_consulta = a["id"]
        for boton, captura in ((w.boton_grafica_superior, "grafica_h23_mae_punto.png"), (w.boton_grafica_inferior, None)):
            comprobar(_visor(v, boton.click, (1, 12, 23), captura), (1, 12, 23))
        comprobar(_visor(v, v._abrir_popup_grafica, (1, 12, 23)), (1, 12, 23))
        zoom = _visor(v, w.boton_grafica_superior.click, (23,), acciones=lambda visor: (visor.acercar(), visor.alejar(),
                                                                                         visor.restablecer_vista()))
        comprobar(zoom, (23,))
        tema = v.tema_actual
        try:
            v._aplicar_tema("oscuro" if tema == "claro" else "claro", persistir=False)
            comprobar(_visor(v, w.boton_grafica_superior.click, (1, 23), "grafica_h23_otro_tema.png"), (1, 23))
        finally:
            v._aplicar_tema(tema, persistir=False)

        # Sin MAE(h) para h >= 20 (instantánea antigua simulada): no se dibuja ni se inventa nada en esos puntos.
        tabla = a["resultado"]["proyeccion"]["horizonte_info"]["tabla_horizontes"]
        a["resultado"]["proyeccion"]["horizonte_info"]["tabla_horizontes"] = [x for x in tabla if x["horizonte"] < 20]
        g = _visor(v, w.boton_grafica_superior.click, (19, 23))
        assert g["detalle"][23]["mae"] is None and "MAE histórico por horizonte no disponible" in g["textos"][23]
        assert g["detalle"][19]["mae"] == mae[19]
        assert not any(abs(vx - g["x"][22]) < 1e-9 for vx, _ in g["vertices"])   # sin límites falsos en h=23
        v._activar_analisis(a["id"])   # Resultados relee la instantánea (ahora sin MAE para H23)
        assert v.valores_kpi["error_historico"].text() == "No disponible" and v.valores_kpi["indice"].text() == f"{tray[22]:.3f}"
        assert "No disponible" in v.texto_resultados.toPlainText()
    finally:
        v.close()
