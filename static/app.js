// ────────────────────────────────────────────────
//  CONFIGURACIÓN – CAMBIA ESTOS VALORES
// ────────────────────────────────────────────────
const BIN_ID       = "PON_AQUÍ_TU_BIN_ID";          // ej: 67b8f2a39d8c4e2f1a3b4567
const MASTER_KEY   = "PON_AQUÍ_TU_SECRET_KEY";      // ej: $2a$10$xxxxxxxxxxxxxxxxxxxxxxxxxxxx
const ASSET_KEY    = "luna_cc";                      // clave dentro del JSON
const UPDATE_FACTOR = 0.001;                         // cuánto sube/baja por unidad
const MIN_PRICE    = 0.01;

// ────────────────────────────────────────────────
//  FUNCIONES PRINCIPALES
// ────────────────────────────────────────────────
const BASE_URL = `https://api.jsonbin.io/v3/b/${BIN_ID}`;

async function loadMarket() {
    const trendEl = document.getElementById("trend");
    const priceEl = document.getElementById("price");

    trendEl.textContent = "Conectando…";

    try {
        const headers = MASTER_KEY ? { "X-Master-Key": MASTER_KEY } : {};
        const resp = await fetch(BASE_URL, { headers });

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }

        const json = await resp.json();
        const data = json.record?.[ASSET_KEY];

        if (!data || typeof data.price !== "number") {
            throw new Error("Formato de datos inválido");
        }

        priceEl.textContent = data.price.toFixed(4);
        const time = new Date(data.last_update).toLocaleTimeString("es", {timeStyle: "short"});
        trendEl.textContent = `Últ. act. ${time}`;
    } catch (err) {
        console.error(err);
        trendEl.textContent = "Error al conectar";
        priceEl.textContent = "—";
    }
}

async function updatePrice(newPrice) {
    if (!MASTER_KEY) {
        alert("Modo solo lectura – no se puede modificar el precio");
        return false;
    }

    try {
        const resp = await fetch(BASE_URL, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-Master-Key": MASTER_KEY
            },
            body: JSON.stringify({
                [ASSET_KEY]: {
                    price: Number(newPrice.toFixed(4)),
                    last_update: new Date().toISOString()
                }
            })
        });

        if (!resp.ok) {
            throw new Error(`HTTP ${resp.status}`);
        }

        await loadMarket();  // refrescar vista
        return true;
    } catch (err) {
        console.error("Error al guardar precio:", err);
        alert("No se pudo actualizar el precio");
        return false;
    }
}

// ────────────────────────────────────────────────
//  ACCIONES DE COMPRA / VENTA
// ────────────────────────────────────────────────
function buy(amount) {
    if (amount <= 0) return;

    const currentStr = document.getElementById("price").textContent;
    let current = currentStr === "—" ? 1.00 : parseFloat(currentStr);

    const increment = amount * UPDATE_FACTOR;
    const newPrice = current + increment;

    updatePrice(newPrice).then(ok => {
        if (ok) alert(`Compraste ${amount} → nuevo precio: ${newPrice.toFixed(4)}`);
    });
}

function sell(amount) {
    if (amount <= 0) return;

    const currentStr = document.getElementById("price").textContent;
    let current = currentStr === "—" ? 1.00 : parseFloat(currentStr);

    const decrement = amount * UPDATE_FACTOR;
    const newPrice = Math.max(MIN_PRICE, current - decrement);

    updatePrice(newPrice).then(ok => {
        if (ok) alert(`Vendiste ${amount} → nuevo precio: ${newPrice.toFixed(4)}`);
    });
}

// ────────────────────────────────────────────────
//  INICIO
// ────────────────────────────────────────────────
window.addEventListener("load", () => {
    loadMarket();
    // Opcional: refrescar cada 20–40 segundos
    setInterval(loadMarket, 35000);
});
