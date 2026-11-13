"""Plugin de pytest (G4 de AS-028 para 2D-1): oculta en memoria las seis definiciones que retiraría 2D-1.

No edita producción: borra los atributos del módulo ya importado, solo dentro de este proceso. Los auxiliares
compartidos con 2D-3 (`_tipo_uso_horizonte`, `_mayor_horizonte_permitido`) NO se ocultan.
Uso: pytest -p ocultar_2d1 ... (con este directorio en PYTHONPATH).
"""

OBJETIVO = ("determinar_horizonte_maximo_estadistico", "_serializar_evaluaciones_horizonte", "_item_horizonte_global",
            "_mayor_horizonte_con", "_ultimo_horizonte_por_clasificacion", "_evidencia_horizonte")
COMPARTIDOS = ("_tipo_uso_horizonte", "_mayor_horizonte_permitido")


def pytest_configure(config):
    from app_icociv.proyeccion import servicio_proyeccion as sp

    for nombre in OBJETIVO:
        delattr(sp, nombre)
    assert not any(hasattr(sp, n) for n in OBJETIVO)
    assert all(hasattr(sp, n) for n in COMPARTIDOS)
    print(f"[G4] 2D-1 oculto en memoria: {OBJETIVO}; compartidos presentes: {COMPARTIDOS}")
