"""Carga de CPU controlada para la campaña de diagnóstico: N procesos en bucle durante S segundos."""
import multiprocessing as mp
import sys
import time


def quemar(fin):
    x = 0
    while time.time() < fin:
        x = (x * 1103515245 + 12345) % 2147483648


if __name__ == "__main__":
    n, s = int(sys.argv[1]), float(sys.argv[2])
    fin = time.time() + s
    ps = [mp.Process(target=quemar, args=(fin,)) for _ in range(n)]
    [p.start() for p in ps]
    [p.join() for p in ps]
