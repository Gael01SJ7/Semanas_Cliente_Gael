import asyncio
import time

async def get_products():
    await asyncio.sleep(0.5)
    return "Productos OK"

async def get_categories():
    await asyncio.sleep(0.5)
    raise asyncio.TimeoutError("Timeout en /categories")

async def get_profile():
    await asyncio.sleep(0.5)
    return "Perfil OK"

async def main():
    start = time.time()

    results = await asyncio.gather(
        get_products(),
        get_categories(),
        get_profile(),
        return_exceptions=True
    )

    for r in results:
        if isinstance(r, Exception):
            print("Error:", r)
        else:
            print("Resultado:", r)

    print("Tiempo total:", time.time() - start)

asyncio.run(main())
