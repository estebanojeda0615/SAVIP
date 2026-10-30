"""Plugin de pytest / preludio: simula en memoria el retiro de 2D-5 (no toca archivos)."""
import app_icociv.proyeccion.servicio_proyeccion as sp
for nombre in ("tramo_evidencia_oos", "TRAMO_OOS_SIN_EVIDENCIA", "TRAMO_OOS_MUY_LIMITADA", "TRAMO_OOS_DISPONIBLE"):
    delattr(sp, nombre)
