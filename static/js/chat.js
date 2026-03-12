/* ═══════════════════════════════════════════════════════════
   Chat.js — AI Chat Interface
   ═══════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    if (!requireAuth()) return;
    loadChatHistory();
});


async function sendMessage() {
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const question = input.value.trim();

    if (!question) return;

    // Add user message bubble
    addMessage(question, 'user');
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;

    // Show typing indicator
    showTyping();

    try {
        const res = await apiFetch('/api/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ question }),
        });

        hideTyping();

        if (res.ok) {
            const data = await res.json();
            addMessage(data.answer, 'ai');
        } else {
            const err = await res.json();
            addMessage('Sorry, I had trouble processing your question. ' + (err.detail || ''), 'ai');
        }
    } catch (err) {
        hideTyping();
        addMessage('Network error. Please check your connection and try again.', 'ai');
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        input.focus();
    }
}


function addMessage(text, sender) {
    const container = document.getElementById('chat-messages');
    const avatar = sender === 'user' ? getInitial() : '🤖';

    const div = document.createElement('div');
    div.className = `chat-message ${sender}`;
    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble">${formatMessageText(text)}</div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}


function formatMessageText(text) {
    // Convert markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/• /g, '&bull; ');
}


function showTyping() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'chat-message ai';
    div.id = 'typing-indicator';
    div.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}


function hideTyping() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}


function getInitial() {
    const user = getUser();
    if (user && user.full_name) return user.full_name.charAt(0).toUpperCase();
    return '👤';
}


async function loadChatHistory() {
    try {
        const res = await apiFetch('/api/ai/history?limit=10');
        if (!res.ok) return;

        const data = await res.json();
        const conversations = data.conversations.reverse(); // oldest first

        conversations.forEach(c => {
            addMessage(c.question, 'user');
            addMessage(c.answer, 'ai');
        });
    } catch (err) {
        console.error('Failed to load chat history:', err);
    }
}
