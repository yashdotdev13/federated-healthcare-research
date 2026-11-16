import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base



class LearningAlgorithm(str, Enum):
    CENTRALIZED = "centralized"
    FEDAVG = "fedavg"
    LOCAL_TRAINING = "local_training"


class PartitionStrategy(str, Enum):
    IID = "iid"
    NON_IID = "non_iid"


class ExperimentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"




class Experiment(Base):
    __tablename__ = "experiments"

    __table_args__ = (
        CheckConstraint(
            "client_count > 0",
            name="ck_experiments_client_count_positive",
        ),
        CheckConstraint(
            "num_rounds > 0",
            name="ck_experiments_rounds_positive",
        ),
        CheckConstraint(
            "local_epochs > 0",
            name="ck_experiments_local_epochs_positive",
        ),
        CheckConstraint(
            "learning_rate > 0",
            name="ck_experiments_learning_rate_positive",
        ),
        CheckConstraint(
            "secure_aggregation = false OR algorithm = 'fedavg'",
            name="ck_experiments_secure_aggregation_fedavg",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    algorithm: Mapped[LearningAlgorithm] = mapped_column(
        SqlEnum(
            LearningAlgorithm,
            name="learning_algorithm",
            native_enum=False,
            length=30,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    dataset_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    partition_strategy: Mapped[PartitionStrategy] = mapped_column(
        SqlEnum(
            PartitionStrategy,
            name="partition_strategy",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )

    client_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    num_rounds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    local_epochs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    learning_rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.01,
    )

    random_seed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=42,
    )

    differential_privacy: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    dp_noise_multiplier: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    dp_max_grad_norm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    secure_aggregation: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    status: Mapped[ExperimentStatus] = mapped_column(
        SqlEnum(
            ExperimentStatus,
            name="experiment_status",
            native_enum=False,
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=ExperimentStatus.CREATED,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )



class ClientTrainingMetric(Base):
    __tablename__ = "client_training_metrics"

    __table_args__ = (
        CheckConstraint(
            "sample_count > 0",
            name="ck_client_metric_sample_count_positive",
        ),
        CheckConstraint(
            "training_accuracy >= 0 AND training_accuracy <= 1",
            name="ck_client_metric_accuracy_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    experiment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "experiments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    client_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    partition_strategy: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
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

    epochs_completed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

