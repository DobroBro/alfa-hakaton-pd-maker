import json
import os
import threading
import time
from dataclasses import dataclass

from app import crypto
from app.settings import REDIS_URL, STORE, STORE_TTL_SECONDS


@dataclass
class Record:
    original: str
    masked: str


class _MemoryLock:
    def __init__(self, lock: threading.Lock) -> None:
        self._lock = lock

    def release(self) -> None:
        self._lock.release()


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, Record] = {}
        self._locks: dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def get(self, payload_id: str) -> Record | None:
        with self._guard:
            return self._data.get(payload_id)

    def set(self, payload_id: str, original: str, masked: str) -> None:
        with self._guard:
            self._data[payload_id] = Record(original=original, masked=masked)

    def acquire_lock(self, payload_id: str, timeout: float):
        with self._guard:
            lock = self._locks.get(payload_id)
            if lock is None:
                lock = threading.Lock()
                self._locks[payload_id] = lock
        if lock.acquire(timeout=timeout):
            return _MemoryLock(lock)
        return None


class _RedisLock:
    def __init__(self, redis, script, key: str, token: str) -> None:
        self._redis = redis
        self._script = script
        self._key = key
        self._token = token

    def release(self) -> None:
        try:
            self._script(keys=[self._key], args=[self._token])
        except Exception:
            pass


class RedisStore:
    def __init__(self, redis_url: str, key: str) -> None:
        import redis

        self._redis = redis.Redis.from_url(redis_url, decode_responses=False)
        self._key = crypto.load_key(key)
        self._lock_script = self._redis.register_script(
            "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
        )

    def get(self, payload_id: str) -> Record | None:
        raw = self._redis.get(f"pd:{payload_id}")
        if raw is None:
            return None
        data = crypto.decrypt(self._key, raw, payload_id)
        obj = json.loads(data)
        return Record(original=obj["o"], masked=obj["m"])

    def set(self, payload_id: str, original: str, masked: str) -> None:
        obj = json.dumps({"o": original, "m": masked}).encode()
        raw = crypto.encrypt(self._key, obj, payload_id)
        self._redis.set(f"pd:{payload_id}", raw, ex=STORE_TTL_SECONDS)

    def acquire_lock(self, payload_id: str, timeout: float):
        deadline = time.monotonic() + timeout
        while True:
            token = os.urandom(16).hex()
            ok = self._redis.set(f"lock:{payload_id}", token, nx=True, px=15000)
            if ok:
                return _RedisLock(self._redis, self._lock_script, f"lock:{payload_id}", token)
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.01)


def create_store():
    if STORE == "redis":
        if not REDIS_URL:
            raise RuntimeError("STORE=redis requires REDIS_URL")
        if not os.environ.get("PD_STORE_KEY"):
            raise RuntimeError("STORE=redis requires PD_STORE_KEY")
        return RedisStore(REDIS_URL, os.environ["PD_STORE_KEY"])
    return MemoryStore()