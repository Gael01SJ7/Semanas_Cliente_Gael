Reporte
Autor: Christian Ortiz
Curso: Programación Concurrente / Semana 3

Descripción del Proyecto

Este proyecto consiste en la implementación de un cliente HTTP asíncrono en Python que consume múltiples endpoints de un servidor simulado utilizando json-server.

El sistema realiza operaciones CRUD sobre productos y además construye un dashboard que consulta de manera concurrente los siguientes endpoints:

/productos

/categorias

/perfil

El objetivo principal fue aplicar programación asíncrona utilizando asyncio y aiohttp, incorporando control de concurrencia, manejo de errores y pruebas automatizadas.

- Python 3.9

- asyncio

- aiohttp

- pytest

- pytest-asyncio

- aioresponses

- json-server (backend simulado)

Ejecución del Proyecto
1. Levantar el servidor
json-server --watch db.json --port 3000

El servidor quedará disponible en:

http://localhost:3000
2. Ejecutar el cliente
python3 cliente_async_ecomarket.py
3. Ejecutar los tests
pytest test_cliente_async.py -v

Todos los tests deben pasar correctamente (22/22).

Características Implementadas

Cliente HTTP asíncrono con aiohttp

Uso de asyncio.gather para concurrencia

Control de concurrencia mediante Semaphore

Manejo estructurado de errores (timeout, errores HTTP, fallos de conexión)

Dashboard concurrente tolerante a fallos

Pruebas automatizadas para escenarios de éxito y error

Simulación de API REST con json-server

Reflexión Final

Este proyecto permitió aplicar programación asíncrona en un escenario realista: un cliente HTTP que consume múltiples endpoints de forma concurrente. Más allá de que el código funcione, el aprendizaje principal estuvo en entender cómo controlar y estructurar la concurrencia de manera responsable.

Primero, se aprendió que usar asyncio y aiohttp no es solo hacer todo al mismo tiempo, sino administrar recursos correctamente. El uso de un Semaphore demostró que la concurrencia debe limitarse para evitar saturar el servidor o el propio cliente. Esto introduce la idea de control y no simplemente paralelismo desmedido.

La implementación de asyncio.gather con return_exceptions=True permitió construir un sistema tolerante a fallos. En lugar de que una petición fallida detuviera todo el proceso, el sistema pudo continuar y reportar errores de manera estructurada. Esto refleja un enfoque más profesional en el diseño de sistemas distribuidos.

En conjunto, el proyecto fortaleció la comprensión de la concurrencia en Python y la importancia de diseñar sistemas robustos, estables y correctamente testeados.