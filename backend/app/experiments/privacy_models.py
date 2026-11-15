import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrivacyAccountingMetric(Base):
    __tablename__ = "privacy_accounting_metrics"

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "round_number",
            name="uq_privacy_accounting_experiment_round",
        ),
        CheckConstraint(
            "round_number > 0 AND steps > 0",
            name="ck_privacy_accounting_round_steps_positive",
        ),
        CheckConstraint(
            "epsilon >= 0 AND delta > 0 AND delta < 1",
            name="ck_privacy_accounting_epsilon_delta",
        ),
        CheckConstraint(
            """
            noise_multiplier > 0
            AND max_update_norm > 0
            AND max_client_weight > 0
            AND max_client_weight <= 1
            AND sensitivity > 0
            """,
            name="ck_privacy_accounting_parameters_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    epsilon: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    delta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    noise_multiplier: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    steps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    optimal_order: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    max_update_norm: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    max_client_weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    sensitivity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    accounting_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    adjacency: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
