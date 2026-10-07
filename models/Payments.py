import uuid
import datetime
from sqlalchemy import String, Text, Numeric, JSON, func
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from configurations.db import Base
from enums.Currency import Currency
from enums.Status import Status


class Payments(Base):
    __tablename__ = 'payments'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sum: Mapped[float] = mapped_column(Numeric, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(
        PgEnum(Currency, name='currency_enum', create_type=False),
        nullable=False,
        default=Currency.RUB)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_info: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True, default=dict)
    status: Mapped[str] = mapped_column(
        PgEnum(Status, name='status_enum', create_type=False),
        nullable=False,
        default=Status.PENDING)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        default=uuid.uuid4,
        unique=True)
    webhook_url: Mapped[str] = mapped_column(String, nullable=False, default="")
    create_datetime: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())
    handle_datetime: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP,
                                                                      nullable=True)