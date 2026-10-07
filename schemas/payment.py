import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enums.Currency import Currency
from enums.Status import Status


class PaymentCreate(BaseModel):
    """Схема для создания платежа (request body)"""
    sum: float = Field(..., gt=0, description="Сумма платежа")
    currency: Currency = Field(..., description="Валюта платежа")
    description: Optional[str] = Field(None, max_length=500, description="Описание платежа")
    metadata: Optional[dict] = Field(default_factory=dict, description="Метаданные")
    webhook_url: str = Field(..., description="URL для webhook уведомления")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sum": 100.50,
                "currency": "RUB",
                "description": "Оплата заказа #123",
                "metadata": {"order_id": "123", "customer_email": "test@example.com"},
                "webhook_url": "https://example.com/webhook"
            }
        }
    )


class PaymentResponse(BaseModel):
    """Схема ответа при создании платежа"""
    payment_id: uuid.UUID
    status: Status
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentDetail(BaseModel):
    """Схема детальной информации о платеже"""
    id: uuid.UUID
    sum: float
    currency: Currency
    description: Optional[str]
    metadata: Optional[dict] = Field(alias="metadata")
    status: Status
    idempotency_key: uuid.UUID
    webhook_url: str
    create_datetime: datetime
    handle_datetime: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)