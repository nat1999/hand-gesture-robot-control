# PRUEBAS DEL CONTEO DE DEDOS

# Se prueba contar_dedos() sin cámara, inventando los puntos de la mano
# Para correrlas:
# PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test

import os
import sys

# Para poder importar Control_Robot.py que está en la carpeta de arriba
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Control_Robot import contar_dedos  # noqa: E402


# Arma una mano derecha falsa con los 21 puntos
# pulgar = True si el pulgar está abierto
# levantados = los dedos que van arriba ('indice', 'medio', 'anular', 'menique')
def mano(pulgar, levantados):
    lm = [(0, 0)] * 21
    lm[0] = (200, 400)                      # muñeca
    lm[17] = (260, 300)                     # nudillo del meñique
    lm[3] = (150, 330)                      # nudillo del pulgar
    # Pulgar abierto lejos del meñique, cerrado cerca
    lm[4] = (110, 320) if pulgar else (190, 330)
    # punta, articulación y posición en x de cada dedo
    columnas = {'indice': (8, 6, 170), 'medio': (12, 10, 200),
                'anular': (16, 14, 230), 'menique': (20, 18, 260)}
    for nombre, (punta, art, x) in columnas.items():
        lm[art] = (x, 250)
        # Levantado la punta queda arriba (y menor), bajado queda abajo
        lm[punta] = (x, 180) if nombre in levantados else (x, 290)
    return lm


# Voltea la mano para que quede como mano izquierda
def espejo(lm):
    return [(640 - x, y) for x, y in lm]


# Puño
def test_puno():
    assert contar_dedos(mano(False, set())) == 0


# Solo el indice
def test_un_dedo():
    assert contar_dedos(mano(False, {'indice'})) == 1


# Indice y medio
def test_dos_dedos():
    assert contar_dedos(mano(False, {'indice', 'medio'})) == 2


# Todos menos el pulgar
def test_cuatro_dedos():
    assert contar_dedos(mano(False, {'indice', 'medio', 'anular', 'menique'})) == 4


# Mano abierta
def test_palma_abierta():
    assert contar_dedos(mano(True, {'indice', 'medio', 'anular', 'menique'})) == 5


# Mano izquierda, para ver que el pulgar también funcione
def test_mano_izquierda():
    assert contar_dedos(espejo(mano(True, set()))) == 1
    assert contar_dedos(espejo(mano(False, set()))) == 0
