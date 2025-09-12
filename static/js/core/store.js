// El Store es nuestra "única fuente de la verdad".
// Gestiona el estado de la autenticación.

const TOKEN_KEY = 'authToken';

export const saveToken = (token) => {
    localStorage.setItem(TOKEN_KEY, token);
};

export const getToken = () => {
    return localStorage.getItem(TOKEN_KEY);
};

export const removeToken = () => {
    localStorage.removeItem(TOKEN_KEY);
};

export const isLoggedIn = () => {
    const token = getToken();
    return !!token; // Devuelve true si el token existe, false si no.
};