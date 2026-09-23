# PD Masker

Сервис маскирования персональных данных (ПД). Принимает строку, находит и маскирует ПД, сохраняет пару «оригинал → маска» по `payload_id` для идемпотентности.

## Пример

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"payload":"Клиент Иванов Иван Иванович, паспорт 4509 123456","payload_id":"1"}'
```

Ответ: `{"result":"Клиент И. И. И., паспорт 45** ****56"}`.

## Настройка

Откройте `config/systems.yaml`. Добавьте систему с `enabled`. Перечислите `types` или `all`. Задайте `demask_enabled` и `combo_rules`. Имя передаётся в `X-System-Id`, без заголовка работает `checker`.

## Запуск

```bash
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Для Docker задайте ключ шифрования перед запуском:

```bash
export PD_STORE_KEY=$(python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())")
docker compose up
```

Демо-страница открывается по адресу сервиса `/`.

## Тесты

```bash
PYTHONPATH=. pytest -q
```
