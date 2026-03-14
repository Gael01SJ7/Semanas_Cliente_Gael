import asyncio
import aiohttp
from aiohttp import ClientTimeout, ClientConnectorError

BASE_URL = "http://localhost:3000"



# WRAPPER HTTP GENERICO
async def request_json(session, method, url, semaforo=None, timeout_seg=5, **kwargs):
    if semaforo is None:
        semaforo = asyncio.Semaphore(1000)  # prácticamente sin límite

    try:
        async with semaforo:
            async with session.request(
                method,
                url,
                timeout=ClientTimeout(total=timeout_seg),
                **kwargs
            ) as response:
                response.raise_for_status()
                if response.status == 204:
                    return None
                return await response.json()

    except asyncio.TimeoutError:
        raise Exception(f"Timeout en {url}")

    except ClientConnectorError:
        raise Exception("Servidor inalcanzable")

    except aiohttp.ClientResponseError as e:
        raise Exception(f"Error HTTP {e.status} en {url}")



# FUNCIONES CRUD API PUBLICA ESTABLE

async def listar_productos(session, categoria=None, orden=None, semaforo=None):
    params = {}
    if categoria:
        params["categoria"] = categoria
    if orden:
        params["orden"] = orden

    return await request_json(
        session,
        "GET",
        f"{BASE_URL}/api/productos",
        semaforo,
        params=params
    )


async def obtener_producto(session, producto_id, semaforo=None):
    return await request_json(
        session,
        "GET",
        f"{BASE_URL}/api/productos/{producto_id}",
        semaforo
    )


async def crear_producto(session, datos, semaforo=None):
    return await request_json(
        session,
        "POST",
        f"{BASE_URL}/api/productos",
        semaforo,
        json=datos
    )


async def actualizar_producto_total(session, producto_id, datos, semaforo=None):
    return await request_json(
        session,
        "PUT",
        f"{BASE_URL}/api/productos/{producto_id}",
        semaforo,
        json=datos
    )


async def actualizar_producto_parcial(session, producto_id, campos, semaforo=None):
    return await request_json(
        session,
        "PATCH",
        f"{BASE_URL}/api/productos/{producto_id}",
        semaforo,
        json=campos
    )


async def eliminar_producto(session, producto_id, semaforo=None):
    await request_json(
        session,
        "DELETE",
        f"{BASE_URL}/api/productos/{producto_id}",
        semaforo
    )
    return {"eliminado": True}



# FUNCIONES AUXILIARES DASHBOARD
async def obtener_categorias(session, semaforo=None):
    return await request_json(
        session,
        "GET",
        f"{BASE_URL}/api/categorias",
        semaforo
    )


async def obtener_perfil(session, semaforo=None):
    return await request_json(
        session,
        "GET",
        f"{BASE_URL}/api/perfil",
        semaforo
    )



# DASHBOARD
async def cargar_dashboard():
    semaforo = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        tareas = {
            "productos": listar_productos(session, semaforo=semaforo),
            "categorias": obtener_categorias(session, semaforo=semaforo),
            "perfil": obtener_perfil(session, semaforo=semaforo),
        }

        resultados = await asyncio.gather(
            *tareas.values(),
            return_exceptions=True
        )

        datos = {}
        errores = {}

        for key, resultado in zip(tareas.keys(), resultados):
            if isinstance(resultado, Exception):
                errores[key] = str(resultado)
            else:
                datos[key] = resultado

        return {
            "datos": datos,
            "errores": errores
        }



# CREAR MULTIPLES PRODUCTOS
async def crear_multiples_productos(lista_productos):
    semaforo = asyncio.Semaphore(10)

    async with aiohttp.ClientSession() as session:
        tareas = [
            crear_producto(session, producto, semaforo=semaforo)
            for producto in lista_productos
        ]

        resultados = await asyncio.gather(
            *tareas,
            return_exceptions=True
        )

        creados = []
        fallidos = []

        for producto, resultado in zip(lista_productos, resultados):
            if isinstance(resultado, Exception):
                fallidos.append({
                    "producto": producto,
                    "error": str(resultado)
                })
            else:
                creados.append(resultado)

        return creados, fallidos


if __name__ == "__main__":
    import time

    inicio = time.time()
    resultado = asyncio.run(cargar_dashboard())
    fin = time.time()

    print("\nResultado del dashboard:")
    print(resultado)
    print("Tiempo total:", round(fin - inicio, 3), "segundos")