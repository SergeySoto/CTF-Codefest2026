"""Baremo: puntos = coeficiente(dificultad) x segundos restantes."""

COEFICIENTES = {"Fácil": 1, "Media": 2, "Difícil": 3}


def puntos(coef: int, segundos_restantes: float) -> int:
    """Nunca negativo: si el tiempo se agotó, el envío no puntúa."""
    return max(0, int(coef * segundos_restantes))


def normalizar(entrada: str) -> str:
    """Tolerante: un principiante no puede perder por una mayúscula o un espacio."""
    return "".join(entrada.split()).lower()
