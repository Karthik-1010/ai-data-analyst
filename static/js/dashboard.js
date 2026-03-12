/* ═══════════════════════════════════════════════════════════
   Dashboard.js — KPIs, Charts, AI Insights
   ═══════════════════════════════════════════════════════════ */

// Chart.js global config for dark mode
Chart.defaults.color = '#a0a0b8';
Chart.defaults.borderColor = '#2a2a40';
Chart.defaults.font.family = "'Inter', sans-serif";

const CHART_COLORS = [
    '#6c5ce7', '#a29bfe', '#74b9ff', '#00cec9',
    '#55efc4', '#fdcb6e', '#ff6b6b', '#e17055',
];

// ─── Load Dashboard Data ───────────────────────────────────

document.addEventListener('DOMContentLoaded', async () => {
    if (!requireAuth()) return;

    await Promise.all([
        loadKPIs(),
        loadDepartmentCharts(),
        loadTrendCharts(),
        loadAIInsights(),
    ]);
});


async function loadKPIs() {
    try {
        const res = await apiFetch('/api/analytics/summary');
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById('kpi-total').textContent = formatNumber(data.total_records, 0);
        document.getElementById('kpi-salary').textContent = formatCurrency(data.avg_salary);
        document.getElementById('kpi-score').textContent = formatNumber(data.avg_score, 1);
        document.getElementById('kpi-total-salary').textContent = formatCurrency(data.total_salary);
    } catch (err) {
        console.error('KPI load error:', err);
    }
}


async function loadDepartmentCharts() {
    try {
        const res = await apiFetch('/api/analytics/by-department');
        if (!res.ok) return;
        const data = await res.json();

        if (!data.length) return;

        const labels = data.map(d => d.department);
        const salaries = data.map(d => d.avg_salary);
        const scores = data.map(d => d.avg_score);
        const counts = data.map(d => d.count);

        // Bar chart — Salary by Department
        new Chart(document.getElementById('chart-department-salary'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Avg Salary ($)',
                    data: salaries,
                    backgroundColor: CHART_COLORS.slice(0, labels.length).map(c => c + '99'),
                    borderColor: CHART_COLORS.slice(0, labels.length),
                    borderWidth: 1,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: '#1a1a2e' } },
                    x: { grid: { display: false } },
                },
            },
        });

        // Bar chart — Performance by Department
        new Chart(document.getElementById('chart-department-score'), {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Avg Score',
                    data: scores,
                    backgroundColor: '#00cec999',
                    borderColor: '#00cec9',
                    borderWidth: 1,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, max: 100, grid: { color: '#1a1a2e' } },
                    x: { grid: { display: false } },
                },
            },
        });

        // Pie chart — Department Distribution
        new Chart(document.getElementById('chart-dept-pie'), {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: counts,
                    backgroundColor: CHART_COLORS.slice(0, labels.length),
                    borderColor: '#1a1a2e',
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { padding: 16, usePointStyle: true, pointStyle: 'circle' },
                    },
                },
            },
        });

    } catch (err) {
        console.error('Department chart error:', err);
    }
}


async function loadTrendCharts() {
    try {
        const res = await apiFetch('/api/analytics/trends');
        if (!res.ok) return;
        const data = await res.json();

        if (!data.length) return;

        const labels = data.map(d => d.month);
        const salaries = data.map(d => d.avg_salary);

        new Chart(document.getElementById('chart-trend-salary'), {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Avg Salary ($)',
                    data: salaries,
                    borderColor: '#6c5ce7',
                    backgroundColor: 'rgba(108, 92, 231, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#6c5ce7',
                    pointBorderColor: '#1a1a2e',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: false, grid: { color: '#1a1a2e' } },
                    x: { grid: { display: false } },
                },
            },
        });

    } catch (err) {
        console.error('Trend chart error:', err);
    }
}


async function loadAIInsights() {
    const container = document.getElementById('ai-insights');

    try {
        const res = await apiFetch('/api/ai/chat', {
            method: 'POST',
            body: JSON.stringify({
                question: 'Give me a brief summary of the data including total records, average salary, top department by salary, and any notable patterns. Keep it concise in 3-4 bullet points.'
            }),
        });

        if (res.ok) {
            const data = await res.json();
            container.innerHTML = `<div style="white-space: pre-wrap;">${data.answer}</div>`;
        } else {
            container.innerHTML = '<p style="color: var(--text-muted);">AI insights unavailable. Configure your API key in .env to enable this feature.</p>';
        }
    } catch (err) {
        container.innerHTML = '<p style="color: var(--text-muted);">Could not load AI insights.</p>';
    }
}
