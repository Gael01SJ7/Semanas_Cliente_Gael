"""
Monitor de Inventario - EcoMarket
ServicioPolling con polling adaptativo usando ETag.

Trade-off del polling:
El polling permite consultar periódicamente una API para detectar cambios en los datos.
Si el intervalo es muy corto, puede generar demasiadas solicitudes innecesarias.

El uso de ETag permite que el cliente pregunte al servidor si los datos han cambiado
sin tener que descargar toda la información nuevamente. Si los datos no cambiaron,
el servidor responde con 304 Not Modified y no envía el contenido completo.

Esto reduce el consumo de red y mejora la eficiencia del monitoreo del inventario.
"""

import asyncio
import aiohttp
from datetime import datetime


class Observable:
    def __init__(self):
        self._observadores = []

    def suscribir(self, funcion):
        self._observadores.append(funcion)

    def notificar(self, datos):
        for obs in self._observadores:
            obs(datos)


class ServicioPolling(Observable):
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.etag = None
        self.intervalo = 5
        self._activo = False
        self.max_intervalo = 60

    async def _consultar(self, session):
        headers = {}

        if self.etag:
            headers["If-None-Match"] = self.etag

        try:
            async with session.get(self.url, headers=headers, timeout=10) as resp:

                if resp.status == 200:
                    datos = await resp.json()

                    self.etag = resp.headers.get("ETag")

                    print(f"{datetime.now()} | 200 OK | intervalo={self.intervalo}s")

                    self.notificar(datos)

                    self.intervalo = 5

                elif resp.status == 304:
                    print(f"{datetime.now()} | 304 Not Modified | intervalo={self.intervalo}s")

                    self.intervalo = min(self.intervalo * 2, self.max_intervalo)

                else:
                    print(f"{datetime.now()} | Error HTTP {resp.status}")

        except Exception as e:
            print(f"{datetime.now()} | Error: {e}")

    async def iniciar(self, ciclos=5):
        self._activo = True

        async with aiohttp.ClientSession() as session:
            contador = 0

            while self._activo and contador < ciclos:
                await self._consultar(session)
                await asyncio.sleep(self.intervalo)
                contador += 1

    def detener(self):
        self._activo = False


# Observadores (funciones independientes)

def observador_ui(productos):
    print("Productos recibidos:", len(productos))


def observador_stock(productos):
    for p in productos:
        if "stock" in p and p["stock"] == 0:
            print(f"⚠ Producto agotado: {p['name']}")


def observador_error(datos):
    pass


async def main():
    url = "https://jsonplaceholder.typicode.com/posts"

    monitor = ServicioPolling(url)

    monitor.suscribir(observador_ui)
    monitor.suscribir(observador_stock)
    monitor.suscribir(observador_error)

    await monitor.iniciar(ciclos=5)

    monitor.detener()


if __name__ == "__main__":
    asyncio.run(main())