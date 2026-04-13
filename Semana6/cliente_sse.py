# 🎯 RETO 2: APLICA - CLIENTE SSE COMPLETO
## Semana 6 - Programación Distribuida del Lado del Cliente

"""
SIMULACRO DEL EXAMEN: Construir un cliente SSE funcional.

ESCENARIO:
  EcoMarket necesita un cliente que reciba alertas en tiempo real sobre:
  1. Cambios de precio de productos
  2. Stock crítico
  3. Nuevos pedidos
  
ENDPOINTS:
  GET /eventos → Server-Sent Events
  Headers esperados: Last-Event-ID (para reconexiones)
  
Tipos de eventos del servidor:
  event: producto_actualizado
  event: stock_critico
  event: nuevo_pedido
  event: error (cuando el servidor tiene problemas)
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==========================================
# INTERFAZ OBSERVADOR (igual que Semana 5)
# ==========================================

class Observador(ABC):
    """Todo observador debe implementar este método"""
    
    @abstractmethod
    async def actualizar(self, evento: Dict[str, Any]) -> None:
        pass


# ==========================================
# OBSERVABLE (igual que Semana 5)
# ==========================================

class Observable:
    """Patrón Observer: mantiene lista de observadores y notifica"""
    
    def __init__(self):
        self._observadores: List[Observador] = []
    
    def suscribir(self, observador: Observador) -> None:
        if observador not in self._observadores:
            self._observadores.append(observador)
            logger.info(f"✅ Suscrito: {observador.__class__.__name__}")
    
    def desuscribir(self, observador: Observador) -> None:
        if observador in self._observadores:
            self._observadores.remove(observador)
            logger.info(f"❌ Desuscrito: {observador.__class__.__name__}")
    
    async def _notificar(self, evento: Dict[str, Any]) -> None:
        """Notifica a TODOS los observadores de forma idéntica"""
        for observador in self._observadores:
            try:
                await observador.actualizar(evento)
            except Exception as e:
                logger.error(f"⚠️ Error en observador {observador.__class__.__name__}: {e}")



# CLIENTE SSE (NUEVO EN SEMANA 6)
class ClienteSSE(Observable):
    """
    Cliente que se conecta a un endpoint SSE y recibe eventos en tiempo real.
    """
    
    # Constantes
    BASE_URL = "http://localhost:8000"
    TIMEOUT_SSE = 30  # Más largo que Semana 5 
    BACKOFF_INICIAL = 2  # segundos
    BACKOFF_MAX = 60  # segundos
    
    def __init__(self, base_url: str = BASE_URL):
        super().__init__()
        self.base_url = base_url
        self.ejecutando = False
        self.ultimo_id: Optional[str] = None
        self.backoff_actual = self.BACKOFF_INICIAL
        logger.info(f"📍 ClienteSSE inicializado: {base_url}")
    
    async def conectar(self) -> None:
        """
        Conectar al servidor SSE y comenzar a recibir eventos.
        """
        self.ejecutando = True
        logger.info("Conectando a SSE...")
        
        while self.ejecutando:
            try:
                # Preparar headers
                headers = {}
                if self.ultimo_id:
                    headers["Last-Event-ID"] = self.ultimo_id
                    logger.debug(f"Last-Event-ID: {self.ultimo_id}")
                
                # Importar aquí para que sea más flexible
                import urllib.request
                
                req = urllib.request.Request(
                    f"{self.base_url}/eventos",
                    headers=headers
                )
                
                # Simular SSE (en producción usarías aiohttp)
                await self._leer_stream_simulado()
                
            except asyncio.TimeoutError:
                logger.error(f"⏱️  Timeout en conexión SSE")
                self.backoff_actual = min(
                    self.backoff_actual * 2,
                    self.BACKOFF_MAX
                )
                logger.info(f"Reconectando en {self.backoff_actual}s...")
                await asyncio.sleep(self.backoff_actual)
            
            except Exception as e:
                logger.error(f"🔴 Error en SSE: {type(e).__name__}: {e}")
                self.backoff_actual = min(
                    self.backoff_actual * 2,
                    self.BACKOFF_MAX
                )
                await asyncio.sleep(self.backoff_actual)
        
        logger.info("Cliente SSE detenido")
    
    async def _leer_stream_simulado(self) -> None:
      
        # Simular eventos que el servidor enviaría
        eventos_simulados = [
            "id: 1\nevent: producto_actualizado\ndata: {\"id\": \"P001\", \"precio\": 450.00}\n\n",
            "id: 2\nevent: stock_critico\ndata: {\"producto\": \"Arroz\", \"stock\": 5}\n\n",
            "id: 3\nevent: nuevo_pedido\ndata: {\"id\": \"PED001\", \"cliente\": \"Ana\", \"total\": 120.50}\n\n",
        ]
        
        evento_actual = {}
        
        for evento_texto in eventos_simulados:
            if not self.ejecutando:
                break
            
            for linea in evento_texto.split('\n'):
                linea = linea.strip()
                
                if not linea:
                    # Línea vacía = fin del evento
                    if evento_actual.get("data"):
                        self.ultimo_id = evento_actual.get("id", self.ultimo_id)
                        # Resetear backoff cuando recibimos evento exitosamente
                        self.backoff_actual = self.BACKOFF_INICIAL
                        await self._notificar(evento_actual)
                    evento_actual = {}
                
                elif linea.startswith("id:"):
                    evento_actual["id"] = linea[4:].strip()
                
                elif linea.startswith("event:"):
                    evento_actual["event"] = linea[7:].strip()
                
                elif linea.startswith("data:"):
                    evento_actual["data"] = linea[6:].strip()
                
                elif linea.startswith("retry:"):
                    evento_actual["retry"] = int(linea[7:].strip())
            
            # Simular latencia de red
            await asyncio.sleep(1)
    
    async def _notificar(self, evento: Dict[str, Any]) -> None:
        """
        Notificar observadores, pero antes parsear el campo 'data' si es JSON.
        
        CAMBIO vs Semana 5:
        - Semana 5: Observable recibía datos ya parseados
        - Semana 6: Recibe eventos SSE con data en string, necesita parsearlo
        """
        
        # Intentar parsear data como JSON
        if "data" in evento and isinstance(evento["data"], str):
            try:
                evento["data"] = json.loads(evento["data"])
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Data no es JSON válido: {evento['data']}")
                # Mantener como string si no es JSON
        
        # Llamar a Observable
        await super()._notificar(evento)
    
    def detener(self) -> None:
        """
        Cierre suave: solo cambiar bandera ejecutando.
        El ciclo while verá False en la próxima iteración.
        """
        logger.info("⏹️  Solicitando detención del cliente SSE")
        self.ejecutando = False



# OBSERVADORES (Receptores de Eventos)
class ObservadorProductos(Observador):
    """
    Observador que reacciona a cambios de productos.
    Solo procesa eventos de tipo "producto_actualizado".
    """
    
    async def actualizar(self, evento: Dict[str, Any]) -> None:
        """
        Recibe el evento SSE completo:
          {
            "id": "1",
            "event": "producto_actualizado",
            "data": {"id": "P001", "precio": 450.00}
          }
        """
        if evento.get("event") == "producto_actualizado":
            datos = evento.get("data", {})
            if isinstance(datos, dict):
                logger.info(
                    f"Producto actualizado: "
                    f"[{datos.get('id')}] Precio: ${datos.get('precio', 0):.2f}"
                )
            else:
                logger.warning(f"⚠️ Data no es dict: {datos}")


class ObservadorStock(Observador):
    """
    Observador que alerta sobre stock crítico.
    Solo procesa eventos de tipo "stock_critico".
    """
    
    async def actualizar(self, evento: Dict[str, Any]) -> None:
        if evento.get("event") == "stock_critico":
            datos = evento.get("data", {})
            if isinstance(datos, dict):
                logger.warning(
                    f"🚨 ALERTA: Stock crítico - "
                    f"{datos.get('producto')} "
                    f"(quedan {datos.get('stock')} unidades)"
                )


class ObservadorPedidos(Observador):
    """
    Observador que registra nuevos pedidos.
    Solo procesa eventos de tipo "nuevo_pedido".
    """
    
    async def actualizar(self, evento: Dict[str, Any]) -> None:
        if evento.get("event") == "nuevo_pedido":
            datos = evento.get("data", {})
            if isinstance(datos, dict):
                logger.info(
                    f"📦 Nuevo pedido: "
                    f"[{datos.get('id')}] Cliente: {datos.get('cliente')} "
                    f"Total: ${datos.get('total', 0):.2f}"
                )


class ObservadorAuditoria(Observador):
    """
    Observador que registra TODOS los eventos (sin filtrar por tipo).
    Útil para debugging y auditoría.
    """
    
    async def actualizar(self, evento: Dict[str, Any]) -> None:
        logger.debug(
            f"🔍 EVENTO: tipo={evento.get('event')} "
            f"id={evento.get('id')} "
            f"data={evento.get('data')}"
        )


# PROGRAMA PRINCIPAL
async def main():
    """
    Ejemplo de uso del cliente SSE.
    Crea el cliente, suscribe observadores, y comienza a recibir eventos.
    """
    
    # 1. Crear cliente
    cliente = ClienteSSE(base_url="http://localhost:8000")
    
    # 2. Crear observadores
    obs_productos = ObservadorProductos()
    obs_stock = ObservadorStock()
    obs_pedidos = ObservadorPedidos()
    obs_auditoria = ObservadorAuditoria()
    
    # 3. Suscribir observadores
    cliente.suscribir(obs_productos)
    cliente.suscribir(obs_stock)
    cliente.suscribir(obs_pedidos)
    cliente.suscribir(obs_auditoria)
    
    # 4. Iniciar cliente en background
    tarea_sse = asyncio.create_task(cliente.conectar())
    
    try:
        logger.info("⏱️  Cliente ejecutando durante 15 segundos...")
        await asyncio.sleep(15)
    
    finally:
        # 5. Detener limpiamente
        cliente.detener()
        
        # 6. Esperar a que termine
        await tarea_sse
        
        logger.info("✅ Programa finalizado")


if __name__ == "__main__":
    asyncio.run(main())

