import asyncio
import aiohttp
from abc import ABC, abstractmethod
from datetime import datetime

BASE_URL = "http://ecomarket.local/api/v1"
TOKEN = "eyJ0eXAiO..." 
INTERVALO_BASE = 5
INTERVALO_MAX = 60
TIMEOUT = 10

class Observador(ABC):
    @abstractmethod
    async def actualizar(self, inventario: dict):
        pass

class MonitorInventario:
    def __init__(self):
        self._observadores = []
        self._ultimo_etag = None
        self._ultimo_estado = None
        self._ejecutando = False
        self._intervalo = INTERVALO_BASE

    def suscribir(self, obs: Observador):
        self._observadores.append(obs)

    def desuscribir(self, obs: Observador):
        if obs in self._observadores:
            self._observadores.remove(obs)

    async def _notificar(self, inventario: dict):
        for obs in self._observadores:
            try:
                await obs.actualizar(inventario)
            except Exception as e:
                print(f"Warning: observador {obs} falló: {e}")

    async def _consultar_inventario(self):
        headers = {"Authorization": f"Bearer {TOKEN}"}
        if self._ultimo_etag:
            headers["If-None-Match"] = self._ultimo_etag

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/inventario", headers=headers, timeout=TIMEOUT) as resp:
                    status = resp.status
                    if status == 200:
                        etag = resp.headers.get("ETag")
                        data = await resp.json()
                        if "productos" not in data:
                            print("Warning: inventario incompleto")
                            return None
                        self._ultimo_etag = etag
                        self._ultimo_estado = data
                        self._intervalo = INTERVALO_BASE
                        return data
                    elif status == 304:
                        self._intervalo = min(self._intervalo * 2, INTERVALO_MAX)
                        return None
                    elif status in (400, 401):
                        print(f"Error {status}: {resp.reason}")
                        return None
                    elif status >= 500:
                        print(f"Server error {status}, aplicando backoff")
                        self._intervalo = min(self._intervalo * 2, INTERVALO_MAX)
                        return None
        except (asyncio.TimeoutError, aiohttp.ClientError):
            print("Warning: No se pudo conectar, usando inventario simulado")
            return {
                "productos": [
                    {"id": "PROD-001", "nombre": "Arroz Premium 5kg", "stock": 45, "stock_minimo": 50, "status": "BAJO_MINIMO"},
                    {"id": "PROD-002", "nombre": "Aceite Vegetal 1L", "stock": 120, "stock_minimo": 30, "status": "NORMAL"}
                ],
                "ultima_actualizacion": datetime.utcnow().isoformat() + "Z"
            }

    async def iniciar(self):
        self._ejecutando = True
        while self._ejecutando:
            inventario = await self._consultar_inventario()
            if inventario and inventario != self._ultimo_estado:
                await self._notificar(inventario)
            await asyncio.sleep(self._intervalo)

    def detener(self):
        self._ejecutando = False

class ModuloCompras(Observador):
    async def actualizar(self, inventario: dict):
        print("ModuloCompras: productos bajo mínimo")
        for p in inventario.get("productos", []):
            if p.get("status") == "BAJO_MINIMO":
                print(f"- {p['nombre']} Stock: {p['stock']} Mínimo: {p['stock_minimo']}")

class ModuloAlertas(Observador):
    async def actualizar(self, inventario: dict):
        async with aiohttp.ClientSession() as session:
            for p in inventario.get("productos", []):
                if p.get("status") == "BAJO_MINIMO":
                    payload = {
                        "producto_id": p["id"],
                        "stock_actual": p["stock"],
                        "stock_minimo": p["stock_minimo"],
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                    try:
                        async with session.post(f"{BASE_URL}/alertas", json=payload) as resp:
                            if resp.status == 201:
                                print(f"Alerta enviada: {p['nombre']}")
                            elif resp.status == 422:
                                print(f"Alerta inválida (422) para {p['nombre']}")
                    except aiohttp.ClientError as e:
                        print(f"Error al enviar alerta: {e}")

async def main():
    monitor = MonitorInventario()
    monitor.suscribir(ModuloCompras())
    monitor.suscribir(ModuloAlertas())
    try:
        await monitor.iniciar()
    except KeyboardInterrupt:
        monitor.detener()
        print("Monitor detenido por usuario")

if __name__ == "__main__":
    asyncio.run(main())