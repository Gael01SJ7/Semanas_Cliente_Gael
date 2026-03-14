// ================================
// CLIENTE HTTP - EcoMarket
// Reto 4
// ================================

// URL base de una API de prueba (JSONPlaceholder)
const BASE_URL = "https://jsonplaceholder.typicode.com";

// Headers comunes para todas las peticiones
const headers = {
  "Content-Type": "application/json",
  "X-Client-Version": "1.0" // Header personalizado solicitado
};

/*
  Función: Obtener todos los productos
  Simula GET /api/productos
*/
async function getProductos() {
  try {
    const response = await fetch(`${BASE_URL}/posts`, {
      method: "GET",
      headers: headers
    });

    // Validación de error general
    if (!response.ok) {
      throw new Error("Error al obtener productos");
    }

    const productos = await response.json();

    console.log("=== LISTA DE PRODUCTOS ===");

    // Mostrar solo algunos para evitar saturar consola
    productos.slice(0, 5).forEach(producto => {
      console.log(`ID: ${producto.id}`);
      console.log(`Nombre: ${producto.title}`);
      console.log("-----------------------");
    });

  } catch (error) {
    console.error("No se pudo conectar con el servidor:", error.message);
  }
}

/*
  Función: Obtener producto por ID
  Simula GET /api/productos/{id}
*/
async function getProductoById(id) {
  try {
    const response = await fetch(`${BASE_URL}/posts/${id}`, {
      method: "GET",
      headers: headers
    });

    if (response.status === 404) {
      console.log("Producto no encontrado");
      return;
    }

    if (!response.ok) {
      throw new Error("Error al consultar producto");
    }

    const producto = await response.json();

    console.log("=== PRODUCTO ENCONTRADO ===");
    console.log(`ID: ${producto.id}`);
    console.log(`Nombre: ${producto.title}`);
    console.log(`Descripción: ${producto.body}`);

  } catch (error) {
    console.error("Ocurrió un error:", error.message);
  }
}

/*
  Función: Crear producto
  Simula POST /api/productos
*/
async function crearProducto(producto) {
  try {
    const response = await fetch(`${BASE_URL}/posts`, {
      method: "POST",
      headers: headers,
      body: JSON.stringify(producto)
    });

    if (response.status === 201) {
      const data = await response.json();
      console.log("Producto creado exitosamente:");
      console.log(data);
    } else if (response.status === 400) {
      console.log("Datos inválidos para crear producto");
    } else {
      throw new Error("Error al crear producto");
    }

  } catch (error) {
    console.error("No se pudo crear el producto:", error.message);
  }
}

/* ==========================
   EJEMPLOS DE EJECUCIÓN
========================== */

getProductos();        // Listar productos
getProductoById(1);    // Obtener producto con ID 1

crearProducto({
  title: "Miel Orgánica",
  body: "Miel 100% natural",
  userId: 1
});
