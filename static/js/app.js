/* ═══════════════════════════════════════════════════════════
   App.js — Shared utilities for AI Data Analyst
   ═══════════════════════════════════════════════════════════ */

const API_BASE = '';

// ─── Token Management ──────────────────────────────────────

function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function getUser() {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
}

function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// ─── Auth Guard ────────────────────────────────────────────

function requireAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    loadUserInfo();
    return true;
}

async function loadUserInfo() {
    const user = getUser();
    if (user) {
        updateSidebarUser(user);
        return;
    }

    try {
        const res = await apiFetch('/api/auth/me');
        if (res.ok) {
            const data = await res.json();
            setUser(data);
            updateSidebarUser(data);
        }
    } catch (err) {
        console.error('Failed to load user info:', err);
    }
}

function updateSidebarUser(user) {
    const nameEl = document.getElementById('user-name');
    const roleEl = document.getElementById('user-role');
    const avatarEl = document.getElementById('user-avatar');

    if (nameEl) nameEl.textContent = user.full_name || user.email;
    if (roleEl) roleEl.textContent = user.role;
    if (avatarEl) avatarEl.textContent = (user.full_name || user.email).charAt(0).toUpperCase();
}

// ─── API Helper ────────────────────────────────────────────

async function apiFetch(url, options = {}) {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    return fetch(API_BASE + url, {
        ...options,
        headers,
    });
}

// ─── Toast Notifications ───────────────────────────────────

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ─── Number Formatting ─────────────────────────────────────

function formatCurrency(num) {
    if (!num && num !== 0) return '$0';
    return '$' + Number(num).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

function formatNumber(num, decimals = 1) {
    if (!num && num !== 0) return '0';
    return Number(num).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

// ─── Init on protected pages ───────────────────────────────

if (document.querySelector('.app-layout')) {
    requireAuth();
}
