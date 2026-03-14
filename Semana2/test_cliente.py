import pytest
import responses
from cliente_ecomarket import (
    listar_productos, obtener_producto, crear_producto,
    actualizar_producto_total, actualizar_producto_parcial, eliminar_producto,
    BASE_URL, ValidationError, ServerError, ResourceNotFoundError
)

PRODUCTO_EJEMPLO = {
    "id": 1,
    "nombre": "Manzana",
    "precio": 20.0,
    "categoria": "frutas"
}


@responses.activate
def test_listar_productos_happy_path():
    responses.add(responses.GET, f"{BASE_URL}products", json=[PRODUCTO_EJEMPLO], status=200)
    productos = listar_productos()
    assert len(productos) == 1
    assert productos[0]['nombre'] == "Manzana"


@responses.activate
def test_obtener_producto_happy_path():
    responses.add(responses.GET, f"{BASE_URL}products/1", json=PRODUCTO_EJEMPLO, status=200)
    prod = obtener_producto(1)
    assert prod['id'] == 1


@responses.activate
def test_crear_producto_happy_path():
    responses.add(responses.POST, f"{BASE_URL}products", json=PRODUCTO_EJEMPLO, status=201)
    prod = crear_producto({"nombre": "Manzana", "precio": 20, "categoria": "frutas"})
    assert prod['id'] == 1


@responses.activate
def test_eliminar_happy_path():
    responses.add(responses.DELETE, f"{BASE_URL}products/1", status=204)
    assert eliminar_producto(1) is True


@responses.activate
def test_producto_precio_negativo_validacion():
    prod_malo = PRODUCTO_EJEMPLO.copy()
    prod_malo['precio'] = -10
    responses.add(responses.GET, f"{BASE_URL}products/1", json=prod_malo, status=200)
    with pytest.raises(ValidationError):
        obtener_producto(1)

import requests

@responses.activate
def test_timeout_global():
    responses.add(
        responses.GET,
        f"{BASE_URL}products",
        body=requests.exceptions.Timeout()
    )

    with pytest.raises(ServerError):
        listar_productos()

