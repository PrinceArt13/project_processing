import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from configurations.db import get_db
from dependencies.auth import verify_api_key
from schemas.payment import PaymentCreate, PaymentResponse, PaymentDetail
from models import Payments
from configurations.outbox import add_to_outbox
from enums.Status import Status

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Создать платеж",
    description="Создает новый платеж и публикует событие в outbox"
)
async def create_payment(
        payment_data: PaymentCreate,
        idempotency_key: str = Header(..., alias="Idempotency-Key"),
        db: AsyncSession = Depends(get_db),
        _: str = Depends(verify_api_key)
):
    try:
        idempotency_uuid = uuid.UUID(idempotency_key)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Idempotency-Key format (must be UUID)"
        )

    stmt = select(Payments).where(Payments.idempotency_key == idempotency_uuid)
    result = await db.execute(stmt)
    existing_payment = result.scalar_one_or_none()

    if existing_payment:
        return PaymentResponse(
            payment_id=existing_payment.id,
            status=existing_payment.status,
            created_at=existing_payment.create_datetime
        )

    new_payment_id = uuid.uuid4()

    new_payment = Payments(
        id=new_payment_id,
        sum=payment_data.sum,
        currency=payment_data.currency,
        description=payment_data.description,
        meta_info=payment_data.metadata,
        status=Status.PENDING,
        idempotency_key=idempotency_uuid,
        webhook_url=payment_data.webhook_url
    )

    db.add(new_payment)

    await add_to_outbox(
        session=db,
        event_type="payment.created",
        aggregate_id=new_payment_id,
        payload={
            "payment_id": str(new_payment_id),
            "webhook_url": payment_data.webhook_url,
            "sum": payment_data.sum,
            "currency": payment_data.currency.value,
            "status": Status.PENDING.value
        }
    )

    await db.commit()
    await db.refresh(new_payment)

    return PaymentResponse(
        payment_id=new_payment.id,
        status=new_payment.status,
        created_at=new_payment.create_datetime
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentDetail,
    summary="Получить информацию о платеже",
    description="Возвращает детальную информацию о платеже по его ID"
)
async def get_payment(
        payment_id: uuid.UUID,
        db: AsyncSession = Depends(get_db),
        _: str = Depends(verify_api_key)
):

    stmt = select(Payments).where(Payments.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment with id {payment_id} not found"
        )

    return payment
