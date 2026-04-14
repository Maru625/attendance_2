"""
attendance_service.py
- Selenium 기반 출석 자동화 서비스
- headless Chrome으로 출석 웹사이트 접속 → JS 함수 반환값과 화면 상태를 함께 검사
"""

import json
import logging
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

TARGET_URL = "https://construction-montgomery-roof-tagged.trycloudflare.com/attendance"
LATE_REASONS = [
    "교통 지연",
    "개인 사유",
    "업무 관련",
    "기타",
]
DEFAULT_LATE_REASON = "개인 사유"
SUCCESS_EVENTS = {"checkin", "checkout"}
WARNING_EVENTS = {"already_checked_out", "checkout_locked", "duplicate_scan"}
_employees: dict[str, str] = {}


def _get_employees_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "employees.json")


def load_employees() -> dict[str, str]:
    global _employees
    path = _get_employees_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            _employees = json.load(f)
        logger.info(f"직원 {len(_employees)}명 로드됨")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"employees.json 로드 실패: {e}")
        _employees = {}
    return _employees


def get_employees() -> dict[str, str]:
    if not _employees:
        load_employees()
    return _employees


def get_employee_names() -> list[str]:
    return list(get_employees().keys())


def get_qr_data(name: str) -> str | None:
    return get_employees().get(name)


def get_late_reasons() -> list[str]:
    return LATE_REASONS


def get_default_late_reason() -> str:
    return DEFAULT_LATE_REASON


def get_target_url() -> str:
    return TARGET_URL


def set_target_url(url: str):
    global TARGET_URL
    TARGET_URL = url
    logger.info(f"출석 사이트 URL 변경: {url}")


def check_site_health() -> dict:
    try:
        resp = requests.get(TARGET_URL, timeout=10)
        if resp.status_code == 200:
            return {"healthy": True, "status_code": resp.status_code, "message": "사이트 정상"}
        return {"healthy": False, "status_code": resp.status_code, "message": f"HTTP {resp.status_code}"}
    except requests.ConnectionError:
        return {"healthy": False, "status_code": None, "message": "사이트에 연결할 수 없습니다."}
    except requests.Timeout:
        return {"healthy": False, "status_code": None, "message": "사이트 응답 시간 초과 (10초)"}
    except Exception as e:
        return {"healthy": False, "status_code": None, "message": f"알 수 없는 오류: {e}"}


def _create_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    return webdriver.Chrome(options=chrome_options)


def _wait_until_ready(driver: webdriver.Chrome):
    WebDriverWait(driver, 15).until(
        lambda d: d.execute_script("return typeof window.kadaSubmitAttendance === 'function'")
    )


def _get_selected_employee_name(driver: webdriver.Chrome) -> str:
    return driver.execute_script(
        "return document.querySelector('[data-selected-employee-name]')?.textContent?.trim() || '';"
    )


def _get_row_for_employee(driver: webdriver.Chrome, qr_data: str) -> dict:
    return driver.execute_script(
        """
        const row = document.querySelector(`[data-row-employee="${arguments[0]}"]`);
        if (!row) {
            return null;
        }
        const cells = row.querySelectorAll('td');
        const badge = row.querySelector('.badge');
        return {
            name: cells[0]?.textContent?.trim() || '',
            checkin: cells[1]?.textContent?.trim() || '',
            checkout: cells[2]?.textContent?.trim() || '',
            reason: cells[3]?.textContent?.trim() || '',
            status: badge?.textContent?.trim() || '',
        };
        """,
        qr_data,
    )


def _submit_attendance(driver: webdriver.Chrome, qr_data: str, late_reason: str = "") -> dict:
    return driver.execute_async_script(
        """
        const [code, reason, done] = arguments;
        Promise.resolve(window.kadaSubmitAttendance({
            action: 'attendance',
            code,
            reason,
            clearReason: true,
            keepFocus: false,
            origin: 'automation',
            cameraLabel: 'OpenClaw Automation',
            liveness: 'passed',
            scannerEngine: 'selenium',
        }))
          .then((payload) => done(payload || {}))
          .catch((error) => done({
            ok: false,
            message: String(error?.message || error || 'unknown_error'),
          }));
        """,
        qr_data,
        late_reason,
    )


def _interpret_result(payload: dict, row: dict | None, late_reason: str) -> dict:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = bool(payload.get("ok"))
    event = str(payload.get("attendance_event") or "").strip()
    message = str(payload.get("message") or "").strip()
    requires_reason = bool(payload.get("requires_reason"))

    if requires_reason:
        return {
            "status": "실패",
            "message": "지각 사유 자동 제출에 실패했습니다. 사유 선택 상태가 남아 있습니다.",
            "timestamp": timestamp,
            "payload": payload,
        }

    if ok and event in SUCCESS_EVENTS:
        if late_reason and row and row.get("reason") and row.get("reason") != "-":
            return {
                "status": "성공",
                "message": f"지각 처리 완료 (사유: {row.get('reason')})",
                "timestamp": timestamp,
                "payload": payload,
            }
        return {
            "status": "성공",
            "message": message or "출석이 정상 처리되었습니다.",
            "timestamp": timestamp,
            "payload": payload,
        }

    if event in WARNING_EVENTS:
        return {
            "status": "실패",
            "message": message or f"출석 처리 경고 상태: {event}",
            "timestamp": timestamp,
            "payload": payload,
        }

    return {
        "status": "실패",
        "message": message or "출석 처리 결과를 확인할 수 없습니다.",
        "timestamp": timestamp,
        "payload": payload,
    }


def auto_check_in(qr_data: str, late_reason: str = "") -> dict:
    resolved_late_reason = late_reason.strip() or DEFAULT_LATE_REASON
    health = check_site_health()
    if not health["healthy"]:
        return {
            "status": "실패",
            "message": f"출석 사이트 접속 불가: {health['message']}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    driver = None
    try:
        driver = _create_driver()
        driver.get(TARGET_URL)
        _wait_until_ready(driver)

        selected_name = _get_selected_employee_name(driver)
        logger.info(f"자동 출석 시작, 대상 QR={qr_data}, 현재 선택={selected_name}")

        payload = _submit_attendance(driver, qr_data, "")
        if payload.get("requires_reason"):
            logger.info(f"지각 감지, 사유 자동 제출 시도: {resolved_late_reason}")
            payload = _submit_attendance(driver, qr_data, resolved_late_reason)

        row = _get_row_for_employee(driver, qr_data)
        logger.info(f"출석 결과 payload={payload}, row={row}")
        return _interpret_result(payload, row, resolved_late_reason)
    except Exception as e:
        logger.error(f"출석 중 오류 발생: {e}")
        return {
            "status": "실패",
            "message": f"출석 처리 중 오류: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
