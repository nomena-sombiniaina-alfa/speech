document.addEventListener('DOMContentLoaded', function() {
    const passwordToggles = document.querySelectorAll('.toggle-password');

    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function () {
            const passwordInput = toggle.closest('.input-group').querySelector('input');
            const icon = toggle.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
        });
    });
}); 