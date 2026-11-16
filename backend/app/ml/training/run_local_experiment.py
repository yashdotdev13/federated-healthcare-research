
import logging
import uuid

import torch

from app.core.database import SessionLocal
from app.experiments.models import (
    ClientTrainingMetric,
    Experiment,
    ExperimentStatus,
    LearningAlgorithm,
    PartitionStrategy,
)
from app.ml.clients.hospital_client import HospitalClient
from app.ml.data.dataset import load_breast_cancer_dataset
from app.ml.data.partitioner import partition_iid
from app.ml.models.diagnostic_model import DiagnosticMLP


logger = logging.getLogger(__name__)



NUM_CLIENTS = 3
LOCAL_EPOCHS = 5
BATCH_SIZE = 32
LEARNING_RATE = 0.01
RANDOM_SEED = 42

DATASET_NAME = "Wisconsin Diagnostic Breast Cancer"
EXPERIMENT_NAME = "Initial Hospital Local Training"



def run_local_experiment() -> uuid.UUID:
    """
    Execute independent local training across simulated hospitals.

    Workflow:
        1. Load and preprocess the benchmark dataset.
        2. Partition training samples across hospitals.
        3. Persist experiment metadata.
        4. Initialize a common starting model.
        5. Train each hospital independently.
        6. Persist hospital training metrics.
        7. Mark the experiment as completed or failed.

    Note:
        This experiment performs independent local training only.
        It does not perform FedAvg or global model aggregation.
    """

    db = SessionLocal()
    experiment_id: uuid.UUID | None = None

    try:

        logger.info("Loading dataset: %s", DATASET_NAME)

        dataset = load_breast_cancer_dataset(
            random_seed=RANDOM_SEED,
        )

        logger.info(
            "Dataset loaded: %d training samples, %d test samples",
            len(dataset.x_train),
            len(dataset.x_test),
        )

        partitions = partition_iid(
            labels=dataset.y_train,
            num_clients=NUM_CLIENTS,
            random_seed=RANDOM_SEED,
        )

        if len(partitions) != NUM_CLIENTS:
            raise RuntimeError("Unexpected number of hospital partitions")

        logger.info(
            "Training data partitioned across %d hospitals",
            NUM_CLIENTS,
        )

        experiment = Experiment(
            name=EXPERIMENT_NAME,
            description=(
                "Independent local model training across three "
                "simulated hospitals using the WDBC dataset."
            ),
            algorithm=LearningAlgorithm.LOCAL_TRAINING,
            dataset_name=DATASET_NAME,
            partition_strategy=PartitionStrategy.IID,
            client_count=NUM_CLIENTS,
            num_rounds=1,
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
            "Experiment created successfully. ID: %s",
            experiment_id,
        )


        torch.manual_seed(RANDOM_SEED)

        initial_model = DiagnosticMLP(
            input_dim=len(dataset.feature_names),
            num_classes=len(dataset.class_names),
        )

        # Keep an immutable snapshot for verification.
        initial_state = {
            name: tensor.detach().clone()
            for name, tensor in initial_model.state_dict().items()
        }


        clients = [
            HospitalClient(
                client_id=f"hospital-{index + 1}",
                x_train=dataset.x_train[indices],
                y_train=dataset.y_train[indices],
            )
            for index, indices in enumerate(partitions)
        ]

        logger.info(
            "Created %d simulated hospital clients",
            len(clients),
        )


        training_results = []

        for client in clients:

            logger.info(
                "Starting local training for %s",
                client.client_id,
            )

            result = client.train(
                initial_model=initial_model,
                epochs=LOCAL_EPOCHS,
                batch_size=BATCH_SIZE,
                learning_rate=LEARNING_RATE,
                random_seed=RANDOM_SEED,
            )

            training_results.append(result)

            logger.info(
                "%s completed: samples=%d, loss=%.4f, accuracy=%.4f",
                client.client_id,
                result.sample_count,
                result.average_loss,
                result.accuracy,
            )


            metric = ClientTrainingMetric(
                experiment_id=experiment_id,
                client_id=client.client_id,
                partition_strategy=PartitionStrategy.IID.value,
                sample_count=result.sample_count,
                training_loss=result.average_loss,
                training_accuracy=result.accuracy,
                epochs_completed=result.epochs_completed,
            )

            db.add(metric)

        if len(training_results) != NUM_CLIENTS:
            raise RuntimeError(
                "Not all hospital clients completed training"
            )

        if any(
            result.epochs_completed != LOCAL_EPOCHS
            for result in training_results
        ):
            raise RuntimeError(
                "At least one hospital did not complete all local epochs"
            )

        # Verify that local training did not modify the original model.
        for name, tensor in initial_model.state_dict().items():
            if not torch.equal(tensor, initial_state[name]):
                raise RuntimeError(
                    f"Initial global model was unexpectedly modified: {name}"
                )


        experiment = db.get(Experiment, experiment_id)

        if experiment is None:
            raise RuntimeError("Experiment record disappeared")

        experiment.status = ExperimentStatus.COMPLETED

        db.commit()

        logger.info(
            "All hospital metrics persisted successfully."
        )

        logger.info(
            "Experiment completed successfully. ID: %s",
            experiment_id,
        )

        return experiment_id

    except Exception:
        db.rollback()

        # The experiment record was committed before training.
        # Update its status in a separate transaction.
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

        logger.exception(
            "Local training experiment failed"
        )

        raise

    finally:
        db.close()



if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    run_local_experiment()
