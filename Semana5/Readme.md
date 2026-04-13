# Semana 5 — Cliente REST con Polling y Observer

## Reto 1: Diagrama de Polling con ETag

El cliente realiza consultas periódicas al servidor usando polling. En cada petición, envía el header `If-None-Match` con el último ETag recibido.

- Si el servidor responde **200 OK**, significa que hay cambios:
  - Se actualiza el ETag
  - Se procesan los datos
  - Se notifica a los observadores
  - El intervalo vuelve al valor base

- Si responde **304 Not Modified**:
  - No hay cambios
  - El cliente aumenta el intervalo (backoff)

Esto evita procesar datos innecesarios y reduce tráfico de red.

---

## Reto 2: Monitor de Inventario

Se implementó un sistema con:

- Polling adaptativo con backoff
- Uso de ETag para detectar cambios
- Patrón Observer para desacoplar componentes

Observadores implementados:

- UI → muestra datos
- Alertas → detecta stock bajo
- Log → registra eventos

---

## Reto 3: Análisis de Trade-offs

| Decisión | Beneficio | Costo |
|--------|----------|------|
| Timeout 10s | Evita bloqueo | Puede cortar respuestas lentas |
| Polling 5s | Datos frescos | Más tráfico |
| Backoff | Menos carga | Mayor latencia |
| Observer | Desacoplamiento | Más complejidad |

### Carga estimada

Con 500 usuarios:
- 1 request cada 5s → 100 req/s aprox

Con backoff:
- Menos requests cuando no hay cambios

---

## Reto 4: Validación

Se probaron 4 escenarios:

1. Datos normales → funciona
2. Stock bajo → alerta se activa
3. Sin cambios → no notifica
4. Error servidor → no crashea

El sistema demuestra desacoplamiento:
los observadores funcionan independientemente.

---

## Uso de IA

Se utilizó IA para:
- Corregir manejo de errores
- Mejorar estructura del código
- Detectar fallos en validación

Se ajustaron respuestas sugeridas para cumplir requisitos del curso.