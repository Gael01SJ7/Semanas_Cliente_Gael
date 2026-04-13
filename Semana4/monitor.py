import asyncio
import logging
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


#OBSERVER
class Observador(ABC):
    @abstractmethod
    async def actualizar(self, datos: Dict[str, Any]) -> None:
        pass


class Observable:
    def __init__(self):
        self._observadores: List[Observador] = []

    def suscribir(self, obs: Observador):
        self._observadores.append(obs)

    async def notificar(self, datos: Dict[str, Any]):
        for obs in self._observadores:
            try:
                await obs.actualizar(datos)
            except Exception as e:
                logger.error(f"Error en observador: {e}")


#SERVICIO DE POLLING
class ServicioPolling:
    def __init__(self):
        self.etag = None
        self.backoff = 1

    async def consultar_api(self):
        """
        Simula una API con ETag.
        """
        await asyncio.sleep(1)

        nuevo_etag = random.choice(["A", "B", "C"])

        if nuevo_etag == self.etag:
            return 304, None, self.etag

        self.etag = nuevo_etag
        data = {
            "producto": "Arroz",
            "stock": random.randint(1, 10)
        }

        return 200, data, self.etag


# MONITOR
class MonitorInventario(Observable):
    def __init__(self):
        super().__init__()
        self.servicio = ServicioPolling()
        self.ejecutando = True

    async def iniciar(self):
        while self.ejecutando:
            try:
                status, data, etag = await self.servicio.consultar_api()

                if status == 200:
                    logger.info(f"Cambio detectado: {data}")
                    await self.notificar(data)
                    self.servicio.backoff = 1

                elif status == 304:
                    logger.info("Sin cambios")
                    self.servicio.backoff = min(self.servicio.backoff * 2, 10)

                await asyncio.sleep(self.servicio.backoff)

            except Exception as e:
                logger.error(f"Error en polling: {e}")

    def detener(self):
        self.ejecutando = False



# OBSERVADORES
class UIObservador(Observador):
    async def actualizar(self, datos):
        logger.info(f"[UI] Mostrando datos: {datos}")


class AlertaObservador(Observador):
    async def actualizar(self, datos):
        if datos["stock"] <= 3:
            logger.warning(f"[ALERTA] Stock bajo: {datos}")


class LogObservador(Observador):
    async def actualizar(self, datos):
        logger.info(f"[LOG] Registro: {datos}")



# MAIN
async def main():
    monitor = MonitorInventario()

    monitor.suscribir(UIObservador())
    monitor.suscribir(AlertaObservador())
    monitor.suscribir(LogObservador())

    tarea = asyncio.create_task(monitor.iniciar())

    await asyncio.sleep(10)

    monitor.detener()
    await tarea


if __name__ == "__main__":
    asyncio.run(main())