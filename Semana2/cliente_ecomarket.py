import requests
from urllib.parse import urljoin
from validadores import (
    validar_producto,
    validar_lista_productos,
    ValidationError
)

BASE_URL = "http://127.0.0.1:4010/"
TIMEOUT = 10
HEADERS_BASE = {"Content-Type": "application/json"}


class EcoMarketError(Exception):
    pass


class ServerError(EcoMarketError):
    pass


class ConflictError(EcoMarketError):
    pass


class ResourceNotFoundError(EcoMarketError):
    pass


def _verificar_respuesta(response):
    if response.status_code >= 500:
        raise ServerError(f"Error del servidor: {response.status_code}")

    if response.status_code == 404:
        raise ResourceNotFoundError("Recurso no encontrado")

    if response.status_code == 409:
        raise ConflictError("Conflicto de entidad")

    if response.status_code >= 400:
        raise ValidationError(f"Error cliente: {response.status_code}")

    if response.status_code != 204:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValidationError(f"Respuesta no es JSON: {content_type}")

    return response


def _parsear_json_seguro(response):
    try:
        return response.json()
    except ValueError:
        raise ValidationError("JSON malformado")



# PRODUCTOS
def listar_productos(categoria=None, orden=None):
    url = urljoin(BASE_URL, "products")

    params = {}
    if categoria:
        params["categoria"] = categoria
    if orden:
        params["orden"] = orden

    response = requests.get(url, params=params, timeout=TIMEOUT)
    _verificar_respuesta(response)

    data = _parsear_json_seguro(response)
    return validar_lista_productos(data)


def obtener_producto(producto_id):
    url = urljoin(BASE_URL, f"products/{producto_id}")

    response = requests.get(url, timeout=TIMEOUT)
    _verificar_respuesta(response)

    data = _parsear_json_seguro(response)
    return validar_producto(data)


def crear_producto(datos: dict):
    url = urljoin(BASE_URL, "products")

    response = requests.post(
        url,
        json=datos,
        headers=HEADERS_BASE,
        timeout=TIMEOUT
    )

    _verificar_respuesta(response)

    if response.status_code != 201:
        raise ValidationError("Se esperaba 201 Created")

    data = _parsear_json_seguro(response)
    return validar_producto(data)


def actualizar_producto_total(producto_id: int, datos: dict):
    url = urljoin(BASE_URL, f"products/{producto_id}")

    response = requests.put(
        url,
        json=datos,
        headers=HEADERS_BASE,
        timeout=TIMEOUT
    )

    _verificar_respuesta(response)

    data = _parsear_json_seguro(response)
    return validar_producto(data)


def actualizar_producto_parcial(producto_id: int, campos: dict):
    url = urljoin(BASE_URL, f"products/{producto_id}")

    response = requests.patch(
        url,
        json=campos,
        headers=HEADERS_BASE,
        timeout=TIMEOUT
    )

    _verificar_respuesta(response)

    data = _parsear_json_seguro(response)
    return validar_producto(data)


def eliminar_producto(producto_id: int):
    url = urljoin(BASE_URL, f"products/{producto_id}")

    response = requests.delete(url, timeout=TIMEOUT)
    _verificar_respuesta(response)

    if response.status_code != 204:
        raise ValidationError("Se esperaba 204 No Content")

    return True



# PRUEBA RÁPIDA

if __name__ == "__main__":
    try:
        print("Probando listar_productos...")
        productos = listar_productos()
        print("Respuesta:", productos)
    except Exception as e:
        print("Error:", e)
