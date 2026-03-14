from datetime import datetime


class ValidationError(Exception):
    pass


CATEGORIAS_VALIDAS = ["frutas", "verduras", "miel"]


def validar_producto(data: dict):

    campos_requeridos = ["id", "nombre", "precio", "categoria"]

    for campo in campos_requeridos:
        if campo not in data:
            raise ValidationError(f"Falta campo requerido: {campo}")

    if not isinstance(data["id"], int):
        raise ValidationError("id debe ser int")

    if not isinstance(data["nombre"], str):
        raise ValidationError("nombre debe ser string")

    if not isinstance(data["precio"], (int, float)):
        raise ValidationError("precio debe ser number")

    if data["precio"] < 0:
        raise ValidationError("precio debe ser positivo")

    if data["categoria"] not in CATEGORIAS_VALIDAS:
        raise ValidationError("categoria inválida")

    if "creado_en" in data:
        try:
            datetime.fromisoformat(data["creado_en"].replace("Z", "+00:00"))
        except Exception:
            raise ValidationError("creado_en debe ser fecha ISO válida")

    return data


def validar_lista_productos(lista):
    if not isinstance(lista, list):
        raise ValidationError("Se esperaba lista de productos")

    return [validar_producto(p) for p in lista]
