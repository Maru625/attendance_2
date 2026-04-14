# ⏰ 원격 출석 예약 시스템

지정된 시간에 자동으로 출석을 처리하는 FastAPI 기반 예약 시스템입니다.  
Selenium headless Chrome으로 출석 페이지를 열고, `window.kadaSubmitAttendance(...)`의 반환 payload와 화면 반영 결과를 함께 확인해 성공 여부를 판단합니다.

---

## 주요 특징

- 예약 시간에 자동으로 출근/퇴근 처리
- 지각 감지 시 예약 시 입력한 사유 자동 제출
- 지각 사유 미입력 시 기본 사유 자동 적용
- 예약 데이터 JSON 저장 및 서버 재시작 후 복원
- ngrok을 통한 외부 접속 지원
- 앱 startup에서만 스케줄러를 초기화하여 중복 실행 위험 완화

---

## 📁 프로젝트 구조

```text
attendance_2/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── routers/
│   │   └── reservation_router.py
│   └── services/
│       ├── attendance_service.py
│       └── reservation_service.py
├── static/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── employees.json
├── reservations.json
├── pyproject.toml
├── requirements.txt
├── start_server.bat
├── start_ngrok.bat
├── start_all.bat
└── README.md
```

---

## ⚙️ 사전 요구사항

- Python 3.11+
- Google Chrome 설치
- `uv` 또는 `pip`
- `ngrok` 설치 및 PATH 등록, 또는 실행 파일 위치 확인 가능해야 함

---

## 🚀 설치

### 1) 의존성 설치

```powershell
uv sync
```

또는

```powershell
pip install -r requirements.txt
```

### 2) 직원 정보 설정

`employees.json` 예시:

```json
{
  "한재욱": "E9F10880A05",
  "김민지": "E9D84A06597"
}
```

### 3) 출석 사이트 URL 확인

`app/services/attendance_service.py`의 `TARGET_URL`을 실제 출석 페이지 주소로 맞춥니다.

---

## ▶ 실행 방법

### 로컬 서버만 실행

```powershell
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

또는 아래 배치 파일 실행:

```powershell
.\start_server.bat
```

접속 주소:
- 로컬: <http://localhost:8000/static/index.html>
- 같은 네트워크: `http://[서버IP]:8000/static/index.html`

---

## 🌐 ngrok으로 외부 접속

### 방법 1) ngrok만 실행

```powershell
.\start_ngrok.bat
```

이 스크립트는:
- 8000 포트를 ngrok으로 터널링
- 로그를 `ngrok.log`에 저장

### 방법 2) 서버와 ngrok 각각 실행

터미널 1:

```powershell
.\start_server.bat
```

터미널 2:

```powershell
.\start_ngrok.bat
```

### 방법 3) 서버 + ngrok 동시 실행

```powershell
.\start_all.bat
```

이 스크립트는 새 창 2개를 열어:
- FastAPI 서버 실행
- ngrok 터널 실행

### ngrok 주소 확인

- 실행 창 출력 확인
- 또는 `ngrok.log` 확인
- 또는 `http://127.0.0.1:4040`에서 터널 상태 확인

---

## 🔄 동작 흐름

```text
1. 웹 UI에서 직원 / 날짜 / 시간 / 유형 / 지각 사유 입력
2. 예약 등록 후 reservations.json에 저장
3. 앱 시작 시 startup에서 스케줄러 1회 초기화
4. 예약 시간에 Selenium이 출석 페이지 접속
5. kadaSubmitAttendance(...) 반환 payload 확인
6. 필요 시 지각 사유 자동 재제출
7. payload + 오늘 기록 행(row) 기반으로 성공/실패 판정
8. 예약 상태 저장
```

---

## 📡 API 엔드포인트

- `GET /employees` 등록된 직원 목록
- `GET /late-reasons` 지각 사유 목록
- `GET /site-health` 출석 사이트 상태 확인
- `POST /schedule` 예약 등록
- `PUT /schedule/{id}` 예약 수정
- `DELETE /schedule/{id}` 예약 삭제
- `GET /reservations` 전체 예약 목록
- `GET /reservations/{type}` 유형별 예약 목록

---

## 📝 실행 스크립트 설명

### `start_server.bat`
- 프로젝트 루트로 이동
- `uvicorn` 서버 실행

### `start_ngrok.bat`
- 8000 포트를 ngrok에 연결
- 로그를 `ngrok.log`에 저장

### `start_all.bat`
- 서버와 ngrok를 각각 새 창으로 실행
- 가장 편한 운영용 시작 스크립트

---

## ⚠ 운영 메모

- 현재 스케줄러는 **단일 프로세스 운영 전제**입니다.
- uvicorn 다중 worker 모드에서는 별도 분산락/DB jobstore 없이 중복 실행 위험이 있습니다.
- Windows 작업 스케줄러나 NSSM으로 실행할 때도 **서버 프로세스는 1개만 유지**하는 것을 권장합니다.

---

## 🛠 문제 해결

| 증상 | 원인 | 해결 |
|------|------|------|
| 출석 사이트 접속 실패 | TARGET_URL 또는 네트워크 문제 | URL 확인, 사이트 상태 확인 |
| ChromeDriver/브라우저 오류 | Chrome 환경 문제 | Chrome 설치 및 업데이트 확인 |
| 예약이 실행되지 않음 | 서버 미실행 또는 예약 시간 경과 | 서버 상태와 예약 시간 확인 |
| 외부에서 접속 안 됨 | ngrok 미실행 또는 주소 변경 | ngrok 다시 실행 후 새 URL 확인 |
| 중복 실행 의심 | 서버 프로세스가 2개 이상 실행됨 | 서버를 1개만 실행하도록 정리 |
