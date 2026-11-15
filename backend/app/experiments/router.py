from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.experiments import service
from app.experiments.schemas import (
    DashboardSummary,
    ExperimentMetricsResponse,
    ExperimentRead,
)

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    return service.get_dashboard_summary(db)


@router.get("", response_model=list[ExperimentRead])
def list_experiments(db: Session = Depends(get_db)):
    return service.list_experiments(db)


@router.get(
    "/{experiment_id}/metrics",
    response_model=ExperimentMetricsResponse,
)
def experiment_metrics(
    experiment_id: UUID,
    db: Session = Depends(get_db),
):
    result = service.get_experiment_metrics(db, experiment_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return result


@router.get("/{experiment_id}", response_model=ExperimentRead)
def experiment_details(
    experiment_id: UUID,
    db: Session = Depends(get_db),
):
    experiment = service.repository.get_experiment(db, experiment_id)

    if experiment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    return experiment
