let KDS_CENTRO_ID;
let timers = {};
let audioContextUnlocked = false;
let alertTimer;

// --- FUNCIONES DE API ---
async function fetchAPI(url) {
    try {
        const response = await fetch(url, { credentials: 'include' });
        if (response.status === 401) {
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

const getPedidosPendientes = (centroId) => fetchAPI(`/api/v1/panel/kds/${centroId}/pedidos-pendientes`);
const getPedidosCompletados = (centroId) => fetchAPI(`/api/v1/panel/kds/${centroId}/pedidos-completados`);
const actualizarEstadoPedido = (pedidoId, nuevoEstado) => fetch(`/api/v1/panel/pedidos/${pedidoId}/actualizar-estado`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ nuevo_estado: nuevoEstado }) });
const marcarComoPagadoAPI = (pedidoId) => fetch(`/api/v1/panel/pedidos/${pedidoId}/marcar-pagado`, { method: 'POST', credentials: 'include' });
const getPedidosEnEspera = () => fetchAPI(`/api/v1/panel/negocio/pedidos-en-espera`);

// --- LÓGICA DE WEBSOCKET ---
function conectarWebSocket(centroId, onMessageCallback, onStatusChangeCallback) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${proto}//${host}/ws/kds/${centroId}`;
    const socket = new WebSocket(url);

    socket.onopen = () => onStatusChangeCallback(true);
    socket.onmessage = (event) => { try { onMessageCallback(JSON.parse(event.data)); } catch (e) { console.error("Error al parsear WS:", e); } };
    socket.onclose = () => { onStatusChangeCallback(false); setTimeout(() => conectarWebSocket(centroId, onMessageCallback, onStatusChangeCallback), 3000); };
    socket.onerror = (error) => { console.error("Error WS:", error); socket.close(); };
}

// --- LÓGICA DE LA INTERFAZ (UI) ---
function renderizarComandas(listaComandas, vista) {
    const grid = document.getElementById(`vista-${vista}`);
    if (!grid) return;
    grid.innerHTML = '';
    
    if (!Array.isArray(listaComandas) || listaComandas.length === 0) {
        grid.innerHTML = `<p class="no-comandas">No hay comandas en esta vista.</p>`;
        return;
    }
    
    listaComandas.forEach(comanda => {
        if (comanda.estado === 'PENDIENTE_DE_PAGO') {
            agregarAlertaDeCobro(comanda);
        } else {
            agregarComanda(comanda, false, vista);
        }
    });
}

function agregarComanda(comandaData, animar, vista) {
    const grid = document.getElementById(`vista-${vista}`);
    if (!grid) return;
    const placeholder = grid.querySelector('.no-comandas');
    if (placeholder) placeholder.remove();

    if (audioContextUnlocked && animar) new Audio('/static/sounds/notification.mp3').play();
    
    const comandaElement = document.createElement('div');
    comandaElement.className = 'comanda';
    if (animar) comandaElement.classList.add('agregando');
    comandaElement.id = `pedido-${comandaData.pedido_id}`;
    
    let itemsHTML = comandaData.items.map(item => `<li><span class="item-qty">${item.cantidad}x</span> <span class="item-name">${item.nombre}</span></li>`).join('');

    comandaElement.innerHTML = `
        <div class="comanda-header">
            <div><h2>Mesa ${comandaData.mesa_id}</h2><div class="pedido-id">Pedido #${comandaData.pedido_id}</div></div>
            <div class="header-right"><span class="pedido-total">S/ ${comandaData.total_pedido.toFixed(2)}</span><span class="timer" id="timer-${comandaData.pedido_id}">00:00</span></div>
        </div>
        <div class="comanda-items"><ul>${itemsHTML}</ul></div>
        <div class="comanda-footer"><button class="btn-listo">Marcar como Listo</button></div>
    `;
    
    grid.prepend(comandaElement);
    const boton = comandaElement.querySelector('.btn-listo');
    boton.addEventListener('click', () => handleMarcarComoListo(comandaData.pedido_id, boton));
        
    const timerElement = document.getElementById(`timer-${comandaData.pedido_id}`);
    if (timerElement && comandaData.fecha_creacion) {
        const fechaCreacion = new Date(comandaData.fecha_creacion);
        timers[comandaData.pedido_id] = setInterval(() => {
            const diff = new Date() - fechaCreacion;
            const minutes = String(Math.floor(diff / 60000)).padStart(2, '0');
            const seconds = String(Math.floor((diff % 60000) / 1000)).padStart(2, '0');
            timerElement.textContent = `${minutes}:${seconds}`;
        }, 1000);
    }
    
    if (animar) setTimeout(() => comandaElement.classList.remove('agregando'), 100);
}

function agregarAlertaDeCobro(alertaData) {
    const grid = document.getElementById('vista-pendientes');
    if (!grid) {
        console.error("[UI Error] No se encontró #vista-pendientes para agregar alerta de cobro.");
        return;
    }

    const placeholder = grid.querySelector('.no-comandas');
    if (placeholder) placeholder.remove();

    if (audioContextUnlocked) {
        new Audio('/static/sounds/cash-register.mp3').play().catch(e => console.warn("Error al reproducir sonido de caja:", e));
    }

    const alertaElement = document.createElement('div');
    alertaElement.className = 'comanda alerta-cobro';
    alertaElement.id = `pedido-${alertaData.pedido_id}`;
    
    let itemsHTML = '';
    if (alertaData.items && Array.isArray(alertaData.items)) {
        itemsHTML = alertaData.items.map(item => `<li><span class="item-qty">${item.cantidad}x</span> ${item.nombre}</li>`).join('');
    }

    // --- CORRECCIÓN DEL TYPEERROR ---
    // Verificamos que 'total_cobrar' exista y le damos un valor por defecto si no.
    const totalACobrar = alertaData.total_cobrar || 0.0;

    alertaElement.innerHTML = `
        <div class="comanda-header">
            <h2>Mesa ${alertaData.mesa_id}</h2>
            <span class="total-cobrar">S/ ${totalACobrar.toFixed(2)}</span>
        </div>
        <div class="comanda-items">
            <p><strong>COBRO PENDIENTE</strong> - Pedido #${alertaData.pedido_id}</p>
            <ul>${itemsHTML}</ul>
        </div>
        <div class="comanda-footer">
            <button class="btn-listo btn-cobrado">Marcar como Pagado</button>
        </div>
    `;
    
    grid.prepend(alertaElement);

    alertaElement.querySelector('.btn-cobrado').addEventListener('click', (e) => {
        handleMarcarComoPagado(alertaData.pedido_id, e.currentTarget);
    });
}



function marcarComandaComoLista(pedidoId) {
    const comandaElement = document.getElementById(`pedido-${pedidoId}`);
    if (!comandaElement) return;
    if (timers[pedidoId]) { clearInterval(timers[pedidoId]); delete timers[pedidoId]; }
    const boton = comandaElement.querySelector('.btn-listo');
    comandaElement.classList.add('listo');
    if(boton) { boton.textContent = 'LISTO'; boton.disabled = true; }
    setTimeout(() => {
        comandaElement.classList.add('ocultando');
        comandaElement.addEventListener('transitionend', () => comandaElement.remove());
    }, 3000);
}

function renderizarPedidosEnEspera(mesas) {
    const container = document.getElementById('pedidos-espera-container');
    if (!container) return;
    container.innerHTML = '';
    if (!mesas || mesas.length === 0) {
        container.innerHTML = '<p class="no-pedidos-espera">No hay pedidos con demora.</p>';
    } else {
        mesas.forEach(mesa => {
            const itemEjemploHTML = mesa.item_ejemplo ? `<small>${mesa.item_ejemplo} y más...</small>` : '';
            const cardHTML = `
                <div class="mesa-espera-card">
                    <div class="info">${mesa.zona_nombre} / Mesa ${mesa.mesa_nombre}</div>
                    <div class="item-ejemplo">${itemEjemploHTML}</div>
                    <div class="tiempo">ESPERA HACE ${mesa.minutos_espera} MINUTOS</div>
                </div>`;
            container.insertAdjacentHTML('beforeend', cardHTML);
        });
    }
}


// --- GESTIÓN DE EVENTOS CENTRALIZADA (LA SOLUCIÓN AL BUG) ---
document.addEventListener('DOMContentLoaded', () => {
    const kdsMain = document.getElementById('kds-main');

    // Usamos 'delegación de eventos'. Un solo listener para todo el contenedor.
    kdsMain.addEventListener('click', (event) => {
        const boton = event.target.closest('.btn-listo, .btn-cobrado');
        if (!boton) return; // Si no se hizo clic en un botón, no hacer nada.

        const comandaElement = boton.closest('.comanda');
        if (!comandaElement) return;

        const pedidoId = comandaElement.id.split('-')[1];

        if (boton.classList.contains('btn-cobrado')) {
            handleMarcarComoPagado(pedidoId, boton);
        } else {
            handleMarcarComoListo(pedidoId, boton);
        }
    });
});

// --- MANEJADORES Y LÓGICA PRINCIPAL ---
async function handleCambiarVista(vista) {
    document.querySelectorAll('.comandas-grid').forEach(g => g.classList.remove('active-view'));
    document.getElementById(`vista-${vista}`).classList.add('active-view');
    
    Object.values(timers).forEach(clearInterval);
    timers = {};
    try {
        let pedidos = [];
        if (vista === 'pendientes') {
            pedidos = await getPedidosPendientes(KDS_CENTRO_ID);
        } else if (vista === 'completados') {
            pedidos = await getPedidosCompletados(KDS_CENTRO_ID);
        }
        renderizarComandas(pedidos, vista);
    } catch (error) {
        console.error(`Error al cargar la vista ${vista}:`, error);
        renderizarComandas([], vista);
    }
}

async function handleMarcarComoListo(pedidoId, boton) {
    try {
        await actualizarEstadoPedido(pedidoId, 'LISTO_PARA_RECOGER');
        marcarComandaComoLista(pedidoId);
    } catch (error) {
        console.error('Error al marcar como listo:', error);
        alert('No se pudo marcar el pedido como listo.');
        boton.disabled = false;
        boton.textContent = 'Marcar como Listo';
    }
}

async function handleMarcarComoPagado(pedidoId, boton) {
    boton.disabled = true;
    boton.textContent = 'Procesando...';
    try {
        const response = await fetch(`/api/v1/panel/pedidos/${pedidoId}/marcar-pagado`, {
            method: 'POST',
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error('Falló la confirmación de pago en el servidor.');
        }
        
        const alertaElement = document.getElementById(`pedido-${pedidoId}`);
        if(alertaElement) {
            alertaElement.classList.add('listo'); // Reutilizamos el estilo verde
            setTimeout(() => {
                alertaElement.classList.add('ocultando');
                alertaElement.addEventListener('transitionend', () => alertaElement.remove());
            }, 2000);
        }
    } catch (error) {
        console.error("Error al marcar como pagado:", error);
        alert("No se pudo procesar el pago.");
        boton.disabled = false;
        boton.textContent = 'Marcar como Pagado';
    }
}

function iniciarTimersPeriodicos() {
    if (alertTimer) clearInterval(alertTimer);
    const actualizarAlertas = async () => {
        try {
            const mesasEnEspera = await getPedidosEnEspera();
            renderizarPedidosEnEspera(mesasEnEspera);
        } catch(e) { console.error("Error actualizando pedidos en espera:", e); }
    };
    actualizarAlertas();
    alertTimer = setInterval(actualizarAlertas, 30000); // Actualizar cada 30 segundos
}


// --- FUNCIÓN DE INICIALIZACIÓN GLOBAL ---
function inicializarKDS(centroId) {
    KDS_CENTRO_ID = centroId;
    const overlay = document.getElementById('audio-unlock-overlay');
    const tabs = document.querySelectorAll('.tab-button');
    const statusIndicator = document.getElementById('status-indicator');

    overlay.addEventListener('click', () => {
        overlay.classList.add('hidden');
        if (!audioContextUnlocked) {
            new Audio('/static/sounds/notification.mp3').volume = 0;
            audioContextUnlocked = true;
        }
    }, { once: true });

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            handleCambiarVista(tab.dataset.view);
        });
    });

    handleCambiarVista('pendientes').catch(console.error);

    // --- LÓGICA DE DEPURACIÓN AÑADIDA ---
    conectarWebSocket(
        centroId,
        (mensajeRecibido) => {
            if (mensajeRecibido.tipo_alerta === 'COBRO_PENDIENTE') {
                agregarAlertaDeCobro(mensajeRecibido);
            } else {
                agregarComanda(mensajeRecibido, true, 'pendientes');
            }
        },
        (estaConectado) => {
            statusIndicator.textContent = estaConectado ? 'Conectado' : 'Desconectado';
            statusIndicator.className = `status-indicator ${estaConectado ? 'connected' : 'disconnected'}`;
        }
    );
    
    iniciarTimersPeriodicos();
}

window.inicializarKDS = inicializarKDS;