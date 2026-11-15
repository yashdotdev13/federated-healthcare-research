import logging
import uuid

import torch

from app.core.database import SessionLocal
from app.experiments.federated_models import FederatedRoundMetric
from app.experiments.models import (
    Experiment,
    ExperimentStatus,
    LearningAlgorithm,
    PartitionStrategy,
)
from app.ml.data.dataset import load_breast_cancer_dataset
from app.ml.data.partitioner import partition_iid
from app.ml.evaluation.evaluator import evaluate_model
from app.ml.federation.coordinator import FederatedCoordinator
from app.ml.clients.hospital_client import HospitalClient
from app.ml.models.diagnostic_model import DiagnosticMLP


logger = logging.getLogger(__name__)

# ============================================================
# EXPERIMENT CONFIGURATION
# ============================================================

NUM_CLIENTS = 3
NUM_ROUNDS = 5
LOCAL_EPOCHS = 5
BATCH_SIZE = 32
LEARNING_RATE = 0.01
RANDOM_SEED = 42

DATASET_NAME = "Wisconsin Diagnostic Breast Cancer"
EXPERIMENT_NAME = "FedAvg - Five Communication Rounds"


# ============================================================
# EXPERIMENT ORCHESTRATOR
# ============================================================

def run_fedavg_experiment() -> uuid.UUID:
    """
    Execute five rounds of Federated Averaging across
    three simulated hospitals using the WDBC dataset.

    Each round:
        1. Trains hospital models locally.
        2. Aggregates model parameters using FedAvg.
        3. Evaluates the updated global model.
        4. Persists round-level training and test metrics.
    """

    db = SessionLocal()
    experiment_id = None

    try:
        # ----------------------------------------------------
        # 1. Load and partition the benchmark dataset
        # ----------------------------------------------------

        logger.info("Loading dataset: %s", DATASET_NAME)

        dataset = load_breast_cancer_dataset(
            random_seed=RANDOM_SEED,
        )

        partitions = partition_iid(
            labels=dataset.y_train,
            num_clients=NUM_CLIENTS,
            random_seed=RANDOM_SEED,
        )

        if len(partitions) != NUM_CLIENTS:
            raise RuntimeError("Unexpected number of hospital partitions")

        logger.info(
            "Dataset loaded: training=%d, test=%d, hospitals=%d",
            len(dataset.x_train),
            len(dataset.x_test),
            NUM_CLIENTS,
        )

        # ----------------------------------------------------
        # 2. Create the experiment record
        # ----------------------------------------------------

        experiment = Experiment(
            name=EXPERIMENT_NAME,
            description=(
                "Five-round sample-weighted Federated Averaging "
                "across three simulated hospitals using IID "
                "partitions of the WDBC dataset. No differential "
                "privacy or secure aggregation is enabled."
            ),
            algorithm=LearningAlgorithm.FEDAVG,
            dataset_name=DATASET_NAME,
            partition_strategy=PartitionStrategy.IID,
            client_count=NUM_CLIENTS,
            num_rounds=NUM_ROUNDS,
            local_epochs=LOCAL_EPOCHS,
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
            "FedAvg experiment created. ID: %s",
            experiment_id,
        )

        # ----------------------------------------------------
        # 3. Initialize the global model
        # ----------------------------------------------------

        torch.manual_seed(RANDOM_SEED)

        global_model = DiagnosticMLP(
            input_dim=len(dataset.feature_names),
            num_classes=len(dataset.class_names),
        )

        # ----------------------------------------------------
        # 4. Create simulated hospital clients
        # ----------------------------------------------------

        clients = [
            HospitalClient(
                client_id=f"hospital-{index + 1}",
                x_train=dataset.x_train[indices],
                y_train=dataset.y_train[indices],
            )
            for index, indices in enumerate(partitions)
        ]

        coordinator = FederatedCoordinator(
            global_model=global_model,
            clients=clients,
        )

        # ----------------------------------------------------
        # 5. Execute federated communication rounds
        # ----------------------------------------------------

        round_metrics = []

        for round_number in range(1, NUM_ROUNDS + 1):

            logger.info(
                "Starting federated round %d/%d",
                round_number,
                NUM_ROUNDS,
            )

            round_result = coordinator.run_round(
                round_number=round_number,
                local_epochs=LOCAL_EPOCHS,
                batch_size=BATCH_SIZE,
                learning_rate=LEARNING_RATE,
                random_seed=RANDOM_SEED,
            )

            # Evaluate the updated global model on held-out data.
            evaluation = evaluate_model(
                model=global_model,
                features=dataset.x_test,
                labels=dataset.y_test,
            )

            metric = FederatedRoundMetric(
                experiment_id=experiment_id,
                round_number=round_result.round_number,
                client_count=round_result.client_count,
                total_samples=round_result.total_samples,
                training_loss=round_result.average_training_loss,
                training_accuracy=round_result.average_training_accuracy,
                test_accuracy=evaluation.accuracy,
                precision=evaluation.precision,
                recall=evaluation.recall,
                f1_score=evaluation.f1_score,
                sensitivity=evaluation.sensitivity,
                specificity=evaluation.specificity,
                roc_auc=evaluation.roc_auc,
            )

            round_metrics.append(metric)

            logger.info(
                (
                    "Round %d completed | samples=%d | "
                    "training_loss=%.4f | training_accuracy=%.4f | "
                    "test_accuracy=%.4f | precision=%.4f | "
                    "recall=%.4f | f1=%.4f | roc_auc=%.4f"
                ),
                round_number,
                round_result.total_samples,
                round_result.average_training_loss,
                round_result.average_training_accuracy,
                evaluation.accuracy,
                evaluation.precision,
                evaluation.recall,
                evaluation.f1_score,
                evaluation.roc_auc,
            )

        # ----------------------------------------------------
        # 6. Validate completed rounds
        # ----------------------------------------------------

        if len(round_metrics) != NUM_ROUNDS:
            raise RuntimeError(
                "Not all federated rounds completed successfully"
            )

        if any(
            metric.total_samples != len(dataset.x_train)
            for metric in round_metrics
        ):
            raise RuntimeError(
                "Federated rounds did not process all training samples"
            )

        # ----------------------------------------------------
        # 7. Persist all round metrics and complete experiment
        # ----------------------------------------------------

        db.add_all(round_metrics)

        experiment = db.get(Experiment, experiment_id)

        if experiment is None:
            raise RuntimeError("Experiment record disappeared")

        experiment.status = ExperimentStatus.COMPLETED

        db.commit()

        logger.info(
            "Persisted %d federated round metrics.",
            len(round_metrics),
        )

        logger.info(
            "FedAvg experiment completed successfully. ID: %s",
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

        logger.exception("FedAvg experiment failed")
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

    run_fedavg_experiment()
