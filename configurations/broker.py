import os
import asyncio
import random
import datetime
import uuid
import httpx
from pydantic import BaseModel
from faststream.rabbit import RabbitBroker, RabbitRouter, RabbitQueue
from fastapi import Depends
from sqlalchemy import select

from configurations.db import get_db
from models import Payments, Outbox
from models.Outbox import OutboxStatus
from enums.Status import Status

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

broker = RabbitBroker(RABBITMQ_URL)
router = RabbitRouter()


class PaymentCreatedEvent(BaseModel):
    payment_id: str
    webhook_url: str
    sum: float
    currency: str
    status: str


payments_queue = RabbitQueue(
    "payments.new",
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": "payments.dlq"
    }
)


@router.subscriber(payments_queue)
async def process_payment(event: PaymentCreatedEvent, db=Depends(get_db)):
    payment_id = event.payment_id
    webhook_url = event.webhook_url

    stmt_payment = select(Payments).where(Payments.id == uuid.UUID(payment_id))
    result_payment = await db.execute(stmt_payment)
    payment = result_payment.scalar_one_or_none()

    stmt_outbox = select(Outbox).where(Outbox.aggregate_id == uuid.UUID(payment_id))
    result_outbox = await db.execute(stmt_outbox)
    outbox_record = result_outbox.scalar_one_or_none()

    if not payment or not outbox_record:
        return

    outbox_record.attempts += 1
    await db.commit()

    await asyncio.sleep(random.uniform(2.0, 5.0))

    if random.random() < 0.1:
        if outbox_record.attempts >= 3:
            payment.status = Status.FAILED
            payment.handle_datetime = datetime.datetime.now(datetime.timezone.utc)
            outbox_record.status = OutboxStatus.FAILED
            await db.commit()
            raise Exception("Max retries reached, moving to Dead Letter Queue.")
        else:
            delay = 2 ** outbox_record.attempts
            await asyncio.sleep(delay)
            raise Exception("Simulated random error, triggering retry...")

    payment.status = Status.SUCCEEDED
    payment.handle_datetime = datetime.datetime.now(datetime.timezone.utc)
    outbox_record.status = OutboxStatus.PUBLISHED
    await db.commit()

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                webhook_url,
                json={
                    "payment_id": payment_id,
                    "status": payment.status.value,
                    "sum": event.sum,
                    "currency": event.currency
                },
                timeout=5.0
            )
    except Exception:
        pass