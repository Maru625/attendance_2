# Attendance Camera Interception System (출석 카메라 시스템)

이 프로젝트는 웹 인터페이스를 통해 특정 시간에 가상 카메라로 이미지를 송출하는 시스템입니다. 출근/퇴근 시간에 맞춰 본인의 얼굴 사진 등을 카메라 프로그램(Zoom, Teams 등)에 자동으로 띄워주는 역할을 합니다.

## 📋 사전 요구 사항 (Prerequisites)

이 프로젝트를 실행하기 위해 다음 프로그램들이 필요합니다.

1.  **OBS Studio (또는 OBS Virtual Camera)**
    *   이 시스템은 **가상 카메라(Virtual Camera)** 기술을 사용합니다.
    *   OBS Studio를 설치 후 "Start Virtual Camera"를 한 번 실행해 주거나, OBS Virtual Camera 드라이버가 설치되어 있어야 합니다.
2.  **UV (Python Package Manager)**
    *   이 프로젝트는 `uv`를 사용하여 의존성을 관리합니다.
    *   [UV 설치 가이드](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)를 참고하세요. (보통 `pip install uv` 로 설치 가능)

## 🚀 설치 및 실행 방법

### 1. 프로젝트 클론 및 이동
```bash
git clone <repository-url>
cd attendance_2
```

### 2. 의존성 설치 및 가상환경 설정
`uv`를 사용하면 별도의 가상환경 생성 명령어 없이 바로 실행 시점에 환경이 구성되지만, 명시적으로 동기화할 수 있습니다.

```bash
uv sync
```

### 3. 서버 실행
아래 명령어로 FastAPI 서버를 실행합니다.

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

서버가 실행되면 **http://localhost:5000** 에 접속하여 시스템을 사용할 수 있습니다.

### 4. 외부 접속 방법 (External Access)

외부(같은 와이파이/네트워크에 있는 다른 기기)에서 접속하려면:
1.  위 명령어로 서버를 실행할 때 `--host 0.0.0.0` 옵션을 반드시 포함해야 합니다 (이미 위 명령에 포함됨).
2.  서버 컴퓨터의 IP 주소를 확인합니다 (터미널에서 `ipconfig` 실행 후 IPv4 주소 확인).
3.  다른 기기의 브라우저에서 `http://[서버IP]:5000` 으로 접속합니다.
4.  **방화벽 주의**: 윈도우 방화벽이 외부 접속을 차단할 수 있습니다. `python` 또는 `uvicorn`에 대한 방화벽 허용이 필요할 수 있습니다.

## 📁 폴더 구조 (Directory Structure)

```
attendance_2/
├── app/                      # Backend Source Code
│   ├── main.py               # FastAPI Entry point & App setup
│   ├── schemas.py            # Pydantic Data Models (Reservation 등)
│   ├── routers/              # API Route Handlers
│   │   └── reservation_router.py
│   └── services/             # Business Logic
│       └── camera_service.py # Camera control & Image handling logic
├── static/                   # Frontend Assets (Served at /static)
│   ├── index.html            # Main Web Interface
│   ├── style.css             # Glassmorphism UI Styles
│   └── script.js             # Frontend Logic (Fetch API)
├── images/                   # Image Storage Directory
│   └── [Name].jpg            # 사용자 이름과 동일한 이미지 파일을 이곳에 위치
├── pyproject.toml            # Project Configuration & Dependencies (UV)
├── uv.lock                   # Dependency Lock File
└── README.md                 # Project Documentation
```

## 💡 사용 방법

1.  `images/` 폴더에 본인의 이름(예: `홍길동`)으로 된 이미지 파일(`홍길동.jpg`, `png`, `jpeg`)을 넣습니다.
2.  웹페이지(http://localhost:8000)에서 **이름**, **날짜**, **시간**을 입력하고 **예약하기**를 누릅니다.
3.  지정된 시간이 되면 서버가 자동으로 **OBS Virtual Camera** 장치를 통해 해당 이미지를 30초간 송출합니다.
4.  Zoom이나 Teams 등의 설정에서 카메라를 **OBS Virtual Camera**로 선택해두면 이미지가 나타납니다.

## ⚠️ 주의사항 및 문제 해결 (Troubleshooting)

### 1. 터미널 한글 깨짐 (인코딩 문제)
서버 실행 시 터미널에 한글이 `í™ ê¸¸ë œ` 처럼 깨져서 보인다면, 명령 프롬프트(cmd)나 PowerShell의 인코딩을 UTF-8로 변경해야 합니다.
서버를 실행하기 전에 아래 명령어를 한 번 입력하세요:
```bash
chcp 65001
```
이후 서버를 다시 실행하면 한글이 정상적으로 출력됩니다.

### 2. 외부 접속 불가 (방화벽 및 포트 문제)
외부 기기(스마트폰이나 다른 PC)에서 `http://[서버IP]:5000`으로 접속이 안 되거나 Ping이 안 나가는 경우, Windows 방화벽이 차단하고 있을 확률이 높습니다.
1. Windows 키 누르고 **"방화벽"** 검색 → **"Windows Defender 방화벽이 설정된 고급 보안"** 실행
2. 왼쪽 메뉴 **"인바운드 규칙"** → 우측 **"새 규칙"**
3. **규칙 종류**: `포트`
4. **프로토콜 및 포트**: `TCP`, 특정 로컬 포트에 `5000` 입력
5. **작업**: `연결 허용`
6. **프로필**: `도메인, 개인, 공용` 모두 체크
7. **이름**: `출석 카메라 (포트 5000)` 등 입력 후 완료

### 3. 카메라 및 이미지 문제
*   `OBS Virtual Camera` 장치가 인식되지 않으면 에러 로그가 출력됩니다. OBS를 켜서 Virtual Camera를 활성화했는지 확인하세요.
*   이미지가 `images/` 폴더에 없으면 예약 시 에러가 발생합니다. (단, `.jpg`, `.png`, `.jpeg` 의 대소문자는 구분하지 않고 자동으로 찾습니다)
