# RETO 3: REFLEXIONA - DOCSTRING DE DECISIONES DE DISEÑO
## Semana 5 - Programación Distribuida del Lado del Cliente

"""
PROPÓSITO:
Este reto articula las decisiones de diseño del cliente del Hito 1 (Monitor de Inventario
de las Semanas 1–4) con trade-offs explícitos. No es teoría — es documentación que vive
pegada al código como referencia para futuras decisiones.

FLUJO:
1. Lee la discusión socrática (preguntas + respuestas modelo)
2. Valida que tus decisiones tengan justificación técnica
3. Incorpora el docstring en tu archivo principal del Hito 1
4. La próxima semana (Semana 6), consulta este docstring cuando refactorices el cliente

UBICACIÓN EN TU CÓDIGO:
Este docstring va al inicio de tu archivo principal (monitor_inventario.py):
"""

# ==========================================
# DOCSTRING DE DECISIONES DE DISEÑO
# Copia esto al inicio de tu monitor_inventario.py
# ==========================================

"""
================================================================================
DECISIONES DE DISEÑO — Cliente EcoMarket / Hito 1
Consolidación del Cliente REST Básico (Semanas 1–4)
================================================================================

PREGUNTA 1: ¿QUÉ TIMEOUT CONFIGURASTE Y POR QUÉ?
─────────────────────────────────────────────────

DECISIÓN: TIMEOUT_HTTP = 10 segundos

TRADE-OFF (desde la perspectiva del CLIENTE):
  - Si timeout es muy corto (< 5s):
    El cliente falla peticiones legítimas. El usuario ve "errores de conexión"
    constantemente, aunque el servidor funciona — solo está lento.
    → Mala experiencia: falsos positivos, reintentos frecuentes.
  
  - Si timeout es muy largo (> 30s):
    Si el servidor se cae o congela, el cliente queda bloqueado 30+ segundos.
    El hilo/corrutina se congela. En polling, si hay múltiples peticiones
    concurrentes, se acumulan hilos bloqueados.
    → Mala experiencia: "la app no responde", consumo alto de recursos.

JUSTIFICACIÓN:
  10 segundos es generoso para operaciones de lectura en Internet.
  - La mayoría de conexiones HTTP legítimas resuelven en < 2s.
  - 10s da margen para servidores lentos o redes congestionadas.
  - No es "indefinido" (que congela el cliente).
  - Balance entre resiliencia y responsividad del usuario.

VALIDACIÓN:
  En el examen, si le haces timeout a una petición, el cliente debe:
  1. Capturar asyncio.TimeoutError (no dejar que crashee)
  2. Registrar el error
  3. Aumentar intervalo de polling (backoff)
  4. Continuar el ciclo (no morir silenciosamente)

REFERENCIA EN CÓDIGO:
  try:
      respuesta = await asyncio.wait_for(
          self.sesion.get(url),
          timeout=self.TIMEOUT_HTTP
      )
  except asyncio.TimeoutError:
      # Registrar, backoff, continuar
      logger.warning("Timeout en petición")
      self.intervalo = min(self.intervalo * 2, self.INTERVALO_MAX)


PREGUNTA 2: CUANDO RECIBES UN ERROR 5XX, ¿QUÉ HACE TU CLIENTE?
──────────────────────────────────────────────────────────────

DECISIÓN: 
  - Registra el error
  - Incrementa intervalo (backoff exponencial × 2)
  - Reintenta automáticamente en la próxima iteración del polling
  - NO reintenta inmediatamente (eso sería thundering herd)

REINTENTOS: No contamos "intentos explícitos". El backoff adaptativo
  se encarga: si el servidor sigue caído, el intervalo crece (5s → 10s → 20s
  → 40s → 60s) y eventualmente el cliente consulta cada 60s. Eso es suficiente
  para "reintentos".

TRADE-OFF:
  - Si reintentamos inmediatamente (sin sleep):
    Bombardeamos un servidor ya caído → más daño.
  
  - Si nunca reintentamos:
    El cliente nunca se recupera cuando el servidor se levanta.
  
  - Con backoff exponencial:
    Damos tiempo al servidor para recuperarse, pero seguimos intentando.

JUSTIFICACIÓN:
  El 5xx indica error del servidor, no del cliente.
  - Si es transitorio (caída de 2 minutos), el backoff da tiempo.
  - Si es permanente (outage), después de 60s sin cambios, el usuario vio
    lo que había en caché / última notificación. Nada peor que antes.

VALIDACIÓN:
  En el examen, si tu código hace algo diferente a esto, pregúntate:
  - ¿Estoy reintentando 5xx? ✓
  - ¿Con backoff (no inmediatamente)? ✓
  - ¿Registrando el error? ✓
  - ¿Continuando el ciclo? ✓

REFERENCIA EN CÓDIGO:
  if respuesta.status >= 500:
      logger.error(f"5xx — Error servidor, reintentará")
      self.intervalo = min(self.intervalo * 2, self.INTERVALO_MAX)
      return None  # Sin datos, pero continua el ciclo


PREGUNTA 3: ¿SHORT POLLING O LONG POLLING? ¿POR QUÉ?
──────────────────────────────────────────────────────

DECISIÓN: SHORT POLLING (consultar cada N segundos)

SHORT POLLING:
  El cliente hace GET cada INTERVALO_BASE segundos.
  if datos_cambiaron:
      notificar
  else:
      esperar INTERVALO_BASE

LONG POLLING:
  El cliente hace GET. El servidor ESPERA y responde solo cuando hay cambios
  (o después de timeout largo). El cliente recibe inmediatamente.

TRADE-OFF:
  SHORT POLLING:
    ✓ Más simple de implementar (un ciclo while + sleep)
    ✓ Usa menos conexiones (una petición cada 5-60s)
    ✗ Latencia: el cambio puede tardar hasta INTERVALO_BASE en notificarse
    ✗ En datos críticos (cotizaciones), puede ser lento
  
  LONG POLLING:
    ✓ Latencia casi inmediata (el servidor notifica apenas hay cambios)
    ✗ Más complejo: el servidor debe mantener conexiones abiertas esperando
    ✗ Usa más conexiones y memoria en el servidor
    ✗ Requiere lógica de timeout largo para evitar desconexiones

JUSTIFICACIÓN (para EcoMarket):
  EcoMarket es un sistema de inventario y pedidos. Los cambios son frecuentes
  pero no requieren latencia ultra-baja (< 100ms).
  - Si un pedido se marca COMPLETADO, esperar 5-10 segundos es aceptable.
  - No estamos haciendo trading de acciones (donde <100ms importa).
  - Short polling reduce carga del servidor y es más fácil de mantener.

IMPACTO EN DISPOSITIVO MÓVIL:
  Short polling con backoff adaptativo es AMIGABLE para batería:
  - En reposo (sin cambios): consulta cada 60s (muy bajo impacto)
  - Con cambios: consulta cada 5s (aceptable si hay actividad)
  - Long polling mantendría conexión abierta siempre → más consumo de batería

VALIDACIÓN:
  En el examen, si implementas polling, debe ser SHORT POLLING:
  - Un ciclo while + await asyncio.sleep()
  - No esperes respuestas "asincrónicas" indefinidas
  - Implementa backoff (intervalo crece si no hay cambios)

REFERENCIA EN CÓDIGO:
  while self.ejecutando:
      datos = await self._consultar_pedidos()
      if datos != self.ultimo_estado:
          await self._notificar(datos)
      await asyncio.sleep(self.intervalo)  # ← SHORT POLLING


PREGUNTA 4: ¿CUÁNTOS OBSERVADORES TIENES? ¿ACOPLAMIENTO?
──────────────────────────────────────────────────────────

DECISIÓN: Implementé 3 observadores en el Hito 1
  - ObservadorUI: Mostrar inventario en consola
  - ObservadorAlertas: Filtrar productos con stock bajo
  - ObservadorLog: Registrar cambios en archivo de log

TRADE-OFF:
  - Con 1 observador:
    El Observer Pattern es overhead (la llamada directa sería más simple).
  
  - Con 2–5 observadores:
    El pattern tiene sentido. Cada observador es independiente.
    Agregar uno nuevo: solo llamar suscribir(), sin tocar la fuente.
  
  - Con > 10 observadores con lógica pesada:
    La notificación sincrónica podría hacerse lenta.
    Considerar: notificación asíncrona o bus de eventos.

ACOPLAMIENTO (¿QUÉ CAMBIARÍA EN MI CÓDIGO SI AGREGO UN OBSERVADOR?):
  Hoy: 0 líneas de cambio en ServicioPolling o Observable.
  
  Mañana si necesito "enviar email cuando hay cambios":
    1. Creo clase ObservadorEmail(Observador)
    2. Implemento async def actualizar(self, datos)
    3. Llamo: monitor.suscribir(ObservadorEmail())
    4. ¿Cambié algo en MonitorPedidos? NO.
  
  ✓ Este es el desacoplamiento que buscaba.

VALIDACIÓN:
  En el examen, la rúbrica pregunta: "¿Agregar un observador nuevo requiere
  modificar el Observable?" Si tu respuesta es "Sí, tengo if/switch por tipo",
  hay acoplamiento implícito que debe refactorizarse.

REFERENCIA EN CÓDIGO:
  # ✅ CORRECTO: Observable trata todos igual
  async def _notificar(self, datos):
      for obs in self._observadores:
          await obs.actualizar(datos)
  
  # ❌ INCORRECTO: Observable sabe de observadores específicos
  async def _notificar_mal(self, datos):
      if isinstance(obs, ObservadorUI):
          await obs.actualizar_ui(datos)
      elif isinstance(obs, ObservadorAlertas):
          await obs.actualizar_alertas(datos)


PREGUNTA 5: ¿QUÉ CAMBIARÍAS HOY DE TU CLIENTE?
───────────────────────────────────────────────

DECISIÓN: Refactorizar la separación de responsabilidades

HOY (Semanas 1–4):
  - Archivo único: monitor_inventario.py
  - Mezcla: lógica HTTP + parsing + polling + observadores
  - Funciona, pero es "big ball of mud"

CAMBIO PROPUESTO (Semana 6):
  - Carpeta structure:
      cliente_ecomarket/
      ├── http_client.py       (solo HTTP, sin lógica de negocio)
      ├── repository.py        (abstrae origen de datos — HTTP o caché)
      ├── services/
      │   ├── polling_service.py
      │   ├── cache_service.py
      ├── observers/
      │   ├── ui_observer.py
      │   ├── alerts_observer.py
      │   ├── log_observer.py
      └── main.py              (orquestra todo)
  
  Ventajas:
  - Cada archivo tiene responsabilidad única
  - Testear http_client sin observadores
  - Reemplazar HTTP por WebSocket (Semana 11) sin tocar servicios

TRADE-OFF:
  - Más archivos, más complejos para principiantes
  - Pero necesario para escalabilidad y mantenimiento

VALIDACIÓN:
  En la Semana 6, cuando hagas el Repository Pattern, vuelve a este docstring
  y verifica que el refactoring es coherente con las decisiones aquí documentadas.

REFERENCIA:
  El patrón Observable que implementaste hace posible este refactoring.
  La Semana 6 lo formaliza con el patrón Repository.

================================================================================
TABLA DE TRADE-OFFS: DECISIONES A LO LARGO DE LAS SEMANAS 1–4
================================================================================

┌──────────────────────┬────────────────────┬───────────────────┬────────────────┐
│ Decisión             │ Si es muy bajo      │ Si es muy alto    │ Rango típico   │
├──────────────────────┼────────────────────┼───────────────────┼────────────────┤
│ TIMEOUT_HTTP         │ Falsos positivos,  │ Cliente congelado │ 5–30s          │
│                      │ reintentos         │ si servidor cae   │ (lectura: 10s) │
├──────────────────────┼────────────────────┼───────────────────┼────────────────┤
│ INTERVALO_BASE       │ Alto tráfico,      │ Datos obsoletos,  │ 5–15s para     │
│ (polling)            │ CPU alta, batería  │ latencia          │ semi-RT        │
├──────────────────────┼────────────────────┼───────────────────┼────────────────┤
│ INTERVALO_MAX        │ Backoff inefectivo,│ Tarda mucho en    │ 60–300s        │
│ (backoff)            │ sin alivio         │ enterarse cambios │ (10x base)     │
├──────────────────────┼────────────────────┼───────────────────┼────────────────┤
│ Num. Observadores    │ Pattern overhead   │ Notif. lenta,     │ 2–5            │
│                      │ no justificado     │ considerar async  │ (10+ = bus)    │
└──────────────────────┴────────────────────┴───────────────────┴────────────────┘

================================================================================
CONEXIÓN CON LAS PRÓXIMAS SEMANAS
================================================================================

SEMANA 6 (Arquitectura en Capas):
  - El Observer de hoy es el Repository de mañana
  - La separación de capas que hiciste facilita el refactoring
  - Tu decisión de "Observable no sabe de observadores" = Repository no sabe
    si los datos vienen de HTTP o caché

SEMANA 7 (Caché Local):
  - El INTERVALO_MAX de hoy será reemplazado por cache-first strategy
  - Si hay caché local válido, no consultes cada 60s
  - El Observer notificará con datos de caché localmente

SEMANA 9 (WebSocket):
  - El ServicioPolling será reemplazado por ServicioWebSocket
  - Los observadores NO cambian (mismo patrón)
  - El TIMEOUT_HTTP se convierte en timeout de conexión WebSocket

SEMANA 11 (Circuit Breaker):
  - El backoff de hoy es precario — sin Circuit Breaker
  - El patrón se formalizará: si N 5xx consecutivos, "abre el circuito"
  - No reintentar automáticamente hasta que el servidor demuestre que se recuperó

================================================================================
VALIDACIÓN: ¿CÓMO SUPE QUE ESTABA BIEN?
================================================================================

Checklist que usé para validar las decisiones:

✓ ¿La decisión resuelve un problema real?
  Timeout → evita bloqueos indefinidos
  Backoff → evita bombardear servidor caído
  Observer → permite agregar features sin modificar fuente

✓ ¿Hay trade-off explícito?
  Cada decisión sacrifica algo. Documenté qué se gana vs se pierde.

✓ ¿Es transferible a otro contexto?
  ¿Funciona igual para Monitor de Pedidos, Categorías, etc.?
  Sí → buena abstracción

✓ ¿Entra en el rango típico de producción?
  Timeout 10s: sí (vs 1s o 300s)
  Intervalo base 5s: sí (vs 0.1s o 1000s)
  Observadores 3: sí (vs 1 o 50)

✓ ¿El código refleja la decisión?
  Si documente "backoff exponencial", el código dice `intervalo * 2`
  Si documenta "no reintentar 4xx", el código tiene `if status >= 400`

================================================================================
ÚLTIMA NOTA: SOBRE EL CAMBIO
================================================================================

"Si mirases tu código hoy, después de 4 semanas del curso, ¿qué cambiarías?"

Respuesta: La mayoría de las decisiones TÉCNICAS son sólidas y se mantienen.

Lo que cambiaría es la ESTRUCTURA:
- Hoy: un archivo grande
- Mañana (Semana 6): múltiples archivos con responsabilidades claras
- Pero la lógica = idéntica

Lo que revisaría (pero probablemente es correcto):
- ¿El timeout de 10s es ideal para MI caso de uso específico?
  (Podría ser 15s para operaciones pesadas, 5s para operaciones críticas)
- ¿El backoff exponencial × 2 es agresivo o lento?
  (Podría experimentar con × 1.5 vs × 2 vs × 3)
- ¿Necesito Circuit Breaker para evitar reintentos infinitos?
  (En Semana 9, probablemente sí)

Pero estos son REFINAMIENTOS, no cambios fundamentales.

Las decisiones de hoy son sobre PATRONES (Observer, backoff, timeout).
Los refinamientos serán sobre VALORES (10s vs 15s, × 2 vs × 1.5).

================================================================================
"""

# ==========================================
# RESUMEN EN 5 PUNTOS
# (Para copiar a tu código)
# ==========================================

RESUMEN_DECISIONES = """
1. TIMEOUT_HTTP = 10 segundos
   → Trade-off: Balance entre "falsos positivos" (timeout corto) vs "cliente congelado"
     (timeout largo).
   Decisión: 10s es generoso pero no infinito. Adecuado para EcoMarket.

2. REINTENTOS EN 5xx CON BACKOFF EXPONENCIAL (× 2)
   → Trade-off: Reintentamos para recuperarnos, pero no inmediatamente (evita
     thundering herd).
   Decisión: Backoff da tiempo al servidor para recuperarse, es automático en
     el ciclo de polling.

3. SHORT POLLING (cada 5–60s) vs LONG POLLING
   → Trade-off: Short es simple pero con latencia. Long es rápido pero complejo.
   Decisión: Short polling es amigable para batería y carga del servidor.
     Adecuado para inventario/pedidos (no finanzas).

4. PATRÓN OBSERVER CON 2–5 OBSERVADORES
   → Trade-off: Overhead sin 3+ observadores, pero permite agregar features sin
     modificar fuente.
   Decisión: Observadores son independientes. Agregar uno nuevo = 0 cambios en
     MonitorPedidos.

5. REFACTORIZACIÓN FUTURA: SEPARACIÓN DE CAPAS
   → Trade-off: Más archivos inicialmente, pero escalabilidad a largo plazo.
   Decisión: El Observer facilita esta separación. La Semana 6 la formaliza
     con Repository Pattern.
"""

# ==========================================
# CÓMO USAR ESTE DOCSTRING
# ==========================================

"""
PASO 1: Copia TODO el contenido de la sección "DOCSTRING DE DECISIONES"
        (desde "DECISIONES DE DISEÑO" hasta antes de "RESUMEN EN 5 PUNTOS")

PASO 2: Pégalo al inicio de tu archivo monitor_inventario.py (o el archivo
        principal del Hito 1)

PASO 3: Valida que las respuestas y valores coincidan con tu implementación
        real. Si implementaste timeout=15 en lugar de 10, actualiza el docstring.

PASO 4: Cuando hagas el simulacro (Reto 2) o el Examen Práctico 1, si necesitas
        justificar una decisión, consulta este docstring.

PASO 5: En la Semana 6, cuando refactorice tu código para el Repository Pattern,
        vuelve a este docstring y verifica que el refactoring respeta las
        decisiones aquí documentadas.

UBICACIÓN FINAL EN TU PROYECTO:
────────────────────────────────
mi_proyecto_ecomarket/
├── hito1_cliente_rest/
│   ├── monitor_inventario.py          ← AQUÍ PEGA EL DOCSTRING
│   ├── observadores.py
│   └── ...
└── semana5_reflexion.md               ← O aquí como referencia

VALIDACIÓN ANTES DEL EXAMEN:
────────────────────────────
Pregúntate (y responde sin ver el docstring):
□ ¿Por qué timeout 10s y no 5 ó 30?
□ ¿Por qué reintento 5xx con backoff y no 4xx?
□ ¿Por qué short polling y no long polling?
□ ¿Por qué Observer en lugar de llamadas directas?
□ ¿Qué cambiarías hoy de tu cliente?

Si puedes responder las 5 preguntas sin consultar, estás listo.
"""
