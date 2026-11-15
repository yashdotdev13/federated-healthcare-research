import uuid
from types import SimpleNamespace

import numpy as np
import pytest

from app.experiments.federated_models import FederatedRoundMetric
from app.experiments.models import (
    Experiment,
    ExperimentStatus,
    LearningAlgorithm,
    PartitionStrategy,
)
from app.experiments.privacy_models import PrivacyAccountingMetric
from app.ml.evaluation.evaluator import EvaluationResult
from app.ml.training import run_dp_fedavg_experiment as runner


class FakeSession:

    def __init__(self):
        self.objects = []
        self.experiment = None
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def add(self, obj):
        if isinstance(obj, Experiment):
            obj.id = uuid.uuid4()
            self.experiment = obj

        self.objects.append(obj)

    def add_all(self, objects):
        self.objects.extend(objects)

    def commit(self):
        self.commit_count += 1

    def refresh(self, obj):
        pass

    def get(self, model, identifier):
        if model is Experiment and self.experiment is not None:
            if self.experiment.id == identifier:
                return self.experiment

        return None

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


@pytest.fixture
def fake_dataset():
    rng = np.random.default_rng(42)

    return SimpleNamespace(
        x_train=rng.normal(size=(456, 30)).astype(np.float32),
        y_train=np.array([0, 1] * 228, dtype=np.int64),
        x_test=rng.normal(size=(113, 30)).astype(np.float32),
        y_test=np.array([0, 1] * 56 + [0], dtype=np.int64),
        feature_names=tuple(f"feature_{i}" for i in range(30)),
        class_names=("benign", "malignant"),
    )


@pytest.fixture
def fake_evaluation():
    return EvaluationResult(
        sample_count=113,
        accuracy=0.88,
        precision=0.90,
        recall=0.85,
        f1_score=0.87,
        sensitivity=0.85,
        specificity=0.92,
        roc_auc=0.95,
    )


def configure_common_mocks(
    monkeypatch,
    session,
    fake_dataset,
    fake_evaluation,
):
    monkeypatch.setattr(
        runner,
        "SessionLocal",
        lambda: session,
    )

    monkeypatch.setattr(
        runner,
        "load_breast_cancer_dataset",
        lambda random_seed: fake_dataset,
    )

    monkeypatch.setattr(
        runner,
        "partition_iid",
        lambda labels, num_clients, random_seed: [
            np.arange(0, 152),
            np.arange(152, 304),
            np.arange(304, 456),
        ],
    )

    monkeypatch.setattr(
        runner,
        "evaluate_model",
        lambda model, features, labels: fake_evaluation,
    )


def test_dp_fedavg_experiment_persists_private_metrics(
    monkeypatch,
    fake_dataset,
    fake_evaluation,
):
    session = FakeSession()

    configure_common_mocks(
        monkeypatch,
        session,
        fake_dataset,
        fake_evaluation,
    )

    coordinator_calls = []

    class FakeCoordinator:

        def __init__(self, global_model, clients):
            self.global_model = global_model
            self.clients = clients

        def run_round(self, **kwargs):
            coordinator_calls.append(kwargs)

            return SimpleNamespace(
                round_number=kwargs["round_number"],
                client_count=3,
                total_samples=456,
                average_training_loss=None,
                average_training_accuracy=None,
                clipped_client_count=None,
                max_client_update_norm=None,
                noise_std=2.0 / 3.0,
            )

    monkeypatch.setattr(
        runner,
        "FederatedCoordinator",
        FakeCoordinator,
    )

    experiment_id = runner.run_dp_fedavg_experiment()

    assert experiment_id == session.experiment.id

    experiment = session.experiment

    assert experiment.algorithm == LearningAlgorithm.FEDAVG
    assert experiment.partition_strategy == PartitionStrategy.IID
    assert experiment.client_count == 3
    assert experiment.num_rounds == 5
    assert experiment.local_epochs == 5
    assert experiment.differential_privacy is True
    assert experiment.dp_noise_multiplier == 1.0
    assert experiment.dp_max_grad_norm == 1.0
    assert experiment.secure_aggregation is False
    assert experiment.status == ExperimentStatus.COMPLETED

    assert len(coordinator_calls) == 5

    for index, call in enumerate(coordinator_calls, start=1):
        assert call["round_number"] == index
        assert call["differential_privacy"] is True
        assert call["max_update_norm"] == 1.0
        assert call["noise_multiplier"] == 1.0
        assert call["public_sample_counts"] == (152, 152, 152)

    evaluation_metrics = [
        obj for obj in session.objects
        if isinstance(obj, FederatedRoundMetric)
    ]

    privacy_metrics = [
        obj for obj in session.objects
        if isinstance(obj, PrivacyAccountingMetric)
    ]

    assert len(evaluation_metrics) == 5
    assert len(privacy_metrics) == 5

    for metric in evaluation_metrics:
        assert metric.experiment_id == experiment_id
        assert metric.client_count == 3
        assert metric.total_samples == 456

        assert metric.training_loss is None
        assert metric.training_accuracy is None

        assert metric.test_accuracy == fake_evaluation.accuracy
        assert metric.precision == fake_evaluation.precision
        assert metric.recall == fake_evaluation.recall
        assert metric.f1_score == fake_evaluation.f1_score
        assert metric.roc_auc == fake_evaluation.roc_auc

    assert [metric.round_number for metric in privacy_metrics] == [
        1, 2, 3, 4, 5
    ]

    epsilons = [metric.epsilon for metric in privacy_metrics]

    assert all(
        current > previous
        for previous, current in zip(epsilons, epsilons[1:])
    )

    for index, metric in enumerate(privacy_metrics, start=1):
        assert metric.experiment_id == experiment_id
        assert metric.steps == index
        assert metric.delta == 1e-5
        assert metric.noise_multiplier == 1.0
        assert metric.max_update_norm == 1.0
        assert metric.max_client_weight == pytest.approx(1.0 / 3.0)
        assert metric.sensitivity == pytest.approx(2.0 / 3.0)
        assert metric.accounting_method == "rdp_gaussian_full_participation"
        assert metric.adjacency == "replace_one_client"
        assert metric.optimal_order is not None

    assert session.commit_count == 7
    assert session.rollback_count == 0
    assert session.closed


def test_dp_fedavg_experiment_marks_failure(
    monkeypatch,
    fake_dataset,
    fake_evaluation,
):
    session = FakeSession()

    configure_common_mocks(
        monkeypatch,
        session,
        fake_dataset,
        fake_evaluation,
    )

    class FailingCoordinator:

        def __init__(self, global_model, clients):
            pass

        def run_round(self, **kwargs):
            raise RuntimeError("Simulated DP round failure")

    monkeypatch.setattr(
        runner,
        "FederatedCoordinator",
        FailingCoordinator,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated DP round failure",
    ):
        runner.run_dp_fedavg_experiment()

    assert session.experiment is not None
    assert session.experiment.status == ExperimentStatus.FAILED

    assert session.rollback_count == 1
    assert session.commit_count == 2
    assert session.closed

    evaluation_metrics = [
        obj for obj in session.objects
        if isinstance(obj, FederatedRoundMetric)
    ]

    privacy_metrics = [
        obj for obj in session.objects
        if isinstance(obj, PrivacyAccountingMetric)
    ]

    assert evaluation_metrics == []
    assert privacy_metrics == []
