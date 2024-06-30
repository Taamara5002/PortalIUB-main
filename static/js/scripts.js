$(document).ready(function() {
    // Función para manejar el envío del formulario de registro
    $('#register-form').on('submit', function(e) {
        e.preventDefault(); // Evitar que el formulario se envíe automáticamente
        
        if (!validateRegisterForm()) {
            return; // Si la validación del formulario falla, salir sin enviar
        }

        var email = document.forms["register-form"]["correo"].value;

        // Verificar si el correo ya está registrado
        $.ajax({
            url: '/check_email', // URL para verificar el correo
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ correo: email }),
            success: function(response) {
                if (response.exists) {
                    alert("El correo ya está registrado");
                } else {
                    // Si el correo no está registrado, enviar el formulario
                    $('#register-form')[0].submit();
                }
            },
            error: function(error) {
                console.error("Error al verificar el correo:", error);
            }
        });
    });

    // Función para validar el formulario de registro
    function validateRegisterForm() {
        var email = document.forms["register-form"]["correo"].value;
        var password = document.forms["register-form"]["password"].value;
        var emailPattern = /^[a-zA-Z0-9._%+-]+@unibarranquilla\.edu\.co$/;
        var passwordPattern = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;

        if (!emailPattern.test(email)) {
            alert("El correo debe ser una dirección @unibarranquilla.edu.co");
            return false;
        }
        if (!passwordPattern.test(password)) {
            alert("La contraseña debe tener al menos 8 caracteres, incluyendo una letra mayúscula, una letra minúscula, un número y un carácter especial.");
            return false;
        }
        return true;
    }

    // Funciones para el formulario de chat (mantenido como está en tu código actual)
    $('#chat-form').on('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    function sendMessage() {
        var messageInput = document.getElementById('messageInput'); // Corregido el nombre del id aquí
        var message = messageInput.value.trim();
    
        if (message === '') {
            return;
        }
    
        // Mostrar mensaje del usuario en el chat
        addMessage('user', message);
    
        // Enviar mensaje al servidor Flask
        fetch('/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: 'messageInput=' + encodeURIComponent(message)
        })
        .then(response => response.json())
        .then(data => {
            // Mostrar respuesta del chatbot
            var responses = data.response;
            responses.forEach(function(response) {
                addMessage('bot', response);
            });
    
            // Limpiar campo de entrada
            messageInput.value = '';
        })
        .catch(error => {
            console.error('Error al enviar mensaje:', error);
        });
    }
    
    function addMessage(sender, message) {
        var messagesContainer = document.getElementById('messages');
    
        // Si hay contenido de bienvenida, eliminarlo al enviar el primer mensaje
        var placeholder = document.getElementById('placeholder');
        if (placeholder) {
            placeholder.remove();
        }
    
        var messageElement = document.createElement('div');
        messageElement.classList.add(sender === 'user' ? 'message-user' : 'message-bot');
        messageElement.textContent = message;
    
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
