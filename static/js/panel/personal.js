document.addEventListener('DOMContentLoaded', () => {
    // Selectores del DOM
    const btnNuevoEmpleado = document.getElementById('btn-nuevo-empleado');
    const modal = document.getElementById('modal-empleado');
    const btnCancelarModal = document.getElementById('btn-cancelar-modal');
    const formEmpleado = document.getElementById('form-empleado');
    const tableBody = document.getElementById('personal-table-body');
    const modalError = document.getElementById('modal-error-message');
    const rolSelect = document.getElementById('rol_id');
    const localSelect = document.getElementById('local_asignado_id');
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const eyeIcon = togglePasswordBtn.querySelector('.eye-icon');
    const eyeOffIcon = togglePasswordBtn.querySelector('.eye-off-icon');

    // --- MANEJO DE LA VISIBILIDAD DEL MODAL ---
    const showModal = () => modal.classList.add('visible');
    const hideModal = () => {
        modal.classList.remove('visible');
        formEmpleado.reset();
        modalError.textContent = '';
        modalError.style.display = 'none';
    };

    btnNuevoEmpleado.addEventListener('click', showModal);
    btnCancelarModal.addEventListener('click', hideModal);

    async function fetchAPI(url) {
        try {
            const response = await fetch(url, { credentials: 'include' });
            if (response.status === 401) window.location.href = '/login';
            if (!response.ok) throw new Error(`Error de red: ${response.statusText}`);
            return await response.json();
        } catch (error) {
            console.error(`Error en fetchAPI para ${url}:`, error);
            throw error;
        }
    }

    async function cargarDatosIniciales() {
        tableBody.innerHTML = `<tr><td colspan="5">Cargando...</td></tr>`;
        try {
            const [roles, personal, locales] = await Promise.all([
                fetchAPI('/api/v1/gestion/roles'),
                fetchAPI('/api/v1/gestion/personal'),
                fetchAPI('/api/v1/gestion/locales') // NUEVA LLAMADA
            ]);
            
            rolSelect.innerHTML = '<option value="" disabled selected>Seleccione un rol...</option>';
            roles.forEach(rol => {
                if (rol.nombre !== 'SuperUsuario' && rol.nombre !== 'Dueño') {
                    rolSelect.innerHTML += `<option value="${rol.id}">${rol.nombre}</option>`;
                }
            });

            // === CARGAR LOCALES EN EL DROPDOWN ===
            localSelect.innerHTML = '<option value="" disabled selected>Seleccione un local...</option>';
            locales.forEach(local => {
                localSelect.innerHTML += `<option value="${local.id}">${local.nombre}</option>`;
            });

            tableBody.innerHTML = '';
            if (personal.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="5">Aún no hay personal registrado.</td></tr>`;
            } else {
                personal.forEach(empleado => {
                    const rol = roles.find(r => r.id === empleado.rol_id);
                    const row = `
                        <tr>
                            <td>${empleado.nombre_completo}</td>
                            <td>${empleado.tipo_documento}: ${empleado.numero_documento}</td>
                            <td>${rol ? rol.nombre : 'N/A'}</td>
                            <td>S/ ${empleado.sueldo_base ? parseFloat(empleado.sueldo_base).toFixed(2) : '0.00'}</td>
                            <td>
                                <button class="btn-accion">Editar</button>
                                <button class="btn-accion btn-calcular-deuda">Calcular Deuda</button>
                            </td>
                        </tr>
                    `;
                    tableBody.insertAdjacentHTML('beforeend', row);
                });
            }
        } catch (error) {
            tableBody.innerHTML = `<tr><td colspan="5">No se pudieron cargar los datos.</td></tr>`;
        }
    }

    // --- LÓGICA DEL "OJO" DE LA CONTRASEÑA (CORREGIDA) ---
    togglePasswordBtn.addEventListener('click', () => {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        eyeIcon.style.display = isPassword ? 'none' : 'block';
        eyeOffIcon.style.display = isPassword ? 'block' : 'none';
    });


    // --- VALIDACIÓN DE INPUTS ---
    document.getElementById('numero_documento').addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 8);
    });
    document.getElementById('telefono').addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '').slice(0, 9);
    });

    // --- MANEJO DEL FORMULARIO (CON MANEJO DE ERRORES CORREGIDO) ---
    formEmpleado.addEventListener('submit', async (e) => {
        e.preventDefault();
        modalError.textContent = '';
        modalError.style.display = 'none';

        const formData = new FormData(formEmpleado);
        // --- CONSTRUCCIÓN DE DATOS CORREGIDA Y ROBUSTA ---
        const data = {
            nombre_completo: formData.get('nombre_completo'),
            tipo_documento: 'DNI', // Lo definimos aquí
            numero_documento: formData.get('numero_documento'),
            telefono: formData.get('telefono'),
            email: formData.get('email'),
            password: formData.get('password'),
            rol_id: parseInt(formData.get('rol_id'), 10),
            local_asignado_id: parseInt(formData.get('local_asignado_id'), 10),
            sueldo_base: parseFloat(formData.get('sueldo_base')) || 0.0,
        };

        // Verificación simple para campos requeridos
        if (!data.rol_id || !data.local_asignado_id) {
            modalError.textContent = 'Por favor, seleccione un rol y un local.';
            modalError.style.display = 'block';
            return;
        }

        try {
            const response = await fetch('/api/v1/gestion/personal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(data)
            });

           if (!response.ok) {
                // El error 422 vendrá aquí
                const errorData = await response.json();
                // Pydantic a menudo devuelve un array de errores, lo formateamos
                let errorMessage = errorData.detail;
                if (Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail.map(err => `${err.loc[1]}: ${err.msg}`).join(', ');
                }
                throw new Error(errorMessage || 'Error desconocido al crear empleado.');
            }
            
            hideModal();
            cargarDatosIniciales();
            
        } catch (error) {
            // --- CORRECCIÓN CLAVE ---
            // Usamos error.message para mostrar solo el texto del error.
            modalError.textContent = error.message;
            modalError.style.display = 'block';
        }
    });

    cargarDatosIniciales();
});