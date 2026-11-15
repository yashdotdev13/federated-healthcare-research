from uuid import UUID

from sqlalchemy.orm import Session

from app.experiments import repository
from app.experiments.models import ExperimentStatus
from app.experiments.schemas import (
    DashboardSummary,
    ExperimentMetricsResponse,
    ExperimentPerformance,
)


def list_experiments(db: Session):
    return repository.list_experiments(db)


def get_experiment_metrics(
    db: Session, experiment_id: UUID
) -> ExperimentMetricsResponse | None:
    experiment = repository.get_experiment(db, experiment_id)

    if experiment is None:
        return None

    return ExperimentMetricsResponse(
        experiment=experiment,
        centralized=repository.get_centralized_metric(db, experiment_id),
        federated_rounds=repository.get_federated_rounds(db, experiment_id),
        privacy_accounting=repository.get_privacy_metrics(db, experiment_id),
        client_training_metrics=repository.get_client_metrics(db, experiment_id),
    )


def get_dashboard_summary(db: Session) -> DashboardSummary:
    experiments = repository.list_experiments(db)

    performance = []

    for experiment in experiments:
        centralized = repository.get_centralized_metric(db, experiment.id)
        rounds = repository.get_federated_rounds(db, experiment.id)

        metric = centralized if centralized is not None else (
            rounds[-1] if rounds else None
        )

        if metric is not None:
            performance.append(
                ExperimentPerformance(
                    experiment_id=experiment.id,
                    name=experiment.name,
                    algorithm=experiment.algorithm.value,
                    test_accuracy=metric.test_accuracy,
                    precision=metric.precision,
                    recall=metric.recall,
                    f1_score=metric.f1_score,
                    roc_auc=metric.roc_auc,
                )
            )

    privacy_metrics = repository.list_privacy_metrics(db)
    latest_privacy = privacy_metrics[0] if privacy_metrics else None

    completed = [
        experiment
        for experiment in experiments
        if experiment.status == ExperimentStatus.COMPLETED
    ]

    participating_clients = max(
        (experiment.client_count for experiment in completed),
        default=0,
    )

    best_accuracy = max(
        (item.test_accuracy for item in performance),
        default=None,
    )

    return DashboardSummary(
        total_experiments=len(experiments),
        completed_experiments=len(completed),
        participating_clients=participating_clients,
        best_accuracy=best_accuracy,
        latest_epsilon=latest_privacy.epsilon if latest_privacy else None,
        latest_delta=latest_privacy.delta if latest_privacy else None,
        performance=performance,
    )
