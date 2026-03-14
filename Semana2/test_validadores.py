import pytest
from validadores import validar_producto, ValidationError


def test_validar_producto_exito():
    data = {"id": 1, "nombre": "Miel", "precio": 10.5, "categoria": "miel"}
    assert validar_producto(data) == data


def test_validar_producto_falta_campo():
    data = {"nombre": "Miel", "precio": 10.5, "categoria": "miel"}
    with pytest.raises(ValidationError):
        validar_producto(data)


def test_validar_producto_tipo_incorrecto():
    data = {"id": "no-es-int", "nombre": "Miel", "precio": 10.5, "categoria": "miel"}
    with pytest.raises(ValidationError):
        validar_producto(data)


def test_validar_producto_precio_negativo():
    data = {"id": 1, "nombre": "Miel", "precio": -5, "categoria": "miel"}
    with pytest.raises(ValidationError):
        validar_producto(data)


def test_validar_producto_categoria_invalida():
    data = {"id": 1, "nombre": "Miel", "precio": 10.5, "categoria": "plastico"}
    with pytest.raises(ValidationError):
        validar_producto(data)


def test_validar_producto_fecha_invalida():
    data = {
        "id": 1, "nombre": "Miel", "precio": 10.5,
        "categoria": "miel", "creado_en": "fecha-rara"
    }
    with pytest.raises(ValidationError):
        validar_producto(data)
