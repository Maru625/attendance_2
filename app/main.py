import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import reservation_router
from app.services import attendance_service

logging.basicConfig(level=logging.INFO)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")


class NoCacheMiddleware(BaseHTTPMiddleware):
    """모든 응답에 캐시 비활성화 헤더를 추가하여 ngrok/모바일 브라우저 캐시 문제를 방지"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 초기화 처리"""
    attendance_service.load_employees()
    reservation_router.init_scheduler()
    try:
        yield
    finally:
        reservation_router.shutdown_scheduler()


app = FastAPI(lifespan=lifespan)
app.add_middleware(NoCacheMiddleware)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(reservation_router.router)


@app.get("/")
async def serve_spa():
    return JSONResponse(content={"message": "Please go to /static/index.html"})
