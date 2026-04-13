import asyncio
import logging
import json
from typing import Callable, Dict, Any, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# OBSERVABLE 
class Observable:
    def __init__(self):
        self._suscriptores: List[Callable] = []

    def suscribir(self, fn: Callable):
        if fn not in self._suscriptores:
            self._suscriptores.append(fn)

    async def _notificar(self, evento: Dict[str, Any]):
        for fn in self._suscriptores:
            try:
                await fn(evento)
            except Exception as e:
                logger.error(f"Error en suscriptor: {e}")


# CLIENTE SSE + OBSERVER
class ReceptorAlertas(Observable):
    def __init__(self):
        super().__init__()
        self.ejecutando = True

    async def iniciar(self):
        logger.info("Iniciando receptor SSE con Observer...")

        # Simulación de 10 eventos mixtos
        eventos = [
            {"event": "producto_actualizado", "data": {"id": "P1", "precio": 100}},
            {"event": "stock_critico", "data": {"producto": "Arroz", "stock": 2}},
            {"event": "nuevo_pedido", "data": {"id": "PED1", "cliente": "Ana"}},
            {"event": "producto_actualizado", "data": {"id": "P2", "precio": 200}},
            {"event": "stock_critico", "data": {"producto": "Frijol", "stock": 1}},
            {"event": "nuevo_pedido", "data": {"id": "PED2", "cliente": "Luis"}},
            {"event": "producto_actualizado", "data": {"id": "P3", "precio": 300}},
            {"event": "stock_critico", "data": {"producto": "Azúcar", "stock": 3}},
            {"event": "nuevo_pedido", "data": {"id": "PED3", "cliente": "Maria"}},
            {"event": "producto_actualizado", "data": {"id": "P4", "precio": 400}},
        ]

        for evento in eventos:
            if not self.ejecutando:
                break

            await self.procesar_evento(evento)
            await asyncio.sleep(1)

        logger.info("Receptor detenido")

    async def procesar_evento(self, evento: Dict[str, Any]):
        tipo = evento.get("event")

        logger.info(f"Evento SSE recibido: {tipo}")

        # Aquí ocurre la magia del Observer
        await self._notificar(evento)

    def detener(self):
        self.ejecutando = False


# SUSCRIPTORES (FUNCIONES)
async def actualizador_precios_ui(evento):
    if evento.get("event") == "producto_actualizado":
        data = evento.get("data", {})
        logger.info(f"[UI] Actualizando precio: {data}")


async def alerta_stock_critico(evento):
    if evento.get("event") == "stock_critico":
        data = evento.get("data", {})
        logger.warning(f"[ALERTA] Stock crítico: {data}")


auditoria_log = []

async def registrador_auditoria(evento):
    registro = {
        "timestamp": datetime.now().isoformat(),
        "tipo": evento.get("event"),
        "data": evento.get("data")
    }
    auditoria_log.append(registro)
    logger.info(f"[AUDITORIA] Evento registrado: {registro}")


# MAIN
async def main():
    receptor = ReceptorAlertas()

    # Suscribir funciones
    receptor.suscribir(actualizador_precios_ui)
    receptor.suscribir(alerta_stock_critico)
    receptor.suscribir(registrador_auditoria)

    tarea = asyncio.create_task(receptor.iniciar())

    await asyncio.sleep(12)

    receptor.detener()
    await tarea


if __name__ == "__main__":
    asyncio.run(main())