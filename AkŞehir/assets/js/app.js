document.addEventListener('DOMContentLoaded', () => {
    const loginContainer = document.getElementById('login-container');
    const registerContainer = document.getElementById('register-container');
    const showRegisterLink = document.getElementById('show-register');
    const showLoginLink = document.getElementById('show-login');

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    // Switch to register form
    showRegisterLink.addEventListener('click', (e) => {
        e.preventDefault();
        loginContainer.style.display = 'none';
        registerContainer.style.display = 'block';
    });

    // Switch to login form
    showLoginLink.addEventListener('click', (e) => {
        e.preventDefault();
        registerContainer.style.display = 'none';
        loginContainer.style.display = 'block';
    });

    // Handle Login Form Submission
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitButton = loginForm.querySelector('.btn');
        submitButton.textContent = 'Giriş Yapılıyor...';
        submitButton.disabled = true;

        const formData = new FormData(loginForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('api/login.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                // Rol tabanlı yönlendirme
                if (result.user && result.user.role === 'admin') {
                    window.location.href = 'admin.php';
                } else {
                    window.location.href = 'dashboard.php';
                }
            } else {
                alert(`Giriş Başarısız: ${result.error}`);
            }
        } catch (error) {
            console.error('Login error:', error);
            alert('Bir sunucu hatası oluştu. Lütfen tekrar deneyin.');
        } finally {
            submitButton.textContent = 'Giriş Yap';
            submitButton.disabled = false;
        }
    });

    // Handle Register Form Submission
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitButton = registerForm.querySelector('.btn');
        submitButton.textContent = 'Kayıt Olunuyor...';
        submitButton.disabled = true;

        const formData = new FormData(registerForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch('api/register.php', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                alert('Kayıt başarılı! Lütfen giriş yapın.');
                // Switch to login view
                registerContainer.style.display = 'none';
                loginContainer.style.display = 'block';
                loginForm.reset(); // Clear login form
                registerForm.reset(); // Clear register form
            } else {
                alert(`Kayıt Başarısız: ${result.message}`);
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Bir sunucu hatası oluştu. Lütfen tekrar deneyin.');
        } finally {
            submitButton.textContent = 'Kayıt Ol';
            submitButton.disabled = false;
        }
    });
});
