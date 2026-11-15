import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FederatedRoundMetric(Base):
    __tablename__ = "federated_round_metrics"

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            "round_number",
            name="uq_federated_round_experiment_number",
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

    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    client_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_samples: Mapped[int] = mapped_column(Integer, nullable=False)

    training_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)

    test_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    sensitivity: Mapped[float] = mapped_column(Float, nullable=False)
    specificity: Mapped[float] = mapped_column(Float, nullable=False)
    roc_auc: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

