/* ═══════════════════════════════════════════════════════════
   Data.js — Data Entry & Listing
   ═══════════════════════════════════════════════════════════ */

// ─── Add Data ──────────────────────────────────────────────

async function handleAddData(event) {
    event.preventDefault();

    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving...';

    const payload = {
        employee_name: document.getElementById('employee_name').value.trim(),
        department: document.getElementById('department').value,
        salary: parseFloat(document.getElementById('salary').value),
        performance_score: parseFloat(document.getElementById('performance_score').value),
        record_date: document.getElementById('record_date').value,
    };

    try {
        const res = await apiFetch('/api/data/', {
            method: 'POST',
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            showToast('Record added successfully!');
            document.getElementById('data-form').reset();
        } else {
            const data = await res.json();
            showToast(data.detail || 'Failed to add record', 'error');
        }
    } catch (err) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '➕ Add Record';
    }

    return false;
}


// ─── List Data ─────────────────────────────────────────────

let currentPage = 0;
const PAGE_SIZE = 10;

async function loadRecords(page = 0) {
    currentPage = page;
    const skip = page * PAGE_SIZE;
    const department = document.getElementById('filter-department')?.value || '';

    let url = `/api/data/?skip=${skip}&limit=${PAGE_SIZE}`;
    if (department) url += `&department=${encodeURIComponent(department)}`;

    try {
        const res = await apiFetch(url);
        if (!res.ok) return;

        const data = await res.json();
        renderTable(data.records);
        renderPagination(data.total);

        const countEl = document.getElementById('record-count');
        if (countEl) countEl.textContent = `${data.total} record${data.total !== 1 ? 's' : ''} found`;

    } catch (err) {
        console.error('Load error:', err);
    }
}


function renderTable(records) {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    if (!records.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="icon">📊</div>
                        <h3>No records yet</h3>
                        <p>Start by <a href="/data/add">adding some data</a></p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    tbody.innerHTML = records.map(r => `
        <tr>
            <td><strong>${escapeHtml(r.employee_name)}</strong></td>
            <td><span class="badge badge-accent">${escapeHtml(r.department)}</span></td>
            <td>${formatCurrency(r.salary)}</td>
            <td>
                <span class="badge ${r.performance_score >= 80 ? 'badge-success' : r.performance_score >= 50 ? 'badge-warning' : 'badge-danger'}">
                    ${r.performance_score}
                </span>
            </td>
            <td style="color: var(--text-secondary);">${r.record_date}</td>
            <td>
                <div class="flex gap-sm">
                    <button class="btn btn-secondary btn-sm" onclick="openEditModal(${r.id})">✏️</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteRecord(${r.id})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}


function renderPagination(total) {
    const container = document.getElementById('pagination');
    if (!container) return;

    const totalPages = Math.ceil(total / PAGE_SIZE);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = '';
    for (let i = 0; i < totalPages; i++) {
        const active = i === currentPage ? 'btn-primary' : 'btn-secondary';
        html += `<button class="btn btn-sm ${active}" onclick="loadRecords(${i})">${i + 1}</button>`;
    }
    container.innerHTML = html;
}


async function openEditModal(id) {
    try {
        const res = await apiFetch(`/api/data/${id}`);
        if (!res.ok) {
            showToast('Failed to load record details', 'error');
            return;
        }

        const data = await res.json();

        // Populate modal
        document.getElementById('edit-id').value = data.id;
        document.getElementById('edit-name').value = data.employee_name;
        document.getElementById('edit-department').value = data.department;
        document.getElementById('edit-salary').value = data.salary;
        document.getElementById('edit-score').value = data.performance_score;
        document.getElementById('edit-date').value = data.record_date;

        // Show modal
        document.getElementById('edit-modal').classList.remove('hidden');
    } catch (err) {
        showToast('Error loading record', 'error');
    }
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
    document.getElementById('edit-form').reset();
}

async function handleUpdateData(event) {
    event.preventDefault();

    const id = document.getElementById('edit-id').value;
    const btn = document.getElementById('update-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving...';

    const payload = {
        employee_name: document.getElementById('edit-name').value.trim(),
        department: document.getElementById('edit-department').value,
        salary: parseFloat(document.getElementById('edit-salary').value),
        performance_score: parseFloat(document.getElementById('edit-score').value),
        record_date: document.getElementById('edit-date').value,
    };

    try {
        const res = await apiFetch(`/api/data/${id}`, {
            method: 'PUT',
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            showToast('Record updated successfully!');
            closeEditModal();
            loadRecords(currentPage);
        } else {
            const data = await res.json();
            showToast(data.detail || 'Update failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Save Changes';
    }

    return false;
}


async function deleteRecord(id) {
    if (!confirm('Are you sure you want to delete this record?')) return;

    try {
        const res = await apiFetch(`/api/data/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Record deleted');
            loadRecords(currentPage);
        } else {
            const data = await res.json();
            showToast(data.detail || 'Delete failed', 'error');
        }
    } catch (err) {
        showToast('Network error', 'error');
    }
}


// ─── Utility ───────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ─── Export ────────────────────────────────────────────────

async function downloadExcel() {
    const department = document.getElementById('filter-department')?.value || '';
    let url = `/api/data/export/excel`;
    if (department) {
        url += `?department=${encodeURIComponent(department)}`;
    }

    try {
        const token = getToken();
        showToast('Preparing download...', 'info');
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            showToast('Download failed: ' + errorText, 'error');
            return;
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = downloadUrl;
        a.download = 'data_records.xlsx';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();
        showToast('Download started', 'success');
    } catch (err) {
        console.error('Export error:', err);
        showToast('Error generating Excel file.', 'error');
    }
}
