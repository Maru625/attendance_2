let currentTab = '출근';

document.addEventListener('DOMContentLoaded', () => {
    const dateInput = document.getElementById('date');
    const timeInput = document.getElementById('time');
    
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    
    dateInput.value = `${year}-${month}-${day}`;
    timeInput.value = `${hours}:${minutes}:${seconds}`;
    
    loadReservations();
    
    document.getElementById('scheduleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const loader = submitBtn.querySelector('.loader');
        const messageDiv = document.getElementById('message');
        
        submitBtn.disabled = true;
        btnText.style.opacity = '0';
        loader.style.display = 'block';
        messageDiv.style.display = 'none';
        
        const name = document.getElementById('name').value;
        const date = document.getElementById('date').value;
        const time = document.getElementById('time').value;
        const type = document.querySelector('input[name="type"]:checked').value;
        
        try {
            const response = await fetch('/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, date, time, type }),
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showMessage(messageDiv, result.message, 'success');
                loadReservations();
            } else {
                showMessage(messageDiv, result.detail || result.message || '오류가 발생했습니다.', 'error');
            }
        } catch (error) {
            showMessage(messageDiv, '서버 통신 중 오류가 발생했습니다.', 'error');
            console.error(error);
        } finally {
            submitBtn.disabled = false;
            btnText.style.opacity = '1';
            loader.style.display = 'none';
        }
    });
});

function showMessage(el, text, type) {
    el.textContent = text;
    el.className = `message ${type}`;
    el.style.display = 'block';
}

function switchTab(type) {
    currentTab = type;
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.type === type);
    });
    loadReservations();
}

async function loadReservations() {
    try {
        const response = await fetch('/reservations');
        const reservations = await response.json();
        
        const listEl = document.getElementById('reservationList');
        listEl.innerHTML = '';
        
        const filtered = currentTab === '전체' 
            ? reservations 
            : reservations.filter(r => r.type === currentTab);
        
        if (filtered.length === 0) {
            const label = currentTab === '전체' ? '' : `(${currentTab}) `;
            listEl.innerHTML = `<div class="empty-state">${label}예약된 내역이 없습니다.</div>`;
            return;
        }
        
        filtered.slice().reverse().forEach(res => {
            const item = document.createElement('div');
            item.className = 'reservation-item';
            
            const typeClass = res.type === '출근' ? 'type-in' : 'type-out';
            
            item.innerHTML = `
                <div class="res-info">
                    <div class="res-name">${res.name}</div>
                    <div class="res-time">${res.target_dt}</div>
                </div>
                <div class="res-actions">
                    <span class="res-type ${typeClass}">${res.type}</span>
                    <button class="btn-edit" onclick="openEdit('${res.id}', '${res.name}', '${res.date}', '${res.time}', '${res.type}')">✏️</button>
                    <button class="btn-delete" onclick="deleteReservation('${res.id}')">🗑️</button>
                </div>
            `;
            
            listEl.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load reservations:', error);
    }
}

// === 수정 모달 ===
function openEdit(id, name, date, time, type) {
    document.getElementById('editId').value = id;
    document.getElementById('editName').value = name;
    document.getElementById('editDate').value = date;
    document.getElementById('editTime').value = time;
    document.querySelector(`input[name="editType"][value="${type}"]`).checked = true;
    document.getElementById('editModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('editId').value;
    const name = document.getElementById('editName').value;
    const date = document.getElementById('editDate').value;
    const time = document.getElementById('editTime').value;
    const type = document.querySelector('input[name="editType"]:checked').value;

    try {
        const response = await fetch(`/schedule/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, date, time, type }),
        });
        const result = await response.json();
        
        if (response.ok) {
            closeModal();
            loadReservations();
        } else {
            alert(result.detail || result.message || '수정 실패');
        }
    } catch (error) {
        alert('서버 통신 중 오류가 발생했습니다.');
    }
}

// === 삭제 ===
async function deleteReservation(id) {
    if (!confirm('이 예약을 삭제하시겠습니까?')) return;
    
    try {
        const response = await fetch(`/schedule/${id}`, { method: 'DELETE' });
        const result = await response.json();
        
        if (response.ok) {
            loadReservations();
        } else {
            alert(result.detail || result.message || '삭제 실패');
        }
    } catch (error) {
        alert('서버 통신 중 오류가 발생했습니다.');
    }
}
