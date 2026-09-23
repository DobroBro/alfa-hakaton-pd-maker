import threading

from app.main import _service
from app.store import MemoryStore

FIRST = "Клиент Иванов Иван Иванович, паспорт 4509 123456"
MASKED = "Клиент И. И. И., паспорт 45** ****56"


def test_idempotency(client):
    pid = "idem-1"
    r1 = client.post("/process", json={"payload": FIRST, "payload_id": pid})
    assert r1.status_code == 200
    assert r1.json()["result"] == MASKED

    r2 = client.post("/process", json={"payload": FIRST, "payload_id": pid})
    assert r2.status_code == 200
    assert r2.json()["result"] == MASKED

    store = _service._store
    assert isinstance(store, MemoryStore)
    assert len(store._data) == 1

    r3 = client.post("/process", json={"payload": MASKED, "payload_id": pid})
    assert r3.status_code == 200
    assert r3.json()["result"] == FIRST

    r4 = client.post("/process", json={"payload": "другая строка", "payload_id": pid})
    assert r4.status_code == 200
    assert r4.json()["result"] == FIRST

    r5 = client.post("/process", json={"payload": FIRST, "payload_id": pid})
    assert r5.status_code == 200
    assert r5.json()["result"] == MASKED


def test_parallel_first_calls_same_mask(client):
    pid = "idem-parallel"
    results = []
    lock = threading.Lock()

    def worker():
        r = client.post("/process", json={"payload": FIRST, "payload_id": pid})
        with lock:
            results.append(r.json()["result"])

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(res == MASKED for res in results)
    store = _service._store
    assert len(store._data) == 1