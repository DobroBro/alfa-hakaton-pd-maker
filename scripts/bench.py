import concurrent.futures
import statistics
import time

import httpx

CASES = [
    "Клиент Иванов Иван Иванович, паспорт 4509 123456",
    "Почта ivan.petrov@mail.ru.",
    "Телефон +7 (999) 123-45-67.",
    "карта 4242 4242 4242 4242",
    "ИНН 7707083893",
    "дата рождения 01.02.1990",
    "г. Москва, ул. Тверская, д. 10, кв. 5",
    "Добрый день, хочу узнать статус заявки.",
]

URL = "http://127.0.0.1:8000/process"
DURATION = 10
CONCURRENCY = 50


def worker(payload_id: str):
    payload = CASES[payload_id % len(CASES)]
    with httpx.Client(timeout=10) as client:
        start = time.monotonic()
        resp = client.post(URL, json={"payload": payload, "payload_id": f"bench-{payload_id}"})
        return time.monotonic() - start, resp.status_code


def main() -> None:
    latencies = []
    ok = 0
    deadline = time.monotonic() + DURATION
    counter = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = []
        while time.monotonic() < deadline:
            futures.append(pool.submit(worker, counter))
            counter += 1
            if len(futures) >= CONCURRENCY * 2:
                for f in concurrent.futures.as_completed(futures):
                    lat, code = f.result()
                    latencies.append(lat)
                    if code == 200:
                        ok += 1
                futures = []
        for f in concurrent.futures.as_completed(futures):
            lat, code = f.result()
            latencies.append(lat)
            if code == 200:
                ok += 1

    total = len(latencies)
    rps = total / DURATION
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95) - 1] if latencies else 0
    print(f"requests={total} ok={ok} rps={rps:.1f} p95={p95 * 1000:.1f}ms")


if __name__ == "__main__":
    main()