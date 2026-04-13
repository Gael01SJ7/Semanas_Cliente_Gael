# RETO 2: SIMULACRO DEL EXAMEN - MONITOR DE PEDIDOS
## Semana 5 - Programación Distribuida del Lado del Cliente
## Objetivo: Completar en ≤ 90 minutos

"""
ESCENARIO DEL SIMULACRO:
EcoMarket necesita un Monitor de Pedidos que:
1. Consulte periódicamente GET /pedidos
2. Detecte cambios con ETag
3. Notifique a observadores
4. Maneje errores diferenciados (2xx, 4xx, 5xx, timeout)

Respuesta esperada:
{
  "pedidos": [
    {"id": "P001", "cliente": "Ana", "total": 450.00, "status": "PENDIENTE"},
    {"id": "P002", "cliente": "Carlos", "total": 120.50, "status": "RETRASADO"}
  ],
  "total_registros": 2,
  "ultima_actualizacion": "2025-03-12T10:30:00Z",
  "next_page_token": null
}

Posibles respuestas del servidor:
- 200: datos normales
- 304: sin cambios (si envío ETag)
- 503: temporalmente no disponible
- 408: timeout
- 400: parámetros incorrectos
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# INTERFAZ OBSERVADOR
class Observador(ABC):
    """Interfaz que todo observador debe implementar"""
    
    @abstractmethod
    async def actualizar(self, pedidos: List[Dict[str, Any]]) -> None:
        """Recibe los datos cuando hay cambios"""
        pass


# OBSERVABLE (PROPORCIONADA)
class Observable:
    """Patrón Observer: mantiene lista de observadores y notifica"""
    
    def __init__(self):
        self._observadores: List[Observador] = []
    
    def suscribir(self, observador: Observador) -> None:
        """Agregar observador a la lista"""
        if observador not in self._observadores:
            self._observadores.append(observador)
            logger.info(f"✅ Suscrito: {observador.__class__.__name__}")
    
    def desuscribir(self, observador: Observador) -> None:
        """Remover observador de la lista"""
        if observador in self._observadores:
            self._observadores.remove(observador)
            logger.info(f"❌ Desuscrito: {observador.__class__.__name__}")
    
    async def _notificar(self, pedidos: List[Dict[str, Any]]) -> None:
        """
        Notifica a TODOS los observadores de forma idéntica.
        
        PATRÓN OBSERVER CLAVE:
        - Observable no sabe QUÉ hacen los observadores
        - Solo llama al método actualizar() de cada uno
        - Los observadores pueden cambiar sin modificar Observable
        """
        for observador in self._observadores:
            try:
                await observador.actualizar(pedidos)
            except Exception as e:
                logger.error(f"⚠️ Error en observador {observador.__class__.__name__}: {e}")


# MONITOR DE PEDIDOS
class MonitorPedidos(Observable):
    """
    Monitor de pedidos con polling adaptativo y ETag.
    
    CONSTANTES:
    - INTERVALO_BASE: 5 segundos (consulta seguida cuando hay cambios)
    - INTERVALO_MAX: 60 segundos (consulta lenta cuando no hay cambios)
    - TIMEOUT_HTTP: 10 segundos (límite por petición)
    
    FLUJO:
    1. _consultar_pedidos(): GET con ETag, manejo de errores
    2. iniciar(): ciclo while con backoff adaptativo
    3. detener(): cierre suave (solo cambiar bandera)
    """
    
    INTERVALO_BASE = 5  # segundos
    INTERVALO_MAX = 60
    TIMEOUT_HTTP = 10
    REINTENTOS_MAX = 3
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.ejecutando = False
        self.intervalo_actual = self.INTERVALO_BASE
        self.ultimo_etag: Optional[str] = None
        self.ultimo_estado: Optional[List[Dict]] = None
        self.ultima_consulta = None
        logger.info(f"📍 MonitorPedidos inicializado: {base_url}")
    
    async def _consultar_pedidos(self) -> Optional[List[Dict[str, Any]]]:
        """
        Método 1: GET a /pedidos con manejo diferenciado de errores.
        
        RESPONSABILIDADES:
        1. Construir petición con ETag (If-None-Match)
        2. Validar status code diferenciado:
           - 200: datos nuevos → guardar ETag, retornar datos
           - 304: sin cambios → retornar None
           - 4xx: error del cliente → NO reintentar, retornar None
           - 5xx: error del servidor → SÍ puede reintentar, retornar None
        3. Manejo de errores de red (Timeout, ConnectionError)
        4. Validación del body JSON
        5. Validación de campos esperados
        
        RETORNA:
        - List[Dict]: lista de pedidos válida (hay cambios)
        - None: sin cambios, error, o fallo
        """
        try:
            # Construir headers con ETag
            headers = {}
            if self.ultimo_etag:
                headers["If-None-Match"] = self.ultimo_etag
                logger.debug(f"📤 Enviando If-None-Match: {self.ultimo_etag}")
            
            # Simular petición HTTP (en producción, usar aiohttp)
            # Para este simulacro, usamos datos mock
            respuesta = await self._simular_peticion_http(headers)
            
            self.ultima_consulta = datetime.now()
            
            #MANEJO DIFERENCIADO DE STATUS
            if respuesta["status"] == 200:
                # ✅ CAMBIOS DETECTADOS
                logger.info("✅ 200 OK — Cambios detectados")
                
                try:
                    # Parsear y validar JSON
                    datos = respuesta["body"]
                    
                    # Validar estructura
                    if not isinstance(datos, dict):
                        logger.error("❌ Body no es diccionario")
                        return None
                    
                    pedidos = datos.get("pedidos")
                    
                    # Validar que "pedidos" existe y es lista
                    if not isinstance(pedidos, list):
                        logger.error("❌ 'pedidos' no existe o no es lista")
                        return None
                    
                    # Validar cada pedido
                    for pedido in pedidos:
                        if "id" not in pedido or "status" not in pedido:
                            logger.error(f"❌ Pedido sin campos requeridos: {pedido}")
                            return None
                    
                    # Guardar ETag para próxima petición
                    self.ultimo_etag = respuesta.get("etag")
                    logger.info(f"📌 ETag actualizado: {self.ultimo_etag}")
                    
                    # Resetear backoff (tenemos cambios)
                    self.intervalo_actual = self.INTERVALO_BASE
                    
                    return pedidos
                
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"❌ Error al parsear JSON: {e}")
                    return None
            
            elif respuesta["status"] == 304:
                # ℹ️SIN CAMBIOS
                logger.info(" 304 Not Modified — Sin cambios")
                
                # Aumentar intervalo (backoff): esperar más tiempo
                self.intervalo_actual = min(
                    self.intervalo_actual * 1.5,
                    self.INTERVALO_MAX
                )
                logger.debug(f"  Nuevo intervalo (backoff): {self.intervalo_actual:.1f}s")
                
                return None  # No hay datos nuevos
            
            elif respuesta["status"] >= 500:
                # ERROR DEL SERVIDOR (5xx) → SÍ PUEDE REINTENTAR
                logger.warning(f"  {respuesta['status']} — Error del servidor, puede reintentar")
                
                # Backoff más agresivo
                self.intervalo_actual = min(
                    self.intervalo_actual * 2,
                    self.INTERVALO_MAX
                )
                logger.debug(f" Nuevo intervalo (backoff 5xx): {self.intervalo_actual:.1f}s")
                
                return None
            
            elif respuesta["status"] >= 400:
                #ERROR DEL CLIENTE (4xx) → NO REINTENTAR
                logger.error(
                    f" {respuesta['status']} — Error del cliente, NO reintentará. "
                    f"Mensaje: {respuesta.get('body', {}).get('error', 'Unknown')}"
                )
                
                # No incrementar intervalo; solo registrar y continuar
                return None
            
            else:
                # Otros status inesperados
                logger.warning(f"⚠️  Status inesperado: {respuesta['status']}")
                return None
        
        except asyncio.TimeoutError:
            # TIMEOUT EN LA PETICIÓN
            logger.error("Timeout en petición de pedidos")
            
            # Backoff por timeout
            self.intervalo_actual = min(
                self.intervalo_actual * 2,
                self.INTERVALO_MAX
            )
            
            return None
        
        except Exception as e:
            # OTROS ERRORES DE RED
            logger.error(f" Error de red: {type(e).__name__}: {e}")
            
            # Backoff general
            self.intervalo_actual = min(
                self.intervalo_actual * 2,
                self.INTERVALO_MAX
            )
            
            return None
    
    async def iniciar(self) -> None:
       
        logger.info(" Iniciando Monitor de Pedidos...")
        self.ejecutando = True
        
        while self.ejecutando:
            try:
                # 1. Consultar pedidos (con manejo de errores interno)
                datos = await self._consultar_pedidos()
                
                # 2. Si hay datos nuevos y diferentes a los anteriores
                if datos is not None and datos != self.ultimo_estado:
                    logger.info(f"📬 Cambios detectados: {len(datos)} pedidos")
                    
                    # Guardar estado actual
                    self.ultimo_estado = datos
                    
                    # Notificar a TODOS los observadores
                    await self._notificar(datos)
                
                # 3. Esperar ANTES de la próxima consulta
               
                logger.debug(f"😴 Esperando {self.intervalo_actual:.1f}s antes de próxima consulta...")
                await asyncio.sleep(self.intervalo_actual)
            
            except Exception as e:
                # Si algo crashea aquí, registramos y continuamos
                logger.error(f"Error no esperado en ciclo: {type(e).__name__}: {e}")
                
                # Backoff de emergencia
                self.intervalo_actual = min(
                    self.intervalo_actual * 2,
                    self.INTERVALO_MAX
                )
                
                # Esperar antes de reintentar
                await asyncio.sleep(self.intervalo_actual)
        
        logger.info("Monitor detenido")
    
    def detener(self) -> None:
        """
        Método 3: Detención limpia del ciclo.
        
        RESPONSABILIDAD:
        - Poner ejecutando = False
        - El ciclo while verá que ejecutando es False y terminará en la próxima iteración
        - Esta es una "cierre suave": graceful shutdown
        
        INVARIANTE: No cancela la corrutina de forma forzada
        - No lanza CancelledError
        - Permite que el ciclo termine limpiamente
        - Los observadores reciben las notificaciones hasta el final
        """
        logger.info("Solicitud de detención del Monitor")
        self.ejecutando = False
    
    async def _simular_peticion_http(self, headers: Dict) -> Dict:
        """
        SOLO PARA EL SIMULACRO: simula respuestas HTTP.
        
        En producción, aquí harías:
            async with aiohttp.ClientSession() as session:
                async with session.get(...) as resp:
                    return {...}
        
        Para este simulacro, retorna datos mock basados en el estado.
        """
        # Simular latencia de red
        await asyncio.sleep(0.2)
        
        # Simular cambios: primero 200 con datos, luego 304
        if self.ultimo_etag is None:
            # Primera petición: siempre 200 con datos nuevos
            return {
                "status": 200,
                "etag": "v1-abcd1234",
                "body": {
                    "pedidos": [
                        {"id": "P001", "cliente": "Ana", "total": 450.00, "status": "PENDIENTE"},
                        {"id": "P002", "cliente": "Carlos", "total": 120.50, "status": "RETRASADO"}
                    ],
                    "total_registros": 2,
                    "ultima_actualizacion": "2025-03-12T10:30:00Z",
                    "next_page_token": None
                }
            }
        else:
            # Después: simular respuestas variadas
            # (En examen real, el servidor decidiría)
            import random
            chance = random.random()
            
            if chance < 0.7:  # 70% sin cambios
                return {"status": 304, "body": None}
            else:  # 30% con cambios
                return {
                    "status": 200,
                    "etag": "v2-efgh5678",
                    "body": {
                        "pedidos": [
                            {"id": "P001", "cliente": "Ana", "total": 450.00, "status": "PENDIENTE"},
                            {"id": "P002", "cliente": "Carlos", "total": 120.50, "status": "COMPLETADO"},
                            {"id": "P003", "cliente": "David", "total": 89.99, "status": "RETRASADO"}
                        ],
                        "total_registros": 3,
                        "ultima_actualizacion": "2025-03-12T10:35:00Z",
                        "next_page_token": None
                    }
                }


# OBSERVADORES CONCRETOS
class ObservadorPedidosUI(Observador):
    """
    Observador 1: Muestra pedidos en formato legible en consola.
    
    RESPONSABILIDAD ÚNICA: Presentar datos al usuario de forma clara.
    """
    
    async def actualizar(self, pedidos: List[Dict[str, Any]]) -> None:
        """Mostrar todos los pedidos en formato tabla"""
        logger.info("=" * 70)
        logger.info(" ESTADO ACTUAL DE PEDIDOS")
        logger.info("=" * 70)
        
        if not pedidos:
            logger.info("No hay pedidos")
            return
        
        for pedido in pedidos:
            estado_emoji = {
                "PENDIENTE": "⏳",
                "COMPLETADO": "✅",
                "RETRASADO": "❌"
            }.get(pedido.get("status"), "?")
            
            logger.info(
                f"{estado_emoji} [{pedido.get('id')}] "
                f"Cliente: {pedido.get('cliente'):15} | "
                f"Total: ${pedido.get('total', 0):.2f} | "
                f"Estado: {pedido.get('status')}"
            )
        
        logger.info("=" * 70)


class ObservadorPedidosCriticos(Observador):
    """
    Observador 2: Filtra y alerta sobre pedidos RETRASADOS.
    
    RESPONSABILIDAD ÚNICA: Alertar cuando hay situaciones críticas.
    """
    
    async def actualizar(self, pedidos: List[Dict[str, Any]]) -> None:
        """Filtrar pedidos con status RETRASADO y mostrar alerta"""
        
        # Filtrar solo retrasados
        retrasados = [p for p in pedidos if p.get("status") == "RETRASADO"]
        
        if retrasados:
            logger.warning("🚨 ALERTA: PEDIDOS RETRASADOS DETECTADOS")
            logger.warning("-" * 70)
            
            for pedido in retrasados:
                logger.warning(
                    f"❌ [{pedido.get('id')}] Cliente: {pedido.get('cliente')} | "
                    f"Total: ${pedido.get('total', 0):.2f}"
                )
            
            logger.warning("-" * 70)
        else:
            logger.info("✅ No hay pedidos retrasados")



# PROGRAMA PRINCIPAL
async def main():
    """
    Ejemplo de uso: crear monitor, suscribir observadores, iniciar polling.
    """
    
    # 1. Crear monitor
    monitor = MonitorPedidos(base_url="https://api.ecomarket.local")
    
    # 2. Crear observadores
    ui = ObservadorPedidosUI()
    alertas = ObservadorPedidosCriticos()
    
    # 3. Suscribir observadores
    monitor.suscribir(ui)
    monitor.suscribir(alertas)
    
    # 4. Iniciar ciclo de polling en background
    tarea_polling = asyncio.create_task(monitor.iniciar())
    
    try:
        # 5. Dejar ejecutar por 30 segundos (para prueba)
        logger.info("⏱️  Monitor ejecutando durante 30 segundos...")
        await asyncio.sleep(30)
    
    finally:
        # 6. Detener limpiamente
        monitor.detener()
        
        # 7. Esperar a que termine
        await tarea_polling
        
        logger.info("✅ Programa finalizado")


if __name__ == "__main__":
    asyncio.run(main())



