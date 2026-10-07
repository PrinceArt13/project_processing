import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from models.Outbox import Outbox, OutboxStatus


async def add_to_outbox(
    session: AsyncSession,
    event_type: str,
    aggregate_id: uuid.UUID,
    payload: dict
) -> None:
    outbox_event = Outbox(
        event_type=event_type,
        aggregate_id=aggregate_id,
        payload=payload,
        status=OutboxStatus.PENDING,
        attempts=0
    )
    session.add(outbox_event)
