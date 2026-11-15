import uuid
from types import SimpleNamespace

import numpy as np
import pytest

from app.experiments.centralized_models import CentralizedEvaluationMetric
from app.experiments.models import (
    Experiment,
    ExperimentStatus,
    LearningAlgorithm,
    PartitionStrategy,
)
from app.ml.training.local_trainer import LocalTrainingResult
from app.ml.evaluation.evaluator import EvaluationResult
from app.ml.training import run_centralized_experiment as runner


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


def test_centralized_experiment_persists_evaluation_metrics(
    monkeypatch,
    fake_dataset,
):
    session = FakeSession()

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

    training_calls = {}

    def fake_train_local_model(**kwargs):
        training_calls.update(kwargs)

        return LocalTrainingResult(
            state_dict={},
            average_loss=0.25,
            accuracy=0.90,
            sample_count=456,
            epochs_completed=25,
        )

    monkeypatch.setattr(
        runner,
        "train_local_model",
        fake_train_local_model,
    )

    def fake_evaluate_model(model, features, labels):
        assert features is fake_dataset.x_test
        assert labels is fake_dataset.y_test

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

    monkeypatch.setattr(
        runner,
        "evaluate_model",
        fake_evaluate_model,
    )

    experiment_id = runner.run_centralized_experiment()

    assert experiment_id == session.experiment.id

    experiment = session.experiment

    assert experiment.algorithm == LearningAlgorithm.CENTRALIZED
    assert experiment.partition_strategy == PartitionStrategy.IID
    assert experiment.client_count == 1
    assert experiment.num_rounds == 1
    assert experiment.local_epochs == 25
    assert experiment.status == ExperimentStatus.COMPLETED

    assert training_calls["features"] is fake_dataset.x_train
    assert training_calls["labels"] is fake_dataset.y_train
    assert training_calls["epochs"] == 25
    assert training_calls["batch_size"] == 32
    assert training_calls["learning_rate"] == 0.01
    assert training_calls["random_seed"] == 42

    metrics = [
        obj for obj in session.objects
        if isinstance(obj, CentralizedEvaluationMetric)
    ]

    assert len(metrics) == 1

    metric = metrics[0]

    assert metric.experiment_id == experiment_id
    assert metric.sample_count == 113
    assert metric.training_loss == 0.25
    assert metric.training_accuracy == 0.90
    assert metric.test_accuracy == 0.88
    assert metric.precision == 0.90
    assert metric.recall == 0.85
    assert metric.f1_score == 0.87
    assert metric.sensitivity == 0.85
    assert metric.specificity == 0.92
    assert metric.roc_auc == 0.95

    assert session.commit_count == 2
    assert session.rollback_count == 0
    assert session.closed


def test_centralized_experiment_marks_failure(
    monkeypatch,
    fake_dataset,
):
    session = FakeSession()

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

    def failing_training(**kwargs):
        raise RuntimeError("Simulated training failure")

    monkeypatch.setattr(
        runner,
        "train_local_model",
        failing_training,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated training failure",
    ):
        runner.run_centralized_experiment()

    assert session.experiment is not None
    assert session.experiment.status == ExperimentStatus.FAILED

    assert session.rollback_count == 1
    assert session.commit_count == 2
    assert session.closed

    metrics = [
        obj for obj in session.objects
        if isinstance(obj, CentralizedEvaluationMetric)
    ]

    assert metrics == []
