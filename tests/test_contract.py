def test_response_has_only_result_field(client):
    resp = client.post("/process", json={"payload": "тест", "payload_id": "id1"})
    assert resp.status_code == 200
    assert set(resp.json().keys()) == {"result"}


def test_bad_json_gives_400_without_echo(client):
    resp = client.post(
        "/process",
        content=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json() == {"detail": "bad_request"}
    assert "not json" not in resp.text


def test_empty_payload_id_gives_400(client):
    resp = client.post("/process", json={"payload": "тест", "payload_id": "   "})
    assert resp.status_code == 400
    assert resp.json() == {"detail": "bad_request"}


def test_no_header_no_401_403(client):
    resp = client.post("/process", json={"payload": "тест", "payload_id": "id2"})
    assert resp.status_code == 200
    assert resp.json() == {"result": "тест"}