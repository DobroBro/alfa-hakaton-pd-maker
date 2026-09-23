def test_crm_pin_alone_not_masked(client):
    resp = client.post(
        "/process",
        json={"payload": "пин-код 1234", "payload_id": "c1"},
        headers={"X-System-Id": "crm"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "пин-код 1234"


def test_crm_cvv_alone_not_masked(client):
    resp = client.post(
        "/process",
        json={"payload": "CVV 123", "payload_id": "c2"},
        headers={"X-System-Id": "crm"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "CVV 123"


def test_crm_pin_with_card_masked(client):
    resp = client.post(
        "/process",
        json={"payload": "пин-код 1234, карта 4111111111111111", "payload_id": "c3"},
        headers={"X-System-Id": "crm"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "пин-код ****, карта 4111********1111"


def test_checker_pin_alone_masked(client):
    resp = client.post(
        "/process",
        json={"payload": "пин-код 1234", "payload_id": "c4"},
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == "пин-код ****"


def test_analytics_disabled_gives_403(client):
    resp = client.post(
        "/process",
        json={"payload": "тест", "payload_id": "c5"},
        headers={"X-System-Id": "analytics"},
    )
    assert resp.status_code == 403
    assert resp.json() == {"detail": "system_disabled"}