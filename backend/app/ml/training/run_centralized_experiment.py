import logging
import uuid

import torch

from app.core.database import SessionLocal
from app.experiments.centralized_models import CentralizedEvaluationMetric
from app.experiments.models import (
    Experiment,
    ExperimentStatus,
    LearningAlgorithm,
    PartitionStrategy,
)
from app.ml.data.dataset import load_breast_cancer_dataset
from app.ml.evaluation.evaluator import evaluate_model
from app.ml.models.diagnostic_model import DiagnosticMLP
from app.ml.training.local_trainer import train_local_model


logger = logging.getLogger(__name__)

# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

EPOCHS = 25
BATCH_SIZE = 32
LEARNING_RATE = 0.01
RANDOM_SEED = 42

DATASET_NAME = "Wisconsin Diagnostic Breast Cancer"
EXPERIMENT_NAME = "Centralized Training Baseline"


# ============================================================
# EXPERIMENT ORCHESTRATOR
# ============================================================

def run_centralized_experiment() -> uuid.UUID:
    """
    Train a centralized diagnostic model using the complete
    training dataset and evaluate it on held-out test data.
    """

    db = SessionLocal()
    experiment_id = None

    try:
        # ----------------------------------------------------
        # 1. Load benchmark dataset
        # ----------------------------------------------------

        logger.info("Loading dataset: %s", DATASET_NAME)

        dataset = load_breast_cancer_dataset(
            random_seed=RANDOM_SEED,
        )

        logger.info(
            "Dataset loaded: training=%d, test=%d",
            len(dataset.x_train),
            len(dataset.x_test),
        )

        # ----------------------------------------------------
        # 2. Create experiment record
        # ----------------------------------------------------

        experiment = Experiment(
            name=EXPERIMENT_NAME,
            description=(
                "Centralized training baseline using all WDBC "
                "training samples, the DiagnosticMLP architecture, "
                "and 25 training epochs. Uses the same stratified "
                "train/test split and random seed as the FedAvg "
                "baseline."
            ),
            algorithm=LearningAlgorithm.CENTRALIZED,
            dataset_name=DATASET_NAME,
            partition_strategy=PartitionStrategy.IID,
            client_count=1,
            num_rounds=1,
            local_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            random_seed=RANDOM_SEED,
            differential_privacy=False,
            secure_aggregation=False,
            status=ExperimentStatus.RUNNING,
        )

        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        experiment_id = experiment.id

        logger.info(
            "Centralized experiment created. ID: %s",
            experiment_id,
        )

        # ----------------------------------------------------
        # 3. Initialize centralized model
        # ----------------------------------------------------

        torch.manual_seed(RANDOM_SEED)

        model = DiagnosticMLP(
            input_dim=len(dataset.feature_names),
            num_classes=len(dataset.class_names),
        )

        # ----------------------------------------------------
        # 4. Train using the complete training dataset
        # ----------------------------------------------------

        logger.info(
            "Starting centralized training: epochs=%d, samples=%d",
            EPOCHS,
            len(dataset.x_train),
        )

        training_result = train_local_model(
            model=model,
            features=dataset.x_train,
            labels=dataset.y_train,
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            learning_rate=LEARNING_RATE,
            random_seed=RANDOM_SEED,
        )

        logger.info(
            "Centralized training completed: loss=%.4f, accuracy=%.4f",
            training_result.average_loss,
            training_result.accuracy,
        )

        if training_result.sample_count != len(dataset.x_train):
            raise RuntimeError(
                "Centralized training did not process all training samples"
            )

        if training_result.epochs_completed != EPOCHS:
            raise RuntimeError(
                "Centralized training did not complete all epochs"
            )

        # ----------------------------------------------------
        # 5. Evaluate on held-out test dataset
        # ----------------------------------------------------

        evaluation = evaluate_model(
            model=model,
            features=dataset.x_test,
            labels=dataset.y_test,
        )

        logger.info(
            (
                "Centralized evaluation | accuracy=%.4f | "
                "precision=%.4f | recall=%.4f | "
                "f1=%.4f | roc_auc=%.4f"
            ),
            evaluation.accuracy,
            evaluation.precision,
            evaluation.recall,
            evaluation.f1_score,
            evaluation.roc_auc,
        )

        # ----------------------------------------------------
        # 6. Persist centralized evaluation metrics
        # ----------------------------------------------------

        metric = CentralizedEvaluationMetric(
            experiment_id=experiment_id,
            sample_count=evaluation.sample_count,
            training_loss=training_result.average_loss,
            training_accuracy=training_result.accuracy,
            test_accuracy=evaluation.accuracy,
            precision=evaluation.precision,
            recall=evaluation.recall,
            f1_score=evaluation.f1_score,
            sensitivity=evaluation.sensitivity,
            specificity=evaluation.specificity,
            roc_auc=evaluation.roc_auc,
        )

        db.add(metric)

        # ----------------------------------------------------
        # 7. Complete experiment
        # ----------------------------------------------------

        experiment = db.get(Experiment, experiment_id)

        if experiment is None:
            raise RuntimeError("Experiment record disappeared")

        experiment.status = ExperimentStatus.COMPLETED

        db.commit()

        logger.info(
            "Centralized evaluation metrics persisted successfully."
        )

        logger.info(
            "Centralized experiment completed. ID: %s",
            experiment_id,
        )

        return experiment_id

    except Exception:
        db.rollback()

        if experiment_id is not None:
            try:
                failed_experiment = db.get(
                    Experiment,
                    experiment_id,
                )

                if failed_experiment is not None:
                    failed_experiment.status = ExperimentStatus.FAILED
                    db.commit()

            except Exception:
                db.rollback()
                logger.exception(
                    "Could not persist experiment failure status"
                )

        logger.exception("Centralized experiment failed")
        raise

    finally:
        db.close()


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    run_centralized_experiment()
