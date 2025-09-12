// Contiene toda la lógica para la conexión en tiempo real con el servidor

let socket;

function conectarWebSocket(centroId, onMessageCallback, onStatusChangeCallback) {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${proto}//${host}/ws/kds/${centroId}`;
    
    socket = new WebSocket(url);

    socket.onopen = () => {
        console.log("Conectado al WebSocket del KDS.");
        onStatusChangeCallback(true); // true = conectado
    };

    socket.onmessage = (event) => {
        console.log("Mensaje WS recibido:", event.data);
        try {
            const comandaData = JSON.parse(event.data);
            onMessageCallback(comandaData);
        } catch (e) {
            console.error("Error al parsear mensaje de WebSocket:", e);
        }
    };

    socket.onclose = () => {
        console.log("WebSocket desconectado. Intentando reconectar en 3 segundos...");
        onStatusChangeCallback(false); // false = desconectado
        setTimeout(() => conectarWebSocket(centroId, onMessageCallback, onStatusChangeCallback), 3000);
    };

    socket.onerror = (error) => {
        console.error("Error de WebSocket:", error);
        socket.close(); // Esto disparará el 'onclose' y el intento de reconexión
    };
}