import io
import logging


def test_logs_no_pii(client, monkeypatch):
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("pd")
    old_handlers = list(logger.handlers)
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    try:
        resp = client.post(
            "/process",
            json={"payload": "паспорт 4509 123456 Иванов", "payload_id": "log1"},
        )
        assert resp.status_code == 200
    finally:
        logger.handlers = old_handlers

    log_text = stream.getvalue()
    assert "4509" not in log_text
    assert "123456" not in log_text
    assert "Иванов" not in log_text