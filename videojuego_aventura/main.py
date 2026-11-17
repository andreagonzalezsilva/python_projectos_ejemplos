"""Punto de entrada de Aventura Ecuador. Ejecutar con: python main.py"""
import os
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RAIZ, "src"))
sys.path.insert(0, RAIZ)


def main():
    from motor import Motor
    from escenas import Titulo

    motor = Motor()
    motor.cambiar_escena(Titulo(motor))
    motor.ejecutar()


if __name__ == "__main__":
    main()
