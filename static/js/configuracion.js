document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('config-form');
    const rucInput = document.getElementById('ruc');
    const razonSocialInput = document.getElementById('razon_social');
    const nombreComercialInput = document.getElementById('nombre_comercial');
    const modoCobroSelect = document.getElementById('modo_cobro');
    const themeGallery = document.getElementById('theme-gallery');
    const temaIdInput = document.getElementById('tema_id');

    async function cargarDatos() {
        try {
            // Cargar la configuración del negocio
            const responseNegocio = await fetch('/api/v1/panel/configuracion-negocio', { credentials: 'include' });
            if (!responseNegocio.ok) throw new Error('Error al cargar la configuración.');
            const negocio = await responseNegocio.json();

            rucInput.value = negocio.ruc;
            razonSocialInput.value = negocio.razon_social;
            nombreComercialInput.value = negocio.nombre_comercial;
            modoCobroSelect.value = negocio.modo_cobro;
            temaIdInput.value = negocio.tema_id;

            // Cargar la galería de temas
            const responseTemas = await fetch('/api/v1/temas');
            if (!responseTemas.ok) throw new Error('Error al cargar los temas.');
            const temas = await responseTemas.json();

            themeGallery.innerHTML = '';
            temas.forEach(tema => {
                const themeCard = document.createElement('div');
                themeCard.className = 'theme-card';
                themeCard.dataset.themeId = tema.id;
                themeCard.innerHTML = `
                    <img src="${tema.url_vista_previa_dark || '/static/img/placeholder.png'}" alt="${tema.nombre}">
                    <p>${tema.nombre}</p>
                `;
                if (tema.id === negocio.tema_id) {
                    themeCard.classList.add('selected');
                }
                themeGallery.appendChild(themeCard);
            });

        } catch (error) {
            console.error("Error:", error);
            // Aquí mostraríamos una notificación de error
        }
    }

    themeGallery.addEventListener('click', (e) => {
        const card = e.target.closest('.theme-card');
        if (card) {
            document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            temaIdInput.value = card.dataset.themeId;
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            nombre_comercial: nombreComercialInput.value,
            modo_cobro: modoCobroSelect.value,
            tema_id: parseInt(temaIdInput.value, 10),
            logo_url: null // Aún no manejamos la subida de archivos
        };

        try {
            const response = await fetch('/api/v1/panel/configuracion-negocio', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', 'credentials': 'include' },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al guardar.');
            }
            // Aquí mostraríamos notificación de éxito
            alert('¡Configuración guardada con éxito!');
        } catch (error) {
            console.error("Error al guardar:", error);
            alert(`Error: ${error.message}`);
        }
    });

    cargarDatos();
});