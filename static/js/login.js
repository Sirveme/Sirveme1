import { saveToken } from './core/store.js';

/**
 * Esta función es llamada por HTMX DESPUÉS de que la petición de login se completa.
 * Se define en el objeto `window` para que el atributo hx-on pueda encontrarla.
 * @param {CustomEvent} event - El evento disparado por HTMX.
 */
window.handleLoginResponse = function(event) {
    const errorMessageDiv = document.getElementById('error-message');
    
    // Comprobamos si la petición fue exitosa (código 2xx)
    if (event.detail.successful) {
        try {
            // Extraemos la respuesta JSON del objeto XHR de HTMX
            const responseText = event.detail.xhr.responseText;
            const data = JSON.parse(responseText);

            if (data.access_token) {
                // Si tenemos un token, lo guardamos en nuestro Store
                saveToken(data.access_token);
                
                // Redirigimos al panel principal
                window.location.href = '/panel';
            } else {
                // Esto no debería pasar si la API funciona, pero es una salvaguarda
                errorMessageDiv.textContent = 'Respuesta inesperada del servidor.';
            }

        } catch (error) {
            console.error("Error al procesar la respuesta de login:", error);
            errorMessageDiv.textContent = 'Error al procesar la respuesta del servidor.';
        }
    }
    // Si la petición NO fue exitosa, HTMX ya se encarga de poner el error
    // en el div #error-message gracias al atributo hx-target-4xx.
    // No necesitamos hacer nada en el caso de error.
}

// Opcional: Limpiar el script de redirección de tu HTML
// El nuevo sistema de autenticación que construiremos se encargará de esto
// de una forma más robusta. Por ahora, puedes dejarlo o quitarlo.