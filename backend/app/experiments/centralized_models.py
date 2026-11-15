import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CentralizedEvaluationMetric(Base):
    __tablename__ = "centralized_evaluation_metrics"

    __table_args__ = (
        UniqueConstraint(
            "experiment_id",
            name="uq_centralized_evaluation_experiment",
        ),
        CheckConstraint(
            "sample_count > 0",
            name="ck_centralized_evaluation_sample_count_positive",
        ),
        CheckConstraint(
            """
            training_accuracy BETWEEN 0 AND 1
            AND test_accuracy BETWEEN 0 AND 1
            AND precision BETWEEN 0 AND 1
            AND recall BETWEEN 0 AND 1
            AND f1_score BETWEEN 0 AND 1
            AND sensitivity BETWEEN 0 AND 1
            AND specificity BETWEEN 0 AND 1
            AND roc_auc BETWEEN 0 AND 1
            """,
            name="ck_centralized_evaluation_metrics_range",
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

    sample_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    training_loss: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    training_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    test_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    precision: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    recall: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    f1_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    sensitivity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    specificity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    roc_auc: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
