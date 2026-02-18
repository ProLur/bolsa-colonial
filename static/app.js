// ────────────────────────────────────────────────
//  CONFIGURACIÓN
// ────────────────────────────────────────────────
const BIN_ID = "69958d2743b1c97be98825d3";
const BASE_URL = `https://api.jsonbin.io/v3/b/${BIN_ID}`;

const ASSET_KEY = "luna_cc";
const UPDATE_FACTOR = 0.001;    // cambio por cada unidad comprada/vendida
const MIN_PRICE = 0.01;

// ────────────────────────────────────────────────
//  FUNCIONES PRINCIPALES
// ────────────────────────────────────────────────

async function loadMarket() {
  const priceEl = document.getElementById("price");
  const trendEl = document.getElementById("trend");

  trendEl.textContent = "Conectando…";

  try {
    const response = await fetch(BASE_URL);
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}`);
    }

    const json = await response.json();
    const data = json.record?.[ASSET_KEY];

    if (!data || typeof data.price !== 'number') {
      throw new Error("Formato de datos inválido");
    }

    priceEl.textContent = data.price.toFixed(4);
    
    if (data.last_update) {
      const date = new Date(data.last_update);
      const timeStr = date.toLocaleTimeString('es', {hour:'2-digit', minute:'2-digit'});
      trendEl.textContent = `Última actualización: ${timeStr}`;
    } else {
      trendEl.textContent = "Datos cargados";
    }

  } catch (err) {
    console.error(err);
    priceEl.textContent = "—";
    trendEl.textContent = "No se pudo conectar con el mercado";
  }
}

async function updatePrice(newPrice) {
  // Este bin es público → NO se permite escritura directa desde frontend
  // Mostramos mensaje explicativo
  alert(
    "Este mercado está en modo SOLO LECTURA\n\n" +
    "El precio se muestra correctamente, pero las compras y ventas\n" +
    "son simuladas porque el bin es público y no permite modificaciones\n" +
    "desde el navegador.\n\n" +
    "Precio simulado después de la operación: " + newPrice.toFixed(4)
  );
  return false;
}

function buy(amount = 100) {
  const currentText = document.getElementById("price").textContent;
  const current = currentText === "—" ? 1.00 : parseFloat(currentText);
  
  const newPrice = current + (amount * UPDATE_FACTOR);
  
  updatePrice(newPrice);
}

function sell(amount = 100) {
  const currentText = document.getElementById("price").textContent;
  const current = currentText === "—" ? 1.00 : parseFloat(currentText);
  
  const newPrice = Math.max(MIN_PRICE, current - (amount * UPDATE_FACTOR));
  
  updatePrice(newPrice);
}

// ────────────────────────────────────────────────
//  INICIO
// ────────────────────────────────────────────────

window.addEventListener("load", () => {
  loadMarket();
  // Refrescar cada 25–40 segundos (evita abuso de la API gratuita)
  setInterval(loadMarket, 32000);
});
