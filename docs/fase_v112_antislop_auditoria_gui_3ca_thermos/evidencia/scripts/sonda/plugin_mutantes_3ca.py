"""Mutaciones adversariales TEMPORALES (solo en el proceso de la prueba, nunca en producción ni en el commit).

Uso: PYTHONPATH=<dir> MUTANTE_3CA=<nombre> pytest -p plugin_mutantes_3ca <nodo>
Cada mutante altera, en memoria, el comportamiento de la UI real que la prueba debe vigilar. La prueba debe FALLAR con
cada uno, tanto en la versión base como en la parcheada.

  doble_emision     un clic válido en «contraer» emite `contraccion_cambiada` DOS veces (estado final correcto)
  sin_emision       el clic cambia el estado pero no emite `contraccion_cambiada`
  estado_erroneo    el clic emite pero deja la navegación contraída (destino final erróneo)
  navegacion_rota   el clic en un botón de navegación no cambia la pestaña ni emite `seleccion_cambiada`
  boton_inoperable  el botón «contraer» no responde al clic (clicked desconectado)
"""
import os


def pytest_runtest_setup(item):
    mutante = os.environ.get("MUTANTE_3CA")
    if not mutante:
        return
    from app_icociv.interfaz.componentes import navegacion as nv

    clase = nv.NavegacionLateral
    if mutante == "doble_emision":
        original = clase.alternar_contraccion

        def doble(self):
            original(self)
            self.contraccion_cambiada.emit(self._contraida)
        clase.alternar_contraccion = doble
    elif mutante == "sin_emision":
        def silencioso(self):
            self.blockSignals(True)
            try:
                self.establecer_contraccion(not self._contraida)
            finally:
                self.blockSignals(False)
        clase.alternar_contraccion = silencioso
    elif mutante == "estado_erroneo":
        clase.alternar_contraccion = lambda self: self.establecer_contraccion(True)
    elif mutante == "navegacion_rota":
        original_init = clase.__init__

        def init_sin_nav(self, *a, **k):
            original_init(self, *a, **k)
            self._grupo.idClicked.disconnect()  # el clic ya no notifica la selección
        clase.__init__ = init_sin_nav
    elif mutante == "boton_inoperable":
        original_init = clase.__init__

        def init_inoperable(self, *a, **k):
            original_init(self, *a, **k)
            self.boton_contraer.clicked.disconnect()
        clase.__init__ = init_inoperable
    else:
        raise RuntimeError(f"mutante desconocido: {mutante}")
