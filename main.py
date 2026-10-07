import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from configurations.db import engine, Base
from configurations.broker import broker, router
from configurations.publisher import outbox_publisher
from api.payments import router as payments_router

publisher_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global publisher_task

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    broker.include_router(router)
    await broker.start()

    publisher_task = asyncio.create_task(outbox_publisher())

    yield

    if publisher_task:
        publisher_task.cancel()
        try:
            await publisher_task
        except asyncio.CancelledError:
            pass
    await broker.close()


app = FastAPI(
    title="Payment Processing API",
    version="1.0.0",
    description="Микросервис для асинхронной обработки платежей с Outbox pattern",
    lifespan=lifespan
)

app.include_router(payments_router)


@app.get("/")
async def root():
    return {"message": "Payment Processing API is running. Check /docs for API."}