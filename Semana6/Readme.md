# Receptor de Alertas EcoMarket (SSE)

## Traza SSE

t=0 → Cliente envía GET /eventos con Accept: text/event-stream
Servidor responde 200 OK

t=2 → id:1 evento producto_actualizado
t=5 → id:2 evento stock_critico
t=10 → : ping (keep-alive)
t=15 → id:3 evento nuevo_pedido

t=25 → conexión se pierde
t=28 → reconexión con Last-Event-ID: 3

## Diferencia con polling

En polling el cliente hace múltiples peticiones (muchas vacías).
En SSE hay una sola conexión y el servidor envía datos solo cuando hay cambios.
