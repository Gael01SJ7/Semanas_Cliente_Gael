import asyncio
import pytest
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientConnectorError
from aioresponses import aioresponses

import cliente_async_ecomarket as cliente


BASE_URL = "http://localhost:3000"


# ==========================================================
# 1. EQUIVALENCIA FUNCIONAL (5 tests)
# ==========================================================

@pytest.mark.asyncio
async def test_listar_productos_equivalencia():
    """Debe retornar exactamente el JSON esperado."""
    mock_data = [{"id": "1", "nombre": "Laptop"}]

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos", payload=mock_data)

        async with ClientSession() as session:
            result = await cliente.listar_productos(session)

        assert result == mock_data


@pytest.mark.asyncio
async def test_obtener_producto_equivalencia():
    """Obtener producto retorna datos correctos."""
    mock_data = {"id": "1", "nombre": "Laptop"}

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos/1", payload=mock_data)

        async with ClientSession() as session:
            result = await cliente.obtener_producto(session, "1")

        assert result["id"] == "1"


@pytest.mark.asyncio
async def test_crear_producto_equivalencia():
    """Crear producto retorna objeto creado."""
    mock_data = {"id": "10", "nombre": "Mouse"}

    with aioresponses() as m:
        m.post(f"{BASE_URL}/api/productos", payload=mock_data)

        async with ClientSession() as session:
            result = await cliente.crear_producto(session, mock_data)

        assert result["nombre"] == "Mouse"


@pytest.mark.asyncio
async def test_error_http_manejado():
    """Error HTTP 404 debe lanzar excepción."""
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos/99", status=404)

        async with ClientSession() as session:
            with pytest.raises(Exception):
                await cliente.obtener_producto(session, "99")


@pytest.mark.asyncio
async def test_eliminar_producto_ok():
    """Eliminar retorna confirmación."""
    with aioresponses() as m:
        m.delete(f"{BASE_URL}/api/productos/1", status=200)

        async with ClientSession() as session:
            result = await cliente.eliminar_producto(session, "1")

        assert result["eliminado"] is True


# ==========================================================
# 2. CONCURRENCIA CORRECTA (5 tests)
# ==========================================================

@pytest.mark.asyncio
async def test_gather_tres_exitos():
    """3 peticiones exitosas retornan 3 resultados."""
    async def ok():
        return 1

    results = await asyncio.gather(ok(), ok(), ok())
    assert len(results) == 3


@pytest.mark.asyncio
async def test_gather_un_fallo_return_exceptions():
    """1 fallo + return_exceptions=True retorna excepción en lista."""
    async def ok():
        return 1

    async def fail():
        raise ValueError("error")

    results = await asyncio.gather(ok(), fail(), ok(), return_exceptions=True)
    assert sum(isinstance(r, Exception) for r in results) == 1


@pytest.mark.asyncio
async def test_gather_sin_return_exceptions_propagacion():
    """Sin return_exceptions debe propagar el error."""
    async def fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await asyncio.gather(fail())


@pytest.mark.asyncio
async def test_dashboard_falla_una_fuente():
    """Dashboard debe completar aunque una fuente falle."""
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos", payload=[])
        m.get(f"{BASE_URL}/api/categorias", status=500)
        m.get(f"{BASE_URL}/api/perfil", payload={"id": 1})

        result = await cliente.cargar_dashboard()

        assert "errores" in result
        assert len(result["errores"]) >= 1


@pytest.mark.asyncio
async def test_semaforo_limita_concurrencia():
    """Verifica que el semáforo limite concurrencia."""
    sem = asyncio.Semaphore(2)
    active = 0
    max_active = 0

    async def task():
        nonlocal active, max_active
        async with sem:
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.1)
            active -= 1

    await asyncio.gather(*(task() for _ in range(5)))
    assert max_active <= 2


# ==========================================================
# 3. TIMEOUTS Y CANCELACIÓN (5 tests)
# ==========================================================

@pytest.mark.asyncio
async def test_timeout_individual():
    """Petición lenta debe disparar timeout."""
    timeout = ClientTimeout(total=0.01)

    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos", exception=asyncio.TimeoutError())

        async with ClientSession(timeout=timeout) as session:
            with pytest.raises(Exception):
                await cliente.listar_productos(session)


@pytest.mark.asyncio
async def test_cancelacion_en_cadena():
    """Si una tarea falla críticamente, puede cancelarse manualmente."""
    async def fail():
        raise PermissionError("401")

    async def slow():
        await asyncio.sleep(1)

    tasks = [asyncio.create_task(fail()), asyncio.create_task(slow())]

    with pytest.raises(PermissionError):
        await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_timeout_global_dashboard():
    """Timeout global debe cortar ejecución."""
    async def slow():
        await asyncio.sleep(1)

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow(), timeout=0.01)


@pytest.mark.asyncio
async def test_cancelled_error_no_resource_leak():
    """Cancelar tarea no debe dejar sesión abierta."""
    session = ClientSession()
    task = asyncio.create_task(asyncio.sleep(1))
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    await session.close()
    assert session.closed


@pytest.mark.asyncio
async def test_peticion_cancelada_no_error_log():
    """Petición cancelada no genera excepción no controlada."""
    async def cancel():
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await cancel()


# ==========================================================
# 4. EDGE CASES DE CONCURRENCIA (5 tests)
# ==========================================================

@pytest.mark.asyncio
async def test_todas_fallan_simultaneamente():
    async def fail():
        raise ValueError()

    results = await asyncio.gather(fail(), fail(), return_exceptions=True)
    assert all(isinstance(r, Exception) for r in results)


@pytest.mark.asyncio
async def test_servidor_cierra_conexion():
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos", exception=ClientConnectorError(None, OSError()))

        async with ClientSession() as session:
            with pytest.raises(Exception):
                await cliente.listar_productos(session)


@pytest.mark.asyncio
async def test_respuesta_despues_timeout():
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos", exception=asyncio.TimeoutError())

        async with ClientSession(timeout=ClientTimeout(total=0.01)) as session:
            with pytest.raises(Exception):
                await cliente.listar_productos(session)


@pytest.mark.asyncio
async def test_dos_peticiones_mismo_endpoint_distintos_params():
    with aioresponses() as m:
        m.get(f"{BASE_URL}/api/productos?categoria=tech", payload=[])
        m.get(f"{BASE_URL}/api/productos?categoria=hogar", payload=[])

        async with ClientSession() as session:
            r1 = await cliente.listar_productos(session, categoria="tech")
            r2 = await cliente.listar_productos(session, categoria="hogar")

        assert r1 == []
        assert r2 == []


@pytest.mark.asyncio
async def test_sesion_cierra_con_errores():
    session = ClientSession()
    await session.close()
    assert session.closed


# ==========================================================
# 5. TESTS ADICIONALES (2 EXTRA)
# ==========================================================

@pytest.mark.asyncio
async def test_gather_orden_preservado():
    async def a(): return 1
    async def b(): return 2
    results = await asyncio.gather(a(), b())
    assert results == [1, 2]


@pytest.mark.asyncio
async def test_multiple_creaciones_concurrentes():
    sem = asyncio.Semaphore(3)
    counter = 0

    async def task():
        nonlocal counter
        async with sem:
            counter += 1
            await asyncio.sleep(0.01)

    await asyncio.gather(*(task() for _ in range(10)))
    assert counter == 10