# Semana 4 - Monitor de Inventario con Polling + Observer
# Alumno: Christian Gael Ortiz Ramirez
## Reto 1: Diagrama temporal

El polling funciona como preguntar constantemente al servidor si hay cambios.

Cliente → petición → servidor  
Servidor → responde con datos o 304  

Si no hay cambios (304), el cliente espera más tiempo (backoff).  
Si hay cambios (200), actualiza y notifica a los observadores.

---

## Reto 3: Trade-offs

| Característica | Polling | SSE |
|--------------|--------|-----|
| Tiempo real | No | Sí |
| Consumo red | Alto | Bajo |
| Complejidad | Baja | Media |
| Escalabilidad | Limitada | Mejor |

### Cálculo:
500 usuarios * 1 request/segundo = 500 req/s

Esto genera alta carga.

### Mejora:
Usar SSE o WebSockets para reducir peticiones.

---

## Desacoplamiento

El patrón Observer permite que los observadores funcionen de forma independiente.  
Si uno falla, los demás siguen funcionando.