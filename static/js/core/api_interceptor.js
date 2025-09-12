import { getToken, removeToken } from './store.js';

// Esta es nuestra nueva función 'fetch' personalizada.
export const fetchWithAuth = async (url, options = {}) => {
    const token = getToken();

    // Preparamos las cabeceras (headers)
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers, // Permite sobreescribir o añadir cabeceras
    };

    // Si tenemos un token, lo añadimos a la cabecera de autorización.
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Unimos las nuevas opciones con las que nos pasaron.
    const newOptions = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(url, newOptions);

        // Si la respuesta es 401 Unauthorized, el token es inválido o expiró.
        if (response.status === 401) {
            console.warn("Token inválido o expirado. Cerrando sesión.");
            removeToken(); // Limpiamos el token viejo.
            window.location.href = '/login'; // Redirigimos al login.
            // Lanzamos un error para detener la ejecución del código que llamó a fetch.
            throw new Error('No autenticado');
        }
        
        return response;

    } catch (error) {
        // Si hay un error de red (ej: el servidor está caído), lo relanzamos.
        console.error("Error de red en fetchWithAuth:", error);
        throw error;
    }
};