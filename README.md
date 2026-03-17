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
### 4. 도메인(DNS) 연결 방법
로컬 서버를 정식 도메인(예: `attendance.mycompany.com`)으로 연결하려면 다음 방법 중 하나를 사용할 수 있습니다.

**방법 A. Cloudflare Tunnels / ngrok 사용 (가장 추천 & 안전)**
공유기 포트포워딩 없이 가장 쉽고 안전하게 도메인을 연결하는 방법입니다.
1. **Cloudflare Tunnels**: Cloudflare에 도메인을 등록 후 Zero Trust 대시보드에서 터널을 생성합니다. 서버 PC에 커넥터를 설치하고 `localhost:5000`으로 라우팅하면 무료로 HTTPS 도메인 연결이 완료됩니다.
2. **ngrok (가장 간편한 방법)**
   별도의 공유기 설정 없이 대상 PC에서 터미널 명령어 한 줄로 외부 접속을 허용합니다.
   * **설치**: [ngrok 공식 홈페이지](https://ngrok.com/)에서 가입 후 프로그램을 다운로드하거나, 터미널에서 `winget install ngrok` (Windows)로 설치합니다.
   * **초기 설정**: 가입 후 제공되는 Authtoken을 터미널에 입력합니다. (`ngrok config add-authtoken 본인의토큰`)
   * **실행 방법**: **대상 PC**에서 서버를 실행(`uv run uvicorn...`)해둔 상태로, 새 터미널 창을 열고 아래 명령어를 입력합니다.
     ```bash
     ngrok http 5000
     ```
   * **URL 확인 및 주의사항**: 
     * 실행하면 검은 화면에 `Forwarding  https://abcd-12-34-56.ngrok-free.app -> http://localhost:5000` 와 같이 뜹니다. 이 `https://...` 주소가 스마트폰 등 외부에서 접속할 주소입니다.
     * ⚠️ **무료 버전의 한계**: ngrok을 **껐다가 다시 켜면 주소가 매번 바뀝니다**. 고정된 웹 주소를 계속 사용하고 싶다면 ngrok 유료 요금제를 쓰거나, 개인 도메인 구매 후 **Cloudflare Tunnels**(평생 무료)를 사용하는 것을 강력히 추천합니다.

**방법 B. 공유기 포트포워딩 + DNS A 레코드 설정 (전통적 방법)**
1. **Public IP 확인**: 서버가 있는 네트워크의 공인 IP를 확인합니다. (네이버에 "내 IP" 검색)
2. **공유기 설정 (포트포워딩)**: 공유기 설정 페이지에 접속해 외부 포트(80 또는 실제 사용할 포트)를 내부 서버 PC의 IP(`103.218.162.226`) 및 포트(`5000`)로 연결합니다.
3. **DNS 설정**: 가비아, 후이즈 등 도메인 구입처의 DNS 관리 페이지로 이동합니다.
4. **A 레코드 추가**: `A` 레코드를 생성하고 값으로 1번에서 찾은 **공인 IP**를 입력합니다.
5. (선택) Nginx 등을 설치하여 리버스 프록시 및 SSL(HTTPS) 설정을 추가하면 더 안전합니다.
