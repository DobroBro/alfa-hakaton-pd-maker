import json
import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app import metrics
from app.logging_setup import setup_logging
from app.profiles import load_profiles
from app.schemas import ProcessRequest
from app.service import RateLimited, Service, StoreUnavailable
from app.settings import MAX_IN_FLIGHT
from app.store import create_store

setup_logging()

logger = logging.getLogger("pd")

app = FastAPI()

_profiles = load_profiles()
_store = create_store()
_service = Service(_store, _profiles, MAX_IN_FLIGHT)

MAX_PAYLOAD = 2_000_000
MAX_PAYLOAD_ID = 128

_STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


@app.get("/")
async def index():
    return FileResponse(_STATIC_INDEX)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"detail": "bad_request"})


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "internal_error"})


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics_endpoint():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/process")
async def process(request: Request):
    start = time.monotonic()
    path = "/process"
    try:
        body = await request.body()
        if len(body) > MAX_PAYLOAD:
            metrics.http_requests_total.labels(path, "400").inc()
            return JSONResponse(status_code=400, content={"detail": "bad_request"})
        try:
            data = ProcessRequest.model_validate_json(body)
        except Exception:
            metrics.http_requests_total.labels(path, "400").inc()
            return JSONResponse(status_code=400, content={"detail": "bad_request"})

        payload = data.payload
        payload_id = data.payload_id.strip()
        if not payload_id or len(payload_id) > MAX_PAYLOAD_ID or len(payload) > MAX_PAYLOAD:
            metrics.http_requests_total.labels(path, "400").inc()
            return JSONResponse(status_code=400, content={"detail": "bad_request"})

        system_id = request.headers.get("X-System-Id")
        profile = _service.get_profile(system_id)
        if profile is None or not profile.enabled:
            logger.info(
                json.dumps(
                    {"event": "rejected", "payload_id": payload_id, "system": system_id or ""},
                    ensure_ascii=False,
                )
            )
            metrics.http_requests_total.labels(path, "403").inc()
            return JSONResponse(status_code=403, content={"detail": "system_disabled"})

        try:
            result = _service.process(payload, payload_id, profile)
        except RateLimited:
            metrics.http_requests_total.labels(path, "429").inc()
            return JSONResponse(
                status_code=429,
                content={"detail": "rate_limited"},
                headers={"Retry-After": "1"},
            )
        except StoreUnavailable:
            metrics.store_errors_total.inc()
            metrics.http_requests_total.labels(path, "500").inc()
            return JSONResponse(status_code=500, content={"detail": "store_unavailable"})
        except Exception:
            metrics.http_requests_total.labels(path, "500").inc()
            return JSONResponse(status_code=500, content={"detail": "internal_error"})

        metrics.tokens_processed_total.inc(max(1, len(payload) // 4))
        metrics.http_requests_total.labels(path, "200").inc()
        return JSONResponse(content={"result": result})
    finally:
        metrics.http_request_duration_seconds.observe(time.monotonic() - start)