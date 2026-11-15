import logging
import math
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
from app.experiments.privacy_models import PrivacyAccountingMetric
from app.ml.data.dataset import load_breast_cancer_dataset
from app.ml.data.partitioner import partition_iid
from app.ml.evaluation.evaluator import evaluate_model
from app.ml.federation.coordinator import FederatedCoordinator
from app.ml.clients.hospital_client import HospitalClient
from app.ml.models.diagnostic_model import DiagnosticMLP
from app.ml.privacy.privacy_accountant import compute_rdp_epsilon


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

MAX_UPDATE_NORM = 1.0
NOISE_MULTIPLIER = 1.0
DELTA = 1e-5

PUBLIC_SAMPLE_COUNTS = (152, 152, 152)

DATASET_NAME = "Wisconsin Diagnostic Breast Cancer"
EXPERIMENT_NAME = "DP-FedAvg - Five Communication Rounds"

ACCOUNTING_METHOD = "rdp_gaussian_full_participation"
ADJACENCY = "replace_one_client"


# ============================================================
# EXPERIMENT ORCHESTRATOR
# ============================================================

def run_dp_fedavg_experiment() -> uuid.UUID:
    """
    Execute differentially private Federated Averaging.

    Each communication round:
        1. Trains hospital models locally.
        2. Clips client model updates.
        3. Aggregates updates using fixed public weights.
        4. Adds Gaussian noise to the aggregate update.
        5. Evaluates the updated global model.
        6. Computes cumulative RDP privacy expenditure.
        7. Persists evaluation and privacy metrics.

    The held-out WDBC benchmark is public. The privacy accounting
    concerns client-level training data under the configured
    fixed-weight, full-participation assumptions.
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
            raise RuntimeError(
                "Unexpected number of hospital partitions"
            )

        actual_partition_counts = tuple(
            len(indices) for indices in partitions
        )

        if actual_partition_counts != PUBLIC_SAMPLE_COUNTS:
            raise RuntimeError(
                "Dataset partition sizes do not match the "
                "configured public sample counts"
            )

        if sum(PUBLIC_SAMPLE_COUNTS) != len(dataset.x_train):
            raise RuntimeError(
                "Public sample counts do not match the training dataset"
            )

        logger.info(
            "Dataset loaded: training=%d, test=%d, hospitals=%d",
            len(dataset.x_train),
            len(dataset.x_test),
            NUM_CLIENTS,
        )

        # ----------------------------------------------------
        # 2. Calculate public aggregation sensitivity
        # ----------------------------------------------------

        total_public_samples = sum(PUBLIC_SAMPLE_COUNTS)

        max_client_weight = (
            max(PUBLIC_SAMPLE_COUNTS) / total_public_samples
        )

        sensitivity = (
            2.0 * MAX_UPDATE_NORM * max_client_weight
        )

        if not math.isfinite(sensitivity) or sensitivity <= 0:
            raise RuntimeError(
                "Invalid aggregate sensitivity calculation"
            )

        # ----------------------------------------------------
        # 3. Create the experiment record
        # ----------------------------------------------------

        experiment = Experiment(
            name=EXPERIMENT_NAME,
            description=(
                "Five-round client-level differentially private "
                "FedAvg experiment using three simulated hospitals, "
                "IID WDBC partitions, client-update clipping, and "
                "Gaussian noise. Uses fixed public aggregation weights "
                "and full client participation. Secure aggregation "
                "is not enabled."
            ),
            algorithm=LearningAlgorithm.FEDAVG,
            dataset_name=DATASET_NAME,
            partition_strategy=PartitionStrategy.IID,
            client_count=NUM_CLIENTS,
            num_rounds=NUM_ROUNDS,
            local_epochs=LOCAL_EPOCHS,
            learning_rate=LEARNING_RATE,
            random_seed=RANDOM_SEED,
            differential_privacy=True,
            dp_noise_multiplier=NOISE_MULTIPLIER,
            dp_max_grad_norm=MAX_UPDATE_NORM,
            secure_aggregation=False,
            status=ExperimentStatus.RUNNING,
        )

        db.add(experiment)
        db.commit()
        db.refresh(experiment)

        experiment_id = experiment.id

        logger.info(
            "DP-FedAvg experiment created. ID: %s",
            experiment_id,
        )

        # ----------------------------------------------------
        # 4. Initialize global model
        # ----------------------------------------------------

        torch.manual_seed(RANDOM_SEED)

        global_model = DiagnosticMLP(
            input_dim=len(dataset.feature_names),
            num_classes=len(dataset.class_names),
        )

        # ----------------------------------------------------
        # 5. Create simulated hospital clients
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
        # 6. Execute private federated communication rounds
        # ----------------------------------------------------

        for round_number in range(1, NUM_ROUNDS + 1):

            logger.info(
                "Starting DP federated round %d/%d",
                round_number,
                NUM_ROUNDS,
            )

            round_result = coordinator.run_round(
                round_number=round_number,
                local_epochs=LOCAL_EPOCHS,
                batch_size=BATCH_SIZE,
                learning_rate=LEARNING_RATE,
                random_seed=RANDOM_SEED,
                differential_privacy=True,
                max_update_norm=MAX_UPDATE_NORM,
                noise_multiplier=NOISE_MULTIPLIER,
                public_sample_counts=PUBLIC_SAMPLE_COUNTS,
            )

            if round_result.noise_std is None:
                raise RuntimeError(
                    "DP coordinator did not return Gaussian noise scale"
                )

            if round_result.total_samples != total_public_samples:
                raise RuntimeError(
                    "Unexpected sample count in DP aggregation"
                )

            # ------------------------------------------------
            # 7. Evaluate the updated global model
            # ------------------------------------------------

            evaluation = evaluate_model(
                model=global_model,
                features=dataset.x_test,
                labels=dataset.y_test,
            )

            # ------------------------------------------------
            # 8. Calculate cumulative privacy expenditure
            # ------------------------------------------------

            privacy_result = compute_rdp_epsilon(
                noise_multiplier=NOISE_MULTIPLIER,
                steps=round_number,
                delta=DELTA,
            )

            if not math.isfinite(privacy_result.epsilon):
                raise RuntimeError(
                    "Privacy accountant returned non-finite epsilon"
                )

            # ------------------------------------------------
            # 9. Prepare evaluation metrics
            # ------------------------------------------------

            round_metric = FederatedRoundMetric(
                experiment_id=experiment_id,
                round_number=round_number,
                client_count=round_result.client_count,
                total_samples=round_result.total_samples,

                # Raw training metrics are deliberately not released.
                training_loss=None,
                training_accuracy=None,

                test_accuracy=evaluation.accuracy,
                precision=evaluation.precision,
                recall=evaluation.recall,
                f1_score=evaluation.f1_score,
                sensitivity=evaluation.sensitivity,
                specificity=evaluation.specificity,
                roc_auc=evaluation.roc_auc,
            )

            # ------------------------------------------------
            # 10. Prepare privacy accounting metrics
            # ------------------------------------------------

            privacy_metric = PrivacyAccountingMetric(
                experiment_id=experiment_id,
                round_number=round_number,
                epsilon=privacy_result.epsilon,
                delta=privacy_result.delta,
                noise_multiplier=privacy_result.noise_multiplier,
                steps=privacy_result.steps,
                optimal_order=privacy_result.optimal_order,
                max_update_norm=MAX_UPDATE_NORM,
                max_client_weight=max_client_weight,
                sensitivity=sensitivity,
                accounting_method=ACCOUNTING_METHOD,
                adjacency=ADJACENCY,
            )

            # Persist each completed round independently.
            db.add_all([round_metric, privacy_metric])
            db.commit()

            logger.info(
                (
                    "DP round %d completed | "
                    "test_accuracy=%.4f | "
                    "f1=%.4f | roc_auc=%.4f | "
                    "epsilon=%.6f | delta=%.8f"
                ),
                round_number,
                evaluation.accuracy,
                evaluation.f1_score,
                evaluation.roc_auc,
                privacy_result.epsilon,
                privacy_result.delta,
            )

        # ----------------------------------------------------
        # 11. Validate persisted experiment results
        # ----------------------------------------------------

        experiment = db.get(Experiment, experiment_id)

        if experiment is None:
            raise RuntimeError("Experiment record disappeared")

        experiment.status = ExperimentStatus.COMPLETED
        db.commit()

        logger.info(
            "DP-FedAvg experiment completed successfully. ID: %s",
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

        logger.exception("DP-FedAvg experiment failed")
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

    run_dp_fedavg_experiment()
