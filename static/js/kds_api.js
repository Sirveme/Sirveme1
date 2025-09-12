// Contiene todas las funciones que se comunican con el backend (llamadas fetch)

const BASE_URL_KDS = "/api/v1/panel/kds";
const BASE_URL_PANEL = "/api/v1/panel";

async function fetchAPI(url) {
    // Esta función centraliza el fetch y el manejo de errores de autenticación
    try {
        const response = await fetch(url, { credentials: 'include' });
        if (response.status === 401) {
            // Si el token expiró, redirigir al login
            window.location.href = '/login';
            return Promise.reject('No autenticado');
        }
        if (!response.ok) {
            throw new Error(`Error de red: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error en fetchAPI para la URL ${url}:`, error);
        throw error;
    }
}

function getPedidosPendientes(centroId) {
    return fetchAPI(`${BASE_URL_KDS}/${centroId}/pedidos-pendientes`);
}

function getPedidosCompletados(centroId) {
    return fetchAPI(`${BASE_URL_KDS}/${centroId}/pedidos-completados`);
}

function actualizarEstadoPedido(pedidoId, nuevoEstado) {
    return fetch(`/api/v1/panel/pedidos/${pedidoId}/actualizar-estado`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ nuevo_estado: nuevoEstado })
    });
}

function getMesasEnEspera() {
    return fetchAPI(`${BASE_URL_PANEL}/negocio/mesas-en-espera`);
}

function getAlertasDeTiempo() {
    return fetchAPI(`${BASE_URL_PANEL}/negocio/alertas-tiempo`);
}