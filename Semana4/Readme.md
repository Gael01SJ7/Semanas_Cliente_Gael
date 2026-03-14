# TRAZA MENTAL: CICLO DE SHORT POLLING CON ETAG (ECOMARKET)
# Analogía:
# Es como llamar a un restaurante para preguntar si tu pedido ya está listo.
# La primera vez te dicen todo el estado del pedido y un código (ETag).
# Después solo preguntas: “¿Sigue igual que la versión abc123?”.
# Si no cambió, solo te responden que sigue igual y no repiten toda la información.

# Consulta 1
# Cliente envía:
# GET /api/productos
# Headers del cliente: ninguno especial
# Servidor responde: 200 OK
# Header: ETag: "abc123"
# Datos transferidos: datos completos de productos (~2KB por ejemplo)
# Acción del cliente: guarda el ETag "abc123" y muestra los productos
# Intervalo de polling: 5 segundos

# Consulta 2
# Cliente envía:
# GET /api/productos
# Header: If-None-Match: "abc123"
# Servidor responde: 304 Not Modified porque los datos no cambiaron
# Datos transferidos: 0 bytes
# Acción del cliente: no actualiza nada y sigue usando los mismos datos
# Intervalo de polling: aumenta a 7.5 segundos

# Consulta 3
# Cliente envía:
# GET /api/productos
# Header: If-None-Match: "abc123"
# Servidor responde: 304 Not Modified
# Datos transferidos: 0 bytes
# Acción del cliente: mantiene los datos actuales
# Intervalo de polling: aumenta a aproximadamente 11 segundos

# Consulta 4
# Cliente envía:
# GET /api/productos
# Header: If-None-Match: "abc123"
# Servidor responde: 200 OK
# Header: ETag: "def456"
# Motivo: alguien actualizó el precio de un producto
# Datos transferidos: datos completos nuevamente (~2KB)
# Acción del cliente: actualiza los productos y guarda el nuevo ETag "def456"
# Intervalo de polling: vuelve a 5 segundos

# Por qué ETag es más eficiente
# ETag funciona como una versión de los datos.
# Si los datos no cambiaron, el servidor responde 304 y no envía toda la información otra vez.
# Esto reduce tráfico de red y evita transferir datos innecesarios cuando no hay cambios.