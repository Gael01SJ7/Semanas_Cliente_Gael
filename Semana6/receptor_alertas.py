import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClienteSSE:
    def __init__(self, url: str):
        self.url = url
        self.ultimo_id: Optional[str] = None
        self.ejecutando = True
        self.reintentos = 0
        self.max_reintentos = 5
        self.retry_ms = 3000

    async def conectar(self):
        timeout = aiohttp.ClientTimeout(total=30)

        while self.ejecutando and self.reintentos < self.max_reintentos:
            try:
                headers = {"Accept": "text/event-stream"}

                if self.ultimo_id:
                    headers["Last-Event-ID"] = self.ultimo_id
                    logger.info(f"Reconexion con Last-Event-ID: {self.ultimo_id}")

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(self.url, headers=headers) as resp:

                        if resp.status == 204:
                            logger.info("Servidor indico fin del stream")
                            break

                        if resp.status != 200:
                            raise Exception(f"HTTP {resp.status}")

                        logger.info("Conectado al stream SSE")

                        buffer = []

                        async for linea in resp.content:
                            linea = linea.decode().strip()

                            if linea == "":
                                if buffer:
                                    evento = self._parsear_evento(buffer)
                                    buffer = []

                                    if evento:
                                        await self.procesar_evento(evento)
                                continue

                            buffer.append(linea)

            except asyncio.TimeoutError:
                logger.error("Timeout en conexion")

            except Exception as e:
                logger.error(f"Error: {e}")

            self.reintentos += 1
            espera = (self.retry_ms / 1000) * (2 ** self.reintentos)
            logger.info(f"Reconectando en {espera}s...")
            await asyncio.sleep(espera)

        logger.info("Cliente detenido")

    def _parsear_evento(self, lineas):
        evento = {}

        for linea in lineas:
            if linea.startswith("id:"):
                evento["id"] = linea[3:].strip()

            elif linea.startswith("event:"):
                evento["event"] = linea[6:].strip()

            elif linea.startswith("data:"):
                data = linea[5:].strip()
                try:
                    evento["data"] = json.loads(data)
                except:
                    evento["data"] = data

            elif linea.startswith("retry:"):
                self.retry_ms = int(linea[6:].strip())

        return evento

    async def procesar_evento(self, evento: Dict[str, Any]):
        if "id" in evento:
            self.ultimo_id = evento["id"]

        tipo = evento.get("event", "desconocido")

        if tipo == "producto_actualizado":
            data = evento.get("data", {})
            logger.info(f"Producto actualizado: {data}")

        elif tipo == "stock_critico":
            data = evento.get("data", {})
            logger.warning(f"Stock critico: {data}")

        elif tipo == "nuevo_pedido":
            data = evento.get("data", {})
            logger.info(f"Nuevo pedido: {data}")

        else:
            logger.info(f"Evento recibido: {evento}")

    def detener(self):
        self.ejecutando = False


async def main():
    cliente = ClienteSSE("https://sse.dev/test")

    tarea = asyncio.create_task(cliente.conectar())

    await asyncio.sleep(15)

    cliente.detener()
    await tarea


if __name__ == "__main__":
    asyncio.run(main())