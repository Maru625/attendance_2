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
    timeInput.value = `${hours}:${minutes}`;
    document.getElementById('second').value = seconds;
    
    // 직원 목록 & 지각 사유 로드
    loadEmployees();
    loadLateReasons();
    checkSiteHealth();
    loadReservations();

    // 5초마다 목록 자동 갱신
    setInterval(loadReservations, 5000);
    // 60초마다 사이트 상태 확인
    setInterval(checkSiteHealth, 60000);
    
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
        
        let timeVal = document.getElementById('time').value;
        const secVal = document.getElementById('second').value.padStart(2, '0') || '00';
        if (timeVal.split(':').length === 3) {
            timeVal = timeVal.split(':').slice(0, 2).join(':');
        }
        const time = `${timeVal}:${secVal}`;
        const type = document.querySelector('input[name="type"]:checked').value;
        const late_reason = document.getElementById('lateReason').value;
        
        try {
            const response = await fetch('/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, date, time, type, late_reason }),
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


// === 데이터 로드 ===

async function loadEmployees() {
    try {
        const response = await fetch('/employees');
        const employees = await response.json();
        
        const selects = [
            document.getElementById('name'),
            document.getElementById('editName'),
        ];
        
        selects.forEach(select => {
            // 첫 번째 옵션(placeholder) 유지
            const firstOption = select.querySelector('option');
            select.innerHTML = '';
            if (firstOption) select.appendChild(firstOption);
            
            employees.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('직원 목록 로드 실패:', error);
    }
}

async function loadLateReasons() {
    try {
        const response = await fetch('/late-reasons');
        const reasons = await response.json();
        
        const selects = [
            document.getElementById('lateReason'),
            document.getElementById('editLateReason'),
        ];
        
        selects.forEach(select => {
            select.innerHTML = '';
            
            const noneOpt = document.createElement('option');
            noneOpt.value = '';
            noneOpt.textContent = '미지정 시 기본값 자동 적용';
            select.appendChild(noneOpt);
            
            reasons.forEach(reason => {
                const option = document.createElement('option');
                option.value = reason;
                option.textContent = reason;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('지각 사유 목록 로드 실패:', error);
    }
}

async function checkSiteHealth() {
    const statusEl = document.getElementById('siteStatus');
    const dotEl = statusEl.querySelector('.status-dot');
    const textEl = statusEl.querySelector('.status-text');
    
    try {
        const response = await fetch('/site-health');
        const health = await response.json();
        
        statusEl.className = 'site-status ' + (health.healthy ? 'healthy' : 'unhealthy');
        textEl.textContent = health.healthy ? '출석 사이트 정상' : `⚠️ ${health.message}`;
    } catch (error) {
        statusEl.className = 'site-status unhealthy';
        textEl.textContent = '⚠️ 상태 확인 실패';
    }
}


// === 유틸 ===

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


// === 예약 목록 ===

function getStatusClass(status) {
    const map = {
        '대기중': 'status-pending',
        '진행중': 'status-running',
        '성공': 'status-success',
        '실패': 'status-failed',
        '사유입력필요': 'status-reason',
    };
    return map[status] || 'status-pending';
}

function getStatusLabel(status) {
    const map = {
        '대기중': '⏳ 대기중',
        '진행중': '🔄 진행중',
        '성공': '✅ 성공',
        '실패': '❌ 실패',
        '사유입력필요': '⚠️ 사유필요',
    };
    return map[status] || status || '⏳ 대기중';
}

async function loadReservations() {
    const listEl = document.getElementById('reservationList');
    try {
        const response = await fetch(`/reservations?t=${new Date().getTime()}`, { cache: 'no-store' });
        if (!response.ok) {
            listEl.innerHTML = `<div class="empty-state">서버 오류 (${response.status})</div>`;
            return;
        }
        const reservations = await response.json();
        
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
            const status = res.status || '대기중';
            const statusClass = getStatusClass(status);
            const statusLabel = getStatusLabel(status);
            
            const infoDiv = document.createElement('div');
            infoDiv.className = 'res-info';
            infoDiv.innerHTML = `<div class="res-name">${res.name || ''}</div><div class="res-time">${res.target_dt || ''}</div>`;

            // 상태 메시지가 있으면 표시
            if (res.status_message) {
                const msgDiv = document.createElement('div');
                msgDiv.className = 'res-status-msg';
                msgDiv.textContent = res.status_message;
                infoDiv.appendChild(msgDiv);
            }
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'res-actions';
            
            const statusSpan = document.createElement('span');
            statusSpan.className = `res-status-badge ${statusClass}`;
            statusSpan.textContent = statusLabel;
            
            const typeSpan = document.createElement('span');
            typeSpan.className = `res-type ${typeClass}`;
            typeSpan.textContent = res.type;

            actionsDiv.appendChild(statusSpan);
            actionsDiv.appendChild(typeSpan);
            
            // 대기중일 때만 수정/삭제 가능
            if (status === '대기중') {
                const editBtn = document.createElement('button');
                editBtn.className = 'btn-edit';
                editBtn.textContent = '✏️';
                editBtn.addEventListener('click', () => openEdit(res.id, res.name, res.date, res.time, res.type, res.late_reason || ''));
                
                const deleteBtn = document.createElement('button');
                deleteBtn.className = 'btn-delete';
                deleteBtn.textContent = '🗑️';
                deleteBtn.addEventListener('click', () => deleteReservation(res.id));
                
                actionsDiv.appendChild(editBtn);
                actionsDiv.appendChild(deleteBtn);
            }
            
            item.appendChild(infoDiv);
            item.appendChild(actionsDiv);
            
            listEl.appendChild(item);
        });
    } catch (error) {
        console.error('Failed to load reservations:', error);
        listEl.innerHTML = `<div class="empty-state">목록을 불러올 수 없습니다.</div>`;
    }
}


// === 수정 모달 ===

function openEdit(id, name, date, time, type, lateReason) {
    document.getElementById('editId').value = id;
    document.getElementById('editName').value = name;
    document.getElementById('editDate').value = date;
    
    let timeParts = time.split(':');
    if (timeParts.length === 3) {
        document.getElementById('editTime').value = `${timeParts[0]}:${timeParts[1]}`;
        document.getElementById('editSecond').value = timeParts[2];
    } else {
        document.getElementById('editTime').value = time;
        document.getElementById('editSecond').value = '00';
    }
    
    document.querySelector(`input[name="editType"][value="${type}"]`).checked = true;
    document.getElementById('editLateReason').value = lateReason || '';
    document.getElementById('editModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

async function saveEdit() {
    const id = document.getElementById('editId').value;
    const name = document.getElementById('editName').value;
    const date = document.getElementById('editDate').value;
    
    let editTimeVal = document.getElementById('editTime').value;
    const editSecVal = document.getElementById('editSecond').value.padStart(2, '0') || '00';
    if (editTimeVal.split(':').length === 3) {
        editTimeVal = editTimeVal.split(':').slice(0, 2).join(':');
    }
    const time = `${editTimeVal}:${editSecVal}`;
    const type = document.querySelector('input[name="editType"]:checked').value;
    const late_reason = document.getElementById('editLateReason').value;

    try {
        const response = await fetch(`/schedule/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, date, time, type, late_reason }),
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
