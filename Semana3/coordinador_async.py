import asyncio
import aiohttp


# CONTROL DE CONCURRENCIA
semaforo = asyncio.Semaphore(2)  # Cambia a 5 si quieres más concurrencia



# WRAPPER CON TIMEOUT INDIVIDUAL
async def with_timeout(coro, timeout, nombre):
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {nombre} excedió {timeout}s")
        return None
    except asyncio.CancelledError:
        print(f"[CANCELADA] {nombre}")
        raise



# PETICIÓN HTTP CON SEMÁFORO
async def fetch(session, url, nombre):
    async with semaforo:
        try:
            print(f"[INICIO] {nombre}")

            async with session.get(url) as resp:
                if resp.status == 401:
                    raise PermissionError("401 No autorizado")

                if resp.status >= 400:
                    print(f"[ERROR HTTP] {nombre} → {resp.status}")
                    return None

                data = await resp.json()

                print(f"[OK] {nombre} recibido")
                return data

        except asyncio.CancelledError:
            print(f"[CANCELADA] {nombre}")
            raise

        except Exception as e:
            print(f"[ERROR] {nombre}: {e}")
            return None


# CANCELACIÓN DE TAREAS RESTANTES
def cancel_remaining(tasks):
    for task in tasks:
        if not task.done():
            task.cancel()



# CARGA CON PRIORIDAD
async def cargar_con_prioridad(base_url):
    async with aiohttp.ClientSession() as session:

        tareas = {
            "productos": asyncio.create_task(
                with_timeout(
                    fetch(session, f"{base_url}/productos", "productos"),
                    5,
                    "productos"
                )
            ),
            "perfil": asyncio.create_task(
                with_timeout(
                    fetch(session, f"{base_url}/perfil", "perfil"),
                    2,
                    "perfil"
                )
            ),
            "categorias": asyncio.create_task(
                with_timeout(
                    fetch(session, f"{base_url}/categorias", "categorias"),
                    3,
                    "categorias"
                )
            ),
            "notificaciones": asyncio.create_task(
                with_timeout(
                    fetch(session, f"{base_url}/notificaciones", "notificaciones"),
                    4,
                    "notificaciones"
                )
            ),
        }

        resultados = {}
        criticos = {"productos", "perfil"}
        pending = set(tareas.values())

        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                nombre = next(k for k, v in tareas.items() if v == task)

                try:
                    resultado = task.result()
                    resultados[nombre] = resultado

                    if criticos.issubset(resultados.keys()):
                        print("[INFO] Dashboard parcial listo (productos + perfil)")

                except PermissionError:
                    print("[ERROR] Perfil no autorizado → cancelando tareas restantes")
                    cancel_remaining(pending)
                    return resultados

                except asyncio.CancelledError:
                    pass

        return resultados



# TEST TIMEOUT INDIVIDUAL
async def test_timeout_individual():
    print("\n=== TEST TIMEOUT INDIVIDUAL ===")

    async with aiohttp.ClientSession() as session:
        tareas = [
            with_timeout(fetch(session, "http://localhost:3000/productos", "productos"), 5, "productos"),
            with_timeout(fetch(session, "http://localhost:3000/categorias", "categorias"), 3, "categorias"),
            with_timeout(fetch(session, "http://localhost:3000/perfil", "perfil"), 2, "perfil"),
        ]

        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        print("Resultados finales:", resultados)



# TEST CANCELACIÓN Y PRIORIDAD
async def test_cancelacion_y_prioridad():
    print("\n=== TEST CANCELACIÓN Y PRIORIDAD ===")
    resultados = await cargar_con_prioridad("http://localhost:3000")
    print("Resultados finales:", resultados)



# MAIN
async def main():
    await test_timeout_individual()
    await test_cancelacion_y_prioridad()


if __name__ == "__main__":
    asyncio.run(main())