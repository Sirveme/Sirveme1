document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM completamente cargado y script ejecutándose.");

    // --- ELEMENTOS DEL DOM ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const micButton = document.getElementById('mic-button');
    const textInput = document.getElementById('chat-text-input');
    const introPlaceholder = document.getElementById('intro-placeholder');
    const carritoContainer = document.getElementById('carrito-container');
    const carritoFooter = document.getElementById('carrito-footer');
    const totalEl = document.getElementById('carrito-total');
    const cantidadEl = document.getElementById('carrito-cantidad');
    const verMenuLink = document.getElementById('ver-menu-link');
    const menuSection = document.getElementById('menu-section');
    const closeMenuBtn = document.getElementById('close-menu-btn');
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const toast = document.getElementById('toast-notification');
    const btnConfirmarPedidoFooter = document.getElementById('btn-confirmar-pedido');
    
    // Elementos del Modal de Pago
    const modalPago = document.getElementById('modal-pago');
    const montoTotalPago = document.getElementById('monto-total-pago');
    const paso1Metodos = document.getElementById('paso1-metodos');
    const paso2Efectivo = document.getElementById('paso2-efectivo');

    // --- MODO OSCURO ---
    function setTheme(theme) {
        document.body.className = theme === 'light' ? 'light-mode' : '';
        themeToggleBtn.textContent = theme === 'light' ? '🌙' : '☀️';
        localStorage.setItem('theme', theme);
    }

    // --- FEEDBACK SONORO ---
    let audioQueue = [];
    let isSpeaking = false;
    function hablarTexto(texto, highPriority = false) {
        if ('speechSynthesis' in window) {
            const textoParaHablar = texto.replace('#', 'número ');
            if (highPriority) audioQueue.unshift(textoParaHablar);
            else audioQueue.push(textoParaHablar);
            procesarColaDeAudio();
        }
    }
    function procesarColaDeAudio() {
        if (isSpeaking || audioQueue.length === 0) return;
        isSpeaking = true;
        const texto = audioQueue.shift();
        const utterance = new SpeechSynthesisUtterance(texto);
        utterance.lang = 'es-ES';
        utterance.onend = () => { isSpeaking = false; procesarColaDeAudio(); };
        window.speechSynthesis.speak(utterance);
    }
    
    // --- RECONOCIMIENTO DE VOZ ---
    if (SpeechRecognition) {
        const recognitionInstance = new SpeechRecognition();
        recognitionInstance.lang = 'es-PE';
        recognitionInstance.interimResults = false;
        recognitionInstance.maxAlternatives = 1;
        
        recognitionInstance.onstart = () => micButton.classList.add('is-listening');
        recognitionInstance.onend = () => micButton.classList.remove('is-listening');
        recognitionInstance.onerror = (event) => console.error("Speech recognition error:", event.error);
        
        recognitionInstance.onresult = (event) => {
            const transcript = event.results[0][0].transcript.trim();
            if (transcript) {
                procesarComandoDeVoz(transcript);
            }
        };
        micButton.addEventListener('click', () => {
            micButton.classList.contains('is-listening') ? recognitionInstance.stop() : recognitionInstance.start();
        });
    } else {
        if(micButton) micButton.style.display = 'none';
    }

    // --- EVENT LISTENERS ---
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = localStorage.getItem('theme') || 'dark';
        setTheme(currentTheme === 'light' ? 'dark' : 'light');
    });

    textInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && textInput.value.trim()) {
            event.preventDefault();
            procesarComandoDeVoz(textInput.value.trim());
            textInput.value = '';
        }
    });

    verMenuLink.addEventListener('click', (e) => { e.preventDefault(); menuSection.classList.add('visible'); });
    closeMenuBtn.addEventListener('click', (e) => { e.preventDefault(); menuSection.classList.remove('visible'); });

    // --- FLUJO DE CONFIRMACIÓN DE PEDIDO (CORREGIDO) ---
    btnConfirmarPedidoFooter.addEventListener('click', iniciarProcesoDePedido);

    function iniciarProcesoDePedido() {
        const itemCards = carritoContainer.querySelectorAll('.carrito-product-card');
        if (itemCards.length === 0) {
            mostrarNotificacion("Tu carrito está vacío.");
            return;
        }
        btnConfirmarPedidoFooter.disabled = true;
        btnConfirmarPedidoFooter.textContent = 'Procesando...';
        const itemsParaEnviar = Array.from(itemCards).map(card => {
            const selectVariante = card.querySelector('.variante-select');
            const modificadoresSeleccionados = Array.from(card.querySelectorAll('.modificador-opcion input:checked')).map(input => parseInt(input.value));
            const notaCocinaInput = card.querySelector('.nota-cocina-input');
            const notaCocina = notaCocinaInput ? notaCocinaInput.value.trim() : null;
            return {
                producto_id: parseInt(card.dataset.productoId),
                cantidad: parseInt(card.querySelector('.cantidad-input').value),
                variante_id: selectVariante ? parseInt(selectVariante.value) : null,
                modificadores_seleccionados: modificadoresSeleccionados,
                nota_cocina: notaCocina || null
            };
        });
        const pathParts = window.location.pathname.split('/');
        const slugNegocio = pathParts[2];
        const zonaId = parseInt(pathParts[3]);
        const mesaId = parseInt(pathParts[4]);
        const pedidoData = { items: itemsParaEnviar, cliente: {}, zona_id: zonaId, mesa_id: mesaId };
        
        fetch(`/api/v1/carta/${slugNegocio}/${zonaId}/${mesaId}/iniciar-proceso-pedido`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(pedidoData)
        })
        .then(response => {
             if (!response.ok) {
                return response.json().then(err => Promise.reject(err.detail || 'Los datos enviados son incorrectos.'));
            }
            return response.json();
        })
        .then(data => {
            manejarRespuestaDeProceso(data);
        })
        .catch(error => {
            console.error("Error al iniciar proceso de pedido:", error);
            mostrarNotificacion(error.toString());
        })
        .finally(() => {
            btnConfirmarPedidoFooter.disabled = false;
            btnConfirmarPedidoFooter.textContent = 'Confirmar Pedido';
        });
    }

    function manejarRespuestaDeProceso(respuesta) {
        if (respuesta.status === "enviado_a_cocina") {
            const mensajeConfirmacion = `¡Pedido #${respuesta.pedido_id} confirmado!`;
            mostrarNotificacion(mensajeConfirmacion, 'success');
            resetearCarrito(false);
        } 
        else if (respuesta.status === "pago_requerido") {
            montoTotalPago.textContent = totalEl.textContent;
            paso1Metodos.style.display = 'grid';
            paso2Efectivo.style.display = 'none';
            modalPago.classList.add('visible');
            const btnEfectivo = paso1Metodos.querySelector('[data-metodo="efectivo"]');
            const btnVolver = paso2Efectivo.querySelector('#btn-volver-metodos');
            const btnAvisarCaja = paso2Efectivo.querySelector('#btn-avisar-caja');
            const efectivoHandler = () => {
                paso1Metodos.style.display = 'none';
                paso2Efectivo.style.display = 'block';
            };
            const volverHandler = () => {
                paso2Efectivo.style.display = 'none';
                paso1Metodos.style.display = 'grid';
            };
            const avisarCajaHandler = async () => {
                const aliasInput = document.getElementById('alias-cliente');
                const alias = aliasInput.value.trim();
                if (!alias) {
                    mostrarNotificacion("Por favor, ingresa un nombre o alias.");
                    return;
                }
                const pedidoId = respuesta.pedido_id;
                if (!pedidoId) {
                    mostrarNotificacion("Error: No se pudo obtener el ID del pedido. Intenta de nuevo.");
                    return;
                }
                btnAvisarCaja.disabled = true;
                btnAvisarCaja.textContent = 'Enviando...';
                try {
                    const response = await fetch(`/api/v1/panel/pedidos/${pedidoId}/notificar-cobro-efectivo`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ alias_cliente: alias })
                    });
                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.detail || 'No se pudo notificar a caja.');
                    }
                    mostrarNotificacion("¡Excelente! Hemos avisado a caja. Atento a tu nombre.", 'success', 6000);
                    modalPago.classList.remove('visible');
                    resetearCarrito(false);
                } catch (error) {
                    mostrarNotificacion(error.message);
                } finally {
                    btnAvisarCaja.disabled = false;
                    btnAvisarCaja.textContent = 'Avisar a Caja';
                }
            };
            btnEfectivo.replaceWith(btnEfectivo.cloneNode(true));
            paso1Metodos.querySelector('[data-metodo="efectivo"]').addEventListener('click', efectivoHandler);
            btnVolver.replaceWith(btnVolver.cloneNode(true));
            paso2Efectivo.querySelector('#btn-volver-metodos').addEventListener('click', volverHandler);
            btnAvisarCaja.replaceWith(btnAvisarCaja.cloneNode(true));
            paso2Efectivo.querySelector('#btn-avisar-caja').addEventListener('click', avisarCajaHandler);
        }
    }

    // --- El resto de las funciones (DOM, Carrito, etc) se quedan igual ---
    carritoContainer.addEventListener('click', (event) => {
        if (event.target.closest('.card-toggle-collapse')) {
            event.target.closest('.carrito-product-card').classList.toggle('is-collapsed');
        }
        if (event.target.closest('.remove-item-btn')) {
            event.target.closest('.carrito-product-card').remove();
            actualizarCalculoTotal();
        }
        if (event.target.classList.contains('card-image-placeholder')) {
            const productName = event.target.dataset.productName;
            mostrarNotificacion(`Mostrando detalles de ${productName}`, 'info');
        }
    });
    carritoContainer.addEventListener('input', (event) => {
        if (event.target.matches('.cantidad-input, .variante-select, .nota-cocina-input')) {
            actualizarCalculoTotal();
        }
    });
    carritoContainer.addEventListener('change', (event) => {
        if (event.target.matches('input[type="radio"], input[type="checkbox"]')) {
            actualizarCalculoTotal();
        }
    });
    const savedTheme = localStorage.getItem('theme') || 'dark';
    setTheme(savedTheme);
    function procesarComandoDeVoz(texto) {
        const pathParts = window.location.pathname.split('/');
        const slugNegocio = pathParts[2];
        fetch(`/api/v1/carta/${slugNegocio}/parse-orden-voz`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ texto_orden: texto })
        })
        .then(response => response.ok ? response.json() : Promise.reject('Respuesta del servidor no fue OK.'))
        .then(data => {
            console.log("Respuesta de Intención:", data);
            despacharAccion(data);
        })
        .catch(error => {
            console.error("Error al procesar comando:", error);
            mostrarNotificacion("Lo sentimos, no pudimos procesar tu pedido.");
        });
    }
    function despacharAccion(respuesta) {
        const intent = respuesta.intent;
        const entities = respuesta.entities;
        if (!intent || !entities) {
            mostrarNotificacion("No entendí lo que dijiste, intenta de nuevo.");
            return;
        }
        switch(intent) {
            case "ADD_ITEMS": agregarOActualizarItems(entities, false); break;
            case "MODIFY_QUANTITY": agregarOActualizarItems(entities, true); break;
            case "REMOVE_ITEMS": eliminarItems(entities); break;
            case "RESET_ORDER": resetearCarrito(); if (entities.length > 0) { agregarOActualizarItems(entities, false); } break;
            case "NOT_FOUND": const productName = entities[0]?.product_name || "El producto"; mostrarNotificacion(`Lo sentimos, no vendemos "${productName}".`); break;
            default: mostrarNotificacion("No entendí lo que dijiste, por favor sé más específico.");
        }
        const resumenAccion = generarResumen(intent, entities);
        if (resumenAccion) { hablarTexto(resumenAccion, true); }
    }
    function generarResumen(intent, entities) {
        if (entities.length === 0) return null;
        const count = entities.length;
        const primerProducto = entities[0].full_product_data?.nombre || 'un producto';
        switch(intent) {
            case "ADD_ITEMS": return count > 1 ? `${count} productos añadidos.` : `Añadido ${primerProducto}.`;
            case "MODIFY_QUANTITY": return count > 1 ? `Cantidades corregidas.` : `Cantidad de ${primerProducto} corregida.`;
            case "REMOVE_ITEMS": return count > 1 ? `Se han eliminado varios productos.` : `Se ha modificado tu pedido de ${primerProducto}.`;
            default: return null;
        }
    }
    function agregarOActualizarItems(items, esModificacion = false) {
        if (items.length === 0) { if (!esModificacion) mostrarNotificacion("No encontramos productos que coincidan."); return; }
        let itemAgregado = false;
        items.forEach(item => {
            const productoCompleto = item.full_product_data;
            if (!productoCompleto) return;
            const existingItemCard = carritoContainer.querySelector(`[data-producto-id="${productoCompleto.id}"]`);
            if (existingItemCard) {
                const cantidadInput = existingItemCard.querySelector('.cantidad-input');
                cantidadInput.value = esModificacion ? item.quantity : parseInt(cantidadInput.value) + item.quantity;
                mostrarFeedbackVisual(existingItemCard);
            } else {
                let opcionesHTML = '';
                if (productoCompleto.variantes_disponibles && productoCompleto.variantes_disponibles.length > 0) {
                    const opciones = productoCompleto.variantes_disponibles.map(v => `<option value="${v.id}" data-precio="${v.precio}">${v.nombre}</option>`).join('');
                    opcionesHTML = `<div class="card-product-options"><select name="variante" class="variante-select">${opciones}</select></div>`;
                }
                let modificadoresHTML = '';
                if (productoCompleto.modificadores_disponibles && productoCompleto.modificadores_disponibles.length > 0) {
                    productoCompleto.modificadores_disponibles.forEach(grupo => {
                        const tipoInput = grupo.seleccion_maxima === 1 ? 'radio' : 'checkbox';
                        const opcionesModificador = grupo.opciones.map(op => `
                            <label class="modificador-opcion">
                                <span class="opcion-label">
                                    <input type="${tipoInput}" name="grupo-${productoCompleto.id}-${grupo.id}" value="${op.id}" data-precio-extra="${op.precio_extra}">
                                    <span>${op.nombre}</span>
                                </span>
                                ${op.precio_extra > 0 ? `<span class="opcion-precio">+S/${parseFloat(op.precio_extra).toFixed(2)}</span>` : ''}
                            </label>`).join('');
                        modificadoresHTML += `<div class="modificador-grupo"><h4>${grupo.nombre} (Elige hasta ${grupo.seleccion_maxima})</h4>${opcionesModificador}</div>`;
                    });
                }
                const cardHTML = `
                    <div class="carrito-product-card" data-producto-id="${productoCompleto.id}" data-precio-base="${productoCompleto.precio_base || 0}">
                        <div class="card-feedback-icon">✓</div>
                        <div class="card-image-placeholder" data-product-name="${productoCompleto.nombre}"></div>
                        <div class="card-content">
                            <div class="card-product-header">
                                <h3>${productoCompleto.nombre}</h3>
                                <div class="card-main-actions">
                                    <div class="card-product-actions">
                                        <input type="number" class="cantidad-input" value="${item.quantity}" min="1">
                                        <div class="item-subtotal"></div>
                                        <button type="button" class="remove-item-btn" title="Quitar item">&times;</button>
                                    </div>
                                    <button type="button" class="card-toggle-collapse">
                                       <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 15.75l7.5-7.5 7.5 7.5" /></svg>
                                    </button>
                                </div>
                            </div>
                            <div class="card-product-details">
                                ${opcionesHTML}
                                ${modificadoresHTML}
                            </div>
                            <div class="card-kitchen-note">
                               <textarea class="nota-cocina-input" placeholder="Mensaje para Cocina..."></textarea>
                            </div>
                        </div>
                    </div>`;
                carritoContainer.insertAdjacentHTML('beforeend', cardHTML);
                mostrarFeedbackVisual(carritoContainer.lastElementChild);
            }
            itemAgregado = true;
        });
        if(itemAgregado) actualizarCalculoTotal();
    }
    function eliminarItems(items) {
        items.forEach(item => {
            const cardToRemove = carritoContainer.querySelector(`[data-producto-id="${item.product_id}"]`);
            if (cardToRemove) {
                const cantidadInput = cardToRemove.querySelector('.cantidad-input');
                const cantidadActual = parseInt(cantidadInput.value);
                const nuevaCantidad = cantidadActual - item.quantity;
                if (nuevaCantidad <= 0 || item.quantity >= 999) {
                    cardToRemove.remove();
                } else {
                    cantidadInput.value = nuevaCantidad;
                    mostrarFeedbackVisual(cardToRemove, 'remove');
                }
            }
        });
        actualizarCalculoTotal();
    }
    function resetearCarrito(conMensaje = true) {
        carritoContainer.innerHTML = '';
        actualizarCalculoTotal();
        if (conMensaje) { mostrarNotificacion("Tu pedido ha sido reiniciado.", "info"); }
    }
    function mostrarFeedbackVisual(cardElement, type = 'add') {
        const icon = cardElement.querySelector('.card-feedback-icon');
        if (!icon) return;
        icon.textContent = type === 'add' ? '✓' : '−';
        icon.style.color = type === 'add' ? `var(--success-color)` : `var(--danger-color)`;
        cardElement.classList.add('show-feedback');
        setTimeout(() => { cardElement.classList.remove('show-feedback'); }, 1000);
    }
    function actualizarCalculoTotal() {
        const itemCards = carritoContainer.querySelectorAll('.carrito-product-card');
        let totalGeneral = 0;
        let cantidadTotalItems = 0;
        itemCards.forEach(card => {
            const cantidad = parseInt(card.querySelector('.cantidad-input').value) || 0;
            let precioUnitario = 0;
            const selectVariante = card.querySelector('.variante-select');
            if (selectVariante) {
                precioUnitario = parseFloat(selectVariante.options[selectVariante.selectedIndex].dataset.precio);
            } else {
                precioUnitario = parseFloat(card.dataset.precioBase);
            }
            let precioModificadores = 0;
            card.querySelectorAll('.modificador-opcion input:checked').forEach(input => {
                precioModificadores += parseFloat(input.dataset.precioExtra);
            });
            const subtotal = cantidad * (precioUnitario + precioModificadores);
            card.querySelector('.item-subtotal').textContent = `S/ ${subtotal.toFixed(2)}`;
            totalGeneral += subtotal;
            cantidadTotalItems += cantidad;
        });
        totalEl.textContent = `S/ ${totalGeneral.toFixed(2)}`;
        cantidadEl.textContent = cantidadTotalItems;
        if (itemCards.length > 0) {
            introPlaceholder.classList.add('hidden');
            carritoFooter.classList.add('visible');
        } else {
            introPlaceholder.classList.remove('hidden');
            carritoFooter.classList.remove('visible');
        }
    }
});