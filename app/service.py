import json
import logging

from app import metrics, pipeline
from app.limiter import InFlightLimiter
from app.profiles import Profile

logger = logging.getLogger("pd")


class Service:
    def __init__(self, store, profiles: dict[str, Profile], max_in_flight: int) -> None:
        self._store = store
        self._profiles = profiles
        self._limiter = InFlightLimiter(max_in_flight)

    def get_profile(self, system_id: str | None) -> Profile | None:
        if not system_id:
            return self._profiles.get("checker")
        return self._profiles.get(system_id)

    async def process(self, payload: str, payload_id: str, profile: Profile) -> str:
        if not self._limiter.try_acquire():
            self._log_event("rate_limited", payload_id, profile.name)
            raise RateLimited
        try:
            lock = await self._acquire_lock(payload_id, profile.name)
            if lock is None:
                self._log_event("rate_limited", payload_id, profile.name)
                raise RateLimited
            try:
                record = self._get_record(payload_id, profile.name)
                if record is not None:
                    if record.original == payload:
                        self._log_event("retry", payload_id, profile.name)
                        return record.masked
                    if profile.demask_enabled:
                        self._log_event("demasked", payload_id, profile.name)
                        return record.original
                    self._log_event("retry", payload_id, profile.name)
                    return record.masked
                spans = pipeline.detect(payload, profile)
                masked = pipeline.apply(payload, spans, profile.mask_style)
                self._store_pair(payload_id, payload, masked, profile.name)
                self._log_masked(payload_id, profile.name, spans)
                for s in spans:
                    metrics.pii_detected_total.labels(s.type).inc()
                return masked
            finally:
                self._release_lock(lock)
        finally:
            self._limiter.release()

    async def _acquire_lock(self, payload_id: str, system: str):
        try:
            return await self._store.acquire_lock(payload_id, timeout=2.0)
        except Exception as exc:  # noqa: BLE001
            self._log_store_error(exc)
            self._log_event("store_unavailable", payload_id, system)
            raise StoreUnavailable from None

    def _get_record(self, payload_id: str, system: str):
        try:
            return self._store.get(payload_id)
        except Exception as exc:  # noqa: BLE001
            self._log_store_error(exc)
            self._log_event("store_unavailable", payload_id, system)
            raise StoreUnavailable from None

    def _store_pair(self, payload_id: str, original: str, masked: str, system: str) -> None:
        try:
            self._store.set(payload_id, original=original, masked=masked)
        except Exception as exc:  # noqa: BLE001
            self._log_store_error(exc)
            self._log_event("store_unavailable", payload_id, system)
            raise StoreUnavailable from None

    def _release_lock(self, lock) -> None:
        release = getattr(lock, "release", None)
        if release is not None:
            release()

    def _log_event(self, event: str, payload_id: str, system: str) -> None:
        logger.info(
            json.dumps(
                {"event": event, "payload_id": payload_id, "system": system},
                ensure_ascii=False,
            )
        )

    def _log_store_error(self, exc: Exception) -> None:
        logger.error(
            json.dumps(
                {"event": "store_error", "error_type": type(exc).__name__},
                ensure_ascii=False,
            )
        )

    def _log_masked(self, payload_id: str, system: str, spans) -> None:
        types = sorted({s.type for s in spans})
        masked_types = sorted({s.type for s in spans if s.mask})
        span_data = [{"type": s.type, "start": s.start, "end": s.end} for s in spans]
        logger.info(
            json.dumps(
                {
                    "event": "masked",
                    "payload_id": payload_id,
                    "system": system,
                    "types": types,
                    "masked_types": masked_types,
                    "spans": span_data,
                },
                ensure_ascii=False,
            )
        )


class RateLimited(Exception):
    pass


class StoreUnavailable(Exception):
    pass