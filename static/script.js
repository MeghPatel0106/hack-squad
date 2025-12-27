/* Global Cache */
let allEquipment = [];
let allTeams = [];
let currentUserRole = null; // Will need to be set by the page

/* --- Equipment Page --- */
async function loadEquipment() {
    const list = document.getElementById('equipment-list');
    if (!list) return;

    const res = await fetch('/api/equipment');
    const data = await res.json();
    allEquipment = data;

    list.innerHTML = data.map(item => `
        <tr style="${item.is_scrapped ? 'opacity: 0.5; text-decoration: line-through;' : ''}">
            <td><a href="/equipment/${item.id}" style="color: var(--text-main); font-weight: 500; text-decoration: none;">${item.name}</a></td>
            <td>${item.serial_number}</td>
            <td>${item.department}</td>
            <td>${item.location}</td>
            <td>${item.team_name || 'Unassigned'}</td>
            <td>
                ${item.technician_name ?
            `<div style="display:flex;align-items:center;gap:0.5rem">
                    <i class="fa-solid fa-user-gear"></i> ${item.technician_name}
                 </div>` : 'None'}
            </td>
            <td>
                 ${item.is_scrapped ? '<span style="color:var(--danger)">Scrapped</span>' : 'Active'}
            </td>
            <td>
                <a href="/equipment/${item.id}" class="smart-badge">
                    <i class="fa-solid fa-eye"></i> Details
                </a>
            </td>
        </tr>
    `).join('');
}

/* --- Kanban Board --- */
async function loadKanban() {
    const urlParams = new URLSearchParams(window.location.search);
    const equipmentId = urlParams.get('equipment_id');

    let url = '/api/requests';
    if (equipmentId) url += `?equipment_id=${equipmentId}`;

    const res = await fetch(url);
    const requests = await res.json();

    // Clear columns
    ['New', 'InProgress', 'Repaired', 'Scrap'].forEach(stage => {
        const col = document.getElementById(`list-${stage}`);
        const colContainer = document.getElementById(`col-${stage}`);
        if (col) col.innerHTML = '';

        // Update counts
        const count = requests.filter(r => r.stage.replace(' ', '') === stage).length;
        const badge = colContainer.querySelector('.count-badge');
        if (badge) badge.innerText = count;
    });

    requests.forEach(req => {
        // Map DB stage to ID (remove spaces)
        let stageId = req.stage.replace(' ', '');
        const col = document.getElementById(`list-${stageId}`);
        if (col) {
            const isOverdue = new Date(req.scheduled_date) < new Date() && req.stage !== 'Repaired' && req.stage !== 'Scrap';

            const card = document.createElement('div');
            card.className = 'kanban-card';
            card.draggable = true;
            card.ondragstart = (e) => drag(e);
            card.id = `req-${req.id}`;
            card.dataset.id = req.id;

            card.innerHTML = `
                <div class="card-tag" style="background:${getPriorityColor(req.request_type)}">${req.request_type}</div>
                <div class="card-title">${req.subject}</div>
                <div style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.5rem;">
                    <i class="fa-solid fa-cube"></i> ${req.equipment_name}
                </div>
                <div class="card-footer">
                    <div class="date-indicator ${isOverdue ? 'overdue' : ''}">
                        <i class="fa-regular fa-clock"></i> ${req.scheduled_date || 'No Date'}
                    </div>
                </div>
                <div style="margin-top: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                    ${req.avatar_url ? `<img src="${req.avatar_url}" class="tech-avatar" title="${req.technician_name}">` : '<span style="font-size:0.8rem; color:var(--text-muted);">Unassigned</span>'}
                    
                    <button onclick="confirmDelete(${req.id})" class="btn-icon-danger" title="Delete Request" style="background: none; border: none; color: var(--danger); cursor: pointer; opacity: 0.6; transition: 0.2s;">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            `;
            col.appendChild(card);
        }
    });
}

function getPriorityColor(type) {
    return type === 'Corrective' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)';
}

// Drag & Drop
let draggedCardId = null;

function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    draggedCardId = ev.target.dataset.id;
    ev.dataTransfer.setData("text", ev.target.id);
}

async function drop(ev) {
    ev.preventDefault();
    const targetCol = ev.target.closest('.kanban-column');
    if (!targetCol) return;

    let newStage = targetCol.id.replace('col-', '');
    if (newStage === 'InProgress') newStage = 'In Progress';

    if (newStage === 'Repaired') {
        const hours = prompt("Enter repair duration (hours):", "1.0");
        if (hours === null) return;
        await updateRequest(draggedCardId, { stage: newStage, duration_hours: hours });
    } else if (newStage === 'Scrap') {
        if (!confirm("WARNING: Moving to Scrap will permanently mark the equipment as SCRAPPED. Continue?")) return;
        await updateRequest(draggedCardId, { stage: newStage });
    } else {
        await updateRequest(draggedCardId, { stage: newStage });
    }

    loadKanban();
}

async function updateRequest(id, data) {
    await fetch(`/api/requests/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

async function confirmDelete(id) {
    if (!confirm('Are you sure you want to delete this request? This action cannot be undone.')) return;

    const res = await fetch(`/api/requests/${id}`, { method: 'DELETE' });
    if (res.ok) {
        // Reload current view
        if (window.location.pathname.includes('kanban')) loadKanban();
        else if (window.location.pathname.includes('dashboard')) location.reload();
    } else {
        const err = await res.json();
        alert('Error: ' + (err.error || 'Could not delete'));
    }
}

/* --- Form Logic --- */
async function loadFormDependencies() {
    const eqSelect = document.getElementById('equipmentSelect');
    if (!eqSelect) return;

    try {
        const eqRes = await fetch('/api/equipment');
        if (!eqRes.ok) throw new Error('Failed to load equipment');

        allEquipment = await eqRes.json();

        // Filter out scrapped equipment for new requests? The requirements say "load all existing". Assuming active ones.
        // Backend API doesn't filter scrapped by default? Let's assume we show all or just active. 
        // Best UX: Show only active. But user might need to see them? 
        // Let's filter out scrapped for creating new requests to be safe/clean.
        const activeEquipment = allEquipment.filter(e => !e.is_scrapped);

        const currentEqId = new URLSearchParams(window.location.search).get('equipment_id');

        if (activeEquipment.length === 0) {
            eqSelect.innerHTML = '<option value="">No Active Equipment Found</option>';
        } else {
            eqSelect.innerHTML = '<option value="">Select Equipment</option>' +
                activeEquipment.map(e => `<option value="${e.id}" ${e.id == currentEqId ? 'selected' : ''}>${e.name} (${e.serial_number})</option>`).join('');
        }
    } catch (err) {
        console.error(err);
        eqSelect.innerHTML = '<option value="">Error loading equipment</option>';
    }
}

// Removed autoFillTeam as it is handled by backend and elements don't exist in DOM
async function autoFillTeam() {
    // Legacy function kept to prevent reference errors if called from HTML (though removed from HTML)
    return;
}

async function submitRequest(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Basic Validation
    if (!data.equipment_id) {
        alert("Please select equipment.");
        return;
    }
    if (!data.scheduled_date) {
        alert("Scheduled Date is missing. Please select a date from the Calendar.");
        return;
    }

    try {
        const res = await fetch('/api/requests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            // alert('Request Created Successfully!'); // Optional: Remove alert for smoother flow? User asked for no errors.
            // Redirect to Calendar or Kanban? Request implies "Request creation flow". 
            // Let's redirect to Calendar as that's where they came from mostly, or maybe dashboard.
            // Requirement: "Request appears in: Calendar, Kanban, List".
            window.location.href = '/calendar';
        } else {
            const err = await res.json();
            alert('Error: ' + (err.error || 'Could not create request'));
        }
    } catch (error) {
        console.error('Submission error:', error);
        alert('Network or Server Error: Could not submit request.');
    }
}

/* --- Calendar Logic --- */
let currentDate = new Date();

async function initCalendar() {
    renderCalendarGrid();
}

function changeMonth(delta) {
    currentDate.setMonth(currentDate.getMonth() + delta);
    renderCalendarGrid();
}

async function renderCalendarGrid() {
    const calendarBody = document.getElementById('calendar-body');
    const header = document.getElementById('month-year-header');
    if (!calendarBody) return;

    header.innerText = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    const res = await fetch('/api/requests');
    const allRequests = await res.json();
    const preventive = allRequests.filter(r => r.request_type === 'Preventive' && r.scheduled_date);

    calendarBody.innerHTML = '';

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) {
        calendarBody.innerHTML += `<div></div>`;
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayEvents = preventive.filter(r => r.scheduled_date.startsWith(dateStr));

        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        dayCell.onclick = () => window.location.href = `/create_request?date=${dateStr}`;

        dayCell.innerHTML = `
            <span class="day-number">${day}</span>
            ${dayEvents.map(e => `<div class="day-event" title="${e.subject}">${e.equipment_name}</div>`).join('')}
        `;
        calendarBody.appendChild(dayCell);
    }
}
