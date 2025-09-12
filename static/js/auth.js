async function checkLoginStatus() {
    // Esta función se ejecuta en las páginas del panel para verificar la sesión.
    try {
        const response = await fetch('/api/v1/auth/users/me', { credentials: 'include' });
        if (!response.ok) {
            // Si el token es inválido, el backend devolverá 401 Unauthorized
            throw new Error('Token inválido o expirado');
        }
        console.log("Sesión activa y válida.");
    } catch (error) {
        console.warn("Error de sesión. Cerrando sesión en el frontend.");
        // Si hay un error, el token ya no es válido. Limpiamos.
        localStorage.removeItem('isLoggedIn'); // Opcional, pero bueno para limpiar
        window.location.href = '/login'; // Redirigimos al login
    }
}

// Ejecutar la verificación en páginas que no sean el login
if (window.location.pathname !== '/login') {
    checkLoginStatus();
}