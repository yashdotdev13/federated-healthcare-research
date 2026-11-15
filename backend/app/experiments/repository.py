from uuid import UUID

from sqlalchemy.orm import Session

from app.experiments.models import Experiment, ClientTrainingMetric
from app.experiments.centralized_models import CentralizedEvaluationMetric
from app.experiments.federated_models import FederatedRoundMetric
from app.experiments.privacy_models import PrivacyAccountingMetric


def list_experiments(db: Session) -> list[Experiment]:
    return (
        db.query(Experiment)
        .order_by(Experiment.created_at.desc())
        .all()
    )


def get_experiment(db: Session, experiment_id: UUID) -> Experiment | None:
    return db.query(Experiment).filter(
        Experiment.id == experiment_id
    ).first()


def get_centralized_metric(
    db: Session, experiment_id: UUID
) -> CentralizedEvaluationMetric | None:
    return db.query(CentralizedEvaluationMetric).filter(
        CentralizedEvaluationMetric.experiment_id == experiment_id
    ).first()


def get_federated_rounds(
    db: Session, experiment_id: UUID
) -> list[FederatedRoundMetric]:
    return (
        db.query(FederatedRoundMetric)
        .filter(FederatedRoundMetric.experiment_id == experiment_id)
        .order_by(FederatedRoundMetric.round_number.asc())
        .all()
    )


def get_privacy_metrics(
    db: Session, experiment_id: UUID
) -> list[PrivacyAccountingMetric]:
    return (
        db.query(PrivacyAccountingMetric)
        .filter(PrivacyAccountingMetric.experiment_id == experiment_id)
        .order_by(PrivacyAccountingMetric.round_number.asc())
        .all()
    )


def get_client_metrics(
    db: Session, experiment_id: UUID
) -> list[ClientTrainingMetric]:
    return (
        db.query(ClientTrainingMetric)
        .filter(ClientTrainingMetric.experiment_id == experiment_id)
        .order_by(ClientTrainingMetric.created_at.asc())
        .all()
    )


def list_privacy_metrics(db: Session) -> list[PrivacyAccountingMetric]:
    return (
        db.query(PrivacyAccountingMetric)
        .order_by(PrivacyAccountingMetric.created_at.desc())
        .all()
    )
