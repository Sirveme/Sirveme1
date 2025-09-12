// Contiene todas las funciones que manipulan el DOM (lo que se ve en pantalla)

let DOM = {};
let eventHandlers = {};
let audioContextUnlocked = false;

function inicializarUI(handlers) {
    eventHandlers = handlers;
    DOM = {
        main: document.getElementById('kds-main'),
        grid: document.getElementById('comandas-grid'),
        status: document.getElementById('status-indicator'),
        overlay: document.getElementById('audio-unlock-overlay'),
        tabs: document.querySelectorAll('.tab-button'),
        mesasEsperaContainer: document.getElementById('mesas-espera-container')
    };
    DOM.overlay.addEventListener('click', unlockAudioAndInterface, { once: true });
    DOM.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            DOM.tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            eventHandlers.cambiarVistaHandler(tab.dataset.view);
        });
    });
}

function unlockAudioAndInterface() {
    DOM.overlay.classList.add('hidden');
    if (audioContextUnlocked) return;
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.volume = 0;
    audio.play().then(() => {
        audioContextUnlocked = true;
        console.log("Contexto de audio activado.");
    }).catch(e => console.warn("No se pudo activar el audio automáticamente."));
}

function renderizarComandas(listaComandas, vista, timers) {
    if (!DOM.grid) {
        console.error("Elemento 'comandas-grid' no encontrado en el DOM.");
        return;
    }
    if (!Array.isArray(listaComandas)) {
        console.error("Error: se esperaba un array de comandas, pero se recibió:", listaComandas);
        DOM.grid.innerHTML = `<p class="no-comandas">Error al cargar comandas.</p>`;
        return;
    }

    DOM.grid.innerHTML = '';
    if (listaComandas.length === 0) {
        DOM.grid.innerHTML = `<p class="no-comandas">No hay comandas en esta vista.</p>`;
    } else {
        listaComandas.forEach(comanda => agregarComanda(comanda, false, vista, timers));
    }
}

function agregarComanda(comandaData, animar, vista, timers) {
    if (!DOM.grid) return;
    
    const vistaActiva = document.querySelector('.tab-button.active')?.dataset.view;
    if (vistaActiva !== 'pendientes' && animar) return;

    const placeholder = DOM.grid.querySelector('.no-comandas');
    if (placeholder) placeholder.remove();

    if (audioContextUnlocked && animar) {
        new Audio('/static/sounds/notification.mp3').play();
    }
    
    const comandaElement = document.createElement('div');
    comandaElement.className = 'comanda';
    if (animar) comandaElement.classList.add('agregando');
    comandaElement.id = `pedido-${comandaData.pedido_id}`;
    
    let itemsHTML = '';
    comandaData.items.forEach(item => {
        let notaHTML = item.nota ? `<small class="item-nota">Nota: ${item.nota}</small>` : '';
        itemsHTML += `<li><span class="item-qty">${item.cantidad}x</span> <span class="item-name">${item.nombre}</span>${notaHTML}</li>`;
    });

    let footerHTML = '';
    if (vista === 'pendientes') {
        footerHTML = `<div class="comanda-footer"><button class="btn-listo">Marcar como Listo</button></div>`;
    } else {
        comandaElement.classList.add('completado');
        footerHTML = `<div class="comanda-footer"><p class="completed-text">Completado</p></div>`;
    }

    comandaElement.innerHTML = `
        <div class="comanda-header">
            <h2>Mesa ${comandaData.mesa_id}</h2>
            <span class="timer" id="timer-${comandaData.pedido_id}">00:00</span>
        </div>
        <div class="comanda-items"><ul>${itemsHTML}</ul></div>
        ${footerHTML}
    `;
    
    DOM.grid.prepend(comandaElement);

    if (vista === 'pendientes') {
        const boton = comandaElement.querySelector('.btn-listo');
        boton.addEventListener('click', () => {
            boton.textContent = 'Marcando...';
            boton.disabled = true;
            eventHandlers.marcarComoListoHandler(comandaData.pedido_id, boton);
        });

        const timerElement = document.getElementById(`timer-${comandaData.pedido_id}`);
        if(timerElement && comandaData.fecha_creacion) {
            const fechaCreacion = new Date(comandaData.fecha_creacion);
            timers[comandaData.pedido_id] = setInterval(() => {
                const ahora = new Date();
                const diff = ahora - fechaCreacion;
                const minutes = Math.floor(diff / 60000);
                const seconds = Math.floor((diff % 60000) / 1000);
                timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }, 1000);
        }
    } else {
        const timerElement = document.getElementById(`timer-${comandaData.pedido_id}`);
        if(timerElement) timerElement.textContent = "Cerrado";
    }

    if (animar) {
        setTimeout(() => comandaElement.classList.remove('agregando'), 100);
    }
}

function marcarComandaComoLista(pedidoId, timers) {
    const comandaElement = document.getElementById(`pedido-${pedidoId}`);
    if (!comandaElement) return;

    if(timers[pedidoId]) {
        clearInterval(timers[pedidoId]);
        delete timers[pedidoId];
    }

    const boton = comandaElement.querySelector('.btn-listo');
    comandaElement.classList.add('listo');
    if(boton) {
        boton.textContent = 'LISTO';
        boton.disabled = true;
    }
    
    setTimeout(() => {
        comandaElement.classList.add('ocultando');
        comandaElement.addEventListener('transitionend', () => {
            comandaElement.remove();
            if (DOM.grid && DOM.grid.childElementCount === 0) {
                DOM.grid.innerHTML = `<p class="no-comandas">No hay comandas en esta vista.</p>`;
            }
        });
    }, 3000);
}

function actualizarEstadoConexion(estaConectado) {
    if (estaConectado) {
        DOM.status.textContent = 'Conectado';
        DOM.status.className = 'status-indicator connected';
    } else {
        DOM.status.textContent = 'Desconectado';
        DOM.status.className = 'status-indicator disconnected';
    }
}

function renderizarMesasEnEspera(mesas) {
    DOM.mesasEsperaContainer.innerHTML = '';
    if (!mesas || mesas.length === 0) {
        DOM.mesasEsperaContainer.innerHTML = '<p class="no-mesas-espera">No hay mesas con demoras.</p>';
        return;
    }
    mesas.forEach(mesa => {
        const cardHTML = `
            <div class="mesa-espera-card">
                <div class="info">${mesa.zona_nombre} / Mesa ${mesa.mesa_nombre}</div>
                <div class="tiempo">ESPERA HACE ${mesa.minutos_espera} MINUTOS</div>
            </div>
        `;
        DOM.mesasEsperaContainer.insertAdjacentHTML('beforeend', cardHTML);
    });
}

function hablarTexto(texto, highPriority = false) {
    let audioQueue = [];
    let isSpeaking = false;

    if ('speechSynthesis' in window) {
        if (highPriority) audioQueue.unshift(texto);
        else audioQueue.push(texto);
        procesarColaDeAudio();
    }

    function procesarColaDeAudio() {
        if (isSpeaking || audioQueue.length === 0) return;
        isSpeaking = true;
        const textoActual = audioQueue.shift();
        const utterance = new SpeechSynthesisUtterance(textoActual);
        utterance.lang = 'es-ES';
        utterance.onend = () => { isSpeaking = false; procesarColaDeAudio(); };
        window.speechSynthesis.speak(utterance);
    }
}