import { fetchWithAuth } from '/static/js/core/api_interceptor.js';

document.addEventListener('DOMContentLoaded', () => {
    const btnNuevoNegocio = document.getElementById('btn-nuevo-negocio');
    const modal = document.getElementById('modal-negocio');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    const formNegocio = document.getElementById('form-negocio');
    const tableBody = document.getElementById('negocios-table-body');
    const modalError = document.getElementById('modal-error-message');
    
    const showModal = () => modal.classList.add('visible');
    const hideModal = () => {
        modal.classList.remove('visible');
        formNegocio.reset();
        modalError.textContent = '';
    };

    btnNuevoNegocio.addEventListener('click', showModal);
    btnCancelarModal.addEventListener('click', hideModal);

    // Cargar la tabla de negocios al iniciar
    async function cargarNegocios() {
        try {
            const response = await fetchWithAuth('/api/v1/superadmin/negocios');
            const negocios = await response.json();
            
            tableBody.innerHTML = '';
            negocios.forEach(negocio => {
                const row = `
                    <tr>
                        <td>${negocio.id}</td>
                        <td>${negocio.ruc}</td>
                        <td>${negocio.razon_social}</td>
                        <td>${negocio.nombre_comercial}</td>
                        <td>${negocio.activo ? 'Sí' : 'No'}</td>
                    </tr>
                `;
                tableBody.insertAdjacentHTML('beforeend', row);
            });
        } catch (error) {
            console.error("Error al cargar negocios:", error);
            tableBody.innerHTML = `<tr><td colspan="5">No se pudieron cargar los datos.</td></tr>`;
        }
    }

    // Manejar el envío del formulario
    formNegocio.addEventListener('submit', async (e) => {
        e.preventDefault();
        modalError.textContent = '';

        const formData = new FormData(formNegocio);
        
        // Estructurar el JSON como lo espera el backend
        const data = {
            ruc: formData.get('ruc'),
            razon_social: formData.get('razon_social'),
            nombre_comercial: formData.get('nombre_comercial'),
            dueño: {
                nombre_completo: formData.get('dueño-nombre_completo'),
                tipo_documento: 'DNI', // Asumimos DNI por ahora
                numero_documento: formData.get('dueño-numero_documento'),
                email: formData.get('dueño-email'),
                telefono: formData.get('dueño-telefono'),
                password: formData.get('dueño-password')
            }
        };

        try {
            const response = await fetchWithAuth('/api/v1/superadmin/negocios', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error desconocido');
            }

            hideModal();
            cargarNegocios(); // Recargar la tabla con el nuevo negocio
            // Aquí podríamos mostrar una notificación de éxito
            
        } catch (error) {
            modalError.textContent = error.message;
        }
    });

    cargarNegocios();
});