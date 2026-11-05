"""Plugin de pytest para el sondeo G3 de AS-028: oculta en memoria el par que retirará 2D-2.

No edita producción: borra los atributos del módulo ya importado, solo dentro de este proceso.
Uso: pytest -p ocultar_par_2d2 ... (con este directorio en PYTHONPATH).
"""

PAR = ("seleccionar_modelo_por_rmse_oos_global", "_errores_oos_por_par")


def pytest_configure(config):
    from app_icociv.proyeccion import servicio_proyeccion as sp

    for nombre in PAR:
        delattr(sp, nombre)
    assert not any(hasattr(sp, n) for n in PAR)
    print(f"[G3] par oculto en memoria: {PAR}")
