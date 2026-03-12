/* ═══════════════════════════════════════════════════════════
   Auth.js — Login & Registration
   ═══════════════════════════════════════════════════════════ */

async function handleLogin(event) {
    event.preventDefault();

    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Signing in...';

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    try {
        const res = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });

        const data = await res.json();

        if (res.ok) {
            setToken(data.access_token);
            setUser(data.user);
            showToast('Welcome back, ' + data.user.full_name + '!');
            setTimeout(() => window.location.href = '/dashboard', 500);
        } else {
            showToast(data.detail || 'Login failed', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Sign In';
    }

    return false;
}


async function handleRegister(event) {
    event.preventDefault();

    const btn = document.getElementById('register-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating account...';

    const full_name = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    try {
        const res = await fetch('/api/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name, email, password }),
        });

        const data = await res.json();

        if (res.ok) {
            setToken(data.access_token);
            setUser(data.user);
            const roleMsg = data.user.role === 'admin'
                ? ' You are the first user — you have been promoted to Admin!'
                : '';
            showToast('Account created!' + roleMsg);
            setTimeout(() => window.location.href = '/dashboard', 500);
        } else {
            showToast(data.detail || 'Registration failed', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Create Account';
    }

    return false;
}

// Redirect if already logged in
if (getToken()) {
    window.location.href = '/dashboard';
}
