"""AS-007: contratos VIGENTES de `tests/test_residuales_auditoria_independiente_r3.py` como pruebas recolectables.

r3 es un script (`python tests/test_residuales_auditoria_independiente_r3.py`): sus funciones no empiezan por `test_`
y ningún perfil lo ejecuta. Sus controles C1–C7 (P0-C: el intervalo retirado no se publica en el objeto, el DataFrame,
la sesión, el CSV, la interfaz, el DOCX ni el PDF) y las partes vigentes de C12 y HG5 (P0-E) pasan sobre la ruta vigente
y no tenían prueba recolectada equivalente: se migran aquí con los mismos datos (serie ondulada n=48, h=6).

Alcance de C1, sin ampliarlo: revisa las tablas de ventanas (DataFrames con `Origen`/`Horizonte`) y las claves `ci_*`.
NO cubre `backtesting_comparativo.<modelo_h>.metricas.errores_extremos.observaciones[*].error_absoluto`, que hoy publica
el error absoluto de cada ventana y permite reconstruir el IC95 retirado (hallazgo Thermos B-A1, residual P0-C de
producción, pendiente de decisión del propietario: 04 y 05 del informe de esta fase).

No se importa r3 ni `tramo_evidencia_oos`, y no se recalcula el intervalo: si apareciera una columna de errores, el
mensaje dice dónde, sin reconstruir la banda. Inventario y destino de los 27 controles de r3:
docs/fase_v112_antislop_as007_preparacion_2d5_thermos/01_INVENTARIO_R3_Y_DEPENDENCIAS.csv.
"""
import json
import math
import re
import zipfile
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from app_icociv.proyeccion.servicio_proyeccion import ejecutar_proyeccion

#: Vocabulario del intervalo retirado (r3, VOCABULARIO_INTERVALO). No puede aparecer en texto público.
VOCABULARIO_INTERVALO = (
    "σ̂", "sigma_h", "ancho relativo", "semiancho", "cobertura efectiva",
    "cobertura empírica", "cobertura empirica", "nivel nominal",
    "ic95", "ic 95", "ip95", "cuantil", "percentil",
)
#: Columnas con las que se reconstruye `sigma_h` (r3, COLUMNAS_PROHIBIDAS_OOS).
COLUMNAS_PROHIBIDAS_OOS = ("Observado", "Predicho", "Error", "Error_abs", "Error_pct",
                           "Error_escalado_abs", "Escala_naive_insample")
#: Agregados que SÍ deben publicarse (r3, AGREGADOS_EXIGIDOS).
AGREGADOS_EXIGIDOS = ("rmse", "mae", "mase")


def _ondulada(n: int) -> pd.DataFrame:
    valores = [100.0 + 0.4 * i + 3.0 * math.sin(i * 0.7) for i in range(n)]
    return pd.DataFrame({"Periodo": [f"{2021 + i // 12}_{i % 12 + 1}" for i in range(n)], "Indice": valores})


@lru_cache(maxsize=1)
def _caso_ordinario() -> dict:
    """n=48, h=6: el caso con el que se demostró la reconstrucción del IC95 (r3). Compartido: ninguna prueba lo muta."""
    datos = _ondulada(48)
    anio, mes = map(int, datos.iloc[-1]["Periodo"].split("_")[:2])
    total = anio * 12 + mes - 1 + 6
    return ejecutar_proyeccion(datos, total // 12, total % 12 + 1, 2021)


def _tablas_de_ventanas(objeto) -> list[tuple[str, pd.DataFrame]]:
    """Toda tabla pública con forma de tabla de ventanas de backtesting (columnas Origen u Horizonte)."""
    encontradas, vistos = [], set()

    def recorrer(nodo, ruta=""):
        if id(nodo) in vistos:
            return
        vistos.add(id(nodo))
        if isinstance(nodo, pd.DataFrame):
            if "Origen" in nodo.columns or "Horizonte" in nodo.columns:
                encontradas.append((ruta, nodo))
        elif isinstance(nodo, dict):
            for clave, valor in nodo.items():
                recorrer(valor, f"{ruta}.{clave}")
        elif isinstance(nodo, (list, tuple)):
            for i, valor in enumerate(nodo):
                recorrer(valor, f"{ruta}[{i}]")

    recorrer(objeto)
    return encontradas


def _errores_recuperables(objeto) -> list[str]:
    """Columnas públicas con al menos dos números bajo un nombre de error/observado/predicho (por forma)."""
    sospechosas = []
    for ruta, tabla in _tablas_de_ventanas(objeto):
        for columna in tabla.columns:
            if columna in COLUMNAS_PROHIBIDAS_OOS:
                if len(pd.to_numeric(tabla[columna], errors="coerce").dropna()) >= 2:
                    sospechosas.append(f"{ruta}<{columna}>")
    return sospechosas


def _informe():
    from app_icociv.reportes.contenido import DatosProyeccion, construir_informe_proyeccion
    from app_icociv.reportes.modelo import ConfiguracionInforme

    serie = _ondulada(48)
    datos = DatosProyeccion(
        resultado=_caso_ordinario(), serie_df=serie, fuente_label="T_16", archivo_excel="anexo_icociv.xlsb",
        ruta_jerarquica=[{"nivel": "Serie", "valor": "Serie de prueba"}], fila=serie.head(1),
        year_month=list(serie["Periodo"]), usuario="Prueba",
    )
    return construir_informe_proyeccion(datos, ConfiguracionInforme.desde_tipo("tecnico"))


def test_p0c_objeto_sin_tablas_de_errores_ni_limites():
    """r3 C1. Ninguna tabla de ventanas del objeto lleva columnas de error y no hay límites `ci_*`; el punto sí.

    No revisa `errores_extremos.observaciones` (ver docstring del módulo): ese residual queda fuera de esta prueba.
    """
    resultado = _caso_ordinario()
    assert resultado.get("y_proj") is not None and np.isfinite(float(resultado["y_proj"]))
    assert _errores_recuperables(resultado) == []
    for clave in ("ci_lo", "ci_hi", "ci80_lo", "ci80_hi", "ci95_lo", "ci95_hi"):
        assert resultado.get(clave) is None, f"'{clave}' volvió a publicarse."


def test_p0c_dataframe_de_proyecciones_sin_columnas_de_intervalo():
    """r3 C2. La tabla de proyecciones no publica valores del intervalo y sí el punto de cada paso."""
    tabla = _caso_ordinario().get("proyecciones")
    assert isinstance(tabla, pd.DataFrame) and not tabla.empty
    for columna in tabla.columns:
        if any(marca in columna.lower() for marca in
               ("limite", "sigma", "ancho_relativo", "q80", "q95", "percentil", "ic95")):
            assert pd.to_numeric(tabla[columna], errors="coerce").dropna().empty, columna
    assert len(pd.to_numeric(tabla["indice_proyectado"], errors="coerce").dropna()) == len(tabla)


def test_p0c_sesion_json_sin_errores_oos_y_con_agregados():
    """r3 C3. La sesión serializada no lleva columnas de error por ventana ni vocabulario; sí los agregados."""
    from app_icociv.interfaz.controladores.controlador_principal import ControladorPrincipal

    serializado = ControladorPrincipal._proyeccion_serializable(_caso_ordinario())
    texto = json.dumps(serializado, ensure_ascii=False, default=str).lower()
    for fila in (serializado.get("backtesting") or {}).get("predicciones") or []:
        assert not [c for c in COLUMNAS_PROHIBIDAS_OOS if c in fila]
    for palabra in ("σ̂", "cobertura efectiva", "ancho relativo"):
        assert palabra not in texto
    metricas = (serializado.get("backtesting") or {}).get("metricas") or {}
    assert [a for a in AGREGADOS_EXIGIDOS if a not in metricas] == []


def test_p0c_csv_sin_columnas_de_intervalo_y_con_agregados():
    """r3 C4. El CSV escrito en disco no lleva columnas ni vocabulario del intervalo; sí agregados por horizonte."""
    from app_icociv.reportes.generador_reportes import generar_csv_reproducibilidad

    with TemporaryDirectory() as tmp:
        ruta = generar_csv_reproducibilidad(Path(tmp) / "reproducible.csv", _ondulada(48), _caso_ordinario(),
                                            [{"nivel": "Serie", "valor": "Serie de prueba"}])
        csv = pd.read_csv(ruta, encoding="utf-8-sig")
    assert not csv.empty
    for columna in csv.columns:
        assert not any(m in columna.lower() for m in
                       ("sigma_h", "q95_intervalo", "percentil_95", "ic95_inferior", "ic95_superior")), columna
    texto = csv.astype(str).to_csv(index=False).lower()
    for palabra in ("σ̂", "cobertura efectiva", "ancho relativo"):
        assert palabra not in texto
    for columna in ("rmse_horizonte", "mae_horizonte", "mase_horizonte", "iteraciones_backtesting_horizonte"):
        assert columna in csv.columns


def test_p0c_interfaz_sin_vocabulario_de_intervalo():
    """r3 C5. El HTML que muestra la interfaz no usa vocabulario del intervalo y muestra el modelo."""
    from app_icociv.interfaz.presentacion_resultados import (
        construir_html_detalle_horizonte,
        construir_html_resultados,
    )

    resultado = _caso_ordinario()
    html = construir_html_resultados(resultado) + construir_html_detalle_horizonte(resultado)
    assert [p for p in VOCABULARIO_INTERVALO if p.lower() in html.lower()] == []
    assert resultado.get("model_name") and str(resultado["model_name"]) in html


def test_p0c_docx_sin_vocabulario_ni_columnas_de_error():
    """r3 C6. El DOCX escrito en disco no usa vocabulario del intervalo ni encabezados de error por ventana."""
    from app_icociv.reportes import docx_render

    informe = _informe()
    with TemporaryDirectory() as tmp:
        ruta = docx_render.guardar(informe, Path(tmp) / "tecnico.docx")
        with zipfile.ZipFile(ruta) as paquete:
            texto = re.sub(r"<[^>]+>", " ", paquete.read("word/document.xml").decode("utf-8")).lower()
    assert [p for p in VOCABULARIO_INTERVALO if p.lower() in texto] == []
    for seccion in informe.secciones_visibles():
        for bloque in seccion.bloques:
            encabezados = [str(x).lower() for x in (getattr(bloque, "encabezados", None) or [])]
            prohibidas = {"observado", "predicho", "error abs", "error pct", "error"}
            prohibidas |= {c.lower() for c in COLUMNAS_PROHIBIDAS_OOS}
            assert not prohibidas & set(encabezados), (seccion.clave, prohibidas & set(encabezados))


def test_p0c_pdf_sin_vocabulario_de_intervalo():
    """r3 C7. El PDF se genera y el contenido que dibuja no usa vocabulario del intervalo."""
    from app_icociv.reportes import pdf_render
    from tests.test_informes_rediseno import _texto_informe  # extractor de los ocho tipos de bloque de modelo.py

    informe = _informe()
    with TemporaryDirectory() as tmp:
        assert pdf_render.guardar(informe, Path(tmp) / "tecnico.pdf").read_bytes()[:4] == b"%PDF"
    texto = _texto_informe(informe).lower()
    assert [p for p in VOCABULARIO_INTERVALO if p.lower() in texto] == []


def test_p0e_la_evidencia_oos_se_declara_provisional():
    """r3 HG5, parte vigente. Mientras P0-E siga abierto, el resultado declara la evidencia OOS provisional.

    Las otras dos aserciones de HG5 (`trazabilidad.primer_origen_provisional` y la fórmula publicada) fallan en la
    base: esas claves dejaron de producirse antes de la Fase 2A. Quedan como DECISIÓN PENDIENTE (02 del informe).
    """
    resultado = _caso_ordinario()
    assert resultado.get("evidencia_oos_provisional") is True
    assert "P0-E" in (resultado.get("bloqueos_metodologicos") or {})
    assert resultado.get("motivo_evidencia_provisional")


def test_p0c_conserva_agregados_oos_y_diseno_de_ventanas():
    """r3 C12, parte vigente. P0-C retira los errores por ventana, no la evidencia agregada ni el diseño.

    `Periodo` ya no figura en la tabla de ventanas (C12 falla por eso en la base): queda como DECISIÓN PENDIENTE y
    no se exige aquí. `mape`/`smape` tampoco: su tratamiento cuando no son calculables es una decisión abierta.
    """
    backtesting = _caso_ordinario().get("backtesting") or {}
    metricas = backtesting.get("metricas") or {}
    for agregado in AGREGADOS_EXIGIDOS:
        valor = metricas.get(agregado)
        assert valor is not None and np.isfinite(float(valor)), f"Se perdió '{agregado}'."
    assert "sesgo_medio" in metricas
    iteraciones = backtesting.get("iteraciones")
    assert isinstance(iteraciones, int) and iteraciones > 0
    tabla = backtesting.get("predicciones")
    assert isinstance(tabla, pd.DataFrame) and len(tabla) == iteraciones
    assert {"Origen", "Horizonte"} <= set(tabla.columns)
