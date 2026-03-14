import asyncio
from datetime import datetime

class MonitorInventario:
    def __init__(self):
        self._observadores = []
        self._ultimo_estado = None
        self._ejecutando = False
        self._intervalo = 2  # más rápido para prueba

    def suscribir(self, obs):
        self._observadores.append(obs)

    async def _notificar(self, inventario):
        for obs in self._observadores:
            try:
                await obs.actualizar(inventario)
            except Exception:
                pass

    async def _consultar_inventario(self):
        # Simulamos un inventario nuevo cada vez
        inventario = {
            "productos": [
                {"id": "PROD-001", "nombre": "Arroz Premium", "stock": 45, "stock_minimo": 50, "status": "BAJO_MINIMO"},
                {"id": "PROD-002", "nombre": "Aceite 1L", "stock": 120, "stock_minimo": 30, "status": "NORMAL"}
            ],
            "ultima_actualizacion": datetime.utcnow().isoformat() + "Z"
        }
        return inventario

    async def iniciar(self):
        self._ejecutando = True
        while self._ejecutando:
            inventario = await self._consultar_inventario()
            if inventario != self._ultimo_estado:
                self._ultimo_estado = inventario
                await self._notificar(inventario)
            await asyncio.sleep(self._intervalo)

    def detener(self):
        self._ejecutando = False

class ModuloCompras:
    async def actualizar(self, inventario):
        print("ModuloCompras: productos bajo mínimo")
        for p in inventario["productos"]:
            if p["status"] == "BAJO_MINIMO":
                print(f"- {p['nombre']} Stock: {p['stock']} Mínimo: {p['stock_minimo']}")

class ModuloAlertas:
    async def actualizar(self, inventario):
        print("ModuloAlertas: revisar alertas")
        for p in inventario["productos"]:
            if p["status"] == "BAJO_MINIMO":
                print(f"Alerta: {p['nombre']} está bajo mínimo!")

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