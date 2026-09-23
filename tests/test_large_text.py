import time


def test_large_text(client):
    payload = "ivan.petrov@mail.ru" + "а" * 400_000
    start = time.monotonic()
    resp = client.post("/process", json={"payload": payload, "payload_id": "large1"})
    elapsed = time.monotonic() - start
    assert resp.status_code == 200
    assert elapsed < 10
    result = resp.json()["result"]
    assert result.startswith("i***@mail.ru")
    assert result.endswith("а" * 400_000)