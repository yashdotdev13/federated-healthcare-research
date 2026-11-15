from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    algorithm: str
    dataset_name: str
    partition_strategy: str
    client_count: int
    num_rounds: int
    local_epochs: int
    learning_rate: float
    differential_privacy: bool
    dp_noise_multiplier: float | None
    dp_max_grad_norm: float | None
    secure_aggregation: bool
    status: str
    created_at: datetime


class CentralizedMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sample_count: int
    training_loss: float
    training_accuracy: float
    test_accuracy: float
    precision: float
    recall: float
    f1_score: float
    sensitivity: float
    specificity: float
    roc_auc: float
    created_at: datetime


class FederatedRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_number: int
    client_count: int
    total_samples: int
    training_loss: float | None
    training_accuracy: float | None
    test_accuracy: float
    precision: float
    recall: float
    f1_score: float
    sensitivity: float
    specificity: float
    roc_auc: float
    created_at: datetime


class PrivacyMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_number: int
    epsilon: float
    delta: float
    noise_multiplier: float
    steps: int
    optimal_order: float | None
    max_update_norm: float
    max_client_weight: float
    sensitivity: float
    accounting_method: str
    adjacency: str
    created_at: datetime


class ClientTrainingMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    partition_strategy: str
    sample_count: int
    training_loss: float
    training_accuracy: float
    epochs_completed: int
    created_at: datetime


class ExperimentMetricsResponse(BaseModel):
    experiment: ExperimentRead
    centralized: CentralizedMetricRead | None
    federated_rounds: list[FederatedRoundRead]
    privacy_accounting: list[PrivacyMetricRead]
    client_training_metrics: list[ClientTrainingMetricRead]


class ExperimentPerformance(BaseModel):
    experiment_id: UUID
    name: str
    algorithm: str
    test_accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float


class DashboardSummary(BaseModel):
    total_experiments: int
    completed_experiments: int
    participating_clients: int
    best_accuracy: float | None
    latest_epsilon: float | None
    latest_delta: float | None
    performance: list[ExperimentPerformance]
