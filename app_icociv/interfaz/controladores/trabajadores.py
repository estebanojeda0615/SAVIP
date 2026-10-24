"""Trabajadores Qt para ejecutar tareas pesadas fuera del hilo de UI."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QThread, Signal


class TrabajadorFuncion(QThread):
    """Ejecuta una función en segundo plano y emite resultado o error.

    Con ``informar_progreso=True`` la función recibe como primer argumento ``informar(hechos, total)``,
    que emite ``progreso`` desde el hilo de trabajo; Qt la entrega en el hilo de la interfaz (conexión
    en cola), donde se actualizan los widgets. Solo se usa cuando el avance se puede contar de verdad.
    """

    resultado = Signal(object)
    error = Signal(str)
    progreso = Signal(int, int)

    def __init__(self, funcion: Callable[..., Any], *args: Any, informar_progreso: bool = False, **kwargs: Any) -> None:
        super().__init__()
        self.funcion = funcion
        self.args = (self.progreso.emit, *args) if informar_progreso else args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            self.resultado.emit(self.funcion(*self.args, **self.kwargs))
        except Exception as exc:
            self.error.emit(str(exc))
