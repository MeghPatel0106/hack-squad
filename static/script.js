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
/* Old loadKanban replaced by the one below dayCell logic */

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

    // Load Teams first for autoFill
    const teamRes = await fetch('/api/teams');
    allTeams = await teamRes.json();

    try {
        const eqRes = await fetch('/api/equipment');
        if (!eqRes.ok) throw new Error('Failed to load equipment');

        allEquipment = await eqRes.json();
        const activeEquipment = allEquipment.filter(e => !e.is_scrapped);

        const currentEqId = new URLSearchParams(window.location.search).get('equipment_id');

        // Group by Type
        const computers = activeEquipment.filter(e => e.equipment_type === 'Computer');
        const machines = activeEquipment.filter(e => e.equipment_type === 'Machine');
        const vehicles = activeEquipment.filter(e => e.equipment_type === 'Vehicle');

        // Helper to build options
        const buildOptions = (items) => items.map(e => `<option value="${e.id}" ${e.id == currentEqId ? 'selected' : ''}>${e.name} (${e.serial_number})</option>`).join('');

        let html = '<option value="">Select Equipment</option>';

        if (computers.length) html += `<optgroup label="Computer">${buildOptions(computers)}</optgroup>`;
        if (machines.length) html += `<optgroup label="Machine">${buildOptions(machines)}</optgroup>`;
        if (vehicles.length) html += `<optgroup label="Vehicle">${buildOptions(vehicles)}</optgroup>`;

        // Catch-all
        const others = activeEquipment.filter(e => !['Computer', 'Machine', 'Vehicle'].includes(e.equipment_type));
        if (others.length > 0) {
            html += `<optgroup label="Other">${buildOptions(others)}</optgroup>`;
        }

        if (activeEquipment.length === 0) {
            html = '<option value="">No Active Equipment Available</option>';
        }

        eqSelect.innerHTML = html;

        if (currentEqId) {
            eqSelect.value = currentEqId;
            autoFillTeam();
        }
    } catch (err) {
        console.error(err);
        eqSelect.innerHTML = '<option value="">Error loading equipment</option>';
    }
}

async function autoFillTeam() {
    const eqId = document.getElementById('equipmentSelect').value;
    const teamSelect = document.getElementById('teamSelect');
    const techSelect = document.getElementById('techSelect');

    if (!eqId) return;

    const eq = allEquipment.find(e => e.id == eqId);
    if (!eq) return;

    // Auto-fill Location
    const locInput = document.getElementById('equipmentLocation');
    if (locInput) {
        locInput.value = eq.location || 'Unknown Location';
    }

    // Populate hidden team select
    teamSelect.innerHTML = allTeams.map(t => `<option value="${t.id}" ${t.id === eq.maintenance_team_id ? 'selected' : ''}>${t.team_name}</option>`).join('');

    // Trigger tech fetch if needed, though hidden
    if (eq.maintenance_team_id) {
        const res = await fetch(`/api/technicians?team_id=${eq.maintenance_team_id}`);
        const techs = await res.json();
        techSelect.innerHTML = '<option value="">Any Available</option>' +
            techs.map(t => `<option value="${t.id}">${t.name}</option>`).join('');

        // defaults
        if (eq.default_technician_id) {
            techSelect.value = eq.default_technician_id;
        }
    }
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
    // Prompt: "we cant see the registered date" -> implies showing all requests with dates.
    // Previously filtered only "Preventive". Now showing ALL that have a date.
    const requestsWithDate = allRequests.filter(r => r.scheduled_date);

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
        // Compare using YYYY-MM-DD substring to be safe against time components
        const dayEvents = requestsWithDate.filter(r => {
            if (!r.scheduled_date) return false;
            // Take first 10 chars (YYYY-MM-DD)
            return r.scheduled_date.substring(0, 10) === dateStr;
        });

        const dayCell = document.createElement('div');
        dayCell.className = 'calendar-day';
        // dayCell.onclick = () => openDayModal(dateStr, dayEvents); // OLD
        // Req: "When user clicks a date on Calendar: Kanban board must reload. Only show cards whose scheduled_date equals selected date."
        dayCell.onclick = () => window.location.href = `/kanban?date=${dateStr}`;

        dayCell.innerHTML = `
            <span class="day-number">${day}</span>
            <div class="day-events-container" style="display:flex; flex-direction:column; gap:2px;">
                ${dayEvents.map(e => `
                    <div class="day-event-tag" title="${e.subject}" 
                         style="background: ${getPriorityColor(e.request_type)}; 
                                padding: 4px 6px; 
                                border-radius: 6px; 
                                font-size: 0.75rem; 
                                color: var(--text-main); 
                                border: 1px solid rgba(255,255,255,0.1);
                                overflow: hidden;
                                white-space: nowrap;
                                text-overflow: ellipsis;">
                        <strong style="color:var(--primary);">${e.equipment_name}</strong>
                        <span style="opacity:0.8"> — ${e.subject}</span>
                        ${e.equipment_location ? `<div style="font-size:0.7rem; opacity:0.6"><i class="fa-solid fa-location-dot"></i> ${e.equipment_location}</div>` : ''}
                        ${e.technician_name ? `<div style="font-size:0.7rem; opacity:0.6"><i class="fa-solid fa-user"></i> ${e.technician_name.split(' ')[0]}</div>` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        calendarBody.appendChild(dayCell);
    }
}
/*
function openDayModal(dateStr, events) {
   // REMOVED: Requirement changed to Redirect to Kanban
} 
*/

/* --- Kanban Board Modified for Date Filter --- */
async function loadKanban() {
    const urlParams = new URLSearchParams(window.location.search);
    const equipmentId = urlParams.get('equipment_id');
    const dateFilter = urlParams.get('date'); // NEW

    let url = '/api/requests';
    if (equipmentId) url += `?equipment_id=${equipmentId}`;

    const res = await fetch(url);
    const allRequests = await res.json();

    // Filter by Date if present
    let requests = allRequests;
    if (dateFilter) {
        // Compare YYYY-MM-DD
        requests = allRequests.filter(r => r.scheduled_date && r.scheduled_date.startsWith(dateFilter));

        // Update Board Header to show filtered state
        const header = document.querySelector('h1');
        if (header) header.innerText = `Maintenance Board (${dateFilter})`;
    }

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
        // Map DB stage to ID
        let stageId = req.stage.replace(' ', '');
        const col = document.getElementById(`list-${stageId}`);
        if (col) {
            // Overdue Logic: Strictly past dates (yesterday and before). Today is NOT overdue.
            const todayStr = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD
            const isOverdue = req.scheduled_date && req.scheduled_date < todayStr && req.stage !== 'Repaired' && req.stage !== 'Scrap';
            const isLocked = req.stage === 'Scrap'; // Strict Lock

            const card = document.createElement('div');
            card.className = 'kanban-card';
            if (!isLocked) {
                card.draggable = true;
                card.ondragstart = (e) => drag(e);
            } else {
                card.style.opacity = '0.7';
                card.style.border = '1px solid var(--danger)';
                card.title = "Scrapped - Locked";
            }
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
                    
                    ${!isLocked ? `<button onclick="confirmDelete(${req.id})" class="btn-icon-danger" title="Delete Request" style="background: none; border: none; color: var(--danger); cursor: pointer; opacity: 0.6; transition: 0.2s;">
                        <i class="fa-solid fa-trash"></i>
                    </button>` : '<i class="fa-solid fa-lock" style="color:var(--danger)"></i>'}
                </div>
            `;
            col.appendChild(card);
        }
    });
}
