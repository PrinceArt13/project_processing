# Payment Processing Microservice

Микросервис для асинхронной обработки платежей с гарантией доставки событий.

## Стек технологий
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (асинхронный режим)
- PostgreSQL
- RabbitMQ (FastStream)
- Alembic (миграции)
- Docker + docker-compose
## Запуск через Docker

1. Создайте файл `.env` на основе `.env.example`
2. Запустите инфраструктуру:
```bash
docker-compose up --build -d
```
3. Примените миграции:
```bash
docker-compose exec app alembic upgrade head
 ```

## Локальный запуск
1. Установите зависимости:
```bash
pip install -r requirements.txt
```
2. Запустите postgres и rabbitmq:
```bash
docker-compose up -d postgres rabbitmq
```
3. Примените миграции:
```bash
alembic upgrade head
```

4. Запустите приложение:
```bash
uvicorn main:app --reload
```

## Документация
Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)

В swagger приведены примеры запросов и ответов к ним.

RabbitMQ: [http://localhost:15672](http://localhost:15672) (guest / guest)