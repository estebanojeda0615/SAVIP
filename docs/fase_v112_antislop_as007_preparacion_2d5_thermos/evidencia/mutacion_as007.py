"""Plugin de pytest (solo para medir sensibilidad): rompe un contrato P0-C/P0-E segun MUTACION."""
import os
import pandas as pd
import app_icociv.proyeccion.servicio_proyeccion as sp

M = os.environ.get("MUTACION", "")
_original = sp.ejecutar_proyeccion


def _mutada(*a, **k):
    r = _original(*a, **k)
    if M == "sin_rmse":
        r["backtesting"]["metricas"].pop("rmse")
    elif M == "ci95":
        r["ci95_lo"], r["ci95_hi"] = 1.0, 2.0
    elif M == "errores_ventanas":
        r["tabla_ventanas_extra"] = pd.DataFrame({"Origen": [1, 2, 3], "Error": [0.1, -0.2, 0.3]})
    elif M == "columna_limite":
        t = r["proyecciones"].copy(); t["limite_superior_95"] = 1.0; r["proyecciones"] = t
    elif M == "vocabulario_modelo":
        r["model_name"] = str(r.get("model_name")) + " IC95 cuantil"
    elif M == "sin_model_name":
        r["model_name"] = None
    elif M == "p0e":
        r["evidencia_oos_provisional"] = False
    return r


sp.ejecutar_proyeccion = _mutada

if M == "sesion_vocabulario":
    from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal
    _s = ControladorPrincipal._proyeccion_serializable
    ControladorPrincipal._proyeccion_serializable = staticmethod(lambda r: {**_s(r), "nota": "cobertura efectiva"})
elif M == "csv_sigma":
    import app_icociv.reportes.generador_reportes as g
    _c = g.generar_csv_reproducibilidad
    def _csv(ruta, *a, **k):
        p = _c(ruta, *a, **k); d = pd.read_csv(p, encoding="utf-8-sig"); d["sigma_h"] = 1.0
        d.to_csv(p, index=False, encoding="utf-8-sig"); return p
    g.generar_csv_reproducibilidad = _csv
elif M == "portada_pie":
    import app_icociv.reportes.contenido as ct
    _cp = ct.construir_informe_proyeccion
    def _inf_p(*a, **k):
        inf = _cp(*a, **k); inf.pie = (inf.pie or "") + " IC95 cuantil"; return inf
    ct.construir_informe_proyeccion = _inf_p
elif M in ("formula_general", "encabezado_error_abs"):
    import app_icociv.reportes.contenido as ct
    _ci = ct.construir_informe_proyeccion
    def _inf(*a, **k):
        inf = _ci(*a, **k)
        for s in inf.secciones_visibles():
            for b in s.bloques:
                if M == "formula_general" and isinstance(getattr(b, "general", None), str):
                    object.__setattr__(b, "general", b.general + " sigma_h cuantil"); return inf
                if M == "encabezado_error_abs" and getattr(b, "encabezados", None):
                    object.__setattr__(b, "encabezados", ["Error_abs"] + list(b.encabezados)[1:]); return inf
        raise RuntimeError("mutacion no aplicada")
    ct.construir_informe_proyeccion = _inf
elif M == "anexo_error":
    import app_icociv.reportes.contenido as ct
    _ca = ct.construir_informe_proyeccion
    def _inf_a(*a, **k):
        inf = _ca(*a, **k)
        for s in inf.secciones_visibles():
            if s.clave == "anexos":
                for b in s.bloques:
                    if getattr(b, "encabezados", None):
                        object.__setattr__(b, "encabezados", list(b.encabezados) + ["Error_abs"]); return inf
        raise RuntimeError("anexo de backtesting no presente")
    ct.construir_informe_proyeccion = _inf_a
