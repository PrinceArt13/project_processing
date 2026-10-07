import asyncio
from sqlalchemy import select
from configurations.db import async_session_maker
from configurations.broker import broker
from models.Outbox import Outbox, OutboxStatus


async def outbox_publisher():
    while True:
        try:
            await asyncio.sleep(3)
            async with async_session_maker() as db:
                stmt = (
                    select(Outbox)
                    .where(Outbox.status == OutboxStatus.PENDING)
                    .limit(10)
                )
                result = await db.execute(stmt)
                events = result.scalars().all()

                for event in events:
                    try:
                        await broker.publish(event.payload, "payments.new")
                        event.status = OutboxStatus.PUBLISHED
                        await db.commit()
                    except Exception:
                        await db.rollback()
        except Exception:
            await asyncio.sleep(5)
